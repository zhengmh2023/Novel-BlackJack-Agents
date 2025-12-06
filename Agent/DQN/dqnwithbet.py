import random
from collections import deque, namedtuple
from typing import Tuple, List, Union

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import trange

from Game.BlackJack import BlackJack

# --------------------------------------------------
#  Casino wrapper to add fixed bet rule + bankroll
# --------------------------------------------------

class CasinoBlackJack(BlackJack):
    """BlackJack environment with bankrolls and the user-supplied betrule.
    The game is one round per reset(); when the round ends we call settle()."""

    def __init__(
        self,
        player_bank: float = 10_000.0,
        dealer_bank: float = 5_000_000.0,
        mode: str = "novel",
    ):
        super().__init__(mode)
        self.init_player_bank = player_bank
        self.init_dealer_bank = dealer_bank
        self.player_bank: float = player_bank
        self.dealer_bank: float = dealer_bank
        self.win_cnt = 0
        self.lose_cnt = 0

    # -----------------------------
    #  Fixed betting rule provided by user
    # -----------------------------

    def betrule(self) -> float:
        bet = min(0.1 * self.player_bank, 0.1 * self.dealer_bank)

        # extra multipliers based on cards
        if self.player_hand and (self.player_hand[0]["number"] == "10" or self.player_hand[1]["number"] == "10"):
            bet *= 1.5
        if self.dealer_hand and self.dealer_hand[0]["number"] == "10":
            bet *= 0.75
        if self.win_cnt >= 5:
            bet *= 1.5
        if self.lose_cnt >= 5:
            bet *= 0.5

        bet *= random.choice([1, 1.1, 0.9])
        # Ensure bet is not more than either bankroll (sanity)
        bet = max(1.0, min(bet, self.player_bank, self.dealer_bank))
        return bet

    # -----------------------------
    #  Bankroll settlement
    # -----------------------------

    def settle(self, result: str, bet: float):
        if result == "win":
            self.player_bank += bet
            self.dealer_bank -= bet
            self.win_cnt += 1
            self.lose_cnt = 0
        elif result == "lose":
            self.player_bank -= bet
            self.dealer_bank += bet
            self.lose_cnt += 1
            self.win_cnt = 0
        else:  # draw
            self.win_cnt = 0
            self.lose_cnt = 0

    # -----------------------------
    #  Override reset to keep bankrolls
    # -----------------------------

    def reset_round(self):
        """Reset only deck / hands / status, keep bankroll & streaks."""
        super().reset()

    def full_reset(self):
        """Hard reset bankroll & streaks as well (for new simulation batch)."""
        self.player_bank = self.init_player_bank
        self.dealer_bank = self.init_dealer_bank
        self.win_cnt = 0
        self.lose_cnt = 0
        super().reset()


# --------------------------------------------------
#  Helper functions
# --------------------------------------------------

def has_usable_ace(hand: List[dict]) -> int:
    value, ace = 0, False
    for card in hand:
        num = card["number"]
        if num == "A":
            value += 11
            ace = True
        elif num in ["J", "Q", "K"]:
            value += 10
        else:
            value += int(num)
    return int(ace and value + 10 <= 21)


def extract_state(env: CasinoBlackJack) -> np.ndarray:
    """Return 7-D state vector, normalized to ~[0,1]."""
    player_sum = min(env.get_playervalue(), 32) / 32.0
    dealer_up = min(env.total_value(env.dealer_hand[:1]), 11) / 11.0
    usable = float(has_usable_ace(env.player_hand))
    player_ratio = env.player_bank / env.init_player_bank  # ~ [0, >1]
    dealer_ratio = env.dealer_bank / env.init_dealer_bank
    win_streak = min(env.win_cnt, 5) / 5.0
    lose_streak = min(env.lose_cnt, 5) / 5.0
    return np.array([
        player_sum,
        dealer_up,
        usable,
        player_ratio,
        dealer_ratio,
        win_streak,
        lose_streak,
    ], dtype=np.float32)


# --------------------------------------------------
#  Neural network (simple MLP)
# --------------------------------------------------

class QNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, state_dim)
        return self.net(x)


# --------------------------------------------------
#  Replay Buffer
# --------------------------------------------------

Transition = namedtuple("Transition", ["state", "action", "reward", "next_state", "done"])


class ReplayBuffer:
    def __init__(self, capacity: int = 300_000):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Transition(*args))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def __len__(self):
        return len(self.buffer)


# --------------------------------------------------
#  DQN Agent integrating bankroll & bet reward
# --------------------------------------------------

class DQNAgentwithbet:
    ACTIONS = ["hit", "switch", "fold", "stay"]

    def __init__(
        self,
        alpha: float = 1e-3,
        gamma: float = 0.9,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: int = 150_000,
        batch_size: int = 128,
        target_update: int = 2_000,
        replay_capacity: int = 300_000,
        device: Union[str, torch.device, None] = None,
    ):
        self.gamma = gamma
        self.batch_size = batch_size
        self.device = torch.device(device) if device else torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.state_dim = 7
        self.action_dim = len(self.ACTIONS)

        self.policy_net = QNetwork(self.state_dim, self.action_dim).to(self.device)
        self.target_net = QNetwork(self.state_dim, self.action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=alpha)
        self.replay = ReplayBuffer(replay_capacity)

        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.steps_done = 0
        self.target_update = target_update

    # -------------------------
    #  Epsilon-greedy
    # -------------------------

    def _epsilon(self) -> float:
        return self.epsilon_end + (self.epsilon_start - self.epsilon_end) * np.exp(
            -1.0 * self.steps_done / self.epsilon_decay
        )

    def select_action(self, state: np.ndarray, train: bool = True) -> int:
        """Return an action index (0-3). When train=True, use ε-greedy exploration."""
        self.steps_done += 1
        if train and random.random() < self._epsilon():
            return random.randrange(self.action_dim)
        with torch.no_grad():
            state_t = torch.tensor(state, device=self.device).unsqueeze(0)
            q = self.policy_net(state_t)
            return int(torch.argmax(q).item())

    def choose_action(self, env: CasinoBlackJack, is_train: bool = False) -> str:
        """Compatibility wrapper: from env to action string."""
        state = extract_state(env)
        idx = self.select_action(state, train=is_train)
        return self.ACTIONS[idx]

    # -------------------------
    #  Learning step
    # -------------------------

    def _learn(self):
        if len(self.replay) < self.batch_size:
            return
        batch = self.replay.sample(self.batch_size)
        state_b = torch.tensor(batch.state, device=self.device)
        action_b = torch.tensor(batch.action, dtype=torch.int64, device=self.device).unsqueeze(-1)
        reward_b = torch.tensor(batch.reward, dtype=torch.float32, device=self.device).unsqueeze(-1)
        next_b = torch.tensor(batch.next_state, device=self.device)
        done_b = torch.tensor(batch.done, dtype=torch.float32, device=self.device).unsqueeze(-1)

        q_values = self.policy_net(state_b).gather(1, action_b)
        with torch.no_grad():
            next_q = self.target_net(next_b).max(dim=1, keepdim=True)[0]
            target = reward_b + self.gamma * next_q * (1 - done_b)
        loss = nn.functional.mse_loss(q_values, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    # -------------------------
    #  Training loop (one round = one episode)
    # -------------------------

    def train(self, episodes: int = 200_000):
        env = CasinoBlackJack()  # persistent bankroll across episodes
        for ep in range(episodes):
            if env.player_bank <= 0 or env.dealer_bank <= 0:
                env.full_reset()

            env.reset_round()
            env.start()
            bet = env.betrule()  # fixed for this round
            done = False

            while not done:
                state = extract_state(env)
                action_idx = self.select_action(state, train=True)
                action = self.ACTIONS[action_idx]

                status = env.player_action(action)

                # No mid-round reward except bust/blackjack
                reward = 0.0
                if status == "player_blackjack":
                    reward = bet  # win
                elif status == "player_bust":
                    reward = -bet  # lose

                next_state = extract_state(env)
                terminal = status != "continue" or action == "stay"

                self.replay.push(state, action_idx, reward, next_state, terminal)
                self._learn()

                if terminal:
                    env.dealer_action("basic")
                    result = env.game_result()
                    outcome = 1 if result == "win" else -1 if result == "lose" else 0
                    final_reward = outcome * bet
                    env.settle(result, bet)

                    # Store terminal transition
                    self.replay.push(next_state, 0, final_reward, next_state, True)
                    self._learn()
                    done = True

                if self.steps_done % self.target_update == 0:
                    self.target_net.load_state_dict(self.policy_net.state_dict())

            if (ep + 1) % 10_000 == 0:
                print(
                    f"Ep {ep + 1}/{episodes} | "
                    f"Player bank: {env.player_bank:.0f} | Dealer bank: {env.dealer_bank:.0f} | "
                    f"ε={self._epsilon():.3f}"
                )

    # -------------------------
    #  Evaluation (single round)
    # -------------------------

    def play(self, render: bool = False) -> Tuple[str, float]:
        env = CasinoBlackJack()
        env.reset_round()
        env.start()
        bet = env.betrule()
        done = False
        while not done:
            state = extract_state(env)
            action_idx = self.select_action(state, train=False)
            action = self.ACTIONS[action_idx]
            status = env.player_action(action)
            if status != "continue" or action == "stay":
                done = True
        env.dealer_action("basic")
        result = env.game_result()
        outcome = 1 if result == "win" else -1 if result == "lose" else 0
        bankroll_change = outcome * bet
        if render:
            print(f"Result: {result} | Bet: {bet:.1f} | Δ bankroll: {bankroll_change:+.1f}")
        return result, bankroll_change

    # -------------------------
    #  Persistence
    # -------------------------

    def save(self, path: str = "dqn_bankroll.pt"):
        torch.save(self.policy_net.state_dict(), path)

    def load(self, path: str = "dqn_bankroll.pt"):
        self.policy_net.load_state_dict(torch.load(path, map_location=self.device))
        self.target_net.load_state_dict(self.policy_net.state_dict())


# --------------------------------------------------
#  Example evaluation loop using CasinoBlackJack
# --------------------------------------------------

if __name__ == "__main__":
    # Instantiate agent and optionally load pretrained weights
    agent = DQNAgentwithbet()
    # agent.load("dqn_bankroll.pt")  # uncomment if you have saved weights

    rounds = 10000
    results = {"win": 0, "lose": 0, "draw": 0}

    # Create a single CasinoBlackJack instance for evaluation (bankroll persists across rounds)
    game = CasinoBlackJack(mode="novel")
    for _ in trange(rounds, desc="Evaluating DQNAgentwithbet"):
        # Start a new round (retaining bankroll & streaks)
        game.reset_round()
        game.start()
        # Play until terminal
        while game.status == "continue":
            action = agent.choose_action(game, is_train=False)
            game.play(action, "basic")
            if action in ["stay", "fold", "switch"]:
                break
        # After player finishes, if not bust, let dealer act
        if game.status == "continue":
            game.dealer_action("basic")
        # Record result
        res = game.game_result()
        results[res] += 1
        # Settle bet and bankroll (handled inside train/play; here just for counting)
        bet = game.betrule()
        game.settle(res, bet)

    win_rate = results["win"] / rounds
    draw_rate = results["draw"] / rounds
    lose_rate = results["lose"] / rounds

    print(f"\nAfter {rounds} rounds:")
    print(f"Win rate:  {win_rate:.3f}")
    print(f"Draw rate: {draw_rate:.3f}")
    print(f"Lose rate: {lose_rate:.3f}")
