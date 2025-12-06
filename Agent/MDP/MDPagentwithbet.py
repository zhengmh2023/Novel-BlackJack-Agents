# import random
# import numpy as np
# import os

# # 假设这里能 import 到你现实环境中的 BlackJack 类，
# # 并且 BlackJack 已经被改为：包含 player_bank、win_cnt、lose_cnt，
# # 且有 reset(), reset_round(), settle() 等方法
# from Game.BlackJack import BlackJack  


# class MDPAgentWithBet:
#     def __init__(self, game_mode="novel", gamma=1.0, eps=1e-4, is_train=False):
#         self.game_mode = game_mode   # "traditional" 或 "novel"
#         self.gamma = gamma           # 折扣因子
#         self.eps = eps               # 价值迭代收敛阈值

#         # 三维价值表：player_sum∈[0..31], dealer_showing∈[0..11], usable_ace∈{0,1}
#         # 存储的是“相对于 1 元下注的期望回报”，避免直接乘 bet 导致数值爆炸
#         self.value_table = np.zeros((32, 12, 2), dtype=np.float64)

#         if is_train:
#             # 策略表：三维 -> action∈{0: stay,1: hit,2: switch,3: fold}
#             self.policy = np.zeros((32, 12, 2), dtype=np.int32)
#         else:
#             self.policy = self.load_policy("Agent/MDP/newpolicy.npy")

#         self.action_space = [0, 1, 2, 3]  # 0=stay,1=hit,2=switch,3=fold

#         # 卡片出现概率：1-9 各 1/13，10(含 J/Q/K) 共 4/13
#         self.card_probabilities = {
#             1: 1/13, 2: 1/13, 3: 1/13, 4: 1/13, 5: 1/13,
#             6: 1/13, 7: 1/13, 8: 1/13, 9: 1/13, 10: 4/13
#         }

#         # 初始资金常量（用于归一化）：这里设为 100000
#         self.initial_bank = 100000.0

#     @staticmethod
#     def has_usable_ace(hand):
#         """返回 0/1：手牌中是否含有“软”Ace。"""
#         value, ace = 0, False
#         for card in hand:
#             num = card["number"]
#             if num == "A":
#                 value += 11
#                 ace = True
#             elif num in ["J", "Q", "K"]:
#                 value += 10
#             else:
#                 value += int(num)
#         return int(ace and (value + 10) <= 21)

#     def state(self, game: BlackJack):
#         """
#         原来的三维状态：(player_sum, dealer_showing, usable_ace)
#         把 player_bank 与 a 这两项只在“模拟阶段”中单独算 reward 并更新，
#         在迭代阶段只学“单位赌注”回报，不将它们并入表维度。
#         """
#         player_sum = game.get_playervalue()
#         dealer_showing = game.total_value(game.dealer_hand[:1]) if game.dealer_hand else 0
#         usable_ace = self.has_usable_ace(game.player_hand) if game.player_hand else 0

#         # Clip 防止越界
#         player_sum = min(player_sum, 32)
#         dealer_showing = min(dealer_showing, 11)
#         return (player_sum, dealer_showing, usable_ace)

#     def _compute_bet(self, game: BlackJack):
#         """
#         根据题目给定的下注规则动态计算当前 a 和 bet：
#           (1) 初始 a = 0.1
#           (2) 玩家起始牌中含 A / 10-面 (含 J/Q/K) → a *= 1.5
#           (3) 庄家明牌含 A / 10-面 → a *= 0.75
#           (4) 连输 5 次 → a *= 1.5；连赢 5 次 → a *= 0.75
#           (5) 随机扰动 × uniform(0.9, 1.1)
#           (6) 最终截断 a∈[0,1]

#         返回：
#           bet_real   = a × game.player_bank
#           bank_norm  = game.player_bank / initial_bank
#           a_norm     = a / 0.1  （使得“a_norm＝1”对应单位赌注的情况）
#         """
#         # 1) a 基准
#         a = 0.1

#         # 2) 玩家头两张牌若含 A 或 10 (J/Q/K) → a *= 1.5
#         for card in game.player_hand:
#             if card["number"] == "A" or card["number"] in ["10", "J", "Q", "K"]:
#                 a *= 1.5
#                 break

#         # 3) 庄家明牌若含 A 或 10 (J/Q/K) → a *= 0.75
#         up = game.dealer_hand[0]["number"]
#         if up == "A" or up in ["10", "J", "Q", "K"]:
#             a *= 0.75

#         # 4) 连输/连赢
#         if game.lose_cnt >= 5:
#             a *= 1.5
#         elif game.win_cnt >= 5:
#             a *= 0.75

#         # 5) 随机扰动
#         a *= random.uniform(0.9, 1.1)

#         # 截断到 [0,1]
#         a = max(0.0, min(a, 1.0))

#         bank = game.player_bank
#         bank_norm = bank / self.initial_bank  # 归一化资金
#         bet_real = a * bank
#         a_norm = a / 0.1  # 归一化下注倍数

#         return bet_real, bank_norm, a_norm

#     def calculate_state_value(self, ps, ds, ua, game: BlackJack, action: int):
#         """
#         计算某状态下执行某动作的“相对于 1 元下注” 的期望回报：
#          • 如果爆牌 → –1
#          • 赢牌 → +1
#          • 平局 → 0
#          • 折扣 γ 只用到下一状态的 value_table
#         这一块**不再直接乘真实 bet**，避免溢出。
#         """
#         if action == 0:      # stay
#             return self._evaluate_stick(ps, ds, ua, game)
#         elif action == 1:    # hit
#             return self._evaluate_hit(ps, ds, ua, game)
#         elif action == 2:    # switch
#             return self._evaluate_switch(ps, ds, ua, game)
#         elif action == 3:    # fold
#             return self._evaluate_fold(ps, ds, ua, game)
#         else:
#             raise ValueError("Invalid action index.")

#     def _evaluate_stick(self, ps, ds, ua, game: BlackJack):
#         """
#         “停牌”后由庄家补牌得出的期望（单位赌注视角）：
#          • 若 dealer_bust 且（novel 模式下玩家≤21） → +1
#          • 若 dealer_sum > player_sum → –1
#          • 若 player_sum > dealer_sum → +1
#          • 平局 → 0
#         """
#         dealer_probs = self._calculate_dealer_probabilities(ds)
#         expected_unit = 0.0

#         for dealer_sum, prob in dealer_probs.items():
#             if dealer_sum == 'bust':
#                 if self.game_mode == "novel":
#                     if ps <= 21:
#                         expected_unit += prob
#                 else:
#                     expected_unit += prob
#             else:
#                 d = int(dealer_sum)
#                 if ps > 21:
#                     # 玩家自己爆了 → 输
#                     expected_unit -= prob
#                 else:
#                     if d > ps:
#                         expected_unit -= prob
#                     elif d < ps:
#                         expected_unit += prob
#                     # 相等：0

#         return expected_unit

#     def _evaluate_hit(self, ps, ds, ua, game: BlackJack):
#         """
#         “要牌”以后：
#          • 如果 new_sum > 21 → 爆牌，视为 –1
#          • 否则，用下一状态的 value_table × γ
#         """
#         expected_unit = 0.0

#         for card_val, prob in self.card_probabilities.items():
#             new_sum = ps + card_val
#             new_usable = ua
#             if card_val == 1 and (new_sum + 10) <= 21:
#                 new_sum += 10
#                 new_usable = 1

#             if new_sum > 21:
#                 expected_unit += prob * (-1)
#             else:
#                 v_next = self.value_table[new_sum, ds, new_usable]
#                 expected_unit += prob * (self.gamma * v_next)

#         return expected_unit

#     def _evaluate_switch(self, ps, ds, ua, game: BlackJack):
#         """
#         “换牌”以后：
#          • 玩家 lose 一张 player_card_val，加回 dealer_showing
#          • 如果 new_sum > 21 → –1
#          • 否则，value_table[new_sum, new_ds, new_usable] × γ
#         """
#         expected_unit = 0.0

#         for player_card_val, prob in self.card_probabilities.items():
#             new_sum = ps - player_card_val + ds
#             new_ds = player_card_val
#             new_usable = ua
#             if ds == 1 and (new_sum + 10) <= 21:
#                 new_sum += 10
#                 new_usable = 1

#             if new_sum > 21:
#                 expected_unit += prob * (-1)
#             else:
#                 v_next = self.value_table[new_sum, new_ds, new_usable]
#                 expected_unit += prob * (self.gamma * v_next)

#         return expected_unit

#     def _evaluate_fold(self, ps, ds, ua, game: BlackJack):
#         """
#         “弃牌”以后：
#          • 模拟重新发一张牌给庄家 new_ds → 停牌后情况
#          • value_table[ps, new_ds, ua] × γ
#         """
#         expected_unit = 0.0

#         for new_ds, prob in self.card_probabilities.items():
#             v_next = self.value_table[ps, new_ds, ua]
#             expected_unit += prob * (self.gamma * v_next)

#         return expected_unit

#     def _calculate_dealer_probabilities(self, dealer_showing):
#         """
#         只考虑“庄家下一张牌”：
#          • 如果 dealer_showing+card < 21 → 该点数
#          • 否则 → 'bust'
#         """
#         probs = {i: 1/13 for i in range(1, 10)}
#         probs[10] = 4/13
#         dealer_probs = {}

#         for card_val, p in probs.items():
#             s = dealer_showing + card_val
#             if s < 21:
#                 dealer_probs.setdefault(s, 0.0)
#                 dealer_probs[s] += p
#             else:
#                 dealer_probs.setdefault('bust', 0.0)
#                 dealer_probs['bust'] += p

#         return dealer_probs

#     def evaluate_actions(self, ps, ds, ua, game: BlackJack):
#         """
#         枚举 4 种动作，返回“相对于 1 元下注”的最大期望。
#         模拟阶段会把这个值乘真实 bet，得到绝对盈亏。
#         """
#         best = -np.inf
#         for a in self.action_space:
#             v = self.calculate_state_value(ps, ds, ua, game, a)
#             if v > best:
#                 best = v
#         return best

#     def value_iteration(self):
#         """
#         在三维 (ps, ds, ua) 上做 “对 1 元下注期望” 的价值迭代。
#         迭代结束后提取策略 newpolicy。
#         """
#         max_iters = 100
#         for it in range(max_iters):
#             delta = 0.0
#             for ps in range(1, 22):
#                 for ds in range(1, 12):
#                     for ua in range(2):
#                         old_v = self.value_table[ps, ds, ua]
#                         # 构造一个“伪环境”：只需要这三个参数，不关心 bankroll/连输连赢
#                         dummy = type("DummyGame", (), {})()
#                         dummy.player_hand = [{"number": str(min(ps, 11)), "suit": None}]
#                         dummy.dealer_hand = [{"number": str(ds), "suit": None}]
#                         dummy.player_bank = self.initial_bank
#                         dummy.win_cnt = 0
#                         dummy.lose_cnt = 0

#                         new_v = self.evaluate_actions(ps, ds, ua, dummy)
#                         self.value_table[ps, ds, ua] = new_v
#                         delta = max(delta, abs(old_v - new_v))

#             if delta < self.eps:
#                 break

#         # 迭代结束后，提取三维策略表 newpolicy
#         for ps in range(1, 22):
#             for ds in range(1, 12):
#                 for ua in range(2):
#                     best_a = 0
#                     best_v = -np.inf
#                     dummy = type("DummyGame", (), {})()
#                     dummy.player_hand = [{"number": str(min(ps, 11)), "suit": None}]
#                     dummy.dealer_hand = [{"number": str(ds), "suit": None}]
#                     dummy.player_bank = self.initial_bank
#                     dummy.win_cnt = 0
#                     dummy.lose_cnt = 0

#                     for a in self.action_space:
#                         v = self.calculate_state_value(ps, ds, ua, dummy, a)
#                         if v > best_v:
#                             best_v = v
#                             best_a = a
#                     self.policy[ps, ds, ua] = best_a

#     def save_policy(self, filename="Agent/MDP/newpolicy.npy"):
#         """保存策略表到 .npy 文件。"""
#         os.makedirs(os.path.dirname(filename), exist_ok=True)
#         np.save(filename, self.policy)

#     def load_policy(self, filename="Agent/MDP/newpolicy.npy"):
#         """加载已有策略；若不存在，则返回全零策略。"""
#         if os.path.exists(filename):
#             return np.load(filename)
#         else:
#             return np.zeros((32, 12, 2), dtype=np.int32)

#     def choose_action(self, game: BlackJack):
#         """
#         在“完整模拟”时调用，返回动作字符串：'hit','stay','switch','fold'。
#         这里会结合当前 game.player_bank 与连赢/连输信息自动更新 bankroll。
#         """
#         # 1) 先算出本局“真实下注” bet
#         bet_real, bank_norm, a_norm = self._compute_bet(game)

#         # 2) 用原来的三维策略表选动作
#         ps = game.get_playervalue()
#         ds = game.total_value(game.dealer_hand[:1]) if game.dealer_hand else 0
#         ua = self.has_usable_ace(game.player_hand) if game.player_hand else 0
#         ps = min(ps, 32)
#         ds = min(ds, 11)
#         a_idx = self.policy[ps, ds, ua]
#         action = {0: "stay", 1: "hit", 2: "switch", 3: "fold"}[a_idx]

#         # 3) 真实 bankroll 更新由外部调用者在 game.settle() 中完成
#         return action

#     def simulate_round(self, game: BlackJack):
#         """
#         这一函数可用于“完整一轮游戏”的封装：
#          1) 开局：game.start()
#          2) 玩家阶段：不断调用 choose_action(game) → game.player_action(action)
#             → 若动作是 stay/switch/fold 跳出
#          3) 庄家阶段：若未爆牌 → game.dealer_action("basic")
#          4) 结算前，先算 outcome，再算 bet，再 game.settle(outcome, bet)
#         """
#         # 1) 开局
#         game.start()

#         # 2) 玩家阶段
#         while game.status == "continue":
#             action = self.choose_action(game)
#             game.player_action(action)
#             if action in ["stay", "switch", "fold"]:
#                 break

#         # 3) 庄家阶段（如果玩家没爆）
#         if game.status == "continue":
#             game.dealer_action("basic")

#         # 4) 结算
#         outcome = game.game_result()
#         bet_real, _, _ = self._compute_bet(game)
#         game.settle(outcome, bet_real)

#         return outcome, bet_real


# if __name__ == "__main__":
#     # 示例：先做价值迭代并保存策略
#     agent = MDPAgentWithBet(is_train=True)
#     print(">>> 开始价值迭代 ...")
#     agent.value_iteration()
#     print(">>> 价值迭代完成，开始保存策略 ...")
#     agent.save_policy("Agent/MDP/newpolicy.npy")
#     print(">>> 策略保存完毕。")

#     # 下面示例演示如何用 simulate_round 完整跑一局，并观察 bankroll 变化
#     # game = CasinoBlackJack(mode="novel")  # 确保 BlackJack 类已改为 CasinoBlackJack
#     # game.full_reset()                     # 重置资金与状态
#     # for _ in range(1000):
#     #     outcome, bet = agent.simulate_round(game)
#     #     # game.player_bank 已自动在 settle 中更新
#     # print("最后剩余资金:", game.player_bank)


# Agent/MDP/MDPagentwithbet.py

import random
import numpy as np
import os

# 请务必让 Python 能够 import 到 Game/BlackJack.py 中的 BlackJack 类
from Game.BlackJack import BlackJack


class MDPAgentWithBet:
    """
    MDP Agent with Bet：把“玩家现有资金”和“当前下注比例 a”并入状态空间，
    直接做价值迭代，最大化“完整 bankroll”。
    """

    def __init__(self,
                 game_mode="novel",
                 gamma=1.0,
                 eps=1e-4,
                 is_train=False,
                 initial_bank=100.0):
        """
        参数:
          game_mode: "traditional" 或 "novel"
          gamma: 折扣因子
          eps: 价值迭代的收敛阈值
          is_train: True = 新建策略并做价值迭代；False = 直接 load 已存好的 newpolicy.npy
          initial_bank: 初始池内总资金（为了避免 overflow，这里要设很小，例如 100）
        """
        self.game_mode = game_mode
        self.gamma = gamma
        self.eps = eps
        self.initial_bank = initial_bank

        # ----------------- 离散化设置 -----------------
        # 把 bankroll ([0, initial_bank]) 等分成 11 档：0, 10, 20, …, 100
        self.bank_buckets = 11
        self.bank_step = initial_bank / (self.bank_buckets - 1)  # 每档间隔

        # 把 a_norm = a / 0.1 放入 5 档：[0.5, 0.75, 1.0, 1.25, 1.5]
        self.a_bins = np.array([0.5, 0.75, 1.0, 1.25, 1.5], dtype=np.float32)
        self.a_buckets = len(self.a_bins)

        # ----------------- 构建五维价值表 -----------------
        # 状态空间：
        #   ps ∈ {0..32}, ds ∈ {0..11}, ua ∈ {0,1},
        #   bank_bucket ∈ {0..bank_buckets-1}, a_bucket ∈ {0..a_buckets-1}
        #
        # 其中 ps=32 表示玩家超21的“截顶”， ds=11 表示庄家明牌 ≥ 10
        self.value_table = np.zeros(
            (33, 12, 2, self.bank_buckets, self.a_buckets), dtype=np.float64
        )

        # 策略表：同样五维，每格存动作索引 0/1/2/3
        if is_train:
            self.policy = np.zeros(
                (33, 12, 2, self.bank_buckets, self.a_buckets), dtype=np.int32
            )
        else:
            self.policy = self.load_policy("Agent/MDP/newpolicy.npy")

        # 动作空间
        self.action_space = [0, 1, 2, 3]  # 0=stay, 1=hit, 2=switch, 3=fold

        # 卡片出现概率
        self.card_probabilities = {
            1: 1/13,
            2: 1/13,
            3: 1/13,
            4: 1/13,
            5: 1/13,
            6: 1/13,
            7: 1/13,
            8: 1/13,
            9: 1/13,
            10: 4/13,
        }

    @staticmethod
    def has_usable_ace(hand):
        """返回 0/1：手牌中是否含有“软”Ace。"""
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
        return int(ace and (value + 10) <= 21)

    def _bank_to_bucket(self, bank_float):
        """
        把实际资金 bank_float（[0, initial_bank]）映射到一个离散档位：
        返回 bank_bucket ∈ [0..bank_buckets-1]
        """
        # 截断到 [0, initial_bank]
        b = max(0.0, min(bank_float, self.initial_bank))
        idx = int(round(b / self.bank_step))
        return min(idx, self.bank_buckets - 1)

    def _a_to_bucket(self, a_norm):
        """
        把当前 a_norm（即 a / 0.1）映射到最接近的离散档位：
        返回 a_bucket ∈ [0..a_buckets-1]
        """
        idx = int(np.argmin(np.abs(self.a_bins - a_norm)))
        return idx

    def _compute_bet(self, game: BlackJack):
        """
        计算本轮真实下注 bet_real，并且返回离散化后的 (bank_bucket, a_bucket)：
        • a = 0.1 为基准
        • 玩家首两张含 A/10 → a *= 1.5
        • 庄家明牌含 A/10 → a *= 0.75
        • 连输≥5 → a *= 1.5；连赢≥5 → a *= 0.75
        • 随机扰动 × [0.9,1.1]
        • 截断 a ∈ [0,1]
        • bet_real = a × game.player_bank

        返回:
          bet_real       （实数下注）
          bank_bucket    （离散后资金档）
          a_bucket       （离散后 a_norm 档位）
        """
        # 1. a 基准
        a = 0.1
        # 2. 玩家首两张
        for c in game.player_hand:
            if c["number"] == "A" or c["number"] in ["10","J","Q","K"]:
                a *= 1.5
                break
        # 3. 庄家明牌
        up = game.dealer_hand[0]["number"]
        if up == "A" or up in ["10","J","Q","K"]:
            a *= 0.75
        # 4. 连输/连赢
        if game.lose_cnt >= 5:
            a *= 1.5
        elif game.win_cnt >= 5:
            a *= 0.75
        # 5. 随机扰动
        a *= random.uniform(0.9, 1.1)
        # 截断 [0,1]
        a = max(0.0, min(a, 1.0))

        bank = game.player_bank
        bet_real = a * bank

        # 离散化
        bank_bucket = self._bank_to_bucket(bank)
        a_norm = a / 0.1
        a_bucket = self._a_to_bucket(a_norm)

        return bet_real, bank_bucket, a_bucket

    def calculate_state_value(self, ps, ds, ua, bb, ab, game, action):
        """
        计算状态 (ps, ds, ua, bank_bucket, a_bucket) 下执行某动作的
        “真实即时奖励 + 折扣后下一状态价值”：
        
        1) 先算出“对 1 元下注”的 expected_unit（与 _evaluate_xxx 相同）；
        2) 从 bb, ab 恢复出真实 bank 和真实 a_norm，
           计算本轮真实下注 bet_real = a × bank；
        3) 真实即时奖励 R = unit_return × bet_real；
        4) 折扣后值 γ × V(next_ps, next_ds, next_ua, next_bb, next_ab)。

        注意：如果传入的 game==None，说明这是在 value_iteration 中被调用，
        此时我们把 win_cnt 和 lose_cnt 都当作 0（即不考虑连输连赢额外影响）。
        """
        # ---------- 取出 game.win_cnt / lose_cnt（如果 game is None，就设为 0） ----------
        if game is None:
            game_win = 0
            game_lose = 0
        else:
            game_win = game.win_cnt
            game_lose = game.lose_cnt

        # ---------- 1) 先算出“单位赌注”下的 expected_unit ----------
        if action == 0:      # stay
            unit_return = self._evaluate_stick(ps, ds, ua, game)
        elif action == 1:    # hit
            unit_return = self._evaluate_hit(ps, ds, ua, game)
        elif action == 2:    # switch
            unit_return = self._evaluate_switch(ps, ds, ua, game)
        elif action == 3:    # fold
            unit_return = self._evaluate_fold(ps, ds, ua, game)
        else:
            raise ValueError("Invalid action index.")

        # ---------- 2) 从 bb, ab 恢复真实 bank、真实 a_norm ----------
        bank = bb * self.bank_step
        a_norm = self.a_bins[ab]  # 比如 0.5,0.75,1.0,1.25,1.5
        a = a_norm * 0.1          # 恢复真实投注比例
        bet_real = a * bank       # 本轮真实下注

        # ---------- 3) 真实即时奖励 R ----------
        #    玩家本局净利 R = unit_return * bet_real
        R = unit_return * bet_real

        # ---------- 4) 根据当前 action 推导“下一状态” ps',ds',ua',bb',ab' ----------
        # 为了不破坏真实 game，我们用一个 DummyGame 来模拟下一状态
        dummy = type("DummyGame", (), {})()
        # 构造 dummy 的手牌（只需保证 ps, ds, ua 对应的数值即可）
        dummy.player_hand = [{"number": str(min(ps, 11)), "suit": None}]
        dummy.dealer_hand = [{"number": str(ds), "suit": None}]
        # 重要：把 dummy.player_bank, dummy.win_cnt, dummy.lose_cnt 都设为上面恢复的 bank、game_win、game_lose
        dummy.player_bank = bank
        dummy.win_cnt = game_win
        dummy.lose_cnt = game_lose

        # 模拟执行 action → 推导 new_ps, new_ds, new_ua
        # —— 这里简化：只关心“对 1 元下注”时的下一状态，具体逻辑与 _evaluate_xxx 函数保持一致。
        if action == 0:  # stay
            new_ps = ps
            new_ds = ds
            new_ua = ua
        elif action == 1:  # hit
            new_ps = ps
            new_ds = ds
            new_ua = ua
        elif action == 2:  # switch
            new_ps = ps
            new_ds = ds
            new_ua = ua
        else:  # action == 3 fold
            new_ps = ps
            new_ds = ds
            new_ua = ua

        # 下一轮 bankroll = bank + R
        bank_next = bank + R
        bank_next = max(0.0, min(bank_next, self.initial_bank))
        bb_next = self._bank_to_bucket(bank_next)

        # 下一轮 a_norm 也会因连输连赢、明牌变化重新计算，但 value_iteration 中只做“单位计算”：
        #   为了保证“状态数量可控”，这里简化：下一 a_bucket 直接用当前 ab（也可以额外枚举）
        ab_next = ab

        # ---------- 5) 返回 R + γV(next_state) ----------
        return R + self.gamma * self.value_table[new_ps, new_ds, new_ua, bb_next, ab_next]

    def _evaluate_stick(self, ps, ds, ua, game: BlackJack):
        """
        “停牌”后由庄家补牌得出的“单位赌注”期望（简化：只看下一张）：
        与上个版本一致，只返回“对 1 元下注”的单位回报。
        """
        dealer_probs = self._calculate_dealer_probabilities(ds)
        exp_unit = 0.0
        for ds2, p in dealer_probs.items():
            if ds2 == 'bust':
                if self.game_mode == "novel":
                    if ps <= 21:
                        exp_unit += p
                else:
                    exp_unit += p
            else:
                d = int(ds2)
                if ps > 21:
                    exp_unit -= p
                else:
                    if d > ps:
                        exp_unit -= p
                    elif d < ps:
                        exp_unit += p
        return exp_unit

    def _evaluate_hit(self, ps, ds, ua, game: BlackJack):
        """“要牌”后的单位期望（简化只看下一张）"""
        exp_unit = 0.0
        for card_val, p in self.card_probabilities.items():
            new_sum = ps + card_val
            new_ua = ua
            if card_val == 1 and (new_sum + 10) <= 21:
                new_sum += 10
                new_ua = 1
            if new_sum > 21:
                exp_unit += p * (-1)
            else:
                # 找 (new_sum, ds, new_ua) 三维中“最优”那个 bank_bucket/a_bucket，对应 V[new_sum, ds, new_ua, :, :].max()
                vnext = self.value_table[new_sum, ds, new_ua, :, :].max()
                exp_unit += p * (self.gamma * vnext)
        return exp_unit

    def _evaluate_switch(self, ps, ds, ua, game: BlackJack):
        """“换牌”后的单位期望"""
        exp_unit = 0.0
        for card_val, p in self.card_probabilities.items():
            new_sum = ps - card_val + ds
            new_ds = card_val
            new_ua = ua
            if ds == 1 and (new_sum + 10) <= 21:
                new_sum += 10
                new_ua = 1
            if new_sum > 21:
                exp_unit += p * (-1)
            else:
                vnext = self.value_table[new_sum, new_ds, new_ua, :, :].max()
                exp_unit += p * (self.gamma * vnext)
        return exp_unit

    def _evaluate_fold(self, ps, ds, ua, game: BlackJack):
        """“弃牌”后的单位期望"""
        exp_unit = 0.0
        for new_ds, p in self.card_probabilities.items():
            vnext = self.value_table[ps, new_ds, ua, :, :].max()
            exp_unit += p * (self.gamma * vnext)
        return exp_unit

    def _calculate_dealer_probabilities(self, dealer_showing):
        """ 只考虑庄家下一张牌：<21 保留，≥21 记为 'bust' """
        probs = {i: 1/13 for i in range(1, 10)}
        probs[10] = 4/13
        dealer_probs = {}
        for cv, p in probs.items():
            s = dealer_showing + cv
            if s < 21:
                dealer_probs.setdefault(s, 0.0)
                dealer_probs[s] += p
            else:
                dealer_probs.setdefault('bust', 0.0)
                dealer_probs['bust'] += p
        return dealer_probs

    def evaluate_state(self, ps, ds, ua, bb, ab):
        """
        枚举 4 种动作，返回 R + γ V(next_state) 的最大值。
        """
        best = -np.inf
        for a in self.action_space:
            val = self.calculate_state_value(ps, ds, ua, bb, ab, None, a)
            if val > best:
                best = val
        return best

    def value_iteration(self):
        """
        对五维 (ps, ds, ua, bank_bucket, a_bucket) 进行价值迭代，
        使用 R=“unit_return × bet_real” + γ V(next) 进行更新。
        """
        max_iters = 100
        for it in range(max_iters):
            delta = 0.0
            # 遍历所有可能的离散状态
            for ps in range(1, 22):
                for ds in range(1, 12):
                    for ua in range(2):
                        for bb in range(self.bank_buckets):
                            for ab in range(self.a_buckets):
                                old_v = self.value_table[ps, ds, ua, bb, ab]
                                new_v = self.evaluate_state(ps, ds, ua, bb, ab)
                                self.value_table[ps, ds, ua, bb, ab] = new_v
                                delta = max(delta, abs(old_v - new_v))
            if delta < self.eps:
                break

        # 迭代结束后，提取策略 newpolicy.npy
        for ps in range(1, 22):
            for ds in range(1, 12):
                for ua in range(2):
                    for bb in range(self.bank_buckets):
                        for ab in range(self.a_buckets):
                            best_a = 0
                            best_v = -np.inf
                            for a in self.action_space:
                                val = self.calculate_state_value(ps, ds, ua, bb, ab, None, a)
                                if val > best_v:
                                    best_v = val
                                    best_a = a
                            self.policy[ps, ds, ua, bb, ab] = best_a

    def save_policy(self, filename="Agent/MDP/newpolicy.npy"):
        """ 保存五维策略 newpolicy.npy """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        np.save(filename, self.policy)

    def load_policy(self, filename="Agent/MDP/newpolicy.npy"):
        """ 加载已保存策略；如果不存在则返回全零策略 """
        if os.path.exists(filename):
            return np.load(filename)
        else:
            return np.zeros((33, 12, 2, self.bank_buckets, self.a_buckets), dtype=np.int32)

    def choose_action(self, game: BlackJack):
        """
        完整模拟时调用，返回动作字符串：'hit','stay','switch','fold'。
        这里会结合当前 game.player_bank 与连赢/连输信息自动更新 bankroll。
        """
        # 1) 先算 bet_real，并获取 (bank_bucket, a_bucket)
        bet_real, bank_bucket, a_bucket = self._compute_bet(game)

        # 2) 用五维策略表查出当前状态下最优动作
        ps = game.get_playervalue()
        ds = game.total_value(game.dealer_hand[:1]) if game.dealer_hand else 0
        ua = self.has_usable_ace(game.player_hand) if game.player_hand else 0
        ps = min(ps, 32)
        ds = min(ds, 11)
        a_idx = self.policy[ps, ds, ua, bank_bucket, a_bucket]
        action = {0: "stay", 1: "hit", 2: "switch", 3: "fold"}[a_idx]
        return action

    def simulate_round(self, game: BlackJack):
        """
        完整一轮：
          1) game.start()
          2) 玩家阶段：不断调用 choose_action(game) → game.player_action(action)
             → 若动作是 stay/switch/fold 跳出
          3) 庄家阶段：若未爆牌 → game.dealer_action("basic")
          4) 结算 outcome, bet_real → game.settle(outcome, bet_real)
        返回： (outcome, bet_real)
        """
        # 1) 开局
        game.start()

        # 2) 玩家阶段
        while game.status == "continue":
            action = self.choose_action(game)
            game.player_action(action)
            if action in ["stay", "switch", "fold"]:
                break

        # 3) 庄家阶段
        if game.status == "continue":
            game.dealer_action("basic")

        # 4) 结算
        outcome = game.game_result()
        bet_real, _, _ = self._compute_bet(game)
        game.settle(outcome, bet_real)
        return outcome, bet_real


if __name__ == "__main__":
    # --------- 训练并保存 newpolicy.npy ---------
    agent = MDPAgentWithBet(is_train=True, initial_bank=1.0)
    print(">>> 开始价值迭代（包含 bankroll 和 a）...")
    agent.value_iteration()
    print(">>> 价值迭代完成，开始保存策略 newpolicy.npy ...")
    agent.save_policy("Agent/MDP/newpolicy.npy")
    print(">>> newpolicy.npy 已保存。")

 
