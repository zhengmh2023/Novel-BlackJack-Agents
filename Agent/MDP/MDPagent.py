import random
import numpy as np
import sys
import os
from tqdm import trange

sys.path.append("D:/courses/CS181/BlackJack")

class MDPAgent:
    def __init__(self, game_mode="traditional", gamma=1.0, eps=0.0001, is_train=False):
        self.game_mode = game_mode  # Store game mode ("traditional" or "novel")
        self.gamma = gamma 
        self.eps = eps  # Threshold for convergence
        self.value_table = np.zeros((32, 12, 2))  # Player sum (1-21), dealer card, has_usable_ace
        if is_train:
            self.policy = np.zeros((32, 12, 2), dtype=int)  # Policy: 0 (stay), 1 (hit), 2 (switch), 3 (fold)
        else:
            self.policy = self.load_policy("Agent/MDP/policy.npy")
        self.action_space = [0, 1, 2, 3]  # 0 (stay), 1 (hit), 2 (switch), 3 (fold)
        self.card_probabilities = {1: 1/13, 2: 1/13, 3: 1/13, 4: 1/13, 5: 1/13, 
                                  6: 1/13, 7: 1/13, 8: 1/13, 9: 1/13, 10: 4/13}  # 10 includes J,Q,K

    @staticmethod
    def has_usable_ace(hand):
        """Check if the hand has a usable ace."""
        value, ace = 0, False
        for card in hand:
            card_number = card["number"]
            value += min(10, int(card_number) if card_number not in ["J", "Q", "K", "A"] else 11)
            ace |= card_number == "A"
        return int(ace and value + 10 <= 21)

    def state(self, game):
        """Get the current state: (player_sum, dealer_card_num, has_usable_ace)."""
        player_sum = game.get_playervalue()
        dealer_card_num = game.total_value(game.dealer_hand[:1]) if game.dealer_hand else 0
        has_usable_ace = self.has_usable_ace(game.player_hand) if game.player_hand else 0
        return (player_sum, dealer_card_num, has_usable_ace)

    def calculate_state_value(self, player_sum, dealer_showing, usable_ace, action):
        """Calculate the expected value for a given state and action."""
        #print(f"Calculating state value for action {action} with state ({player_sum}, {dealer_showing}, {usable_ace})")
        if action == 0:  # stay
             return self._evaluate_stick(player_sum, dealer_showing, self.game_mode)
        elif action == 2:  # switch
            return self._evaluate_switch(player_sum, dealer_showing, usable_ace, self.game_mode)
        elif action == 3:  # fold
            return self._evaluate_fold(player_sum, dealer_showing, self.game_mode)
        else:  # hit
            return self._evaluate_hit(player_sum, dealer_showing, usable_ace)

    def _evaluate_stick(self, player_sum, dealer_showing, mode):
        """Evaluate expected reward for staying."""
        dealer_probs = self._calculate_dealer_probabilities(dealer_showing)
        expected_reward = 0
        for dealer_sum, prob in dealer_probs.items():
            if dealer_sum == 'bust':
                expected_reward += prob if mode == "novel" or player_sum <= 21 else 0
            elif dealer_sum != 'bust':
                if int(dealer_sum) > player_sum:
                    expected_reward -= prob
                elif int(dealer_sum) < player_sum and player_sum <= 21:
                    expected_reward += prob
                # Equal case contributes 0 (draw)
        return expected_reward

    def _evaluate_hit(self, player_sum, dealer_showing, usable_ace):
        """Evaluate expected reward for hitting."""
        # return 0 if player_sum <= 21 else -1
        expected_reward = 0
        for card_value, prob in self.card_probabilities.items():
            new_sum = player_sum + card_value
            new_usable_ace = usable_ace
            if card_value == 1 and new_sum + 10 <= 21:
                new_sum += 10
                new_usable_ace = 1
            if new_sum > 21:
                expected_reward += prob * (-1)
            else:
                expected_reward += prob * self.gamma * self.value_table[new_sum, dealer_showing, new_usable_ace]
        return expected_reward

    def _evaluate_switch(self, player_sum, dealer_showing, usable_ace, mode):
        """Evaluate expected reward for switching cards."""
        expected_reward = 0
        # Simulate switch: assume player's hand loses one card and gains dealer's card
        for player_card_value, player_card_prob in self.card_probabilities.items():
            new_player_sum = player_sum - player_card_value + dealer_showing
            new_dealer_showing = player_card_value
            # Recalculate usable ace for the new hand
            new_usable_ace = 1 if dealer_showing == 1 and new_player_sum + 10 <= 21 else usable_ace
            if new_player_sum > 21:
                expected_reward += player_card_prob * (-1)  # Bust
            else:
                new_value = self._evaluate_stick(new_player_sum, new_dealer_showing, mode)
                expected_reward += player_card_prob * self.gamma * new_value
        return expected_reward

    def _evaluate_fold(self, player_sum, dealer_showing, mode):
        """Evaluate expected reward for folding (removing dealer's first card)."""
        expected_reward = 0
        for new_dealer_card, prob in self.card_probabilities.items():
            new_value = self._evaluate_stick(player_sum, new_dealer_card, mode)
            expected_reward += prob * self.gamma * new_value
        return expected_reward

    def _calculate_dealer_probabilities(self, dealer_showing):
        card_probabilities = {1: 1/13, 2: 1/13, 3: 1/13, 4: 1/13, 5: 1/13, 6: 1/13, 7: 1/13, 8: 1/13, 9: 1/13, 10: 4/13}
        dealer_probabilities = {}

        for card_value, prob in card_probabilities.items():
            dealer_sum = dealer_showing + card_value
            if dealer_sum < 21:
                if dealer_sum in dealer_probabilities:
                    dealer_probabilities[dealer_sum] += prob
                else:
                    dealer_probabilities[dealer_sum] = prob

        return dealer_probabilities
    def evaluate_actions(self, player_sum, dealer_showing, usable_ace):
        """Evaluate all actions and return the maximum value."""
        actions_values = np.zeros(len(self.action_space))
        #print(1)
        for action in self.action_space:
            #print(5)
            actions_values[action] = self.calculate_state_value(player_sum, dealer_showing, usable_ace, action)
        #print(9)
        #print(np.max(actions_values))
        #print(actions_values)
        return np.max(actions_values)

    def extract_policy(self):
        """Extract the optimal policy from the value table."""
        for player_sum in range(1, 22):  # Limit to 21 since game ends on bust
            for dealer_showing in range(1, 12):
                for usable_ace in range(2):
                    action_values = np.zeros(len(self.action_space))
                    for action in self.action_space:
                        action_values[action] = self.calculate_state_value(player_sum, dealer_showing, usable_ace, action)
                    self.policy[player_sum, dealer_showing, usable_ace] = np.argmax(action_values)

    def value_iteration(self):
        """Perform value iteration to compute the optimal value function and policy."""
        iterations = 0
        max_iterations = 100  # 限制最大迭代次数
        for iterations in range(max_iterations):
            delta = 0
            for player_sum in range(1, 22):  # Limit to 21 since game ends on bust
                for dealer_showing in range(1, 12):
                    for usable_ace in range(2):
                        # 打印调试信息，检查索引值是否正常
                        v_old = self.value_table[player_sum, dealer_showing, usable_ace]
                        #print(2)
                        v_new = self.evaluate_actions(player_sum, dealer_showing, usable_ace)
                        self.value_table[player_sum, dealer_showing, usable_ace] = v_new
                        delta = max(delta, abs(v_old - v_new))
                        #print(f"State ({player_sum}, {dealer_showing}, {usable_ace}): old value = {v_old}, new value = {v_new}, delta = {abs(v_old - v_new)}")
            if delta < self.eps:
            #     #print(f"Converged after {iterations} iterations")
                break
            #print("Reached maximum iterations without convergence.")
        self.extract_policy()
        

    def save_policy(self, filename="policy.npy"):
        """Save the learned policy to a file."""
        np.save(filename, self.policy)

    def load_policy(self, filename="policy.npy"):
        """Load the policy from a file."""
        if os.path.exists(filename):
            return np.load(filename)
        else:
            return np.zeros((32, 12, 2), dtype=int)


    def choose_action(self, game):
        """Choose an action based on the current state and policy."""
        state = self.state(game)
        action_idx = self.policy[state]
        actions = {0: 'stay', 1: 'hit', 2: 'switch', 3: 'fold'}
        return actions[action_idx]
  
    
if __name__ == "__main__":
    agent = MDPAgent(is_train=True)
    agent.value_iteration()
    agent.save_policy()
    
    

