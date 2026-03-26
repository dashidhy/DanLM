# Wrapper: extract decision logic from client_v5_1.py into Action.parse(msg, myPos)
from Util2 import ACTIONENEMY, ACTIONTEAM, ACTIONFIRST


class Action:
    def __init__(self):
        self.action_team = ACTIONTEAM()
        self.action_first = ACTIONFIRST()
        self.action_enemy = ACTIONENEMY()

    @staticmethod
    def _get_single(message, card_type='Pair'):
        Universal = 'H' + message['curRank']
        action_list = message["actionList"]
        ignoreList = []
        for i in range(len(action_list)):
            type_, cur_rank, cur_action = action_list[i]
            if Universal in cur_action and len(cur_action) > 1:
                ignoreList.append(i)
        cardList = []
        for i in range(len(action_list)):
            type_, cur_rank, cur_action = action_list[i]
            if type_ == card_type and i not in ignoreList:
                count = 0
                for j in action_list[i + 1:]:
                    _type, _cur_rank, _cur_action = j
                    if _cur_rank in ['B', 'R']:
                        continue
                    if cur_rank == _cur_rank and Universal not in _cur_action:
                        count += 1
                if count < 1:
                    cardList.append({'index': i, 'rank': cur_rank, 'action': cur_action})
        return cardList

    @staticmethod
    def _get_pairtrips(message, card_type='Pair'):
        Universal = 'H' + message['curRank']
        action_list = message["actionList"]
        cardIndexList, cardRankList, cardActionList = [], [], []
        for i in range(len(action_list)):
            type_, cur_rank, cur_action = action_list[i]
            if type_ == card_type and Universal not in cur_action:
                cardIndexList.append(i)
                cardRankList.append(cur_rank)
                cardActionList.append(cur_action)
        cardList = []
        for i in range(len(cardRankList)):
            count = cardRankList.count(cardRankList[i])
            if count > 1 or cardRankList[i] in ['B', 'R']:
                continue
            else:
                cardList.append({'index': cardIndexList[i], 'rank': cardRankList[i], 'action': cardActionList[i]})
        return cardList

    def _get_card_type(self, message):
        action_list = message["actionList"]
        cardTypeList = {
            'TwoTrips': [], 'ThreePair': [], 'Straight': [], 'ThreeWithTwo': [],
            'Pair': [], 'Single': [], 'Trips': [], 'Bomb': [], 'StraightFlush': [],
            'PASS': [], 'tribute': [], 'back': [],
        }
        if len(action_list) < 2:
            for i in range(len(action_list)):
                type_, cur_rank, cur_action = action_list[i]
                cardTypeList[type_].append({'index': i, 'rank': cur_rank, 'action': cur_action})
            return cardTypeList

        for i in range(len(action_list)):
            type_, cur_rank, cur_action = action_list[i]
            if cur_action == 'PASS':
                cardTypeList[type_].append({'index': i, 'rank': cur_rank, 'action': cur_action})
            elif len(cur_action) > 3:
                cardTypeList[type_].append({'index': i, 'rank': cur_rank, 'action': cur_action})

        cardTypeList['Single'] = self._get_single(message, card_type='Single')
        cardTypeList['Pair'] = self._get_pairtrips(message, card_type='Pair')
        cardTypeList['Trips'] = self._get_pairtrips(message, card_type='Trips')
        return cardTypeList

    @staticmethod
    def _get_bombCards(message):
        bombCardsLists = {'StraightFlush': [], 'Bomb': []}
        for bomb_type in ['StraightFlush', 'Bomb']:
            bombCardsList = []
            for j in message['actionList']:
                cur_card_type, cur_rank, cur_action = j
                if bomb_type == cur_card_type:
                    for k in cur_action:
                        bombCardsList.append(k)
            bombCardsLists[bomb_type] = bombCardsList
        return bombCardsLists

    def parse(self, msg, myPos):
        bombCardsLists = self._get_bombCards(msg)
        cardTypeList = self._get_card_type(msg)

        if 'PASS' in msg['actionList'][0]:
            if self.action_team.bool_action_team(msg, myPos):
                act_index = self.action_team.ActionTeam(msg, bombCardsLists, cardTypeList, fuckRank=10)
            else:
                act_index = self.action_enemy.ActionEnemy(msg, bombCardsLists, cardTypeList, myPos)
        else:
            act_index = self.action_first.ActionFirst(msg, bombCardsLists, cardTypeList, WarningCard=10)

        # Bounds check
        if act_index < 0 or act_index > msg['indexRange']:
            act_index = 0
        return act_index
