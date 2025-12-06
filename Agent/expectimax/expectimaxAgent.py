import random
from Game.BlackJack import BlackJack

MAX_DEPTH = 1

class ExpectimaxAgent:
    """
    Player that implements an expectimax policy for choosing actions
    """
    def __init__(self):
        # 计算平均牌面值（4张1~10，JQK也算10）
        self.avgVal = float(4 * (1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 10 + 10 + 10)) / float(52)

    def choose_action(self, game: BlackJack):
        averageValue = self.avgVal
        dVal = game.get_dealervalue()
        while dVal < 17:
            dVal += averageValue
        handVal = game.get_playervalue()

        def overall(self, state, agent, pStay, dealerVal, bet, depth=0):
            #print(f"depth: {depth}, state: {state}, dealer: {dealerVal}, agent: {agent}, pStay: {pStay}")

            # 递归终止条件
            if depth > MAX_DEPTH:
                if state > 21:
                    return [-bet]
                elif dealerVal > 21:
                    return [bet]
                elif state > dealerVal:
                    return [bet]
                elif state < dealerVal:
                    return [-bet]
                else:
                    return [0]

            # 玩家停牌或爆牌
            if pStay or state > 21:
                pBust = state > 21
                if pBust and dealerVal <= 21:
                    return [-bet]
                elif dealerVal > 21 and not pBust:
                    return [bet]
                elif dealerVal > state:
                    return [-bet]
                elif state > dealerVal:
                    return [bet]
                else:
                    return [0]

            # 玩家节点
            if agent == 0:
                return maxVal(self, state, agent, pStay, dealerVal, bet, depth + 1)
            # 庄家节点
            else:
                return expVal(self, state, agent, pStay, dealerVal, bet, depth + 1)

        def maxVal(self, state, agent, pStay, dealerVal, bet, depth):
            highScore = [float('-inf')]
            bestAction = None
            actions = ['hit', 'stay', 'fold', 'switch']
            for action in actions:
                nS = generateSuccessor(state, agent, pStay, dealerVal, bet, action)
                score = overall(self, nS[0], 1, nS[1], nS[3], nS[2], depth)
                if score[0] >= highScore[0]:
                    highScore = [score[0], action]
            return highScore

        def expVal(self, state, agent, pStay, dealerVal, bet, depth):
            if dealerVal >= 17:
                nS = generateSuccessor(state, dealerVal, agent, pStay, bet, 'stay')
            else:
                nS = generateSuccessor(state, dealerVal, agent, pStay, bet, 'hit')
            score = overall(self, state, 0, pStay, nS[0], nS[2], depth)
            return [score[0]]

        def generateSuccessor(state, agent, pStay, dealerVal, bet, action):
            averageValue = self.avgVal
            if agent == 0:
                if action == 'hit':
                    return [state + averageValue, pStay, bet, dealerVal]
                elif action == 'stay':
                    return [state, True, bet, dealerVal]
                elif action == 'fold':
                    return [state, pStay, bet, max(0, dealerVal - averageValue)]
                elif action == 'switch':
                    return [state, pStay, bet, dealerVal]
            else:
                if action == 'hit':
                    return [state, pStay, bet, dealerVal + averageValue]
                elif action == 'stay':
                    return [state, pStay, bet, dealerVal]

        # 启动 expectimax 递归并返回最佳动作
        return overall(self, handVal, 0, False, dVal, 10, 0)[1]
