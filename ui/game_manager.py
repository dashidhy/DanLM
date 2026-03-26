"""Game session manager for the GuanDan web UI.

Wraps the engine classes (GuanDanRound, GuanDanGame) and provides
a JSON-serializable state for the frontend.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

import numpy as np

from danzero.engine.actions import (
    DIM_CARDS,
    DIM_PLAY_TYPE,
    PLAY_TYPES,
    play_to_card_vector,
    play_type_of,
)
from danzero.engine.cards import (
    BIG_JOKER,
    CARD_INT_TO_STR,
    NUM_RANKS,
    SMALL_JOKER,
    SUIT_CHARS,
    TOTAL_CARD_TYPES,
    deal_hands,
    is_wild_card,
    level_rank_index,
    single_card_power,
)
from danzero.encoding.tokenizer import order_cards_in_play
from danzero.engine.game import (
    GuanDanGame,
    GuanDanRound,
    Observation,
    compute_level_up,
    compute_reward,
)
from danzero.engine.tribute import (
    TributeRecord,
    perform_tribute,
    transfer_card,
    tribute_back_legal_cards,
    tribute_give_legal_cards,
)

from ui_agent import UIAgent

# Suit display info
SUIT_SYMBOLS = {"H": "\u2665", "S": "\u2660", "C": "\u2663", "D": "\u2666"}
RANK_DISPLAY = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
POSITION_NAMES = {1: "right", 2: "top", 3: "left"}
PLAYER_LABELS = {0: "You", 1: "Next (Right)", 2: "Partner (Top)", 3: "Prev (Left)"}

# AI thinking delay in seconds
AI_THINK_DELAY = 2.0


def _card_info(card_int: int, level: int) -> dict:
    """Convert a card integer to display info."""
    if card_int == SMALL_JOKER:
        return {
            "card_int": card_int,
            "rank": "S",
            "suit": "joker",
            "suit_symbol": "\U0001f0cf",
            "display": "Small",
            "is_wild": False,
            "is_level": False,
        }
    if card_int == SMALL_JOKER + 1:  # BIG_JOKER = 53
        return {
            "card_int": card_int,
            "rank": "B",
            "suit": "joker",
            "suit_symbol": "\U0001f0cf",
            "display": "Big",
            "is_wild": False,
            "is_level": False,
        }
    suit_idx = card_int // NUM_RANKS
    rank_idx = card_int % NUM_RANKS
    suit_char = SUIT_CHARS[suit_idx]
    level_rank = level_rank_index(level)
    return {
        "card_int": card_int,
        "rank": RANK_DISPLAY[rank_idx],
        "suit": suit_char,
        "suit_symbol": SUIT_SYMBOLS[suit_char],
        "display": RANK_DISPLAY[rank_idx],
        "is_wild": is_wild_card(card_int, level),
        "is_level": rank_idx == level_rank,
    }


_RANK_DISPLAY_FULL = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A", "S", "B"]


def _play_to_json(play_80: np.ndarray, index: int, level: int) -> dict:
    """Convert an 80-dim play to JSON-serializable dict."""
    ptype = play_type_of(play_80)
    if ptype == "pass":
        return {"index": index, "cards": [], "type": "pass", "card_ints": [], "rank": None}

    # Use tokenizer's ordering: rank ascending, fullhouse triple-first,
    # wild cards at substitution position, consecutive rank order.
    cards_ec = play_80[:DIM_CARDS]
    rank_oh = play_80[DIM_CARDS + DIM_PLAY_TYPE:]
    rank_idx = int(rank_oh.argmax())
    level_idx = level_rank_index(level)

    card_ints = order_cards_in_play(cards_ec, ptype, rank_idx, level_idx)
    cards = [_card_info(ci, level) for ci in card_ints]
    rank_display = _RANK_DISPLAY_FULL[rank_idx] if rank_idx < len(_RANK_DISPLAY_FULL) else str(rank_idx)
    return {"index": index, "cards": cards, "type": ptype, "card_ints": card_ints, "rank": rank_display}


def _hand_sorted_cards(hand_vec: np.ndarray, level: int) -> list[dict]:
    """Convert hand count vector to sorted card info list."""
    raw = []
    for ci in range(TOTAL_CARD_TYPES):
        for _ in range(int(hand_vec[ci])):
            raw.append(ci)

    def _sort_key(ci: int) -> tuple:
        if ci == BIG_JOKER:
            return (0, 0, 0)
        if ci == SMALL_JOKER:
            return (0, 1, 0)
        power = single_card_power(ci, level)
        suit = ci // NUM_RANKS
        return (1, -power, suit)

    raw.sort(key=_sort_key)
    return [_card_info(ci, level) for ci in raw]


class GameSession:
    """Manages one game session (single round or full game)."""

    def __init__(self, agent: UIAgent, mode: str = "single_round") -> None:
        self.game_id = str(uuid.uuid4())
        self.mode = mode
        self.agent = agent
        self.human_seat = 0
        self.auto_play = False
        self.hint_enabled = False

        # Engine objects
        self.game: GuanDanGame | None = None
        self.current_round: GuanDanRound | None = None
        self.current_obs: Observation | None = None

        # UI state
        self.hand_order: list[int] | None = None  # custom card order for human
        self.trick_plays: list[dict] = []  # plays in current trick
        self.play_history: list[dict] = []  # all plays this round
        self.phase = "idle"  # idle, tribute_give, tribute_back, tribute_give_done, playing, round_over, game_over
        self.result: dict | None = None
        self.tribute_records: list | None = None

        # Tribute state machine
        self._trib: dict | None = None

        # Round start info for pre-game overlay
        self.round_start_info: dict | None = None

        # AI pending queue
        self._ai_pending: list[tuple[int, int]] = []
        self._rng = np.random.default_rng()

    # ------------------------------------------------------------------
    # Round creation
    # ------------------------------------------------------------------

    def new_round(self, seed: int | None = None) -> dict:
        """Start a new single round (with random tribute, matching eval distribution)."""
        rng = np.random.default_rng(seed)
        level = int(rng.integers(2, 15))
        team_levels = (level, level)
        hands = deal_hands(seed=seed)
        has_tribute = bool(rng.integers(2))

        self.result = None
        self.trick_plays = []
        self.play_history = []
        self.hand_order = None
        self._ai_pending = []
        self._trib = None
        self.tribute_records = None

        self.agent.reset_round(level)

        if has_tribute:
            prev_finish_order = rng.permutation(4).tolist()
            self._init_tribute(hands, prev_finish_order, level, team_levels)
            # round_start_info set by _init_tribute
            self._advance_tribute()
            return self.to_state_json()
        else:
            first_player = int(rng.integers(4))
            self.round_start_info = {
                "level": level,
                "tribute_type": "none",
                "first_player": first_player,
            }
            self._create_round(level, hands, first_player, team_levels)
            return self.to_state_json()

    def new_full_game(self) -> dict:
        """Start a new full game (level 2 → A)."""
        self.game = GuanDanGame()
        self.mode = "full_game"
        return self._start_game_round()

    def _start_game_round(self, seed: int | None = None) -> dict:
        """Start the next round in a full game with interactive tribute."""
        assert self.game is not None

        self.result = None
        self.trick_plays = []
        self.play_history = []
        self.hand_order = None
        self._ai_pending = []
        self._trib = None
        self.tribute_records = None

        hands = deal_hands(seed=seed)

        if self.game.last_winners is None:
            # First round: no tribute, random first player
            first_player = int(np.random.randint(4))
            owner_team = self.game.team_of(first_player)
            level = self.game.team_levels[owner_team]
            self.agent.reset_round(level)
            self.round_start_info = {
                "level": level,
                "tribute_type": "none",
                "first_player": first_player,
            }
            self._create_round(level, hands, first_player,
                               tuple(self.game.team_levels))
            self.game.round_count += 1
        else:
            owner = self.game.last_winners[0]
            owner_team = self.game.team_of(owner)
            level = self.game.team_levels[owner_team]
            self.agent.reset_round(level)
            prev_finish_order = list(self.game.last_winners)
            self._init_tribute(hands, prev_finish_order, level,
                               tuple(self.game.team_levels))
            self._advance_tribute()
            self.game.round_count += 1

        return self.to_state_json()

    def _create_round(self, level, hands, first_player, team_levels):
        """Create the GuanDanRound and enter playing phase."""
        self.current_round = GuanDanRound(
            level=level, hands=hands,
            first_player=first_player, team_levels=team_levels,
        )
        self.current_obs = self.current_round.get_observation()
        self.phase = "playing"

    # ------------------------------------------------------------------
    # Interactive tribute state machine
    # ------------------------------------------------------------------

    def _init_tribute(self, hand_vecs, finish_order, level, team_levels):
        """Set up the interactive tribute state machine."""
        p1st, p2nd, p3rd, p4th = finish_order
        same_team = (p3rd - p4th) % 4 == 2

        trib = {
            "hands": hand_vecs,
            "finish_order": finish_order,
            "level": level,
            "team_levels": team_levels,
            "records": [],
            "first_player": p1st,
            "is_double": same_team,
            # For double tribute: collect give cards before transfers
            "give_cards": {},  # giver -> card_int
            # Current step info for human UI
            "current_action": None,  # "give" or "back"
            "current_actor": None,
            "current_target": None,
            "legal_cards": [],
        }
        self._trib = trib

        # Check anti-tribute
        if same_team:
            if hand_vecs[p4th][BIG_JOKER] >= 2:
                self._set_anti_tribute(p4th)
                return
            if hand_vecs[p3rd][BIG_JOKER] >= 2:
                self._set_anti_tribute(p3rd)
                return
            # Double tribute: queue give steps
            trib["pending"] = [
                ("give", p4th),
                ("give", p3rd),
                ("resolve_double",),
                # back steps added after resolve
            ]
            self.round_start_info = {
                "level": level,
                "tribute_type": "double",
                "givers": [p4th, p3rd],
                "receivers": [p1st, p2nd],
            }
        else:
            if hand_vecs[p4th][BIG_JOKER] >= 2:
                self._set_anti_tribute(p4th)
                return
            # Single tribute
            trib["pending"] = [
                ("give", p4th, p1st),
                ("back", p1st, p4th),
            ]
            trib["first_player"] = p4th
            self.round_start_info = {
                "level": level,
                "tribute_type": "single",
                "givers": [p4th],
                "receivers": [p1st],
            }

    def _set_anti_tribute(self, player):
        """Handle anti-tribute (player has 2 HR)."""
        trib = self._trib
        level = trib["level"]
        self.round_start_info = {
            "level": level,
            "tribute_type": "anti",
            "first_player": trib["first_player"],
            "anti_holders": [player],  # one player holds both big jokers
        }
        trib["records"] = [
            {"giver": player, "receiver": player, "card": -1, "card_info": None},
            {"giver": player, "receiver": player, "card": -1, "card_info": None},
        ]
        trib["pending"] = []
        # Finalize immediately
        self._finalize_tribute()

    def _advance_tribute(self):
        """Process tribute steps until human input is needed or tribute completes."""
        trib = self._trib
        if trib is None:
            return

        pending = trib["pending"]
        hands = trib["hands"]
        level = trib["level"]

        while pending:
            step = pending[0]

            # Special: resolve double tribute receivers
            if step[0] == "resolve_double":
                pending.pop(0)
                self._resolve_double_tribute()
                if self._trib is None:
                    return  # Cross anti-tribute finalized
                pending = self._trib["pending"]
                continue

            action = step[0]  # "give" or "back"
            actor = step[1]
            target = step[2] if len(step) > 2 else None

            # Pause before back phase so frontend can show give results
            if action == "back" and not trib.get("give_review_shown"):
                self.phase = "tribute_give_done"
                # Store give records as tribute_records for frontend display
                self.tribute_records = list(trib["records"])
                return

            if actor == self.human_seat:
                # Human needs to choose
                if action == "give":
                    legal = tribute_give_legal_cards(hands[actor], level)
                    self.phase = "tribute_give"
                else:
                    legal = tribute_back_legal_cards(hands[actor], level)
                    self.phase = "tribute_back"
                trib["current_action"] = action
                trib["current_actor"] = actor
                trib["current_target"] = target
                trib["legal_cards"] = legal
                return  # Wait for human input

            # AI auto-picks via agent
            if action == "give":
                legal = tribute_give_legal_cards(hands[actor], level)
                card = self.agent.select_tribute_give(
                    actor, hands[actor], legal, trib["is_double"], target,
                )
                if trib["is_double"] and target is None:
                    # Double tribute give phase: store card, don't transfer yet
                    trib["give_cards"][actor] = card
                else:
                    # Single tribute: transfer immediately
                    transfer_card(hands, actor, target, card)
                trib["records"].append({
                    "action": "give",
                    "giver": actor, "receiver": target if target is not None else -1,
                    "card": card,
                    "card_info": _card_info(card, level),
                })
            else:  # back
                legal = tribute_back_legal_cards(hands[actor], level)
                give_recs = [
                    TributeRecord(r["giver"], r["receiver"], r["card"])
                    for r in trib["records"] if r.get("action") == "give"
                ]
                card = self.agent.select_tribute_back(
                    actor, hands[actor], legal, target, give_recs,
                )
                transfer_card(hands, actor, target, card)
                trib["records"].append({
                    "action": "back",
                    "giver": actor, "receiver": target,
                    "card": card,
                    "card_info": _card_info(card, level),
                })

            pending.pop(0)

        # All steps done
        self._finalize_tribute()

    def _resolve_double_tribute(self):
        """Determine receivers for double tribute and queue back steps."""
        trib = self._trib
        hands = trib["hands"]
        level = trib["level"]
        fo = trib["finish_order"]
        p1st, p2nd, p3rd, p4th = fo

        give_cards = trib["give_cards"]
        card_4th = give_cards[p4th]
        card_3rd = give_cards[p3rd]

        # Cross anti-tribute check
        if card_4th == BIG_JOKER and card_3rd == BIG_JOKER:
            # Replace records with anti-tribute
            trib["records"] = [
                {"giver": p4th, "receiver": p4th, "card": -1, "card_info": None},
                {"giver": p3rd, "receiver": p3rd, "card": -1, "card_info": None},
            ]
            trib["pending"] = []
            self.round_start_info = {
                "level": trib["level"],
                "tribute_type": "anti",
                "first_player": trib["first_player"],
                "anti_holders": [p4th, p3rd],  # each holds one big joker
            }
            self._finalize_tribute()
            return

        # Determine receivers
        power_4th = single_card_power(card_4th, level)
        power_3rd = single_card_power(card_3rd, level)

        if power_4th == power_3rd:
            recv_4th = (p4th + 3) % 4
            recv_3rd = (p3rd + 3) % 4
        elif power_4th > power_3rd:
            recv_4th = p1st
            recv_3rd = p2nd
        else:
            recv_4th = p2nd
            recv_3rd = p1st

        # Execute give transfers
        transfer_card(hands, p4th, recv_4th, card_4th)
        # Update records with correct receivers
        for rec in trib["records"]:
            if rec["giver"] == p4th and rec["receiver"] == -1:
                rec["receiver"] = recv_4th

        transfer_card(hands, p3rd, recv_3rd, card_3rd)
        for rec in trib["records"]:
            if rec["giver"] == p3rd and rec["receiver"] == -1:
                rec["receiver"] = recv_3rd

        # Queue back steps
        trib["pending"] = [
            ("back", recv_4th, p4th),
            ("back", recv_3rd, p3rd),
        ]

        # Who gave to p1st plays first
        trib["first_player"] = p4th if recv_4th == p1st else p3rd

    def tribute_action(self, card_int: int) -> dict:
        """Human selects a card for tribute. Returns updated state."""
        trib = self._trib
        if trib is None:
            return self.to_state_json()

        hands = trib["hands"]
        level = trib["level"]
        actor = trib["current_actor"]
        target = trib["current_target"]
        action = trib["current_action"]
        legal = trib["legal_cards"]

        # Validate
        if card_int not in legal:
            return self.to_state_json()
        if hands[actor][card_int] <= 0:
            return self.to_state_json()

        # Execute human's choice
        if action == "give":
            if trib["is_double"] and target is None:
                # Double tribute give: store card, don't transfer yet
                trib["give_cards"][actor] = card_int
            else:
                transfer_card(hands, actor, target, card_int)
            trib["records"].append({
                "action": "give",
                "giver": actor, "receiver": target if target is not None else -1,
                "card": card_int,
                "card_info": _card_info(card_int, level),
            })
        else:  # back
            transfer_card(hands, actor, target, card_int)
            trib["records"].append({
                "action": "back",
                "giver": actor, "receiver": target,
                "card": card_int,
                "card_info": _card_info(card_int, level),
            })

        # Remove completed step and continue
        trib["pending"].pop(0)
        trib["current_action"] = None
        self._advance_tribute()
        return self.to_state_json()

    def continue_tribute(self) -> dict:
        """Resume tribute after user reviewed give results. Proceeds to back phase."""
        if self.phase != "tribute_give_done" or self._trib is None:
            return self.to_state_json()
        self._trib["give_review_shown"] = True
        self._advance_tribute()
        return self.to_state_json()

    def _visible_tribute_records(self, trib: dict) -> list:
        """Return tribute records with card_info hidden for incomplete batches.

        In double tribute, both givers choose independently before reveal.
        Same for back phase. Hide card_info for the current batch if not
        all participants in that batch have chosen yet.

        Double tribute has 2 give records then 2 back records.
        A batch is incomplete if pending still has steps of the same action type.
        """
        records = trib["records"]
        if not trib["is_double"] or not records:
            return records

        pending = trib["pending"]
        if not pending:
            return records  # All done, show everything

        # Count expected gives and backs
        n_give_records = sum(1 for r in records if r.get("action") == "give")
        n_back_records = sum(1 for r in records if r.get("action") == "back")

        # Give batch incomplete: need 2 gives, have fewer
        # Back batch incomplete: need 2 backs, have fewer
        give_complete = n_give_records >= 2
        back_complete = n_back_records >= 2

        visible = []
        for r in records:
            act = r.get("action")
            if act == "give" and not give_complete:
                visible.append({**r, "card_info": None, "card": -1})
            elif act == "back" and not back_complete:
                visible.append({**r, "card_info": None, "card": -1})
            else:
                visible.append(r)
        return visible

    def _finalize_tribute(self):
        """All tribute steps done. Create round and enter playing phase."""
        trib = self._trib
        hands = trib["hands"]
        level = trib["level"]
        team_levels = trib["team_levels"]
        first_player = trib["first_player"]

        self.tribute_records = trib["records"]
        # Update round_start_info with first_player (now known)
        if self.round_start_info:
            self.round_start_info["first_player"] = first_player

        # Notify agents of tribute results
        records_typed = [
            TributeRecord(r["giver"], r["receiver"], r["card"])
            for r in trib["records"]
        ]
        is_anti = any(r["card"] < 0 for r in trib["records"])
        if is_anti:
            anti_abs = np.zeros((4, 54), dtype=np.float32)
            for r in trib["records"]:
                if r["card"] < 0:
                    anti_abs[r["giver"], BIG_JOKER] += 1.0
            self.agent.notify_tribute(records_typed, anti_abs)
        else:
            self.agent.notify_tribute(records_typed)

        self._create_round(level, hands, first_player, team_levels)
        self._trib = None

    # ------------------------------------------------------------------
    # Playing phase
    # ------------------------------------------------------------------

    def play_action(self, action_index: int) -> dict:
        """Human plays an action. Returns updated state."""
        if self.phase != "playing" or self.current_obs is None:
            return self.to_state_json()

        obs = self.current_obs
        if obs.player != self.human_seat and not self.auto_play:
            return self.to_state_json()

        rnd = self.current_round
        level = rnd.level

        # Record the play
        play_80 = obs.legal_plays[action_index]
        play_json = _play_to_json(play_80, action_index, level)
        play_entry = {
            "player": obs.player,
            "cards": play_json["cards"],
            "type": play_json["type"],
            "is_pass": play_json["type"] == "pass",
        }
        self.trick_plays.append(play_entry)
        self.play_history.append(play_entry)

        # Execute
        new_obs = rnd.step(action_index)

        # Notify agents
        new_trick = (new_obs is not None and new_obs.is_leading
                     and new_obs.player == rnd.state.lead_player)
        self.agent.observe_action(obs.player, play_80, new_trick)

        if new_obs is None or rnd.done:
            self._finish_round()
            return self.to_state_json()

        # Check for new trick
        if new_trick:
            self.trick_plays = []

        self.current_obs = new_obs
        return self.to_state_json()

    def advance_one_ai(self) -> dict | None:
        """Advance one AI turn. Returns state, or None if not AI's turn."""
        if self.phase != "playing" or self.current_obs is None:
            return None
        if self.current_round.done:
            return None

        obs = self.current_obs
        p = obs.player

        # If it's human's turn and not auto-play, do nothing
        if p == self.human_seat and not self.auto_play:
            return None

        rnd = self.current_round
        level = rnd.level

        # Agent selects action
        action_idx = self.agent.select_play(obs, rnd)

        # Record
        play_80 = obs.legal_plays[action_idx]
        play_json = _play_to_json(play_80, action_idx, level)
        play_entry = {
            "player": p,
            "cards": play_json["cards"],
            "type": play_json["type"],
            "is_pass": play_json["type"] == "pass",
        }
        self.trick_plays.append(play_entry)
        self.play_history.append(play_entry)

        # Execute
        new_obs = rnd.step(action_idx)

        # Notify agents
        new_trick = (new_obs is not None and new_obs.is_leading
                     and new_obs.player == rnd.state.lead_player)
        self.agent.observe_action(p, play_80, new_trick)

        if new_obs is None or rnd.done:
            self._finish_round()
            return self.to_state_json()

        # Check for new trick
        if new_trick:
            self.trick_plays = []

        self.current_obs = new_obs
        return self.to_state_json()

    def _finish_round(self) -> None:
        """Handle round completion."""
        rnd = self.current_round
        fo = rnd.finish_order

        if self.mode == "full_game" and self.game is not None:
            game_over = self.game.finish_round(rnd)
            winner_team = 0 if fo[0] % 2 == 0 else 1
            level_up = compute_level_up(fo)
            self.result = {
                "finish_order": fo,
                "rewards": {str(p): compute_reward(fo, p) for p in range(4)},
                "winner_team": winner_team,
                "human_won": self.human_seat in {fo[0], (fo[0] + 2) % 4},
                "level_up": level_up,
                "team_levels": list(self.game.team_levels),
            }
            self.phase = "game_over" if game_over else "round_over"
        else:
            winner_team = 0 if fo[0] % 2 == 0 else 1
            self.result = {
                "finish_order": fo,
                "rewards": {str(p): compute_reward(fo, p) for p in range(4)},
                "winner_team": winner_team,
                "human_won": self.human_seat in {fo[0], (fo[0] + 2) % 4},
            }
            self.phase = "round_over"

        self.current_obs = None

    # ------------------------------------------------------------------
    # Hints
    # ------------------------------------------------------------------

    def get_hints(self) -> list[dict]:
        """Get top 3 AI-recommended plays with Q-values (deduplicated)."""
        if self.current_obs is None:
            return []
        obs = self.current_obs
        level = self.current_round.level
        top_k = self.agent.get_top_k(obs, self.current_round, k=10)
        hints = []
        seen_keys: set[tuple] = set()
        for action_idx, q_val in top_k:
            play_json = _play_to_json(obs.legal_plays[action_idx], action_idx, level)
            dedup_key = (play_json["type"], play_json["rank"], tuple(sorted(play_json["card_ints"])))
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            play_json["q_value"] = round(q_val, 4)
            hints.append(play_json)
            if len(hints) >= 3:
                break
        return hints

    def next_round(self) -> dict:
        """Start next round in full game mode."""
        if self.mode != "full_game" or self.game is None:
            return self.to_state_json()
        return self._start_game_round()

    # ------------------------------------------------------------------
    # State serialization
    # ------------------------------------------------------------------

    def to_state_json(self) -> dict:
        """Serialize current state to JSON for frontend."""
        # During tribute phase, use tribute hands
        if self.phase in ("tribute_give", "tribute_back", "tribute_give_done") and self._trib is not None:
            return self._tribute_state_json()

        rnd = self.current_round
        if rnd is None:
            return {"phase": "idle", "game_id": self.game_id}

        level = rnd.level
        obs = self.current_obs
        state = rnd.state

        # Human's hand cards — sorted by power (descending), jokers first
        hand_vec = state.hands[self.human_seat]
        hand_cards_raw = []
        for ci in range(TOTAL_CARD_TYPES):
            for _ in range(int(hand_vec[ci])):
                hand_cards_raw.append(ci)

        if self.hand_order is not None:
            hand_cards = [_card_info(ci, level) for ci in self.hand_order
                          if ci < TOTAL_CARD_TYPES and hand_vec[ci] > 0]
        else:
            def _sort_key(ci: int) -> tuple:
                if ci == BIG_JOKER:
                    return (0, 0, 0)
                if ci == SMALL_JOKER:
                    return (0, 1, 0)
                power = single_card_power(ci, level)
                suit = ci // NUM_RANKS
                return (1, -power, suit)

            hand_cards_raw.sort(key=_sort_key)
            hand_cards = [_card_info(ci, level) for ci in hand_cards_raw]

        # Opponents info
        opponents = []
        for seat in [1, 2, 3]:
            card_count = int(state.hands[seat].sum())
            finished = seat in state.finish_order
            if finished:
                card_count = 0
            opponents.append({
                "seat": seat,
                "position": POSITION_NAMES[seat],
                "label": PLAYER_LABELS[seat],
                "card_count": card_count,
                "is_teammate": seat == 2,
                "finished": finished,
                "finish_rank": state.finish_order.index(seat) + 1 if finished else None,
                "warn_low": 0 < card_count <= 10,
            })

        # Legal plays (only when it's human's turn)
        legal_plays = []
        if obs is not None and obs.player == self.human_seat and not self.auto_play:
            for i in range(obs.legal_plays.shape[0]):
                legal_plays.append(_play_to_json(obs.legal_plays[i], i, level))

        # Hints
        hints = []
        if self.hint_enabled and obs is not None and obs.player == self.human_seat:
            hints = self.get_hints()

        # Current player info
        current_player = obs.player if obs is not None else None
        is_human_turn = (current_player == self.human_seat) if current_player is not None else False

        # Team levels
        if self.game is not None:
            team_levels = list(self.game.team_levels)
        else:
            team_levels = list(rnd.team_levels)

        return {
            "game_id": self.game_id,
            "phase": self.phase,
            "mode": self.mode,
            "round_level": level,
            "team_levels": team_levels,
            "round_number": self.game.round_count if self.game else 1,
            "current_player": current_player,
            "lead_player": state.lead_player if state else None,
            "is_human_turn": is_human_turn and not self.auto_play,
            "hand": hand_cards,
            "hand_count": int(hand_vec.sum()),
            "opponents": opponents,
            "legal_plays": legal_plays,
            "trick_plays": self.trick_plays,
            "finish_order": state.finish_order,
            "auto_play": self.auto_play,
            "hint_enabled": self.hint_enabled,
            "hints": hints,
            "tribute_records": self.tribute_records,
            "round_start_info": self.round_start_info,
            "result": self.result,
        }

    def _tribute_state_json(self) -> dict:
        """State JSON during tribute phase."""
        trib = self._trib
        level = trib["level"]
        hands = trib["hands"]

        hand_cards = _hand_sorted_cards(hands[self.human_seat], level)

        # Opponent card counts during tribute
        opponents = []
        for seat in [1, 2, 3]:
            card_count = int(hands[seat].sum())
            opponents.append({
                "seat": seat,
                "position": POSITION_NAMES[seat],
                "label": PLAYER_LABELS[seat],
                "card_count": card_count,
                "is_teammate": seat == 2,
                "finished": False,
                "finish_rank": None,
                "warn_low": False,
            })

        # Legal tribute cards for human
        legal_tribute_cards = [
            _card_info(ci, level) for ci in trib.get("legal_cards", [])
        ]

        # Team levels
        if self.game is not None:
            team_levels = list(self.game.team_levels)
        else:
            team_levels = list(trib["team_levels"])

        return {
            "game_id": self.game_id,
            "phase": self.phase,
            "mode": self.mode,
            "round_level": level,
            "team_levels": team_levels,
            "round_number": self.game.round_count if self.game else 1,
            "current_player": trib["current_actor"],
            "is_human_turn": trib["current_actor"] == self.human_seat,
            "hand": hand_cards,
            "hand_count": int(hands[self.human_seat].sum()),
            "opponents": opponents,
            "legal_plays": [],
            "trick_plays": [],
            "finish_order": [],
            "auto_play": self.auto_play,
            "hint_enabled": self.hint_enabled,
            "hints": [],
            "tribute_records": self._visible_tribute_records(trib),
            "round_start_info": self.round_start_info,
            "result": None,
            # Tribute-specific fields
            "tribute_action": trib.get("current_action"),
            "tribute_target": trib.get("current_target"),
            "tribute_legal_cards": legal_tribute_cards,
        }
