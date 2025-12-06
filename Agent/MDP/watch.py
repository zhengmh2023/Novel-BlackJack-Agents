import numpy as np

# 加载 policy 文件
policy = np.load("policy.npy")

# 查看形状
print("Policy shape:", policy.shape)  # 应该是 (32, 12, 2)

# 例如查看 player_sum = 20，dealer_showing = 10，usable_ace = 1 时的策略
print("Policy at (20, 10, 1):", policy[20, 10, 1])  # 输出一个数字（动作编号）

# 遍历所有策略（可选，较长）
for player_sum in range(12, 22):  # 一般从 12 开始比较有意义
    for dealer_showing in range(1, 11):
        for usable_ace in [0, 1]:
            action = policy[player_sum, dealer_showing, usable_ace]
            print(f"Player {player_sum}, Dealer {dealer_showing}, UsableAce {usable_ace} -> Action {action}")

policy = np.load("policy.npy")
print(np.unique(policy))  # 全是0说明策略没学起来
