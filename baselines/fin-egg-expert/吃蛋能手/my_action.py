# -*- coding: utf-8 -*-
# @Time       : 2020/10/14 11:44
# @Author     : fengjie
# @File       : action.py
# @Description: 动作类

from random import randint


# 中英文对照表
ENG2CH = {
    "Single": "单张",
    "Pair": "对子",
    "Trips": "三张",
    "ThreePair": "三连对",
    "ThreeWithTwo": "三带二",
    "TwoTrips": "钢板",
    "Straight": "顺子",
    "StraightFlush": "同花顺",
    "Bomb": "炸弹",
    "PASS": "过"
}


class MyAction(object):

    def __init__(self, logFile):
        import io
        if isinstance(logFile, str):
            logFile = io.StringIO()
        self._logFile = logFile
        self.action = []
        self.act_range = -1

    def parse(self, msg, state):
        self.action = msg["actionList"]
        self.act_range = msg["indexRange"]
        print('\n', file=self._logFile)
        print("1. --- 我方可打牌组：{}".format(self.action), file=self._logFile)
        print("可选动作范围为：0至{}".format(self.act_range), file=self._logFile)
        if self.action[0][0] == 'tribute':
            return 0  # TODO: 选择一张进贡的牌
        elif self.action[0][0] == 'back':
            # 从权值最小的中，选择一张还贡
            # 如果最小的是三带二，从二中拆开
            c = state.myOrderedCards[-1][2][0]
            if state.myOrderedCards[-1][0] == 'ThreeWithTwo':
                greater_card = state.myOrderedCards[-1][1]
                cards = state.myOrderedCards[-1][2]
                c = self.getTwo(cards, greater_card, state._curRank)
            idx = self.findBackIndex(c, self.action)
            print("我方组牌为：{}，准备还贡".format(state.myOrderedCards), file=self._logFile)
            print('我方还贡 = {}'.format(self.action[idx]), file=self._logFile)
            return idx
        else: # 如果队友出的牌不大，则接牌，过大  且上家没接，则pass
            if not state.prevPlayerTaked and state.mateGreater and self.action[0][0] == 'PASS':
                # 队友出过大牌，直接PASS
                print("我方因为队友打出：{}，这轮选择PASS".format(state.notTakeActionReason), file=self._logFile)
                return 0
            else:
                index = self.getActionIndex(state, self.action)  # 第三个函数
                print('打了这个')
                print(self.action[index])
                print("2. --- 我方打出：{}".format(self.action[index]), file=self._logFile)
                return index
                # if index >= 0 and index <= self.act_range:
                #     print("2. --- 我方打出：{}".format(self.action[index]), file=self._logFile)
                #     return index
                # else:
                #     print("2. --- 我方打出：{}".format(self.action[0]), file=self._logFile)
                #     return 0




    def getActionIndex(self, state, actionList):
        """
        从action中搜索我们符合我们牌组，返回index， 要求权值为牌组中最低者
        :param orderCards: 自己组好的牌组
        [
                ['Bomb', '4', ['S4', 'H4', 'C4', 'D4']],
                ['ThreeWithTwo', 'A', ['SA', 'HA', 'DA', 'C8', 'C8']]
            ]
            类似于这样的结构
        :param actionList: exe给出的可出的牌组，类似于
        [['PASS', 'PASS', 'PASS'], ['Bomb', '4', ['S4', 'H4', 'C4', 'D4', 'H2']]] 结构，

        :return: index，官方给的actionList中搜索合适的actionList
        """
        print('可出牌 {}'.format(actionList))
        for i in range(len(state.myOrderedCards) - 1, -1, -1):  # 倒序遍历orderCards，权值从小到大
            c = state.myOrderedCards[i]
            idx = self.inAction(c, actionList)
            if idx != -1:  # 如果此项位于actionList中
                return idx
        # 没在actionList中找到，仅当对手手牌小于17张再硬接
        # if state.competitorCardNums[0] <= 17 or state.competitorCardNums[1] <= 17:
        #     return 1 if len(actionList) > 1 else 0
        if state.competitorCardNums[0] <= 10 or state.competitorCardNums[1] <= 17:
            return 1 if len(actionList) > 1 else 0
        else:
            return 0


    def inAction(self, c, actionList):
        """
        返回 c 是否在 actionList中
        :param c:
        :param actionList:
        :return:
        """
        for index, a in enumerate(actionList):
            if c[0] != a[0] or c[1] != a[1]:
                continue
            if len(c[2]) != len(a[2]):  # 张数不一样 continue
                continue
            tmp = a[2].copy()
            for x in c[2]:
                if x in tmp:
                    tmp.remove(x)
                else:
                    break
            if len(tmp) == 0:
                return index
        return -1


    def findBackIndex(self, c, actionList):
        for idx, a in enumerate(actionList):
            if c == a[2][0]:
                return idx
        return 0


    def getTwo(self, cards, tri, rank_card):
        """
        获得三带二中  二的牌型, 需要考虑万能牌
        :param cards: 三带二共5张牌 ['S4', 'H4', 'C4', 'D4', 'H2']
        :param tri: 三的牌型
        :param rank_card: rank牌
        :return:
        """
        res = None
        for i in range(len(cards)):
            if cards[i][1] != tri:
                res = cards[i][1]
                # 如果不是rank牌，直接返回，是rank牌，还得继续看rank牌是否为凑的
                if res != rank_card:
                    return res
        return res
