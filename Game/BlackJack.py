# import random

# class BlackJack:
#     heart = "\u2665"
#     spade = "\u2660"
#     diamond = "\u2666"
#     club = "\u2663"

#     suits = {
#         "diamonds": diamond,
#         "hearts": heart,
#         "spades": spade,
#         "clubs": club
#     }
    
    
#     def __init__(self, mode = "traditional"):
#         self.deck = self.generate_deck()
#         random.shuffle(self.deck)
#         self.player_hand = []
#         self.dealer_hand = []
#         if mode not in ["traditional", "novel"]:
#             raise ValueError("Invalid game mode")   
        
#         self.card_count = {
#                       '2': 0,
#                       '3': 0,
#                       '4': 0,
#                       '5': 0,
#                       '6': 0,
#                       '7': 0,
#                       '8': 0,
#                       '9': 0,
#                       '10': 0,
#                       'A': 0}
#         self.mode = mode
#         self.status = "continue"

#     @staticmethod
#     def format_cards(cards):
#         """Format a list of cards into a readable string."""
        
#         result = ""
#         for card in cards:
#             suit = BlackJack.suits[card["suit"]]
#             result += f"{card['number']}{suit} "
        
#         return result.strip()
    
#     def generate_deck(self):
#         """Generate a full deck of cards with all suits and numbers."""
        
#         numbers = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
#         suits = ['hearts', 'diamonds', 'clubs', 'spades']
#         deck = [{'number': number, 'suit': suit} for number in numbers for suit in suits]
#         return deck
    
#     def total_value(self, hand: list):
#         """Compute the total value of a hand, taking aces into account."""
        
#         value = 0
#         aces = 0
#         for card in hand:
#             if card['number'] in ['J', 'Q', 'K']:
#                 value += 10
#             elif card['number'] == 'A':
#                 value += 11
#                 aces += 1
#             else:
#                 value += int(card['number'])
                
#         while value > 21 and aces != 0:
#             value -= 10
#             aces -= 1
#         return value
    
#     def draw_card(self):
#         """Draw a card from the deck and update the card count."""
        
#         card = self.deck.pop()
#         if card["number"] in ['J', 'Q', 'K']: 
#             self.card_count["10"] += 1
#         else:
#             self.card_count[card["number"]] += 1
#         return card

#     def fold(self):
#         """Fold a card from the dealer's hand."""
#         if self.dealer_hand == []:
#             print("dealer has no card now")
#         else:
#             self.dealer_hand.pop(0)
#     def switch(self):
#         """Switch a card from the dealer's hand with the player's hand."""
#         if self.dealer_hand == []:
#             print("dealer has no card now")
#         else:
#             card1 = self.dealer_hand.pop(0)
#             card2 = self.player_hand.pop(0)
#             self.dealer_hand.append(card2)
#             self.player_hand.append(card1)

#     def player_action(self, action):
#         """Process the player's action, either hit or stay."""
#         assert action in ["hit", "stay","fold","switch"]
#         if action == "hit":
#             self.player_hand.append(self.draw_card())
#             return self.update_status()
#         elif action == 'fold':
#             self.fold()
#             return self.update_status()
#         elif action == 'switch':
#             self.switch()
#             return self.update_status()
#         elif action == "stay":
#             return self.update_status()
    
#     def dealer_action(self, strategy: str = "basic"):
#         """Make the dealer perform actions based on the specified strategy."""
        
#         if strategy == "basic": #没到17就一直拿，17以上就看自己的牌值，比player高就拿，比player低就停
#             while (self.total_value(self.dealer_hand) < 17 or (self.total_value(self.dealer_hand) >= 17 and self.total_value(self.dealer_hand)<self.total_value(self.player_hand) and self.total_value(self.player_hand)<=21) ):
#                 self.dealer_hand.append(self.draw_card())
#         elif strategy == "greedy":
#             while self.total_value(self.dealer_hand) < 21:
#                 self.dealer_hand.append(self.draw_card())
#         elif strategy == "random":
#             while random.choice([True, False]):
#                 self.dealer_hand.append(self.draw_card())

    
#     def update_status(self, status = "continue"):
#         """Update the game status based on the player's hand value."""
        
#         player_value = self.get_playervalue()
#         if player_value > 21:
#             self.status = "player_bust"
#         else:
#             self.status = status
#         return self.status
    
#     def get_status(self):
#         return self.status

#     def get_dealervalue(self):
#         """Get the total value of the dealer's hand."""
#         return self.total_value(self.dealer_hand)

#     def get_playervalue(self):
#         """Get the total value of the player's hand."""
#         return self.total_value(self.player_hand)
    
    
#     """
#     一共两种gamemode，分别是对于player bust后的不同判断方式
#     traditional：Player bust后直接判lose
#     novel：Player bust后看Dealer，若dealer也bust则算draw
#     """
#     def game_result(self):
#         """Determine the result of the game based on player and dealer hand values."""

#         dealer_value = self.get_dealervalue()
#         player_value = self.get_playervalue()
        
#         if self.mode == "traditional":
#             if player_value > 21:
#                 return "lose"
#             elif dealer_value > 21 or player_value > dealer_value:
#                 return "win"
#             elif player_value == dealer_value:
#                 return "draw"
#             else:
#                 return "lose"
#         elif self.mode == "novel":
#             if player_value > 21 and dealer_value <= 21:
#                 return "lose"
#             elif dealer_value > 21 or player_value > dealer_value:
#                 return "win"
#             elif player_value == dealer_value or (player_value > 21 and dealer_value > 21):
#                 return "draw"
#             else:
#                 return "lose"

        
#     def start(self):
#         """Start a new round by dealing two cards each to the player and dealer."""
        
#         self.player_hand = [self.draw_card(), self.draw_card()]
#         self.dealer_hand = [self.draw_card(), self.draw_card()]
#         self.update_status() # init the status as continue
    
#     def reset(self):
#         """Reset the game state and shuffle a new deck."""
        
#         self.deck = self.generate_deck()
#         random.shuffle(self.deck)
#         self.player_hand = []
#         self.dealer_hand = []
#         self.status = "continue"
#         self.card_count = {
#                       '2': 0,
#                       '3': 0,
#                       '4': 0,
#                       '5': 0,
#                       '6': 0,
#                       '7': 0,
#                       '8': 0,
#                       '9': 0,
#                       '10': 0,
#                       'A': 0}
           
#     def play(self, player_action: str, dealer_strategy: str, output = False):
#         """Simulate a turn of the game with the specified player action and dealer strategy."""
        
#         self.dealer_action(dealer_strategy)
#         self.player_action(player_action)
#         if output:
#             print("Dealer has:", game.format_cards(game.dealer_hand), game.total_value(game.dealer_hand))
#         return self.status
        
        
        
# if __name__ == "__main__":
#     game = BlackJack()
#     for round in range(5):
#         game.start()
#         while game.status == "continue":
#             print("Dealer shows:", game.format_cards(game.dealer_hand[:1]))
#             print("Player shows:",game.format_cards(game.player_hand))
#             print('player total value is:',game.total_value(game.player_hand))
#             action = input("Enter an action (hit/stay/switch/fold): ")
#             game.play(action, "basic")
#             if action == "stay":
#                 break
#         print(f"dealer's hand: {game.format_cards(game.dealer_hand)} {game.get_dealervalue()}  player's hand: {game.format_cards(game.player_hand)} {game.get_playervalue()}")
#         print(game.game_result())
#         print(f"card count: {game.card_count}")
#         print("================================")
#         game.reset()




import random

class BlackJack:
    heart = "\u2665"
    spade = "\u2660"
    diamond = "\u2666"
    club = "\u2663"

    suits = {
        "diamonds": diamond,
        "hearts": heart,
        "spades": spade,
        "clubs": club
    }

    def __init__(
        self,
        mode: str = "traditional",
        player_bank: float = 100000.0,
        dealer_bank: float = 1000000.0,
    ):
        # -------------- 牌局初始化 --------------
        self.deck = self.generate_deck()
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []

        if mode not in ["traditional", "novel"]:
            raise ValueError("Invalid game mode")
        self.mode = mode
        self.status = "continue"

        # 初始化牌点计数（可选）
        self.card_count = {str(n): 0 for n in range(2, 11)}
        self.card_count.update({'J': 0, 'Q': 0, 'K': 0, 'A': 0})

        # -------------- 银行与连胜/连败统计 --------------
        self.init_player_bank = player_bank
        self.init_dealer_bank = dealer_bank
        self.player_bank = player_bank
        self.dealer_bank = dealer_bank
        self.win_cnt = 0    # 连胜计数
        self.lose_cnt = 0   # 连败计数

    @staticmethod
    def format_cards(cards):
        """Format a list of cards into a readable string."""
        result = ""
        for card in cards:
            suit = BlackJack.suits[card["suit"]]
            result += f"{card['number']}{suit} "
        return result.strip()

    def generate_deck(self):
        """Generate a full deck of cards with all suits and numbers."""
        numbers = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        return [{'number': number, 'suit': suit} for number in numbers for suit in suits]

    def total_value(self, hand: list):
        """Compute the total value of a hand, taking aces into account."""
        value = 0
        aces = 0
        for card in hand:
            num = card['number']
            if num in ['J', 'Q', 'K']:
                value += 10
            elif num == 'A':
                value += 11
                aces += 1
            else:
                value += int(num)
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    def draw_card(self):
        """Draw a card from the deck and update the card count."""
        if not self.deck:
            # 如果牌堆空了，就重新洗一副牌
            self.deck = self.generate_deck()
            random.shuffle(self.deck)
        card = self.deck.pop()
        num = card["number"]
        if num in ['J', 'Q', 'K']:
            self.card_count["10"] += 1
        else:
            self.card_count[num] += 1
        return card

    # -------------- 可对外调用的资金/下注相关方法 --------------

    def reset_round(self):
        """
        只重置本局的手牌、状态、以及重新洗牌，
        保留 player_bank, dealer_bank, win_cnt, lose_cnt 不变。
        """
        self.deck = self.generate_deck()
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []
        self.status = "continue"

        # 牌点计数可选是否重置，如果需要从累计数开始，请删除下一行
        self.card_count = {str(n): 0 for n in range(2, 11)}
        self.card_count.update({'J': 0, 'Q': 0, 'K': 0, 'A': 0})

    def full_reset(self):
        """
        硬重置：包括资金、连胜/连败计数都重置。
        """
        self.player_bank = self.init_player_bank
        self.dealer_bank = self.init_dealer_bank
        self.win_cnt = 0
        self.lose_cnt = 0
        self.reset_round()

    def settle(self, result: str, bet: float):
        """
        结算本轮输赢，更新 player_bank、dealer_bank，并更新连胜/连败计数。
        result: "win", "lose", or "draw"
        bet: 本轮下注数量
        """
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

    # -------------- 玩家 & 庄家操作 --------------

    def fold(self):
        """Fold a card from the dealer's hand (移除庄家最顶上的一张牌)."""
        if self.dealer_hand:
            self.dealer_hand.pop(0)

    def switch(self):
        """Switch a card: 玩家与庄家各丢最顶上的一张，交换后各自补牌."""
        if self.dealer_hand and self.player_hand:
            card1 = self.dealer_hand.pop(0)
            card2 = self.player_hand.pop(0)
            self.dealer_hand.append(card2)
            self.player_hand.append(card1)

    def player_action(self, action: str):
        """
        Process the player's action: "hit", "stay", "switch", or "fold".
        返回更新后的 status。
        """
        assert action in ["hit", "stay", "fold", "switch"]
        if action == "hit":
            self.player_hand.append(self.draw_card())
            return self.update_status()
        elif action == "fold":
            self.fold()
            return self.update_status()
        elif action == "switch":
            self.switch()
            return self.update_status()
        else:  # "stay"
            return self.update_status()

    def dealer_action(self, strategy: str = "basic"):
        """
        A) “basic” 策略：点数 < 17 一直要牌；
            点数 ≥ 17 时，如果 dealer 点数 < player 点数 且 player ≤ 21，就继续要牌；否则停牌。
        B) “greedy” 策略：只要 dealer 点数 < 21，就要牌；
        C) “random” 策略：随机决定是否继续要牌。
        """
        if strategy == "basic":
            while (
                self.total_value(self.dealer_hand) < 17
                or (
                    self.total_value(self.dealer_hand) >= 17
                    and self.total_value(self.dealer_hand) < self.total_value(self.player_hand)
                    and self.total_value(self.player_hand) <= 21
                )
            ):
                self.dealer_hand.append(self.draw_card())

        elif strategy == "greedy":
            while self.total_value(self.dealer_hand) < 21:
                self.dealer_hand.append(self.draw_card())

        elif strategy == "random":
            while random.choice([True, False]):
                self.dealer_hand.append(self.draw_card())

    # -------------- 状态更新 & 查询 --------------

    def update_status(self, status: str = "continue"):
        """
        Update the game status based on the player's hand value:
         • 如果 player > 21 → "player_bust"
         • 否则 → status（通常是 "continue" 由调用者传入）
        返回 self.status。
        """
        if self.get_playervalue() > 21:
            self.status = "player_bust"
        else:
            self.status = status
        return self.status

    def get_status(self):
        return self.status

    def get_dealervalue(self):
        """Get the total value of the dealer's hand."""
        return self.total_value(self.dealer_hand)

    def get_playervalue(self):
        """Get the total value of the player's hand."""
        return self.total_value(self.player_hand)

    # -------------- 结果判定 --------------

    def game_result(self):
        """
        Determine the result of the game based on player and dealer hand values.
        返回 "win" / "lose" / "draw"。
        traditional: player bust → lose；否则比较大小。
        novel: player 和 dealer 都 bust → draw；player bust 且 dealer ≤21 → lose；dealer bust 或 player>dealer → win；相同 → draw。
        """
        dealer_value = self.get_dealervalue()
        player_value = self.get_playervalue()

        if self.mode == "traditional":
            if player_value > 21:
                return "lose"
            elif dealer_value > 21 or player_value > dealer_value:
                return "win"
            elif player_value == dealer_value:
                return "draw"
            else:
                return "lose"

        else:  # "novel"
            if player_value > 21 and dealer_value <= 21:
                return "lose"
            elif dealer_value > 21 or player_value > dealer_value:
                return "win"
            elif player_value == dealer_value or (player_value > 21 and dealer_value > 21):
                return "draw"
            else:
                return "lose"

    # -------------- 开始与重置 --------------

    def start(self):
        """
        Start a new round: 给玩家和庄家各发两张牌，马上更新 status。
        """
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        self.update_status()  # 初始 status = "continue"
    
    def reset(self):
        """
        重置游戏状态与牌堆，不重置 bankroll/连胜连败：
        1) 重新生成并打乱整副牌
        2) 清空玩家与庄家手牌
        3) status 回到 "continue"
        4) 牌点计数重置
        """
        self.deck = self.generate_deck()
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []
        self.status = "continue"
        self.card_count = {str(n): 0 for n in range(2, 11)}
        self.card_count.update({'J': 0, 'Q': 0, 'K': 0, 'A': 0})

    def play(self, player_action: str, dealer_strategy: str, output: bool = False):
        """
        Simulate a turn of the game with the specified player action and dealer strategy:
        1) 先让庄家执行一次 dealer_action（因为部分规则希望 dealer 先展示明牌）
        2) 然后执行 player_action
        返回更新后的 status。
        """
        self.dealer_action(dealer_strategy)
        self.player_action(player_action)
        if output:
            print(
                "Dealer has:",
                self.format_cards(self.dealer_hand),
                self.total_value(self.dealer_hand),
            )
        return self.status


if __name__ == "__main__":
    # 简单演示用法
    game = BlackJack(mode="novel", player_bank=1000.0, dealer_bank=5000.0)
    for _ in range(5):
        game.start()
        while game.status == "continue":
            print("Dealer shows:", game.format_cards(game.dealer_hand[:1]))
            print("Player shows:", game.format_cards(game.player_hand))
            print("Player total value is:", game.get_playervalue())
            action = input("Enter an action (hit/stay/switch/fold): ")
            game.play(action, "basic")
            if action == "stay":
                break

        print(
            f"Dealer's hand: {game.format_cards(game.dealer_hand)} {game.get_dealervalue()}  "
            f"Player's hand: {game.format_cards(game.player_hand)} {game.get_playervalue()}"
        )
        result = game.game_result()
        print("Round result:", result)

        # 示例：本轮随机下注 10
        bet_amount = 10.0
        game.settle(result, bet_amount)
        print(f"After settlement → Player bank: {game.player_bank:.2f}, Dealer bank: {game.dealer_bank:.2f}")
        print(f"Win streak: {game.win_cnt}, Lose streak: {game.lose_cnt}")
        print("================================")
        game.reset()
