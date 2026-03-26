# -*- coding: utf-8 -*-
# @Time       : 2020/10/1 21:32
# @Author     : Duofeng Wu
# @File       : action.py
# @Description: 动作类

from random import randint
trans = {'A': 14, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
                 'K': 13, 'B':16,'R':17, 'JOKER': 16, 'PASS':0, 'Straight': 6, 'TripsPair': 1, 'ThreeWithTwo': 6,
                 'ThreePair': 1, 'Trips': 36, 'Pair': 1296, 'Single': 7776, 'Bomb': 279936, 'StraightFlush': 279936,
                 'back': 1, 'tribute': 1}

tran_score = {"Single": 10,
              "Pair": 5,
              "Trips": 0,
              "ThreePair": -5,
              "ThreeWithTwo": -5,
              "TwoTrips": -5,
              "Straight": 5,
              "StraightFlush": 50,
              "Bomb": 30,
              "PASS": 0,
              'tribute': 0,
              'back': 0
              }
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


class Action(object):

    def __init__(self):
        self.action = []
        self.act_range = -1
        self.tran = trans.copy()
        self.rough=[0 for i in range(18)]
        self.curRank = ''
        self.all_match = 0

    def parse(self, msg):
        self.action = msg["actionList"]
        self.act_range = msg["indexRange"]
        self.curRank = msg['curRank']
        self.tran = trans.copy()
        self.tran[msg['curRank']] = 15
        # print(self.action)
        # print("可选动作范围为：0至{}".format(self.act_range))
        l=len(msg['handCards'])
        self.rough = [0 for i in range(18)]
        self.read(msg['handCards'])

        public = msg['publicInfo']

        if l > 20:
            tran_score['PASS'] = 30
        elif l >15:
            tran_score['PASS'] = 60
        else:
            tran_score['PASS'] = 1000

        max_s = 99999999
        ans = 0
        '''for i in range(18):
            print(i,end='  ')
        print()
        print(self.rough)'''
        for i in range(self.act_range + 1):
            type, rank, cards_play = self.action[i]
            tmp_dict={}
            if rank == '':
                continue
            s = tran_score[type] + self.tran[rank]
            if type != 'PASS':
                for card in cards_play:
                    if self.tran[card[1]] not in tmp_dict:
                        tmp_dict[self.tran[card[1]]] = 1
                    else:
                        tmp_dict[self.tran[card[1]]] += 1

                for a in tmp_dict:
                    if a > 14:
                        continue
                    if tmp_dict[a] == self.rough[a]:
                        s -= 10
                    if self.rough[a] >=4 and self.rough[a] - tmp_dict[a] <4:
                        s += 20
                    if self.rough[a] - tmp_dict[a] == 1:
                        s += 10
                    elif self.rough[a] - tmp_dict[a] == 2:
                        s += 5


            # print(self.action[i],s)
            if s < max_s:
                ans = i
                max_s = s
        return ans

    def read(self, cards):
        for card in cards:
            card_suit = card[0]
            card_rank = card[1]
            if card_rank == self.curRank and card_suit == 'H':
                self.all_match += 1
            self.rough[self.tran[card_rank]] += 1

        if self.all_match > 0:
            for i in range(18):
                if self.rough[i] == 3:
                    self.rough[i] += 1
                    self.all_match -= 1
                    break

