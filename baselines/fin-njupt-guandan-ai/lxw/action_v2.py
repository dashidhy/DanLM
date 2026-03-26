# -*- coding: utf-8 -*-
# @Time       : 2020/10/1 21:32
# @Author     : Duofeng Wu
# @File       : action.py
# @Description: 动作类

from random import randint
from lxw.trans import trans,type_trans
tran_score = {"Single": 10,
              "Pair": 5,
              "Trips": 0,
              "ThreePair": -5,
              "ThreeWithTwo": 0,
              "TwoTrips": -5,
              "Straight": -25,
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
        self.myPos =None
        self.pass_score = 0
        self.store =[0 for i in range(18)]

    def parse(self, msg ,myPos,rest):
        self.action = msg["actionList"]
        self.act_range = msg["indexRange"]
        self.curRank = msg['curRank']
        self.tran = trans.copy()
        self.tran[msg['curRank']] = 15
        self.myPos = myPos
        #print(self.action)
        #print("可选动作范围为：0至{}".format(self.act_range))
        l=len(msg['handCards'])
        self.rough = [0 for i in range(18)]
        self.read(msg['handCards'])
        self.store =[0 for i in range(18)]
        le = (self.myPos + 3) % 4
        ri = (self.myPos + 1) % 4
        fe = (self.myPos + 2) % 4
        punish_score = [0 for i in range(13)]
        if rest[le] == 2 or rest[ri] == 2:
            punish_score[1] += 30
            punish_score[7] += 20
            punish_score[3] -= 20
        if rest[le] == 1 or rest[ri] == 1:
            punish_score[0] += 30
            punish_score[7] += 20
            punish_score[3] -= 20
        if rest[le] == 3 or rest[ri] == 3:
            punish_score[2] += 10
            punish_score[3] -= 20
        if rest[le] == 5 or rest[ri] == 5:
            punish_score[3] += 10
            punish_score[0] += 10
        if rest[le] == 6 or rest[ri] == 6:
            punish_score[1] += 10




        max_s = 99999999
        ans = 0

        sinnum = 0
        pnum = 0
        tripnum = 0
        for i in range(15):
            if self.rough[i] == 1:
                sinnum += 1
            elif i<14 and self.rough[i] == 2:
                pnum += 1
            elif i<13 and self.rough[i] == 3:
                tripnum += 1

        bsinnum = 0
        bpnum = 0
        btripnum = 0
        for i in range(13,17):
            if  i > 14 and self.rough[i] >= 1:
                bsinnum += 1
            if  i > 13 and self.rough[i] >= 2:
                bpnum += 1
            if  self.rough[i] == 3:
                btripnum += 1
        bombnum = 0
        for i in range(15):
            if self.rough[i] > 4:
                bombnum += 1
        l -= bombnum * 4
        if l > 15:
            tran_score['PASS'] = 30
        elif l > 10:
            tran_score['PASS'] = 60
        else:
            tran_score['PASS'] = 70
        if rest[ri] < 4 or rest[le] < 4:
            tran_score['PASS'] += 60


        for i in range(self.act_range + 1):
            type, rank, cards_play = self.action[i]
            tmp_dict={}
            s = tran_score[type] + self.tran[rank] + punish_score[type_trans[type]]
            if self.tran[rank] > 14 or type == 'Bomb' or type == 'StraightFlush':
                if rest[ri] > 9 and rest[ri] > 9 and l < 9:
                    if sinnum + pnum + tripnum > bsinnum + bpnum + btripnum + bombnum:
                        s += 40
            '''if type =='PASS':
                s -= self.pass_score'''
            if type != 'PASS':
                for card in cards_play:
                    if self.tran[card[1]] not in tmp_dict:
                        tmp_dict[self.tran[card[1]]] = 1
                    else:
                        tmp_dict[self.tran[card[1]]] += 1

                for a in tmp_dict:
                    if a > 14:
                        continue
                    if a == 17 or a == 16:
                            for j in range(10):
                                if self.rough[j] == 1:
                                    s += 2
                    if a == 15:
                        if type == 'ThreeWithTwo' or type == 'Trips':
                            for j in range(10):
                                if self.rough[j] == 3 or self.rough[j] == 2:
                                    s += 0.5
                    if type != 'Straight':
                        if tmp_dict[a] + self.store[a] == self.rough[a]:
                            s -= 10
                        if self.rough[a] - self.store[a] >= 4 and self.rough[a]-self.store[a] - tmp_dict[a] < 4:
                            s += 20
                        if self.rough[a] - tmp_dict[a] < self.store[a]:
                            s += 20
                        if self.rough[a] - tmp_dict[a] == 1 + self.store[a]:
                            s += 10
                        elif self.rough[a] - tmp_dict[a] == 2 + self.store[a]:
                            s += 5
                    else:
                        if self.rough[a] - tmp_dict[a] == 0:
                            s -= 10
                        if self.rough[a] >= 4 and self.rough[a] - tmp_dict[a] < 4:
                            s += 20
                        if self.rough[a] - tmp_dict[a] == 1:
                            s += 10
                        elif self.rough[a] - tmp_dict[a] == 2:
                            s += 5

            #print(self.action[i],s)
            if s < max_s:
                ans = i
                max_s = s
        if msg['greaterPos'] != -1:
            if (self.tran[self.action[ans][1]] > 12 or self.action[ans][0] == 'Bomb' or self.action[ans][0] == 'StraightFlush') \
                    and (self.myPos - msg['greaterPos'] + 4) % 4 == 2:
                if l == len(self.action[ans][2]):
                    return ans
                return 0
        return ans

    def read(self, cards):
        use =[]
        flag = 0
        for card in cards:
            card_suit = card[0]
            card_rank = card[1]
            if card_rank == self.curRank and card_suit == 'H':
                self.all_match += 1
            else:
                self.rough[self.tran[card_rank]] += 1

        co = self.rough.copy()
        co[1] = co[14]
        co[trans[self.curRank]] = co[15]

        store_tmp = [[0,[]],[0,[]],[0,[]]]
        for it in range(2):
            smin = 9999
            for i in range(1,10):
                use = []
                tmp_dict = {}
                s = 0
                flag = False
                for j in range(5):
                    if co[i + j] > 0:
                        tmp_dict[i + j] = 1
                    elif self.all_match > len(use):
                        if 15 not in tmp_dict:
                            tmp_dict[15] = 1
                        else:
                            tmp_dict[15] += 1
                        use.append(i + j)
                    else:
                        flag = True
                if flag:
                    continue
                for a in tmp_dict:
                    if a > 14:
                        s += 10
                    else:
                        if tmp_dict[a] - co[a] == 0:
                            s -= 10
                        elif co[a] - tmp_dict[a] == 1:
                            s += 10
                        elif co[a] - tmp_dict[a] == 2:
                            s += 5
                        elif co[a] - tmp_dict[a] == 3:
                            s += 15
                if s <= -10 and s < smin:
                    store_tmp[it][0] = i
                    store_tmp[it][1] = use.copy()
                    smin = s

            if store_tmp[it][0] == 0:
                break
            else:
                i = store_tmp[it][0]
                for index in store_tmp[it][1]:
                    if index == 1:
                        self.rough[14] += 1
                    elif index == self.tran[self.curRank]:
                        self.rough[15] += 1
                    else:
                        self.rough[index] += 1
                self.all_match -= len(use)
                for j in range(5):
                    if i + j == 14:
                        co[1] -= 1
                    if i + j == 1:
                        self.store[14] += 1
                        co[14] -= 1
                    elif i + j == self.tran[self.curRank]:
                        self.store[15] += 1
                    else:
                        self.store[i + j] += 1
                    co[i+j] -= 1

        for i in range(2):
            if self.all_match > 0:
                for i in range(18):
                    if self.rough[i] -self.store[i] == 3:
                        self.rough[i] += 1
                        self.all_match -= 1
                        break

