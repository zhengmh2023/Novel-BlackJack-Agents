# Novel Blackjack Agents  
### (ShanghaiTech University CS181 Artificial Intelligence Final Project)  

This repository implements multiple AI agents for a redesigned Blackjack game with expanded actions and dynamic betting rules.  
Compared to classic Blackjack, our novel environment introduces a richer decision space suitable for reinforcement learning, adversarial search, and decision-theoretic approaches.

## Overview

We designed and evaluated several agents for our novel Blackjack game:

- **Random Agent**
- **Expectimax Agent**
- **MDP Agent**
- **MDPWithBet Agent** (bankroll-aware MDP)
- **Q-learning Agent**
- **Improved Q-learning Agent** (with refined reward function)
- **DQN Agent**

Our redesigned Blackjack includes:

- **Four actions:** `Hit`, `Stay`, `Switch`, `Fold`
- **Dynamic betting rules**
- **Casino-style simulation environment**

This makes the game a significantly richer platform for studying decision-making under uncertainty.

## Game Rules Summary

### Player Actions
- **Hit:** Draw a card  
- **Stay:** Stop drawing  
- **Switch:** Swap one card with the dealer  
- **Fold:** Hide one of the dealer’s cards  

### Dealer Rule
- Dealer hits until the hand value reaches **17 or higher**

### Dynamic Betting System
The base bet ratio starts at 10% of the player’s bankroll and is adjusted by:
- Whether the player or dealer has an Ace/10
- Win/loss streaks
- A random multiplier in \[0.9, 1.1\]

This introduces stochasticity and long-term strategy considerations.

# Project Structure

```text
Agent/
├── DQN/
├── MDP/
├── expectimax/
├── qlearning/
└── random/

Game/
└── BlackJack.py

BlackJack.ipynb        # Jupyter notebook for testing/analysis
report.pdf             # Final project report
```

#Installation
1. Clone the repository
git clone https://github.com/zhengmh2023/Novel-BlackJack-Agents.git
cd Novel-BlackJack-Agents

