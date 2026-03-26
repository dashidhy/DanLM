from random import randint
import copy
import logging
import os
import sys
import torch

# Ensure this directory is on sys.path for torch.load (needs passive_module)
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
# Pre-import passive_module so it survives sys.path cleanup in baseline_adapter
import passive_module  # noqa: F401, E402

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

    def __init__(self, name):
        self.action = []
        self.act_range = -1
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
        logging.basicConfig(filename=name + '.log', level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)
        self.model = torch.load(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "passive"),
            weights_only=False, map_location="cpu",
        )
        self.model.eval()

    def combine_handcards(self, handcards, rank, card_val):

        cards = {}
        cards["Single"] = []
        cards["Pair"] = []
        cards["Trips"] = []
        cards["Bomb"] = []
        bomb_info = {}

        handcards = sorted(handcards,key=lambda item:card_val[item[1]])
        start = 0
        for i in range(1, len(handcards) + 1):
            if i == len(handcards) or handcards[i][-1] != handcards[i - 1][-1]:
                if (i - start == 1):
                    cards["Single"].append(handcards[i - 1])
                elif (i - start == 2):
                    cards["Pair"].append(handcards[start:i])
                elif (i - start) == 3:
                    cards["Trips"].append(handcards[start:i])
                else:
                    cards["Bomb"].append(handcards[start:i])
                    bomb_info[handcards[start][-1]] = i-start
                start = i

        rank = rank
        temp = []
        for i in handcards:
            if i[-1] != rank and i[-1] != 'B' and i[-1] != 'R':
                temp.append(i)
        for i in cards['Bomb']:
            if i[0][-1] != rank and i[0][-1] != 'B' and i[0][-1] != 'R':
                for j in i:
                    temp.remove(j)
        cardre = [0] * 14
        for i in temp:
            if i[-1] == 'A':
                cardre[1] += 1
            if i[-1] == '2':
                cardre[2] += 1
            if i[-1] == '3':
                cardre[3] += 1
            if i[-1] == '4':
                cardre[4] += 1
            if i[-1] == '5':
                cardre[5] += 1
            if i[-1] == '6':
                cardre[6] += 1
            if i[-1] == '7':
                cardre[7] += 1
            if i[-1] == '8':
                cardre[8] += 1
            if i[-1] == '9':
                cardre[9] += 1
            if i[-1] == 'T':
                cardre[10] += 1
            if i[-1] == 'J':
                cardre[11] += 1
            if i[-1] == 'Q':
                cardre[12] += 1
            if i[-1] == 'K':
                cardre[13] += 1

        st = []
        minnum = 10
        mintwonum = 10

        for i in range(1, len(cardre) - 4):
            if 0 not in cardre[i:i + 5]:
                onenum = 0
                zeronum = 0
                twonum = 0
                for j in cardre[i:i + 5]:
                    if j - 1 == 0:
                        zeronum += 1
                    if j - 1 == 1:
                        onenum += 1
                    if j - 1 == 2:
                        twonum += 1

                if zeronum > onenum and minnum >= onenum:
                    if len(st) == 0:
                        st.append(i)
                        minnum = onenum
                        mintwonum = twonum
                    else:
                        if minnum == onenum:
                            if mintwonum > twonum:
                                st = []
                                st.append(i)
                                minnum = onenum
                                mintwonum = twonum
                        else:
                            st = []
                            st.append(i)
                            minnum = onenum
                            mintwonum = twonum

        if 0 not in cardre[10:] and cardre[1] != 0:
            onenum = 0
            zeronum = 0
            twonum = 0
            for j in cardre[i:i + 5]:
                if j - 1 == 0:
                    zeronum += 1
                if j - 1 == 1:
                    onenum += 1
                if j - 1 == 2:
                    twonum += 1

            if zeronum > onenum and minnum >= onenum:
                if len(st) == 0:
                    st.append(i)
                    minnum = onenum
                    mintwonum = twonum
                else:
                    if minnum == onenum:
                        if mintwonum > twonum:
                            st = []
                            st.append(i)
                            minnum = onenum
                            mintwonum = twonum
                    else:
                        st = []
                        st.append(i)
                        minnum = onenum
                        mintwonum = twonum

        tmp = []
        nowhandcards = []
        Straight = []
        if len(st) > 0:

            for i in range(st[0], st[0] + 5):
                if 1 < i < 10:
                    Straight.append(str(i))
                if i % 13 == 1:
                    Straight.append('A')
                if i == 10:
                    Straight.append('T')
                if i == 11:
                    Straight.append('J')
                if i == 12:
                    Straight.append('Q')
                if i == 13:
                    Straight.append('K')

        for i in range(0, len(handcards)):
            if handcards[i][-1] in Straight:
                tmp.append(handcards[i])
                Straight.remove(handcards[i][-1])
            else:
                nowhandcards.append(handcards[i])

        newcards = {}
        newcards["Single"] = []
        newcards["Pair"] = []
        newcards["Trips"] = []
        newcards["Bomb"] = []
        newcards['Straight'] =[]
        if len(tmp)==5:
             newcards['Straight'].append(tmp)
        start = 0
        for i in range(1, len(nowhandcards) + 1):
            if i == len(nowhandcards) or nowhandcards[i][-1] != nowhandcards[i - 1][-1]:
                if (i - start == 1):
                    newcards["Single"].append(nowhandcards[i - 1])
                elif (i - start == 2):
                    newcards["Pair"].append(nowhandcards[start:i])
                elif (i - start) == 3:
                    newcards["Trips"].append(nowhandcards[start:i])
                else:
                    newcards["Bomb"].append(nowhandcards[start:i])
                start = i

        return newcards,bomb_info

    def rest_cards(self, handcards, remaincards, rank):
        card_value_v2s = {0: "A", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7", 7: "8", 8: "9", 9: "T", 10: "J",
                          11: "Q", 12: "K"}
        card_value_s2v = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                          "Q": 12, "K": 13, "A": 14, "B": 16, "R": 17}

        card_index = {"A": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8, "T": 9, "J": 10,
                      "Q": 11, "K": 12, "R": 13, "B": 13}
        new_remaincards = {}
        for key,val in remaincards.items():
            new_remaincards[key] = copy.deepcopy(val)
        for card in handcards:
            card_type = str(card[0])
            x = card_index[card[1]]
            new_remaincards[card_type][x] = remaincards[card_type][x]-1

        rest_cards = []

        for key,value in new_remaincards.items():
            for i  in range(0,len(value)):
                if value[i] ==0 :
                    continue
                if i == 13 and key == 'S':
                    val = 'B'
                elif i == 13 and key == 'H':
                    val = 'R'
                else:
                    val = card_value_v2s[i]
                if value[i]==1:
                    rest_cards.append(key+val)
                elif value[i] == 2:
                    rest_cards.append(key + val)
                    rest_cards.append(key + val)
        card_value_s2v[str(rank)] = 15
        rest_cards = sorted(rest_cards,key = lambda item:card_value_s2v[item[1]])
        new_rest_cards = []
        tmp = []
        pre = rest_cards[0][-1]
        tmp = [pre]
        for cards in rest_cards[1:]:
            if cards[-1]!=pre:
                new_rest_cards.append(tmp)
                tmp = [cards]
                pre = cards[-1]
            else:
                tmp.append(cards)
        new_rest_cards.append(tmp)
        return new_rest_cards

    def Single(
            self, actionList, curAction, rank_card, handcards,
            numofnext, rest_cards, card_val,
            myPos, greaterPos, pass_num, my_pass_num):
        sorted_cards, bomb_info = self.combine_handcards(handcards, rank_card[-1],card_val)
        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]

        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb

        tag = 0
        single_actionList = []
        bomb_actionList = []
        for action in actionList[1:]:
            tag += 1
            if action[0] == 'Single':
                single_actionList.append((tag,action))
            else:
                bomb_actionList.append((tag,action))

        curVal = card_val[curAction[1]]  

        max_val = card_val[rest_cards[-1][0][-1]] 
        if numofnext >= 1 and numofnext <= 3:
            if (myPos+2)%4 == greaterPos and curVal >= 15 and numofnext!=1: 
                return 0

            for action in single_actionList:
                Index = action[0]
                action = action[1]
                if card_val[curAction[1]]>= max_val and action[2][0] in single_member and rank_card not in action[2]:
                    return Index
            for action in single_actionList:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= max_val and action[2][0] not in bomb_member and rank_card not in action[2]:
                    return Index

            if numofnext == 1:
                index = self.choose_bomb(bomb_actionList,handcards,sorted_cards,bomb_info,rank_card,card_val)
                if index!=-1:
                    return index

            for action in single_actionList:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= 14 and rank_card not in action[2]:
                    return Index


        def normal(single_actionList,rank_card): 
            for action in single_actionList:
                Index = action[0]
                action = action[1]
                if (action[2][0] in single_member or card_val[action[1]] >= 15) and rank_card not in action[2]:
                    return Index
            return -1

        def special(single_actionList,bomb_member,straight_member,rank_card):
            for action in single_actionList[::-1]:
                Index = action[0]
                action = action[1]
                if (action[2][0] not in bomb_member  or action[2][0] not in straight_member) and rank_card not in action[2]:
                    return Index
            return -1

        if (myPos+2)%4 == greaterPos: 
            if curVal >= 14 or curVal >= max_val:
                return 0
            else:
                index = normal(single_actionList,rank_card)
                if index!=-1:
                    return index
                else:
                    return 0
        else: 
            index = normal(single_actionList, rank_card)
            if index != -1:
                return index
            else:
                if pass_num >= 5 or my_pass_num >= 3:
                    index = special(single_actionList, bomb_member, straight_member, rank_card)
                    if index != -1:
                        return index
                if pass_num >= 7 or curVal >= max_val or my_pass_num >= 5:
                    index = self.choose_bomb(bomb_actionList,handcards,sorted_cards,bomb_info,rank_card,card_val)
                    if index != -1:
                        return index
                    else:
                        return 0
        return 0

    def Pair(self, actionList, curAction, rank_card, handcards, numofnext, rest_cards, card_val, myPos, greaterPos, pass_num, my_pass_num):

        sorted_cards,  bomb_info = self.combine_handcards(handcards,  rank_card[-1], card_val)

        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]

        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb

        pair_actionList = []
        bomb_actionList = []
        tag = 0
        for action in actionList[1:]:
            tag += 1
            if action[0] == 'Pair':
                pair_actionList.append((tag,  action))
            else:
                bomb_actionList.append((tag, action))

        curVal = card_val[curAction[1]]
        rest_cards = rest_cards[::-1]
        max_val = 0
        for cards in rest_cards:
            if len(cards) >= 2:
                max_val = card_val[cards[0][-1]]
                break
        if numofnext >= 2 and numofnext <= 4:

            if (myPos+2) % 4 == greaterPos and curVal >= 15 and numofnext != 2: 
                return 0

            for action in pair_actionList:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= max_val and action[2][0] in pair_member and rank_card not in action[2]:
                    return Index
            for action in pair_actionList:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= max_val and action[2][0] not in bomb_member and rank_card not in action[2]:
                    return Index
            if numofnext == 2:
                index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                if index != -1:
                    return index

            for action in pair_actionList[::-1]:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= 10 and rank_card not in action[2]:
                    return Index
        
        def normal(pair_actionList, pair_member, rank_card):
            for action in pair_actionList:
                Index = action[0]
                action = action[1]

                if (action[2][0] in pair_member or action[1]==rank_card[1]) and rank_card not in action[2] :
                    return Index

            return -1

        def special(pair_actionList, bomb_member, straight_member, rank_card):
            for action in pair_actionList[::-1]:
                Index = action[0]
                action = action[1]

                if (action[2][0] not in bomb_member or action[2][0] not in straight_member) and rank_card not in action[2]:
                    return Index
            return -1

        if (myPos+2)%4 == greaterPos: 
            if curVal >= 13 or curVal >= max_val:
                return 0
            else:
                index = normal(pair_actionList, pair_member, rank_card)
                if index!=-1:
                    return index
                else:
                    return 0
        else:
            index = normal(pair_actionList,  pair_member, rank_card)
            if index!=-1:
                return index
            else:
                if pass_num >= 5 or my_pass_num>=3:
                    index = special(pair_actionList, bomb_member, straight_member, rank_card)
                    if index != -1:
                        return index
                if pass_num >= 7 or curVal >= max_val or my_pass_num>=5:
                    index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                    if index!=-1:
                        return index
                    else:
                        return 0
        return 0

    def ThreeWithTwo(self,  actionList,  curAction, rank_card,  handcards,  numofnext, 
                    rest_cards,  card_val, myPos, greaterPos, pass_num, my_pass_num):
        sorted_cards,  bomb_info = self.combine_handcards(handcards,  rank_card[-1], card_val)

        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]

        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb

        three2_actionList = []
        bomb_actionList = []
        tag = 0

        for action in actionList[1:]:
            tag += 1
            if (action[0] == 'ThreeWithTwo'):
                three2_actionList.append((tag,  action))
            else:
                bomb_actionList.append((tag,  action))


        curVal = card_val[curAction[1]] 
        max_val = 0
        for cards in rest_cards[::-1]:
            if len(cards) >=3:
                max_val = card_val[cards[0][-1]]  
                break
        if numofnext >= 5 and numofnext <= 10:
            if (myPos + 2) % 4 == greaterPos and curVal>=14 and numofnext !=5:
                return 0
            three2_sorted = sorted(three2_actionList, key=lambda item:card_val[item[1][1]], reverse=False)
            for action in three2_sorted:
                index = action[0]
                action = action[1]
                trip = action[2][0]
                pair = action[2][3]
                if trip in trip_member and pair in pair_member and rank_card not in action[2] and card_val[pair[1]]<13:
                    return index
            if numofnext <= 7:
                index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                if index!=-1:
                    return index
                else:
                    return 0

        def normal(three2_actionList, trip_member, pair_member, rank_card):
            for action in three2_actionList:
                index = action[0]
                action = action[1]
                trip = action[2][0]
                pair = action[2][3]
                if trip in trip_member and pair in pair_member and rank_card not in action[2] and card_val[pair[-1]]<13:
                    return index
            return -1

        if (myPos + 2) % 4 == greaterPos:
            if curVal >= 14 or curVal >= max_val:
                return 0
            else:
                index = normal(three2_actionList, trip_member, pair_member, rank_card)
                if index!=-1:
                    return index
                else:
                    return 0
        else:
            index = normal(three2_actionList,  trip_member,  pair_member,  rank_card)
            if index != -1:
                return index
            else:
                if pass_num >= 5 or curVal>=max_val or my_pass_num>=3:
                    index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                    if index!=-1:
                        return index
                    else:
                        return 0
        return 0

    def Trips(self, actionList, curAction, rank_card, handcards, numofnext, rest_cards, card_val, myPos, greaterPos, pass_num, my_pass_num):


        sorted_cards,  bomb_info = self.combine_handcards(handcards,  rank_card[-1], card_val)

        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]

        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb

        trip_actionList = []
        bomb_actionList = []
        tag = 0
        for action in actionList[1:]:
            tag += 1
            if action[0] == 'Trips':
                trip_actionList.append((tag,  action))
            else:
                bomb_actionList.append((tag,  action))

        curVal = card_val[curAction[1]]
        rest_cards = rest_cards[::-1]
        max_val = 0
        for cards in rest_cards:
            if len(cards) >= 3:
                max_val = card_val[cards[0][-1]]
                break
        if numofnext <= 6 and numofnext >= 3:
            if (myPos + 2) % 4 == greaterPos and curVal >= 13 and numofnext != 3:  
                return 0

            for action in trip_actionList:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= max_val and action[2][0] in trip_member and action[2] and rank_card not in action[2]:
                    return Index

            if numofnext == 3:
                index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                if index != -1:
                    return index

            for action in trip_actionList[::-1]:
                Index = action[0]
                action = action[1]
                if card_val[action[1]] >= 10:
                    return Index

        def normal(trip_actionList, rank_card):
            for action in trip_actionList:
                Index = action[0]
                action = action[1]
                if action[2][0] in trip_member and rank_card not in action[2]:
                    return Index
            return -1



        if (myPos+2)%4 == greaterPos: 
            if curVal >= 13 or curVal>=max_val:
                return 0
            else:
                index = normal(trip_actionList, rank_card)
                if index!=-1:
                    return index
                else:
                    return 0
        else:
            index = normal(trip_actionList,  rank_card)
            if index!=-1:
                return index
            else:
                if curVal >= max_val or pass_num >= 5 or my_pass_num>=3:
                    index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                    if index !=-1:
                        return index

        return 0

    def ThreePair(self,  actionList, curAction, rank_card,  handcards,  numofnext, rest_cards,  card_val, myPos, greaterPos, pass_num, my_pass_num):
        sorted_cards,  bomb_info = self.combine_handcards(handcards,  rank_card[-1], card_val)
        card_origin = {"A": 1,  "2": 2,  "3": 3,  "4": 4,  "5": 5,  "6": 6,  "7": 7,  "8": 8,  "9": 9,  "T": 10,  "J": 11, 
                       "Q": 12,  "K": 13}
        card_val['A'] = 1
        card_val[rank_card[1]] = card_origin[rank_card[1]]
        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]
        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb
        pair3_actionList = []
        bomb_actionList = []
        tag = 0
        for action in actionList[1:]:
            tag += 1
            if (action[0] == 'ThreePair'):
                pair3_actionList.append((tag,  action))
            else :
                bomb_actionList.append((tag,  action))
        curVal = card_val[curAction[1]]  
        max_val = 0
        for cards in rest_cards[::-1]:
            if len(cards)>=2:
                max_val = card_val[cards[0][-1]]  
                break
        def normal(pair3_actionList, pair_member, rank_card):
            for action in pair3_actionList:
                index = action[0]
                action = action[1]
                first = action[2][0]
                mid = action[2][2]
                last = action[2][4]

                if first in pair_member and mid in pair_member and last in pair_member and rank_card not in action[2]:
                    return index
            return -1
        if (myPos + 2) % 4 == greaterPos:
            if curVal >= 14:
                return 0
            else:
                index = normal(pair3_actionList, pair_member, rank_card)
                if index!=-1:
                    return index
                else:
                    return 0
        else:
            index = normal(pair3_actionList,  pair_member,  rank_card)
            if index != -1:
                return index
            else:
                if pass_num >= 5 or curVal >= max_val or my_pass_num >= 3:
                    index = self.choose_bomb(bomb_actionList, handcards,sorted_cards,bomb_info,rank_card,card_val)
                    if index!=-1:
                        return index
                    else:
                        return 0
        return 0

    def Straight(self, actionList, rank_card, handcards, numofnext, card_val, pass_num, my_pass_num):
        sorted_cards,  bomb_info = self.combine_handcards(handcards,  rank_card[-1], card_val)
        card_origin = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                       "Q": 12, "K": 13, "R": 14, "B": 15}
        card_val['A'] = 1
        card_val[rank_card[1]] = card_origin[rank_card[1]]

        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]


        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb

        straight_actionList = []
        bomb_actionList = []
        tag = 0
        for action in actionList[1:]:
            tag += 1
            if action[0] == 'Straight':
                straight_actionList.append((tag,  action))
            else:
                bomb_actionList.append((tag,  action))
        if len(sorted_cards["Straight"])>0:
            curVal = sorted_cards["Straight"][0][-1]
            for action in straight_actionList:
                Index = action[0]
                action = action[1]
                if curVal == action[1] and rank_card not in action[2]:
                    return Index
        else:

            if numofnext >=5 and numofnext <= 10 or pass_num >= 5 or my_pass_num>=3:
                index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                if index != -1:
                    return index

        return 0

    def TwoTrips(self,  actionList,  curAction, rank_card, handcards, numofnext,  rest_cards,  card_val, myPos, greaterPos, pass_num, my_pass_num):

        sorted_cards,  bomb_info = self.combine_handcards(handcards,  rank_card[-1],card_val)

        card_origin = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                       "Q": 12, "K": 13, "R": 14, "B": 15}
        card_val['A'] = 1
        card_val[rank_card[1]] = card_origin[rank_card[1]]

        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]

        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb

        twoTripsList = []
        bomb_actionList = []
        tag = 0

        for action in actionList[1:]:
            tag += 1
            if (action[0] == "TwoTrips"):
                twoTripsList.append((tag,  action))
            else :
                bomb_actionList.append((tag,  action))
        curVal = card_val[curAction[1]]  
        max_val = 0
        for cards in rest_cards[::-1]:
            if len(cards) >= 3:
                max_val = card_val[cards[0][-1]]  
                break

        def normal(twoTripsList, trip_member, rank_card):
            for action in twoTripsList:
                index = action[0]
                action = action[1]
                first = action[2][0]
                last = action[2][3]

                if first in trip_member and last in trip_member and rank_card not in action[2]:
                    return index
            return -1

        if (myPos + 2) % 4 == greaterPos:
            if curVal >= 14:
                return 0
            else:
                index = normal(twoTripsList, trip_member, rank_card)
                if index!=-1:
                    return index
                else:
                    return 0
        else:
            index = normal(twoTripsList,  trip_member,  rank_card)
            if index != -1:
                return index
            else:
                if curVal>=max_val or pass_num>=5 or my_pass_num >= 3:
                    index = self.choose_bomb(bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val)
                    if index!=-1:
                        return index
                    else:
                        return 0
        return 0

    def Bomb(self, actionList, curAction, rank_card, handcards, numofnext, rest_cards, card_val,myPos,greaterPos):

        if (myPos + 2) % 4 == greaterPos:
            return 0

        sorted_cards, bomb_info = self.combine_handcards(handcards, rank_card[-1],card_val)

        bomb_member = []
        pair_member = []
        trip_member = []
        single_member = sorted_cards["Single"]
        straight_member = sorted_cards["Straight"]

        for pair in sorted_cards["Pair"]:
            pair_member += pair
        for trip in sorted_cards["Trips"]:
            trip_member += trip
        for bomb in sorted_cards["Bomb"]:
            bomb_member += bomb
        bomb_actionList = []
        tag = 0
        for action in actionList[1:]:
            tag += 1
            bomb_actionList.append((tag, action))
        index = self.choose_bomb(bomb_actionList,handcards,sorted_cards,bomb_info,rank_card,card_val)
        if index!=-1:
            return index
        else:
            return 0

    def passive(self, actionList, handcards, rank, curAction, greaterAction, myPos, greaterPos, remaincards, numofnext, pass_num, my_pass_num):

        rank_card = 'H' + str(rank)
        restcards = self.rest_cards(handcards, remaincards, rank)

        card_value_s2v = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                          "Q": 12, "K": 13, "A": 14, "B": 16, "R": 17}
        card_value_s2v[rank_card[-1]] = 15


        actIndex = 0
        if curAction[0]=="PASS":
            curAction = greaterAction

        if curAction[0] == "Single":
            actIndex = self.Single(actionList,curAction,rank_card,handcards,numofnext,restcards,
                                   card_value_s2v,myPos,greaterPos,pass_num,my_pass_num)

        elif curAction[0] == "Pair":
            actIndex = self.Pair(actionList, curAction, rank_card, handcards, numofnext, restcards,
                                 card_value_s2v, myPos,greaterPos,pass_num,my_pass_num)

        elif curAction[0] == "Trips":
            actIndex = self.Trips(actionList,curAction,rank_card,handcards,numofnext,restcards,
                                  card_value_s2v,myPos,greaterPos,pass_num,my_pass_num)

        elif curAction[0] == "ThreeWithTwo":
            actIndex = self.ThreeWithTwo(actionList, curAction,rank_card, handcards, numofnext,restcards,
                                         card_value_s2v,myPos,greaterPos,pass_num,my_pass_num)

        elif curAction[0] == "ThreePair":
            actIndex = self.ThreePair(actionList,curAction,rank_card, handcards, numofnext,restcards,
                                      card_value_s2v,myPos,greaterPos,pass_num,my_pass_num)

        elif curAction[0] == "TwoTrips":
            actIndex = self.TwoTrips(actionList, curAction,rank_card,handcards,numofnext, restcards,
                                     card_value_s2v,myPos,greaterPos,pass_num,my_pass_num)

        elif curAction[0] == "Straight" :
            actIndex = self.Straight(actionList,rank_card,handcards,numofnext,
                                     card_value_s2v,pass_num,my_pass_num)
        elif curAction[0] == "Bomb":
            actIndex = self.Bomb(actionList,curAction,rank_card,handcards,numofnext,restcards,
                                 card_value_s2v,myPos,greaterPos)

        return actIndex

    def getindex(self, tag, actList, actionList):
        if not actList:
            return 0
        myaction = tag
        mynumber = actList[0][0]
        if myaction == "Single":
            mycard = [actList[0][1]]
        else:
            mycard = actList[0][1]
        my_act = []
        my_act.append(myaction)
        my_act.append(mynumber)
        my_act.append(mycard)

        if my_act in actionList:
            return actionList.index(my_act)
        else:
            return 0

    def active(self,  actionList,  handcards, rank):

        for i in actionList:
            if len(handcards) == len(i[2]):
                return  actionList.index(i)
        single_actionlist = []
        pair_actionlist = []
        trips_actionlist = []
        threepair_actionlist = []
        threetwo_actionlist = []
        twotrips_actionlist = []
        straight_actionlist = []
        bomb_actionlist = []
        action2 = "None"
        action3 = "None"
        rank_card = 'H' + str(rank)

        card_value_s2v = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                          "Q": 12, "K": 13, "A": 14, "B": 16, "R": 17}
        card_value_s2v2 = {"A": 1,"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                          "Q": 12, "K": 13,  "B": 16, "R": 17}
        card_value_s2v[rank_card[-1]] = 15
        sorted_cards, bomb_info = self.combine_handcards(handcards, rank,card_value_s2v)
        
        def mysort(elem):
            return card_value_s2v[elem[0]]

        def mysort1(elem):
            return card_value_s2v2[elem[0]]

        if sorted_cards["Single"]:
            for singlecard in sorted_cards['Single']:
                single_actionlist.append([singlecard[-1], singlecard])
            single_actionlist.sort(key=mysort)


        if sorted_cards["Pair"]:
            for paircard in sorted_cards['Pair']:
                pair_actionlist.append([paircard[0][-1], paircard])
            pair_actionlist.sort(key=mysort)


        if sorted_cards['Trips']:
            for tripcard in sorted_cards['Trips']:
                trips_actionlist.append([tripcard[0][-1], tripcard])
            trips_actionlist.sort(key=mysort)


        if sorted_cards['Pair'] and sorted_cards['Trips']:
            for tripcard in sorted_cards['Trips']:
                for paircard in sorted_cards['Pair']:
                    threetwo_actionlist.append([tripcard[0][-1], tripcard + paircard])
            threetwo_actionlist.sort(key=mysort)


        if len(sorted_cards['Pair']) >= 3:
            for i in range(len(pair_actionlist)-2):
                if card_value_s2v[pair_actionlist[i][0]] == card_value_s2v[pair_actionlist[i+1][0]]-1 and card_value_s2v[pair_actionlist[i+1][0]] == card_value_s2v[pair_actionlist[i+2][0]]-1:
                    action2 = pair_actionlist[i][-1]+pair_actionlist[i+1][-1]+pair_actionlist[i+2][-1]
                    threepair_actionlist.append([action2[0][-1], action2])
            threepair_actionlist.sort(key=mysort1)

        if len(sorted_cards['Trips']) >= 2:
            for i in range(len(trips_actionlist)-1):
                if card_value_s2v[trips_actionlist[i][0]] == card_value_s2v[trips_actionlist[i+1][0]]-1:
                    action3 = trips_actionlist[i][-1]+trips_actionlist[i+1][-1]
                    twotrips_actionlist.append([action3[0][-1], action3])
            twotrips_actionlist.sort(key=mysort1)


        if 'Straight' in sorted_cards.keys() and sorted_cards['Straight']:
            for straightcard in sorted_cards['Straight']:
                straight_actionlist.append([straightcard[0][-1], straightcard])
            straight_actionlist.sort(key=mysort1)




        if sorted_cards['Single']:
            if card_value_s2v[single_actionlist[0][0]] <= 7 and card_value_s2v[single_actionlist[0][0]] != card_value_s2v[rank]:
                return self.getindex("Single", single_actionlist, actionList)

        if threepair_actionlist or threetwo_actionlist or twotrips_actionlist or straight_actionlist:
            n2t = ["ThreePair", "ThreeWithTwo", "TwoTrips", "Straight"]
            if len(sorted_cards['Pair']) == len(sorted_cards['Trips']) or (
                    len(sorted_cards['Pair']) >= 2 and len(sorted_cards['Trips']) >= 2):
                maxlen = [-1,-1,-1,-1]
                if len(threepair_actionlist)>1:
                    maxlen[0] = card_value_s2v[threepair_actionlist[-1][0]]-card_value_s2v[threepair_actionlist[0][0]]

                if len(threetwo_actionlist)>1:
                    maxlen[1] = card_value_s2v[threetwo_actionlist[-1][0]]-card_value_s2v[threetwo_actionlist[0][0]]

                if len(twotrips_actionlist)>1:
                    maxlen[2] = card_value_s2v[twotrips_actionlist[-1][0]]-card_value_s2v[twotrips_actionlist[0][0]]

                if len(straight_actionlist)>1:
                    maxlen[3] = card_value_s2v[straight_actionlist[-1][0]]-card_value_s2v[straight_actionlist[0][0]]

                minpos0 = [100, 100, 100, 100]

                if threepair_actionlist:
                    minpos0[0] = card_value_s2v2[threepair_actionlist[0][0]]

                if threetwo_actionlist:
                    minpos0[1] = card_value_s2v[threetwo_actionlist[0][0]]

                if twotrips_actionlist:
                    minpos0[2] = card_value_s2v2[twotrips_actionlist[0][0]]

                if straight_actionlist:
                    minpos0[3] = card_value_s2v2[straight_actionlist[0][0]]

                min_type0 = minpos0.index(min(minpos0))
                type0 = n2t[min_type0]
                if min_type0 == 0 and card_value_s2v2[threepair_actionlist[0][0]]<=5:
                    return self.getindex(type0,threepair_actionlist,actionList)
                elif min_type0 == 1 and card_value_s2v[threetwo_actionlist[0][0]]<=5:
                    return self.getindex(type0, threetwo_actionlist, actionList)
                elif min_type0 == 2 and card_value_s2v2[twotrips_actionlist[0][0]]<=5:
                    return self.getindex(type0, twotrips_actionlist, actionList)
                elif min_type0 == 3 and card_value_s2v2[straight_actionlist[0][0]]<=5:
                    return self.getindex(type0, straight_actionlist, actionList)

                if maxlen != [-1,-1,-1,-1]:
                    max_type = maxlen.index(max(maxlen))
                    type1 = n2t[max_type]
                    if max_type == 0:
                        typelist1 = threepair_actionlist
                    elif max_type == 1:
                        typelist1 = threetwo_actionlist
                    elif max_type == 2:
                        typelist1 = twotrips_actionlist
                    else:
                        typelist1 = straight_actionlist

                    return self.getindex(type1, typelist1, actionList)
                else:
                    minpos = [100, 100, 100, 100]

                    if threepair_actionlist:
                        minpos[0] = card_value_s2v[threepair_actionlist[0][0]]

                    if threetwo_actionlist:
                        minpos[1] = card_value_s2v[threetwo_actionlist[0][0]]

                    if twotrips_actionlist:
                        minpos[2] = card_value_s2v[twotrips_actionlist[0][0]]

                    if straight_actionlist:
                        minpos[3] = card_value_s2v[straight_actionlist[0][0]]

                    min_type = minpos.index(min(minpos))
                    type = n2t[min_type]
                    if min_type == 0:
                        typelist = threepair_actionlist
                    elif min_type == 1:
                        typelist = threetwo_actionlist
                    elif min_type == 2:
                        typelist = twotrips_actionlist
                    else:
                        typelist = straight_actionlist
                    return self.getindex(type, typelist, actionList)

            elif threepair_actionlist or twotrips_actionlist or straight_actionlist:
                n2t2 = ["ThreePair", "TwoTrips", "Straight"]
                maxlen1 = [-1,-1,-1]
                if len(threepair_actionlist)>1:
                    maxlen1[0] = card_value_s2v[threepair_actionlist[-1][0]]-card_value_s2v[threepair_actionlist[0][0]]

                if len(twotrips_actionlist)>1:
                    maxlen1[1] = card_value_s2v[twotrips_actionlist[-1][0]]-card_value_s2v[twotrips_actionlist[0][0]]

                if len(straight_actionlist)>1:
                    maxlen1[2] = card_value_s2v[straight_actionlist[-1][0]]-card_value_s2v[straight_actionlist[0][0]]

                    minpos4 = [100, 100, 100]

                    if threepair_actionlist:
                        minpos4[0] = card_value_s2v2[threepair_actionlist[0][0]]

                    if twotrips_actionlist:
                        minpos4[1] = card_value_s2v2[twotrips_actionlist[0][0]]

                    if straight_actionlist:
                        minpos4[2] = card_value_s2v2[straight_actionlist[0][0]]

                    min_type4 = minpos4.index(min(minpos4))
                    type4 = n2t[min_type4]
                    if min_type4 == 0 and card_value_s2v2[threepair_actionlist[0][0]] <= 5:
                        return self.getindex(type4, threepair_actionlist, actionList)
                    elif min_type4 == 1 and card_value_s2v2[twotrips_actionlist[0][0]] <= 5:
                        return self.getindex(type4, twotrips_actionlist, actionList)
                    elif min_type4 == 2 and card_value_s2v2[straight_actionlist[0][0]] <= 5:
                        return self.getindex(type4, straight_actionlist, actionList)
                if maxlen1 != [-1,-1,-1]:
                    max_type1 = maxlen1.index(max(maxlen1))
                    type2 = n2t2[max_type1]
                    if max_type1 == 0:
                        typelist2 = threepair_actionlist
                    elif max_type1 == 1:
                        typelist2 = twotrips_actionlist
                    else:
                        typelist2 = straight_actionlist
                    return self.getindex(type2, typelist2, actionList)
                else:
                    minpos1 = [100, 100, 100]
                    if threepair_actionlist:
                        minpos1[0] = card_value_s2v[threepair_actionlist[0][0]]
                    if twotrips_actionlist:
                        minpos1[1] = card_value_s2v[twotrips_actionlist[0][0]]
                    if straight_actionlist:
                        minpos1[2] = card_value_s2v[straight_actionlist[0][0]]
                    min_type1 = minpos1.index(min(minpos1))
                    type3 = n2t2[min_type1]
                    if min_type1 == 0:
                        typelist3 = threepair_actionlist
                    elif min_type1 == 1:
                        typelist3 = twotrips_actionlist
                    elif min_type1 == 2:
                        typelist3 = straight_actionlist
                    return self.getindex(type3, typelist3, actionList)



        if pair_actionlist and trips_actionlist:
            if len(trips_actionlist) > len(pair_actionlist) and card_value_s2v[pair_actionlist[0][0]]<=10:
                return self.getindex("ThreeWithTwo",threetwo_actionlist,actionList)
            if card_value_s2v[pair_actionlist[0][0]] < card_value_s2v[trips_actionlist[0][0]]:
                return self.getindex("Pair",  pair_actionlist, actionList)
            else:
                return self.getindex("Trips", trips_actionlist, actionList)
        if pair_actionlist:
            return self.getindex("Pair",  pair_actionlist, actionList)
        if trips_actionlist:
            return self.getindex("Trips", trips_actionlist, actionList)
        if single_actionlist:
            return self.getindex("Single",single_actionlist,actionList)
        else:
            return 0

    def back_action(self, msg, mypos, tribute_pos):
        self.action = msg["actionList"]

        def check(temp):
            card_value_s2v = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11,
                              "Q": 12, "K": 13, "A": 14, "B": 16, "R": 17}
            card_value_s2v[msg['curRank']] = 15
            cards,_ = self.combine_handcards(temp,msg["curRank"],card_value_s2v)
            for card in cards["Trips"]:
                for c in card:
                    temp.remove(c)
            for card in cards["Bomb"]:
                for c in card:
                    temp.remove(c)

        def get_card_index(target: str):
            for i in range(len(self.action)):
                if self.action[i][2][0] == target:
                    act_index = i
                    return i

        temp = []  
        for card in self.action:
            temp.append(card[2][0])
        check(temp)  

        if (tribute_pos+mypos)%2 != 0:
            back_list = ['S5', 'C5', 'D5', 'ST', 'CT', 'DT']
            
            for card in temp:
                if card == 'H5':
                    return get_card_index(card)
                elif card == 'HT':
                    return get_card_index(card)
                elif card in back_list:
                    return get_card_index(card)
            
            act_index = randint(0, len(temp)-1)
            card = temp[act_index]
            return get_card_index(card)
        else:
            backlist = []
            for card in temp:
                if card[-1] != 'T':
                    if int(card[-1])<5:
                        backlist.append(card)
            if backlist:
               return get_card_index(backlist[randint(0, len(backlist)-1)])
            return get_card_index(temp[randint(0, len(temp)-1)])

    def tribute(self, actionList, rank):

        rank_card = 'H'+rank
        first_action = actionList[0]
        if rank_card in first_action[2]:
            return 1
        else:
            return 0

    def rule_parse(self, msg, mypos, playcards, remaincards, history, pass_num, my_pass_num, back_pos):
        self.action = msg["actionList"]
        if len(self.action) == 1:
            return 0
        if msg["stage"] == "play" and msg["greaterPos"] != mypos and msg["curPos"] != -1:  
            numofnext = history[str((mypos + 1) % 4)]["remain"]
            self.act = self.passive(self.action, msg["handCards"], msg["curRank"], msg['curAction'],msg["greaterAction"],mypos,
                                    msg["greaterPos"],remaincards, numofnext,pass_num,my_pass_num)

        elif msg["stage"] == "play" and (msg["greaterPos"] == -1 or msg["curPos"] == -1):  
            self.act = self.active(self.action, msg["handCards"], msg["curRank"])
        elif msg["stage"] == "back":
            try:
                self.act = self.back_action(msg,mypos,back_pos)
            except Exception as e:
                print(e)
                self.act = 1
        elif msg["stage"] == "tribute":
            try:
                self.act = self.tribute(self.action,msg["curRank"])
            except Exception as e:
                print(e)
                self.act = 0
        else:
            self.act_range = msg["indexRange"]
            self.act = randint(0, self.act_range)

        return self.act

    def handle(self, item, rank_card):
        card = ""
        from utils import card_map, map_card
        if 'Single' == item[0]:
            if rank_card == item[1]:
                card = 'H' + item[1]
            else:
                card = item[1]
        elif 'Pair' == item[0]:
            if rank_card == item[1]:
                card = 'H' + item[1]*2
            else:
                card = item[1]*2
        elif 'Trips' == item[0]:
            if rank_card == item[1]:
                card = 'H' + item[1]*3
            else:
                card = item[1]*3
        elif 'Bomb' == item[0]:
            if rank_card == item[1]:
                card = 'H' + item[1]*len(item[-1])
            else:
                card = item[1]*len(item[-1])
        elif 'ThreeWithTwo' == item[0]:
            arr = []
            for each in item[-1]:
                arr.append(each[-1])
            if rank_card == item[1]:
                tmp = list(set(arr).difference(item[1],rank_card))[0]
                card += rank_card*3 + tmp*2
            else:
                tmp = list(set(arr).difference(item[1],rank_card))
                if len(tmp) == 0:
                    card += item[1]*3 + rank_card*2
                else:
                    card += item[1]*3 + tmp[0]*2
        elif 'ThreePair' == item[0]:
            if item[1] == 'Q':
                card += 'Q'*2 + 'K'*2 + 'A'*2
            else:
                card += card_map[map_card[item[1]]]*2 + card_map[map_card[item[1]] + 1]*2 + card_map[map_card[item[1]] + 2]*2
        elif 'TwoTrips' == item[0]:
            
            if item[1] == 'K':
                card += 'K'*3 + 'A'*3
            else:
                card += card_map[map_card[item[1]]]*3 + card_map[map_card[item[1]]+1]*3
        elif 'Straight' == item[0]:
            if item[1] == 'T':
                for i in range(10,15):
                    card += card_map[i]
            elif item[1] == 'A':
                for i in range(1,6):
                    card += card_map[i]
            else:
                for i in range(int(item[1]),int(item[1]) + 5):
                    card += card_map[i]
        else:
            return "PASS"
        return card
        
    def nw_model(self, msg):
        self.action = msg["actionList"]
        actionList = []
        item = msg["greaterAction"]
        rank_card = msg["curRank"]
        card = ""
        card = self.handle(item, rank_card)
        for item in self.action:
            tmp = self.handle(item, rank_card)
            actionList.append(tmp)
        actionList = list(set(actionList))
        return self.model(card, actionList)

    def choose_bomb(self, bomb_actionList, handcards, sorted_cards, bomb_info, rank_card, card_val):
        unit = 3
        bomb_res = []

        card_val["JOKER"] = 10000

        def is_inStraight(action,sorted_cards):
            flag = 0
            if len(sorted_cards["Straight"]) != 0:
                for card in action[2]:
                    if card in sorted_cards["Straight"]:
                        flag = 1
                        break
            return flag

        for action in bomb_actionList:

            index = action[0]
            action = action[1]

            if action[0] == "Bomb":
                if is_inStraight(action,sorted_cards):
                    continue
                prior = 0
                for card in action[2]:
                    if card == rank_card:
                        prior += unit
                if prior !=0:
                    prior -= 1
                l = len(action[2])
                bomb_res.append((index,card_val[action[1]]+(l-4)*13+prior))
            else : 
                new_handcards = []
                for card in handcards:
                    if card not in action[2]:
                        new_handcards.append(card)
                new_sortedcards,_ = self.combine_handcards(new_handcards,rank_card[-1],card_val)
                if len(new_sortedcards["Single"]) > 2:
                    continue
                if len(new_sortedcards) ==2 and (card_val[new_sortedcards["Single"][0]]<5 or card_val[new_sortedcards["Single"][1]]<5):
                    continue
                if len(new_sortedcards) ==1 and (card_val[new_sortedcards["Single"][0]]<5 or card_val[new_sortedcards["Single"][1]]<5):
                    continue
                bomb_res.append((index,card_val[action[1]]+26))
        if len(bomb_res)==0:
            return -1
        else:
            bomb_res = sorted(bomb_res,key=lambda item:item[1])
            return bomb_res[0][0]

    def random_parse(self,msg):
        self.action = msg["actionList"]
        self.act_range = msg["indexRange"]

        return randint(0,self.act_range)