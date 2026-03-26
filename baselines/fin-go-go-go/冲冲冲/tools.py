from collections import Counter


def key_card_list(action_list):
    key_card = []
    for each_action in action_list:
        if each_action[0] == 'Bomb':
            key_card += each_action[2]
    return set(key_card)


def each_card_amount(hand_card):
    cards = [n[1] for n in hand_card]
    return dict(Counter(cards))


def card_kinds(action_list):
    card_kind_list = []
    for each_action in action_list:
        card_kind_list.append(each_action[0])
    return set(card_kind_list)


def remove_card_kind(hand_cards):
    hand_cards_without_kind = []
    for each_card in hand_cards:
        hand_cards_without_kind.append(each_card[-1])
    return hand_cards_without_kind


def list_diff(action_card, hand_cards):
    list_diff = hand_cards[:]
    for x in action_card:
        if x in list_diff:
            list_diff.remove(x)
    return list_diff


def one_card(action_card, hand_cards):
    amount = 0
    parse_hand_cards = remove_card_kind(hand_cards)
    after_hand_cards = list_diff(action_card, parse_hand_cards)
    for k, v in dict(Counter(remove_card_kind(after_hand_cards))).items():
        if v == 1:
            amount = amount + 1
    return amount


def single_hand_card(hand_cards):
    amount = 0
    for k, v in dict(Counter(remove_card_kind(hand_cards))).items():
        if v == 1:
            amount = amount + 1
    return amount


def my_aciton_list(action_list):
    key_cards = key_card_list(action_list)
    my_aciton_list = action_list[:]
    for x in range(1, 10):
        for card in key_cards:
            for each_action in my_aciton_list:
                if card in each_action[2]:
                    my_aciton_list.remove(each_action)
    for x in range(1, 10):
        for action in my_aciton_list:
            if action[0] == 'StraightFlush':
                my_aciton_list.remove(action)
    return my_aciton_list


def no_divide_action_list(action_list, hand_cards):
    bad_action = []
    if ['PASS', 'PASS', 'PASS'] in action_list:
        action_list.remove(['PASS', 'PASS', 'PASS'])
    hand_cards_without_kind = remove_card_kind(hand_cards)
    for each_action in action_list:
        tmp_hand_cards = hand_cards_without_kind[:]
        action_cards = remove_card_kind(each_action[2])
        for card in action_cards:
            tmp_hand_cards.remove(card)
        for card in action_cards:
            if card in tmp_hand_cards:
                if each_action not in bad_action:
                    bad_action.append(each_action)
    for _ in bad_action:
        action_list.remove(_)
    return action_list


def min_single_card(action_list, hand_cards):
    pri_single_card = single_hand_card(hand_cards)
    item = {}
    single_action_list = []
    for action in action_list:
        action_card = remove_card_kind(action[2])
        amount = one_card(action_card, hand_cards)
        if action == ['PASS', 'PASS', 'PASS']:
            item[str(action)] = 99
        else:
            item[str(action)] = amount
    min_single_card = min([v for k, v in item.items()])
    if min_single_card-1 > pri_single_card:
        return ['PASS', 'PASS', 'PASS']
    else:
        for k, v in item.items():
            if v == min_single_card:
                single_action_list.append(eval(k))
        return single_action_list


def max_length_action(action_list):
    no_pass_action_list = action_list[:]
    if ['PASS', 'PASS', 'PASS'] in no_pass_action_list:
        no_pass_action_list.remove(['PASS', 'PASS', 'PASS'])
    max_length = 0
    for c in no_pass_action_list:
        max_length = 0
        if len(c[2]) > max_length:
            max_length = len(c[2])
    action_list_plus_plus = []
    for c in no_pass_action_list:
        if len(c[2]) == max_length:
            action_list_plus_plus.append(c)
    return action_list_plus_plus[0]


def min_cards_bomb(bomb_action_list):
    min_cards_bomb = 99
    for action in bomb_action_list:
        if len(action[2]) < min_cards_bomb:
            min_cards_bomb = len(action[2])
    for action in bomb_action_list:
        if len(action[2]) != min_cards_bomb:
            bomb_action_list.remove(action)
    return bomb_action_list[0]


def random_aciton(action_list, hand_cards):
    old_action_list = action_list[:]
    if my_aciton_list(action_list) == [['PASS', 'PASS', 'PASS']] and card_kinds(action_list)=={'Bomb', 'PASS'} or card_kinds(action_list)=={'PASS', 'Bomb'}:
        print('*'*50)
        for _ in range(1, 20):
            for action in action_list:
                card_amount = dict(Counter(remove_card_kind(action[2])))
                if min(card_amount.values()) > 1 and len(card_amount)>1 and action[1]!= 'JOKER':
                    action_list.remove(action)
        boom_cards_more_4 = []
        parse_action_list = action_list[:]
        for action in parse_action_list:
            if len(action[2]) > 4:
                boom_cards_more_4.append(action)
        for bomb_action in boom_cards_more_4:
            kind = bomb_action[1]
            cards_amount = len(bomb_action[2])
            for _ in range(1, 10):
                for action in parse_action_list:
                    if action[1] == kind and len(action[2]) < cards_amount:
                        parse_action_list.remove(action)
        if len(parse_action_list)>1:
            action = parse_action_list[1]
            if action[1] == 'JOKER':
                return ['PASS', 'PASS', 'PASS']
        else:
            action = old_action_list[0]
        if len(set(remove_card_kind(action[2]))) > 1:
            hhh_action_list = action_list[:]
            for _ in range(1, 20):
                for action in hhh_action_list:
                    if len(set(remove_card_kind(action[2]))) > 1:
                        hhh_action_list.remove(action)
            boom_cards_more_4_1 = []
            for action in hhh_action_list:
                if len(action[2]) > 4:
                    boom_cards_more_4_1.append(action)
            for bomb_action in boom_cards_more_4_1:
                kind = bomb_action[1]
                cards_amount = len(bomb_action[2])
                for _ in range(1, 10):
                    for action in hhh_action_list:
                        if action[1] == kind and len(action[2]) < cards_amount:
                            hhh_action_list.remove(action)
            if hhh_action_list:
                return min_cards_bomb(hhh_action_list)
            else:
                return action
        else:
            return action


    elif not my_aciton_list(action_list):
        return action_list[-1]
    else:
        my_action = my_aciton_list(action_list)
        min_single_action = min_single_card(my_action, hand_cards)
        print(min_single_action)
        if min_single_action:
            if min_single_action != ['PASS', 'PASS', 'PASS']:
                return max_length_action(min_single_action)
            else:
                return ['PASS', 'PASS', 'PASS']
        else:
            return ['PASS', 'PASS', 'PASS']


def parse_pass(action_list):
    my_action = my_aciton_list(action_list)
    # 如果都是炸弹了
    if not my_action:
        return action_list[-1]
    else:
        return max_length_action(my_action)



if __name__ == '__main__':
    pass

