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
                print('可出牌 {}'.format(self.action))
                if state.othersPlayerPass: # 如果自己上一次出的牌很大，别人都PASS了，为主动出牌阶段
                    # 如果队友只剩一张牌
                    if state.mateCardNums == 1:
                        if len(state.myOrderedCards) == 1: # 自己只剩一手，直接出就赢了
                            return self.getActionIndex(state, self.action)
                        if state.competitorCardNums[1] == 1: # 下家也只剩1张了
                            index = self.getIndexNotSingle(state, self.action)  # 选非单张出牌， 只有单张出最大
                            self.print_my_act(index)
                            return index
                        else:
                            # 优先出最小单张让队友过
                            index = 1 if len(self.action) > 1 and self.action[0][0] == 'Single' else self.getActionIndex(state, self.action)
                            self.print_my_act(index)
                            return index
                    # 如果对手只剩一张手牌了，不能出单张
                    if state.competitorCardNums[0] == 1 or state.competitorCardNums[1] == 1:
                        index = self.getIndexNotSingle(state, self.action) # 选非单张出牌， 只有单张出最大
                        self.print_my_act(index)
                        return index

                    # 优先出顺子
                    for i in range(len(state.myOrderedCards) - 1, -1, -1):  # 倒序遍历orderCards，权值从小到大
                        c = state.myOrderedCards[i]
                        if c[0] == 'Straight':
                            idx = self.inAction(c, self.action)
                            if idx != -1:  # 如果此项位于actionList中
                                return idx

                    # 考虑场上的牌(记牌器)，选择合适的牌型出
                    c = self.getActionConsiderRemaining(state.remainingCards, state.myOrderedCards)
                    if len(c) > 0:
                        index = self.inAction(c, self.action)
                        if index != -1:
                            self.print_my_act(index)
                            return index


                # 正常情况的接牌
                index = self.getActionIndex(state, self.action)
                self.print_my_act(index)
                return index


    def print_my_act(self, index):
        print('打了这个')
        print(self.action[index])
        print("2. --- 我方打出：{}".format(self.action[index]), file=self._logFile)


    def getActionConsiderRemaining(self, remainingCards, myOrderedCards):
        """
        TODO: 通过记牌器remainingCards，考虑下一步出什么牌
        :param remainingCards: 场上剩余没出的手牌，数据格式
        {'A': 2, '2': 2, '3': 8, '4': 8, '5': 5, '6': 8, '7': 6, '8': 8, '9': 8,
                  'T': 4, 'J': 1, 'Q': 8, 'K': 0, 'B': 1, 'R': 2 }
        :param myOrderedCards: 自己组好的牌，数据格式类似于, 权值已经从大到小排好序
        [
            ['Bomb', '4', ['S4', 'H4', 'C4', 'D4']],
            ['ThreeWithTwo', 'A', ['SA', 'HA', 'DA', 'C8', 'C8']]
        ]
        :return: 返回需要出的牌
        """
        danzhang = []
        duizi = []
        guangsan = []
        sandaier = []
        for each in myOrderedCards:
            if each[0] == 'Single':
                danzhang.append(each)
            if each[0] == 'Pair':
                duizi.append(each)
            if each[0] == 'Trips':
                guangsan.append(each)
            if each[0] == 'ThreeWithTwo':
                sandaier.append(each)  # 对各类手牌分类

        x_danzhang = []  # 如果手上没有单张大牌收牌，则先不出小的单张。 到后面统一考虑
        # 如果手上有大的单张，但是没有小的单张，先不出单张
        if danzhang != []:
            for each in danzhang:
                if each[1] == 'R' \
                        or (each[1] == 'B') \
                        or (remainingCards['R'] == 0 and remainingCards['B'] == 0 and each[1] == 'A') \
                        or (remainingCards['R'] == 0 and remainingCards['B'] == 0 and remainingCards['A'] <= 2 and each[
                    1] == 'K') \
                        or (remainingCards['R'] == 0 and remainingCards['B'] == 0 and remainingCards['A'] <= 2 and
                            remainingCards['K'] == 0 and each[1] == 'Q') \
                        or (remainingCards['R'] == 0 and remainingCards['B'] == 0 and remainingCards['A'] <= 2 and
                            remainingCards['K'] == 0 and remainingCards['Q'] == 0 and each[1] == 'J'):

                    # 当手上有单张大小王或者外面没有大小王，或者在残局时的最大手牌与记牌器中牌作比较。
                    for each1 in danzhang:
                        if each1[1] == '3' \
                                or each1[1] == '4' \
                                or each1[1] == '5' \
                                or each1[1] == '6' \
                                or each1[1] == '7' \
                                or each1[1] == '8' \
                                or each1[1] == '9' \
                                or each1[1] == 'T' \
                                or each1[1] == '2':  # 且当手上有小牌时
                            x_danzhang = danzhang[-1]  # 由于权值从大到小出牌，所以选最小的

        y_duizi = []  # 对子和单张同理
        if duizi != []:
            for each in duizi:
                if each[1] == 'R' \
                        or each[1] == 'B' \
                        or each[1] == 'A' \
                        or (remainingCards['R'] < 2 and remainingCards['B'] < 2 and remainingCards['A'] < 3 and each[
                    1] == 'K') \
                        or (remainingCards['R'] < 2 and remainingCards['B'] < 2 and remainingCards['A'] < 3 and
                            remainingCards['K'] < 3 and each[1] == 'Q') \
                        or (remainingCards['R'] < 2 and remainingCards['B'] < 2 and remainingCards['A'] < 3 and
                            remainingCards['K'] < 3 and remainingCards['Q'] < 3 and each[1] == 'J'):
                    for each2 in duizi:
                        if each2[1] == '3' \
                                or each2[1] == '4' \
                                or each2[1] == '5' \
                                or each2[1] == '6' \
                                or each2[1] == '7' \
                                or each2[1] == '8' \
                                or each2[1] == '9' \
                                or each2[1] == 'T' \
                                or each2[1] == '2':
                            y_duizi = duizi[-1]

        z_guangsan = []  # 手上没有大的光三，则先不出光三
        # 手上有大的光三，但是没有小的光三，则先不出光三,到后面统一考虑
        if guangsan != []:
            for each in guangsan:
                if each[1] == 'A' or each[1] == 'K' or (
                        each[1] == 'Q' and remainingCards['A'] <= 4 and remainingCards['K'] <= 4) or (
                        remainingCards['A'] <= 4 and remainingCards['K'] <= 4 and remainingCards['Q'] <= 4 and each[
                    1] == 'J') or (
                        remainingCards['A'] <= 4 and remainingCards['K'] <= 4 and remainingCards['Q'] <= 4 and
                        remainingCards['J'] <= 4 and each[1] == 'T'):
                    # 当我方手上有3个A或者3个k或者3个Q时A的数量小于等于4，K的数量小于等于4
                    for each3 in guangsan:
                        if each3[1] == '3' or each3[1] == '4' or each3[1] == '5' or each3[1] == '6' or each3[
                            1] == '7' or each3[1] == '8' or each3[1] == '9' or each3[1] == '2':  # 当我方有小的光三时
                            z_guangsan = guangsan[-1]

        u_sandaier = []
        if sandaier != []:
            for each in sandaier:
                if each[1] == 'A' \
                        or each[1] == 'K' \
                        or each[1] == 'Q' \
                        or (remainingCards['A'] <= 4 and remainingCards['K'] <= 4 and remainingCards['Q'] <= 4 and each[
                    1] == 'J') \
                        or (remainingCards['A'] <= 4 and remainingCards['K'] <= 4 and remainingCards['Q'] <= 4 and
                            remainingCards['J'] <= 4 and each[1] == 'T'):
                    for each4 in sandaier:
                        if each4[1] == '3' \
                                or each4[1] == '4' \
                                or each4[1] == '5' \
                                or each4[1] == '6' \
                                or each4[1] == '7' \
                                or each4[1] == '8' \
                                or each4[1] == '9' \
                                or each4[1] == '2':
                            u_sandaier = sandaier[-1]

        # 此处返回的数组若为空数组，说明2种情况，第一，有收牌权的大牌，但是没有同类的小牌，所以大牌先留着。
        # 第二，在单张，对子，光三，三带二类型牌中没有收牌权的大牌，但是有小牌，所以先出其他的，一般不可能，
        # 除非运气非常背，若返回的列表包含多种类型的牌，说明都是该类型的小牌，且同时拥有该类型牌的收牌权的牌
        if x_danzhang == [] and y_duizi == [] and z_guangsan == [] and u_sandaier == []:
            fanhuipai = []
        if x_danzhang != []:
            fanhuipai = x_danzhang
        if y_duizi != []:
            fanhuipai = y_duizi
        if z_guangsan != []:
            fanhuipai = z_guangsan
        if u_sandaier != []:
            fanhuipai = u_sandaier
        return [fanhuipai]
        # return ['ThreeWithTwo', 'A', ['SA', 'HA', 'DA', 'C8', 'C8']]


    def getIndexNotSingle(self, state, actionList):
        """
        返回非单张牌
        :param state:
        :param actionList:
        :return:
        """
        for i in range(len(state.myOrderedCards) - 1, -1, -1):  # 倒序遍历orderCards，权值从小到大
            c = state.myOrderedCards[i]
            if c[0] == 'Single':
                continue
            idx = self.inAction(c, actionList)
            if idx != -1:  # 如果此项位于actionList中
                return idx

        # 没有return，说明都是单张，从大到小出
        for i in range(len(state.myOrderedCards)):  # 倒序遍历orderCards，权值从小到大
            c = state.myOrderedCards[i]
            idx = self.inAction(c, actionList)
            if idx != -1:  # 如果此项位于actionList中
                return idx
        # 要不起，PASS
        return 0


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
        for i in range(len(state.myOrderedCards) - 1, -1, -1):  # 倒序遍历orderCards，权值从小到大
            c = state.myOrderedCards[i]
            idx = self.inAction(c, actionList)
            if idx != -1:  # 如果此项位于actionList中
                return idx

        # 如果对面是顺子，不要硬接，免得拆牌
        # if state.curCardType == 'Straight':
        #     return 0
        if state.competitorCardNums[0] <= 10 or state.competitorCardNums[1] <= 17:
            return 1 if len(actionList) > 1 else 0
        # 没在actionList中找到，仅当对手手牌小于17张再硬接
        # if state.competitorCardNums[0] <= 10 or state.competitorCardNums[1] <= 17:
        #     if len(actionList) > 1:
        #         for i in range(1, len(actionList)):
        #             if actionList[i][0] == 'Single': # 单张不强拆
        #                 continue
        #             else:
        #                 return i
        return 0



    def inAction(self, c, actionList):
        """
        返回 c 是否在 actionList中
        :param c:
        :param actionList:
        :return:
        """
        for index, a in enumerate(actionList):
            if c[0] != a[0]:
                continue
            if c[0] != 'Straight' and c[1] != a[1]:  # 顺子只需要考虑是否全部牌一样，不需要考虑 greater 位置
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
