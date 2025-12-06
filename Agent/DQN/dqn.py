# import random
# from collections import deque, namedtuple
# from typing import Union

# import numpy as np
# import torch
# import torch.nn as nn
# import torch.optim as optim

# from Game.BlackJack import BlackJack

# # -----------------------------
# # Helpers
# # -----------------------------

# def has_usable_ace(hand):
#     """Return 1 if the hand has a usable ace (soft hand), otherwise 0."""
#     value, ace = 0, False
#     for card in hand:
#         num = card["number"]
#         if num == "A":
#             value += 11
#             ace = True
#         elif num in ["J", "Q", "K"]:
#             value += 10
#         else:
#             value += int(num)
#     return int(ace and value + 10 <= 21)

# def extract_state(env: BlackJack) -> np.ndarray:
#     """Convert the current game state into a numeric feature vector."""
#     player_sum = env.get_playervalue()
#     dealer_card_val = env.total_value(env.dealer_hand[:1])
#     usable = has_usable_ace(env.player_hand)

#     player_sum = min(player_sum, 32)
#     dealer_card_val = min(dealer_card_val, 11)

#     return np.array([
#         player_sum / 32.0,
#         dealer_card_val / 11.0,
#         float(usable),
#     ], dtype=np.float32)


# # -----------------------------
# # Neural Network
# # -----------------------------

# class QNetwork(nn.Module):
#     def __init__(self, state_dim: int, action_dim: int, hidden: int = 256):
#         super().__init__()
#         self.net = nn.Sequential(
#             nn.Linear(state_dim, hidden),
#             nn.ReLU(),
#             nn.Linear(hidden, hidden),
#             nn.ReLU(),
#             nn.Linear(hidden, action_dim),
#         )

#     def forward(self, x: torch.Tensor) -> torch.Tensor:
#         return self.net(x)


# # -----------------------------
# # Replay Buffer
# # -----------------------------

# Transition = namedtuple(
#     "Transition", ["state", "action", "reward", "next_state", "done"]
# )

# class ReplayBuffer:
#     def __init__(self, capacity: int = 100_000):
#         self.buffer = deque(maxlen=capacity)

#     def push(self, *args):
#         self.buffer.append(Transition(*args))

#     def sample(self, batch_size: int):
#         batch = random.sample(self.buffer, batch_size)
#         return Transition(*zip(*batch))

#     def __len__(self):
#         return len(self.buffer)


# # -----------------------------
# # DQN Agent
# # -----------------------------

# class DQNAgent:
#     ACTIONS = ["hit", "switch", "fold", "stay"]

#     def __init__(
#         self,
#         alpha: float = 5e-5,
#         gamma: float = 0.9,
#         epsilon_start: float = 1.0,
#         epsilon_end: float = 0.01,
#         epsilon_decay: int = 20_000,
#         batch_size: int = 64,
#         target_update: int = 1_000,
#         replay_capacity: int = 200_000,
#         device: Union[str, torch.device, None] = None,
#     ):
#         self.gamma = gamma
#         self.batch_size = batch_size
#         self.device = torch.device(device) if device else torch.device(
#             "cuda" if torch.cuda.is_available() else "cpu"
#         )

#         self.state_dim = 3
#         self.action_dim = len(self.ACTIONS)

#         self.policy_net = QNetwork(self.state_dim, self.action_dim).to(self.device)
#         self.target_net = QNetwork(self.state_dim, self.action_dim).to(self.device)
#         self.target_net.load_state_dict(self.policy_net.state_dict())
#         self.target_net.eval()

#         self.optimizer = optim.Adam(self.policy_net.parameters(), lr=alpha)
#         self.replay = ReplayBuffer(replay_capacity)

#         self.epsilon_start = epsilon_start
#         self.epsilon_end = epsilon_end
#         self.epsilon_decay = epsilon_decay
#         self.steps_done = 0

#         self.target_update = target_update

#     def select_action(self, state: np.ndarray, train: bool = True) -> int:
#         """返回动作索引（0-3）。train=True 时使用 ε-贪婪."""
#         self.steps_done += 1
#         eps = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * np.exp(
#             -1.0 * self.steps_done / self.epsilon_decay
#         )
#         if train and random.random() < eps:
#             return random.randrange(self.action_dim)
#         with torch.no_grad():
#             state_t = torch.tensor(state, device=self.device).unsqueeze(0)
#             q_vals = self.policy_net(state_t)
#             return int(torch.argmax(q_vals).item())

#     def choose_action(self, env: BlackJack, is_train: bool = False) -> str:
#         """
#         兼容旧 Q-Learning 版接口：直接传入 env 对象，返回动作字符串。
#         is_train=False 时不应用探索，始终选最优动作。
#         """
#         state = extract_state(env)
#         idx = self.select_action(state, train=is_train)
#         return self.ACTIONS[idx]

#     def learn_step(self):
#         """从经验回放采样并更新网络."""
#         if len(self.replay) < self.batch_size:
#             return
#         batch = self.replay.sample(self.batch_size)
#         state_b = torch.tensor(batch.state, device=self.device)
#         act_b = torch.tensor(batch.action, dtype=torch.int64, device=self.device).unsqueeze(-1)
#         rew_b = torch.tensor(batch.reward, device=self.device).unsqueeze(-1)
#         next_b = torch.tensor(batch.next_state, device=self.device)
#         done_b = torch.tensor(batch.done, dtype=torch.float32, device=self.device).unsqueeze(-1)

#         q = self.policy_net(state_b).gather(1, act_b)
#         with torch.no_grad():
#             next_q = self.target_net(next_b).max(dim=1, keepdim=True)[0]
#             target = rew_b + self.gamma * next_q * (1 - done_b)
#         loss = nn.functional.mse_loss(q, target)
#         self.optimizer.zero_grad()
#         loss.backward()
#         self.optimizer.step()

#     def train(self, episodes: int = 100_000):
#         """训练 DQN Agent。可保留与 Q-Learning 版相同的 train 调用接口。"""
#         for ep in range(episodes):
#             env = BlackJack("novel")
#             env.start()
#             done = False
#             while not done:
#                 state = extract_state(env)
#                 a_idx = self.select_action(state, train=True)
#                 action = self.ACTIONS[a_idx]

#                 status = env.player_action(action)

#                 reward = 0
#                 if status == "player_blackjack":
#                     reward = 1
#                 elif status == "player_bust":
#                     reward = -1
#                 if action in ["switch", "fold"]:
#                     reward += 0.1

#                 next_state = extract_state(env)
#                 done_flag = status != "continue" or action == "stay"

#                 self.replay.push(state, a_idx, reward, next_state, done_flag)
#                 self.learn_step()

#                 if done_flag:
#                     env.dealer_action("basic")
#                     res = env.game_result()
#                     final_r = 1 if res == "win" else -1 if res == "lose" else 0
#                     # 存终局 transition:
#                     self.replay.push(next_state, 0, final_r, next_state, True)
#                     self.learn_step()
#                     done = True

#                 if self.steps_done % self.target_update == 0:
#                     self.target_net.load_state_dict(self.policy_net.state_dict())

#             if (ep + 1) % 10_000 == 0:
#                 print(f"Episode {ep+1}/{episodes} done")

#     def play(self, render: bool = False) -> str:
#         """使用最优策略（epsilon=0）玩一局，返回结果字符串。"""
#         env = BlackJack("novel")
#         env.start()
#         done = False
#         while not done:
#             state = extract_state(env)
#             a_idx = self.select_action(state, train=False)
#             action = self.ACTIONS[a_idx]
#             status = env.player_action(action)
#             if render:
#                 print(f"Player chose {action}")
#             if status != "continue" or action == "stay":
#                 done = True
#         env.dealer_action("basic")
#         res = env.game_result()
#         if render:
#             print(res)
#         return res

#     def save(self, path: str = "dqn_blackjack.pt"):
#         torch.save(self.policy_net.state_dict(), path)

#     def load(self, path: str = "dqn_blackjack.pt"):
#         self.policy_net.load_state_dict(torch.load(path, map_location=self.device))
#         self.target_net.load_state_dict(self.policy_net.state_dict())

# if __name__ == "__main__":
#     rounds = 10000
#     try:
#         agent = DQNAgent()
#         print("Starting DQN training...")
#         for i in range(rounds):
#             # 每次训练 1 轮，这样可以在主循环里输出进度
#             agent.train(1)
#             if (i + 1) % 10000 == 0:
#                 print(f"  Trained {i + 1}/{rounds} episodes")
#         print("Training complete. Saving model...")
#         agent.save("Agent/DQN/dqn_blackjack.pt")
#         print("Model saved successfully!")
#     except Exception as e:
#         print(f"Error: {e}")



import random
import os
from collections import deque, namedtuple
from typing import Union

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from Game.BlackJack import BlackJack

# -----------------------------
# Helpers
# -----------------------------
def has_usable_ace(hand):
    """Return 1 if the hand has a usable ace (soft hand), otherwise 0."""
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

def extract_state(env: BlackJack) -> np.ndarray:
    """Convert the current game state into a numeric feature vector."""
    player_sum = env.get_playervalue()
    dealer_card_val = env.total_value(env.dealer_hand[:1])
    usable = has_usable_ace(env.player_hand)

    player_sum = min(player_sum, 32)
    dealer_card_val = min(dealer_card_val, 11)

    return np.array([
        player_sum / 32.0,
        dealer_card_val / 11.0,
        float(usable),
    ], dtype=np.float32)


# -----------------------------
# Neural Network (hidden=128)
# -----------------------------
class QNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# -----------------------------
# Replay Buffer
# -----------------------------
Transition = namedtuple(
    "Transition", ["state", "action", "reward", "next_state", "done"]
)

class ReplayBuffer:
    def __init__(self, capacity: int = 100_000):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Transition(*args))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def __len__(self):
        return len(self.buffer)


# -----------------------------
# DQN Agent
# -----------------------------
class DQNAgent:
    ACTIONS = ["hit", "switch", "fold", "stay"]
    MODEL_PATH = "Agent/DQN/dqn_blackjack.pt"

    def __init__(
        self,
        alpha: float = 5e-5,
        gamma: float = 0.9,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: int = 20_000,
        batch_size: int = 64,
        target_update: int = 1_000,
        replay_capacity: int = 200_000,
        device: Union[str, torch.device, None] = None,
    ):
        self.gamma = gamma
        self.batch_size = batch_size
        self.device = torch.device(device) if device else torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.state_dim = 3
        self.action_dim = len(self.ACTIONS)

        # 一定要显式指定 hidden=128，与 checkpoint 中的模型一致
        self.policy_net = QNetwork(self.state_dim, self.action_dim, hidden=128).to(self.device)
        self.target_net = QNetwork(self.state_dim, self.action_dim, hidden=128).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=alpha)
        self.replay = ReplayBuffer(replay_capacity)

        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.steps_done = 0

        self.target_update = target_update

        # 标记模型是否已加载
        self._model_loaded = False

    def select_action(self, state: np.ndarray, train: bool = True) -> int:
        """返回动作索引（0-3）。train=True 时使用 ε-贪婪。"""
        self.steps_done += 1
        eps = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * np.exp(
            -1.0 * self.steps_done / self.epsilon_decay
        )
        if train and random.random() < eps:
            return random.randrange(self.action_dim)
        with torch.no_grad():
            state_t = torch.tensor(state, device=self.device).unsqueeze(0)
            q_vals = self.policy_net(state_t)
            return int(torch.argmax(q_vals).item())

    def choose_action(self, env: BlackJack, is_train: bool = False) -> str:
        """
        兼容旧 Q-Learning 版接口：直接传入 env 对象，返回动作字符串。
        如果磁盘上已有 .pt 模型，会自动加载并将 ε 置 0。
        is_train=False 时（或加载后）不应用探索，始终选最优动作。
        """
        # 第一次调用时，如果模型文件存在且还没加载，就自动加载一次
        if not self._model_loaded and os.path.exists(self.MODEL_PATH):
            self.load(self.MODEL_PATH)
            # 加载后把 epsilon 设为 0：之后所有 select_action(train=False) 都变成 greedy
            self.epsilon_start = 0.0
            self.epsilon_end = 0.0
            self._model_loaded = True

        state = extract_state(env)
        idx = self.select_action(state, train=is_train)
        return self.ACTIONS[idx]

    def learn_step(self):
        """从经验回放采样并更新网络。"""
        if len(self.replay) < self.batch_size:
            return
        batch = self.replay.sample(self.batch_size)
        state_b = torch.tensor(batch.state, device=self.device)
        act_b = torch.tensor(batch.action, dtype=torch.int64, device=self.device).unsqueeze(-1)
        rew_b = torch.tensor(batch.reward, device=self.device).unsqueeze(-1)
        next_b = torch.tensor(batch.next_state, device=self.device)
        done_b = torch.tensor(batch.done, dtype=torch.float32, device=self.device).unsqueeze(-1)

        q = self.policy_net(state_b).gather(1, act_b)
        with torch.no_grad():
            next_q = self.target_net(next_b).max(dim=1, keepdim=True)[0]
            target = rew_b + self.gamma * next_q * (1 - done_b)
        loss = nn.functional.mse_loss(q, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def train(self, episodes: int = 100_000):
        """训练 DQN Agent。"""
        for ep in range(episodes):
            env = BlackJack("novel")
            env.start()
            done = False
            while not done:
                state = extract_state(env)
                a_idx = self.select_action(state, train=True)
                action = self.ACTIONS[a_idx]

                status = env.player_action(action)

                reward = 0
                if status == "player_blackjack":
                    reward = 1
                elif status == "player_bust":
                    reward = -1
                if action in ["switch", "fold"]:
                    reward += 0.1

                next_state = extract_state(env)
                done_flag = status != "continue" or action == "stay"

                self.replay.push(state, a_idx, reward, next_state, done_flag)
                self.learn_step()

                if done_flag:
                    env.dealer_action("basic")
                    res = env.game_result()
                    final_r = 1 if res == "win" else -1 if res == "lose" else 0
                    # 存终局 transition：
                    self.replay.push(next_state, 0, final_r, next_state, True)
                    self.learn_step()
                    done = True

                if self.steps_done % self.target_update == 0:
                    self.target_net.load_state_dict(self.policy_net.state_dict())

            if (ep + 1) % 1000 == 0:
                print(f"Episode {ep+1}/{episodes} done")

    def play(self, render: bool = False) -> str:
        """使用最优策略（ε=0）玩一局，返回结果字符串。"""
        env = BlackJack("novel")
        env.start()
        done = False
        while not done:
            state = extract_state(env)
            a_idx = self.select_action(state, train=False)
            action = self.ACTIONS[a_idx]
            status = env.player_action(action)
            if render:
                print(f"Player chose {action}")
            if status != "continue" or action == "stay":
                done = True
        env.dealer_action("basic")
        res = env.game_result()
        if render:
            print(res)
        return res

    def save(self, path: str = MODEL_PATH):
        """保存当前 policy_net 权重到指定路径（.pt）。"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.policy_net.state_dict(), path)

    def load(self, path: str = MODEL_PATH):
        """从 .pt 文件加载权重，并同步到 target_net。"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found.")
        self.policy_net.load_state_dict(torch.load(path, map_location=self.device))
        self.target_net.load_state_dict(self.policy_net.state_dict())


if __name__ == "__main__":
    rounds = 10000
    try:
        agent = DQNAgent()
        print("Starting DQN training...")
        for i in range(rounds):
            # 每次训练 1 轮，这样可以在主循环里输出进度
            agent.train(1)
            if (i + 1) % 10000 == 0:
                print(f"  Trained {i + 1}/{rounds} episodes")
        print("Training complete. Saving model...")
        agent.save("Agent/DQN/dqn_blackjack.pt")
        print("Model saved successfully!")
    except Exception as e:
        print(f"Error: {e}")