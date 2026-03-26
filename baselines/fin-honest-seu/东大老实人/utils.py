from collections import defaultdict
card_map = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
            9: '9', 10: 'T', 11: 'J', 12: 'Q',
            13: 'K', 14: 'A', 16: 'S', 17: 'H'}
map_card = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': '13'}
cards_mapping = defaultdict(int)


def cards_encode(rank):
    """
        input para : rank card number
        return para : convert str number to value
        description : XXX
    """
    str2val = defaultdict(int)
    for i in range(2, 18):
        if i == 15:
            str2val[str(rank)] = i
        elif i >= 10:
            str2val[card_map[i]] = i
        else:
            str2val[str(i)] = i
    return str2val


def handle_single(rank):
    """
        input : rank card
        return : card to value, including rank card
    """
    return cards_encode(rank)


def handle_pair(rank):
    """
        input : rank card
        return : card to value, including rank card
    """
    pair_encode = defaultdict(int)
    for i in range(2, 18):
        if i == 15:
            continue
        pair_encode[card_map[i]*2] = i
    return pair_encode


def handle_trip(rank):
    trip_encode = defaultdict(int)
    for i in range(2, 15):
        trip_encode[card_map[i]*3] = i
    return trip_encode


def handle_bomb(rank):
    bomb_encode = defaultdict(int)
    for i in range(2, 15):
        for j in range(4, 11):
            bomb_encode[card_map[i]*j] = i
    bomb_encode["JOKER"] = 16
    return bomb_encode


def handle_threewithtwo(rank):
    three_with_two_encode = defaultdict(int)
    for i in range(2, 15):
        for j in range(2, 18):
            if i == j or j == 15:
                continue
            three_with_two_encode[card_map[i]*3 + card_map[j]*2] = i
    return three_with_two_encode


def handle_three_pair(rank):
    three_pair_encode = defaultdict(int)
    for i in range(1, 13):
        three_pair_encode[
            card_map[i]*2 + card_map[i + 1]*2 + card_map[i + 2]*2
            ] = i
    return three_pair_encode


def handle_two_trips(rank):
    two_trips_encode = defaultdict(int)
    for i in range(1, 14):
        two_trips_encode[card_map[i]*3 + card_map[i + 1]*3] = i
    return two_trips_encode


def handle_straight(rank):
    straight_encode = defaultdict(int)
    for i in range(1, 11):
        key = ""
        for j in range(5):
            key += card_map[i + j]
        straight_encode[key] = i
    return straight_encode


def handle_index(rank):
    arr = []
    single_encode = handle_single(rank)
    pair_encode = handle_pair(rank)
    trip_encode = handle_trip(rank)
    bomb_encode = handle_bomb(rank)
    threewithtwo_encode = handle_threewithtwo(rank)
    two_trips_encode = handle_two_trips(rank)
    three_pair_encode = handle_three_pair(rank)
    straight_encode = handle_straight(rank)
    arr.append(single_encode)
    arr.append(pair_encode)
    arr.append(trip_encode)
    arr.append(bomb_encode)
    arr.append(threewithtwo_encode)
    arr.append(two_trips_encode)
    arr.append(three_pair_encode)
    arr.append(straight_encode)
    length = 0
    for item in arr:
        for k, v in item.items():
            cards_mapping[k] = length
            length += 1
    for num in range(1, 9):
        for i in range(2, 15):
            cards_mapping['H' + card_map[i]*num] = length
            length += 1
    for num in range(1, 14):
        for i in range(1, 18):
            if i == num or i == 14 or i == 15:
                continue
            cards_mapping['H' + card_map[num]*3 + card_map[i]*2] = length
            length += 1
    cards_mapping["PASS"] = length


handle_index(2)
