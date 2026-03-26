# -*- coding: utf-8 -*-
# @Time       : 2020/10/11 14:54
# @Author     : fengjie
# @File       : gd_handle.py
# @Description: 将手牌按照权值进行组合

# 花色：黑桃、红桃、梅花、方片分别对应字符S, H, C, D，小王的花色为S，大王的花色为H

# 中英文对照表
# ENG2CH = {
#     "Single": "单张",
#     "Pair": "对子",
#     "Trips": "三张",
#     "ThreePair": "三连对",
#     "ThreeWithTwo": "三带二",
#     "TwoTrips": "钢板",
#     "Straight": "顺子",
#     "StraightFlush": "同花顺",
#     "Bomb": "炸弹",
#     "PASS": "过"
# }

import numpy as np


def getTwo(cards, tri, rank_card):
    """
    获得三带二中  二的牌型, 需要考虑万能牌
    :param cards: 三带二共5张牌
    :param tri: 三的牌型
    :param rank_card: rank牌
    """
    res = None
    for i in range(len(cards)):
        if cards[i][1] != tri:
            res = cards[i][1]
            # 如果不是rank牌，直接返回，是rank牌，还得继续看rank牌是否为凑的
            if res != rank_card:
                return res
    return res


def arrange(weights, handCards, rank):
    list1 = []
    rank_card = 'H' + rank
    wangnengpai = []
    for each in handCards:
        if each == rank_card:
            wangnengpai.append(each)  # 分割出万能牌数组
        else:
            list1.append(each)  # 不是万能牌的数组

    list2 = []
    for i in list1:
        i = i[1]
        i = [i]
        list2 = list2 + i
    handCrads1 = list2  # print(handCrads1) #['3', '4', '4', '4', '4', '5', '5', '6', '6', '7', '7', '7', '8', '8', '9', '9', 'T', 'T', 'T', 'J', 'J', 'J', 'K', '2', '2', '2', 'B']
    # 对不是万能牌的数组全部去除花色
    numberA = handCrads1.count('A')
    number2 = handCrads1.count('2')
    number3 = handCrads1.count('3')
    number4 = handCrads1.count('4')
    number5 = handCrads1.count('5')
    number6 = handCrads1.count('6')
    number7 = handCrads1.count('7')
    number8 = handCrads1.count('8')
    number9 = handCrads1.count('9')
    numberT = handCrads1.count('T')
    numberJ = handCrads1.count('J')
    numberQ = handCrads1.count('Q')
    numberK = handCrads1.count('K')
    numberB = handCrads1.count('B')
    numberR = handCrads1.count('R')  # [0, 1, 4, 2, 2, 3, 2, 2, 3, 3, 0, 1, 3, 1, 0]
    number_HandCrads1 = {'3': number3, '4': number4, '5': number5, '6': number6, '7': number7,
                         '8': number8, '9': number9,
                         'T': numberT, 'J': numberJ, 'Q': numberQ, 'K': numberK, 'A': numberA, '2': number2,
                         'B': numberB,
                         'R': numberR}  # 记各种花色牌的数量，并放入列表
    number_HandCrads2 = {'A': 'numberA', '3': 'number3', '4': 'number4', '5': 'number5', '6': 'number6', '7': 'number7',
                         '8': 'number8', '9': 'number9',
                         'T': 'numberT', 'J': 'numberJ', 'Q': 'numberQ', 'K': 'numberK', '2': 'number2', 'B': 'numberB',
                         'R': 'numberR'}
    traceback = {'numberA': 'A', 'number2': '2', 'number3': '3', 'number4': '4', 'number5': '5', 'number6': '6',
                 'number7': '7', 'number8': '8', 'number9': '9',
                 'numberT': 'T', 'numberJ': 'J', 'numberQ': 'Q', 'numberK': 'K', 'numberB': 'B', 'numberR': 'R'}
    traceback2 = {'A': 1, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
                  'T': 10, 'J': 11, 'Q': 12, 'K': 13, '2': 2, 'B': 'B', 'R': 'R'}
    # print(table['Single'][traceback['numberA']])
    bomb4_yuanpai = []  # print(number_HandCrads1['A'])
    bomb4 = []
    bomb4_quanzhi = 0
    trip_yuanpai = []
    trip = []
    trip_quanzhi = 0
    pair_yuanpai = []
    pair = []
    pair_quanzhi = 0
    single_yuanpai = []
    single = []
    single_quanzhi = 0
    bomb5_yuanpai = []
    bomb5 = []
    bomb5_quanzhi = 0
    bomb6_yuanpai = []
    bomb6 = []
    bomb6_quanzhi = 0
    bomb7_yuanpai = []
    bomb7 = []
    bomb7_quanzhi = 0
    bomb8_yuanpai = []
    bomb8 = []
    bomb8_quanzhi = 0
    for each in number_HandCrads1:

        if number_HandCrads1[each] == 8:
            bomb8_quanzhi_now = weights['8Bomb'][each]
            bomb8_quanzhi = bomb8_quanzhi + bomb8_quanzhi_now
            bomb8_suoyin = -1
            for i in handCrads1:
                bomb8_suoyin = bomb8_suoyin + 1
                if i == each:
                    bomb8_yuanpai = [list1[bomb8_suoyin]]
                    bomb8 = bomb8 + bomb8_yuanpai

        if number_HandCrads1[each] == 7:
            bomb7_quanzhi_now = weights['7Bomb'][each]
            bomb7_quanzhi = bomb7_quanzhi + bomb7_quanzhi_now
            bomb7_suoyin = -1
            for i in handCrads1:
                bomb7_suoyin = bomb7_suoyin + 1
                if i == each:
                    bomb7_yuanpai = [list1[bomb7_suoyin]]
                    bomb7 = bomb7 + bomb7_yuanpai

        if number_HandCrads1[each] == 6:
            bomb6_quanzhi_now = weights['6Bomb'][each]
            bomb6_quanzhi = bomb6_quanzhi + bomb6_quanzhi_now
            bomb6_suoyin = -1
            for i in handCrads1:
                bomb6_suoyin = bomb6_suoyin + 1
                if i == each:
                    bomb6_yuanpai = [list1[bomb6_suoyin]]
                    bomb6 = bomb6 + bomb6_yuanpai

        if number_HandCrads1[each] == 5:
            bomb5_quanzhi_now = weights['5Bomb'][each]
            bomb5_quanzhi = bomb5_quanzhi + bomb5_quanzhi_now
            bomb5_suoyin = -1
            for i in handCrads1:
                bomb5_suoyin = bomb5_suoyin + 1
                if i == each:
                    bomb5_yuanpai = [list1[bomb5_suoyin]]
                    bomb5 = bomb5 + bomb5_yuanpai

        if number_HandCrads1[each] == 4:
            bomb4_quanzhi_now = weights['4Bomb'][each]
            bomb4_quanzhi = bomb4_quanzhi + bomb4_quanzhi_now
            bomb4_suoyin = -1
            for i in handCrads1:
                bomb4_suoyin = bomb4_suoyin + 1
                if i == each:
                    bomb4_yuanpai = [list1[bomb4_suoyin]]
                    bomb4 = bomb4 + bomb4_yuanpai

        if number_HandCrads1[each] == 3:
            trip_quanzhi_now = weights['Trips'][each]
            trip_quanzhi = trip_quanzhi + trip_quanzhi_now
            trip_suoyin = -1
            for i in handCrads1:
                trip_suoyin = trip_suoyin + 1
                if i == each:
                    trip_yuanpai = [list1[trip_suoyin]]
                    trip = trip + trip_yuanpai

        if number_HandCrads1[each] == 2:
            pair_quanzhi_now = weights['Pair'][each]
            pair_quanzhi = pair_quanzhi + pair_quanzhi_now
            pair_suoyin = -1
            for i in handCrads1:
                pair_suoyin = pair_suoyin + 1
                if i == each:
                    pair_yuanpai = [list1[pair_suoyin]]
                    pair = pair + pair_yuanpai

        if number_HandCrads1[each] == 1:
            single_quanzhi_now = weights['Single'][each]
            single_quanzhi = single_quanzhi + single_quanzhi_now
            single_suoyin = -1
            for i in handCrads1:
                single_suoyin = single_suoyin + 1
                if i == each:
                    single_yuanpai = [list1[single_suoyin]]
                    single = single + single_yuanpai
                    # 把大小相同的牌组合到一起

    x = []

    # 分割出带万能牌的炸弹
    while trip != [] and wangnengpai != []:
        wangnengpai_4bomb = []  # 清空前面暂存的，否则出现叠加现象
        wangnengpai_4bomb_now = trip[0:3] + [wangnengpai[0]]
        wangnengpai_4bomb = wangnengpai_4bomb + wangnengpai_4bomb_now
        z = ['Bomb', wangnengpai_4bomb[0][1], wangnengpai_4bomb]
        del wangnengpai[0]
        del trip[0:3]
        x.append(z)

    dui_R = []
    dui_B = []
    if pair != []:
        if pair[-1][1] == 'R':
            dui_R = pair[-2:]
            del pair[-2:]  # 有对大王先拿出来
        if pair != []:  # 如果还不是空集继续判断是否有对小王
            if pair[-1][1] == 'B':
                dui_B = pair[-2:]
                del pair[-2:]
    while pair != [] and wangnengpai != []:  # 再不济混个带万能牌的光三
        wangnengpai_trip = []
        wangnengpai_trip_now = pair[-2:] + [wangnengpai[0]]
        wangnengpai_trip = wangnengpai_trip + wangnengpai_trip_now
        del wangnengpai[0]
        del pair[-2:]
        trip = trip + wangnengpai_trip
    pair = pair + dui_B + dui_R

    dan_R = []
    dan_B = []
    if single != []:
        if single[-1][1] == 'R':
            dan_R = single[-1:]
            del single[-1:]
        if single != []:
            if single[-1][1] == 'B':
                dan_B = single[-1:]
                del single[-1:]
    while single != [] and wangnengpai != []:
        wangnengpai_pair = []
        wangnengpai_pair_now = single[0:1] + [wangnengpai[0]]
        wangnengpai_pair = wangnengpai_pair + wangnengpai_pair_now
        del wangnengpai[0]
        del single[0:1]
        pair = pair + wangnengpai_pair  # 再不济混个带万能牌的对子
    single = single + dan_R + dan_B

    if wangnengpai != [] and len(wangnengpai) == 2:
        pair = pair + wangnengpai
    else:
        wangnengpai != [] and len(wangnengpai) == 1
        single = single + wangnengpai  # 实在不行万能牌原路退回

        # TODO: 顺子 同花顺
    while single != []:  # 分割出顺子和单张
        each = [single[0]]
        del single[0]
        a = ['Single', each[0][1], each]
        if len(single) >= 5:
            if traceback2[each[0][1]] + 1 == traceback2[single[0][1]] \
                    and traceback2[single[0][1]] + 1 == traceback2[single[1][1]] \
                    and traceback2[single[1][1]] + 1 == traceback2[single[2][1]] \
                    and traceback2[single[2][1]] + 1 == traceback2[single[3][1]]:
                # TODO：考虑是同花顺的情况
                each = each + single[0:4]
                del single[0:4]
                a = ['Straight', each[4][1], each]
        x.append(a)

    while pair != []:  # 分割出对子和三联对
        each = pair[0:2]
        if len(pair) <= 4:
            # 小于三对
            b = ['Pair', each[1][1], each]
            del pair[0:2]
            x.append(b)
        # 大于三对 且 J Q K 10 9 8 不组三连对
        elif each[1][1] == 'T' or each[1][1] == 'J' or each[1][1] == 'Q' or each[1][1] == 'K' or each[1][1] == '9' or \
                each[1][1] == '8':
            b = ['Pair', each[1][1], each]
            del pair[0:2]
            x.append(b)
        # 三连对
        elif traceback2[each[1][1]] + 1 == traceback2[pair[2][1]] and traceback2[pair[2][1]] + 1 == traceback2[
            pair[5][1]]:

            each = each + pair[2:6]
            del pair[0:6]
            ThreePair = ['ThreePair', each[5][1], each]
            x.append(ThreePair)
        # 大于三对，且不组成三连对，作为单个对子，不加会导致死循环
        else:
            b = ['Pair', each[1][1], each]
            del pair[0:2]
            x.append(b)

    while trip != []:  # 分割出钢板和光三
        each = trip[0:3]
        if len(trip) == 3:
            c = ['Trips', each[1][1], each]
            del trip[0:3]
            x.append(c)
        elif each[1][1] == 'T' or each[1][1] == 'J' or each[1][1] == 'Q' or each[1][1] == 'K' or each[1][1] == '9':
            c = ['Trips', each[1][1], each]
            del trip[0:3]
            x.append(c)
        # 能组成钢板
        elif traceback2[each[1][1]] + 1 == traceback2[trip[4][1]]:
            each = each + trip[3:6]
            del trip[0:6]
            gangban = ['TwoTrips', each[4][1], each]
            x.append(gangban)
        elif traceback2[each[1][1]] != traceback2[trip[1][1]] + 1:
            c = ['Trips', each[1][1], each]
            del trip[0:3]
            x.append(c)

    while bomb4 != []:  # 分割出炸弹
        each = bomb4[0:4]
        del bomb4[0:4]
        d = ['Bomb', each[1][1], each]
        x.append(d)
    while bomb5 != []:
        each = bomb5[0:5]
        del bomb5[0:5]
        e = ['Bomb', each[1][1], each]
        x.append(e)
    while bomb6 != []:
        each = bomb6[0:6]
        del bomb6[0:6]
        f = ['Bomb', each[1][1], each]
        x.append(f)
    while bomb7 != []:
        each = bomb7[0:7]
        del bomb7[0:7]
        f = ['Bomb', each[1][1], each]
        x.append(f)
    while bomb8 != []:
        each = bomb8[0:8]
        del bomb8[0:8]
        l = ['Bomb', each[1][1], each]
        x.append(l)

    trip_shuzu = []  # 分割出三带二
    pair_shuzu = []
    shuzu = []
    while x != []:
        each = x[0]
        del x[0:1]
        if each[0] == 'Trips':
            trip_shuzu.append(each[2])
        if each[0] == 'Pair':
            pair_shuzu.append(each[2])
        if each[0] != 'Trips' and each[0] != 'Pair':
            shuzu.append(each)

    while trip_shuzu != [] and pair_shuzu != []:
        each_trip = trip_shuzu[0]
        each_pair = pair_shuzu[0]
        del trip_shuzu[0:1]
        del pair_shuzu[0:1]
        threewithtwo = each_trip + each_pair
        Threewithtwo = ['ThreeWithTwo', threewithtwo[0][1], threewithtwo]
        shuzu.append(Threewithtwo)

    if trip_shuzu == [] and pair_shuzu != []:
        while pair_shuzu != []:
            each = pair_shuzu[0]
            del pair_shuzu[0:1]
            g = ['Pair', each[0][1], each]
            shuzu.append(g)

    if pair_shuzu == [] and trip_shuzu != []:
        while trip_shuzu != []:
            each = trip_shuzu[0]
            del trip_shuzu[0:1]
            h = ['Trips', each[0][1], each]
            shuzu.append(h)

    return shuzu


def getWeightTable(rank_card):
    """
    获得权值表
    :param rank_card: 当前的rank等级 为 str 类型
    :return:
    """
    table = {
        'Single': {'A': 4, '2': -6, '3': -5, '4': -4, '5': -3, '6': -2, '7': -1, '8': 0, '9': 1, 'T': 1, 'J': 2,
                   'Q': 2, 'K': 3, 'B': 6, 'R': 7},
        'Pair': {'A': 9, '2': -4, '3': -3, '4': -2, '5': -1, '6': 0, '7': 1, '8': 2, '9': 3, 'T': 4, 'J': 5, 'Q': 6,
                 'K': 7, 'B': 11, 'R': 12},
        'Trips': {'A': 15, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, 'T': 11, 'J': 12, 'Q': 13,
                  'K': 14},
        'ThreePair': {'A': 30, '2': 7, '3': 7, '4': 21, '5': 22, '6': 23, '7': 24, '8': 25, '9': 26, 'T': 27, 'J': 28,
                      'Q': 29,
                      'K': 29},
        'TwoTrips': {'A': 31, '2': 20, '3': 21, '4': 22, '5': 23, '6': 24, '7': 25, '8': 26, '9': 27, 'T': 28, 'J': 29,
                     'Q': 30,
                     'K': 30},
        '4Bomb': {'A': 130, '2': 70, '3': 75, '4': 80, '5': 85, '6': 90, '7': 95, '8': 100, '9': 105, 'T': 110,
                  'J': 115, 'Q': 120, 'K': 125},
        '5Bomb': {'A': 195, '2': 135, '3': 140, '4': 145, '5': 150, '6': 155, '7': 160, '8': 165, '9': 170, 'T': 175,
                  'J': 180, 'Q': 185, 'K': 190},
        '6Bomb': {'A': 260, '2': 200, '3': 205, '4': 210, '5': 215, '6': 220, '7': 225, '8': 230, '9': 235, 'T': 240,
                  'J': 245, 'Q': 250, 'K': 255},
        '7Bomb': {'A': 325, '2': 265, '3': 270, '4': 275, '5': 280, '6': 285, '7': 290, '8': 295, '9': 300, 'T': 305,
                  'J': 310, 'Q': 315, 'K': 320},
        '8Bomb': {'A': 390, '2': 330, '3': 335, '4': 340, '5': 345, '6': 350, '7': 355, '8': 360, '9': 365, 'T': 370,
                  'J': 375, 'Q': 380, 'K': 385},
        'Straight': {'A': 25, '2': 0, '3': 0, '4': 0, '5': 10, '6': 15, '7': 16, '8': 17, '9': 18, 'T': 19,
                     'J': 20, 'Q': 21, 'K': 22},
        'StraightFlush': {'A': 130, '2': 70, '3': 75, '4': 80, '5': 85, '6': 90, '7': 95, '8': 100, '9': 105, 'T': 110,
                          'J': 115, 'Q': 120, 'K': 125},
    }
    table['Single'][rank_card] = 5
    table['Pair'][rank_card] = 10
    table['Trips'][rank_card] = 16
    table['ThreePair'][rank_card] = 6
    table['TwoTrips'][rank_card] = 0
    table['4Bomb'][rank_card] = 132
    table['5Bomb'][rank_card] = 197
    table['6Bomb'][rank_card] = 264
    table['7Bomb'][rank_card] = 327
    table['8Bomb'][rank_card] = 395
    table['Straight'][rank_card] = 26  # 顺子
    table['StraightFlush'][rank_card] = 132  # 同花顺
    return table


def orderHandCards(weights, handCards, rank_card):
    cards_arr = arrange(weights, handCards, rank_card)
    w_arr = []
    for i in range(len(cards_arr)):
        action_type = cards_arr[i][0]  # 'Bomb'
        greater_card = cards_arr[i][1]  # 最大牌 '4'
        cards = cards_arr[i][2]  # 牌组 ['S4', 'H4', 'C4', 'D4', 'H2']
        if action_type == 'Bomb':
            count = len(cards)
            w = weights[str(count) + 'Bomb'][greater_card]
            w_arr.append(w)
        elif action_type == 'StraightFlush':
            w = weights['StraightFlush'][greater_card]
            w_arr.append(w)
        elif action_type == 'Straight':
            w = weights['Straight'][greater_card]
            w_arr.append(w)
        elif action_type == 'TwoTrips':
            w = weights['TwoTrips'][greater_card]
            w_arr.append(w)
        elif action_type == 'ThreeWithTwo':
            two = getTwo(cards, greater_card, rank_card)
            w = weights['Trips'][greater_card] - weights['Pair'][two]
            w_arr.append(w)
        elif action_type == 'ThreePair':
            w = weights['ThreePair'][greater_card]
            w_arr.append(w)
        elif action_type == 'Trips':
            w = weights['Trips'][greater_card]
            w_arr.append(w)
        elif action_type == 'Pair':
            w = weights['Pair'][greater_card]
            w_arr.append(w)
        elif action_type == 'Single':
            w = weights['Single'][greater_card]
            w_arr.append(w)
        else:
            raise Exception('unknown action type: ' + action_type)
    sorted_index = np.argsort(w_arr)
    ordered_cards = []
    for i in sorted_index[::-1]:  # sorted_index为从小到大，这里需要从大到小
        ordered_cards.append(cards_arr[i])
    return ordered_cards

# if __name__ == '__main__':
#     # 可出的牌组
#     # actionlist = [['PASS', 'PASS', 'PASS'],
#     #               ['Single', 'J', ['SJ']],
#     #               ['Bomb', '4', ['S4', 'H4', 'C4', 'D4']],
#     #               ['Single', 'K', ['SK']]]
#     actionList = [['PASS', 'PASS', 'PASS'], ['Bomb', 'A', ['SA', 'HA', 'DA', 'HJ']], ['Bomb', 'J', ['SJ', 'HJ', 'DJ', 'DJ']]]
#
#     # print(['Bomb', '4', ['S4', 'H4', 'D4', 'C4']] in actionlist)
#     print(inAction(['Bomb', 'J', ['SJ', 'DJ', 'DJ', 'HJ']], actionList))
#     # 手牌组合
#     # orderCards = [
#     #         ['Bomb', '4', ['S4', 'H4', 'C4', 'D4']],
#     #         ['ThreeWithTwo', 'A', ['SA', 'HA', 'DA', 'C8', 'C8']],
#     #         ['Single', 'K', ['SK']],
#     #         ['Single', 'J', ['SJ']]
#     #     ]
#     # i = getActionIndex(orderCards, actionlist)
#     # print(i)
#     # print(actionlist[i])
#
#     # arr = orderHandCards(getWeightTable2('2'), ['D3', 'S4', 'H4', 'C4', 'D4', 'S5', 'S5', 'S6', 'H6', 'S7', 'H7', 'D7', 'S8', 'H8', 'S9', 'D9', 'ST', 'ST', 'DT', 'SJ', 'HJ', 'CJ', 'HK', 'S2', 'H2', 'D2', 'SB'])
#     # print(arr)


