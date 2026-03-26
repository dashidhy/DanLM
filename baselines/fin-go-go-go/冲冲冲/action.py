# -*- coding: utf-8 -*-
# @Time       : 2020/10/1 21:32
# @Author     : Duofeng Wu
# @File       : action.py
# @Description: 动作类

from tools import random_aciton, parse_pass

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

    def parse(self, msg):

        self.action = msg["actionList"]
        self.act_range = msg["indexRange"]
        hand_card = msg['handCards']
        if self.act_range == 0:
            index = 0
        else:
            single_action = random_aciton(self.action, hand_card)
            if msg["stage"] == 'back' and single_action == ['PASS', 'PASS', 'PASS']:
                index = 0
            elif single_action == ['PASS', 'PASS', 'PASS'] and ['PASS', 'PASS', 'PASS'] not in msg["actionList"]:
                single_action = parse_pass(self.action)
                index = self.action.index(single_action)
            else:
                index = self.action.index(single_action)
        return index
