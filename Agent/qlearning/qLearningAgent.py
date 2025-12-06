import numpy as np
import sys
from tqdm import tqdm
import os

sys.path.append("../..")
from Game.BlackJack import BlackJack


class qLearningAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1, is_train=False):
        self.alpha = alpha  
        self.gamma = gamma  
        self.epsilon = epsilon  

        if is_train:
            self.Q = np.zeros((33, 12, 2, 4))  
        else:
            self.load_q_table("Agent/qlearning/Q_traditional.npy")

    def choose_action(self, game, is_train=False):
        """选择动作：训练时用ε-贪婪策略，测试时用最优策略"""
        player_sum = game.get_playervalue()
        dealer_card = game.total_value(game.dealer_hand[:1])  
        usable_ace = self.has_usable_ace(game.player_hand)

        player_sum = min(player_sum, 32) 
        dealer_card = min(dealer_card, 11)  

        if is_train and np.random.uniform(0, 1) < self.epsilon:
            return np.random.choice(["hit", "switch", "fold", "stay"])
        else:
            q_values = self.Q[player_sum, dealer_card, usable_ace]
            action_idx = np.argmax(q_values)
            return ["hit", "switch", "fold", "stay"][action_idx]

    def update(self, player_sum, dealer_card, usable_ace, action, reward, new_player_sum, new_dealer_card, new_usable_ace):
        """更新 Q 表"""
        player_sum = min(player_sum, 32)
        dealer_card = min(dealer_card, 11)
        new_player_sum = min(new_player_sum, 32)
        new_dealer_card = min(new_dealer_card, 11)

        action_idx = {"hit": 0, "switch": 1, "fold": 2, "stay": 3}[action]
        
        old_value = self.Q[player_sum, dealer_card, usable_ace, action_idx]
        future_max = np.max(self.Q[new_player_sum, new_dealer_card, new_usable_ace])
        self.Q[player_sum, dealer_card, usable_ace, action_idx] = (
            old_value + self.alpha * (reward + self.gamma * future_max - old_value)
        )

    @staticmethod
    def has_usable_ace(hand):
        """检查手牌是否有可用Ace（软手）"""
        value, ace = 0, False
        for card in hand:
            card_number = card["number"]
            value += min(
                10, int(card_number) if card_number not in ["J", "Q", "K", "A"] else 11
            )
            ace |= card_number == "A"
        return int(ace and value + 10 <= 21)

    def train(self, episodes):
        """训练代理"""
        for _ in tqdm(range(episodes), desc="Training"):
            game = BlackJack("novel")
            game.start()

            dealer_card = game.total_value(game.dealer_hand[:1]) 
            status = "continue"

            while status == "continue":
                player_sum = game.get_playervalue()
                usable_ace = self.has_usable_ace(game.player_hand)
                action = self.choose_action(game, is_train=True)

                prev_dealer_card = dealer_card

                game.player_action(action)

                status = game.get_status()
                new_player_sum = game.get_playervalue()
                new_usable_ace = self.has_usable_ace(game.player_hand)
                new_dealer_card = game.total_value(game.dealer_hand[:1]) 

                reward = 0
                assert status in ["continue", "player_blackjack", "player_bust", "stay"], f"Invalid status: {status}"

                if status == "player_blackjack":
                    reward = 1 
                elif status == "player_bust":
                    reward = -1

                if action == "switch":
                    reward = 0.1
                elif action == "fold":
                    reward = 0.1

                if reward != 0 or action in ["switch", "fold"]:
                    self.update(
                        player_sum,
                        prev_dealer_card,
                        usable_ace,
                        action,
                        reward,
                        new_player_sum,
                        new_dealer_card,
                        new_usable_ace
                    )

                if action == "stay":
                    break

            game.dealer_action("basic")
            final_result = game.game_result()
            final_reward = 1 if final_result == "win" else (-1 if final_result == "lose" else 0)

            self.update(
                player_sum,
                dealer_card,
                usable_ace,
                action,
                final_reward,
                new_player_sum,
                new_dealer_card,
                new_usable_ace,
            )

    def save_q_table(self, filename="Q_traditional.npy"):
        np.save(filename, self.Q)

    def load_q_table(self, filename):
        self.Q = np.load(filename)

    def play(self):
        """测试代理"""
        game = BlackJack("novel")
        game.start()

        status = "continue"
        while status == "continue":
            action = self.choose_action(game)
            status = game.player_action(action)

            if action == "stay" or action in ["switch", "fold"]:
                break

        if status in ["continue", "stay"]:
            game.dealer_action("basic")
        final_result = game.game_result()
        return final_result


if __name__ == "__main__":
    rounds = 100000
    try:
        agent = qLearningAgent(is_train=True)
        print("Starting training...")
        agent.train(rounds)
        print("Training complete. Saving Q-table...")
        agent.save_q_table("Q_traditional.npy")
        print("Q-table saved successfully!")
    except Exception as e:
        print(f"Error: {e}")