#!/usr/bin/env python3
"""Complete game evaluation for DanZero.

Plays full GuanDan games (multiple rounds with level progression from 2 to A)
to compute game-level win rates comparable to the DanZero paper's Table I.

The paper reports win rates over 1000 "episodes" where one episode = one
complete game (many rounds), NOT single-round win rates.

All evaluation uses the unified pluggable eval engine (play_complete_game_agents).
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import time

import numpy as np

from danzero.eval.agents import create_agent


# ---------------------------------------------------------------------------
# Complete game with pluggable agents
# ---------------------------------------------------------------------------

def play_complete_game_agents(
    agents: dict[int, object],
    seed: int | None = None,
    max_rounds: int = 200,
) -> dict:
    """Play one complete game using pluggable EvalAgents.

    Handles tribute via agent methods (model-driven for v1t).
    Uses the same game/level logic as GuanDanGame but with agent-driven tribute.
    """
    from danzero.engine.cards import BIG_JOKER, deal_hands, single_card_power
    from danzero.engine.game import GuanDanRound, NUM_PLAYERS, TEAM_PAIRS, compute_level_up
    from danzero.engine.tribute import (
        TributeRecord,
        perform_tribute,
        transfer_card,
        tribute_back_legal_cards,
        tribute_give_legal_cards,
    )

    team_levels = [2, 2]
    game_point_failures = [0, 0]
    last_winners = None
    rng = np.random.default_rng(seed)

    def team_of(p):
        return p % 2

    for round_idx in range(max_rounds):
        round_seed = seed + round_idx * 1000 if seed is not None else None
        hands = deal_hands(seed=round_seed)

        anti_tribute_abs = None

        if last_winners is None:
            first_player = int(rng.integers(NUM_PLAYERS))
            owner = first_player
            level = team_levels[team_of(owner)]
            tribute_records = []
        else:
            owner = last_winners[0]
            level = team_levels[team_of(owner)]

            p1st, p2nd, p3rd, p4th = last_winners
            same_team = (p3rd - p4th) % 4 == 2

            if same_team:
                anti = hands[p4th][BIG_JOKER] + hands[p3rd][BIG_JOKER] >= 2
            else:
                anti = hands[p4th][BIG_JOKER] >= 2

            if anti:
                # Build anti-tribute encoding before perform_tribute
                anti_tribute_abs = np.zeros((4, 54), dtype=np.float32)
                if same_team:
                    anti_tribute_abs[p4th, BIG_JOKER] = float(hands[p4th][BIG_JOKER])
                    anti_tribute_abs[p3rd, BIG_JOKER] = float(hands[p3rd][BIG_JOKER])
                else:
                    anti_tribute_abs[p4th, BIG_JOKER] = float(hands[p4th][BIG_JOKER])

                tribute_records, first_player = perform_tribute(
                    hands, last_winners, level,
                )
            else:
                tribute_records = []

                if same_team:
                    givers = [p4th, p3rd]
                    receivers = [None, None]
                else:
                    givers = [p4th]
                    receivers = [p1st]

                # Reset agents for this round
                for pid, agent in agents.items():
                    agent.reset(pid, level)

                # Give phase
                for gi, giver in enumerate(givers):
                    legal = tribute_give_legal_cards(hands[giver], level)
                    if len(legal) == 1:
                        chosen = legal[0]
                    else:
                        chosen = agents[giver].select_tribute_give(
                            hands[giver], legal, same_team, receivers[gi],
                        )
                    rec = TributeRecord(giver=giver, receiver=-1, card=chosen)
                    tribute_records.append(rec)

                # Determine receivers
                if same_team:
                    card_4th = tribute_records[0].card
                    card_3rd = tribute_records[1].card
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
                    tribute_records[0].receiver = recv_4th
                    tribute_records[1].receiver = recv_3rd
                    receivers = [recv_4th, recv_3rd]
                    transfer_card(hands, p4th, recv_4th, card_4th)
                    transfer_card(hands, p3rd, recv_3rd, card_3rd)
                    first_player = p4th if recv_4th == p1st else p3rd
                else:
                    receiver = receivers[0]
                    tribute_records[0].receiver = receiver
                    card = tribute_records[0].card
                    transfer_card(hands, givers[0], receiver, card)
                    first_player = givers[0]

                # Back phase
                give_records = list(tribute_records)
                for bi, returner in enumerate(receivers):
                    back_to = givers[bi]
                    legal = tribute_back_legal_cards(hands[returner], level)
                    if len(legal) == 1:
                        chosen = legal[0]
                    else:
                        chosen = agents[returner].select_tribute_back(
                            hands[returner], legal, back_to, give_records,
                        )
                    rec = TributeRecord(giver=returner, receiver=back_to, card=chosen)
                    tribute_records.append(rec)
                    transfer_card(hands, returner, back_to, chosen)

        # Reset agents and notify tribute
        for pid, agent in agents.items():
            agent.reset(pid, level)
        for agent in agents.values():
            agent.notify_tribute(tribute_records, anti_tribute_abs=anti_tribute_abs)

        rnd = GuanDanRound(
            level=level,
            hands=hands,
            first_player=first_player,
            team_levels=tuple(team_levels),
        )

        for pid, agent in agents.items():
            agent.notify_start(rnd.state.hands[pid].copy())

        obs = rnd.get_observation()
        for _ in range(2000):
            if rnd.done:
                break
            p = obs.player
            action_idx = agents[p].select_play(obs, rnd)
            play = obs.legal_plays[action_idx].copy()
            obs = rnd.step(action_idx)
            new_trick = obs is not None and obs.is_leading
            for agent in agents.values():
                agent.observe_action(p, play, new_trick)
            if obs is None:
                break

        # Game state update (same logic as GuanDanGame.finish_round)
        assert rnd.done
        fo = rnd.finish_order

        if last_winners is not None:
            round_owner = last_winners[0]
        else:
            round_owner = fo[0]
        round_owner_team = team_of(round_owner)

        last_winners = fo
        winner = fo[0]
        winner_team = team_of(winner)
        level_up = compute_level_up(fo)
        new_level = min(14, team_levels[winner_team] + level_up)
        team_levels[winner_team] = new_level

        if level == 14:
            owner_players = TEAM_PAIRS[round_owner_team]
            if fo[0] in owner_players and fo[-1] not in owner_players:
                return {
                    "winner_team": round_owner_team,
                    "rounds_played": round_idx + 1,
                    "final_levels": list(team_levels),
                }
            game_point_failures[round_owner_team] += 1
            if game_point_failures[round_owner_team] >= 3:
                team_levels[round_owner_team] = 2

    # Timeout
    if team_levels[0] > team_levels[1]:
        winner = 0
    elif team_levels[1] > team_levels[0]:
        winner = 1
    else:
        winner = -1
    return {
        "winner_team": winner,
        "rounds_played": max_rounds,
        "final_levels": list(team_levels),
    }


# ---------------------------------------------------------------------------
# Parallel worker
# ---------------------------------------------------------------------------

def _eval_worker(
    game_seeds: list[int | None],
    spec_a: str,
    spec_b: str,
    device: str,
    max_rounds: int,
) -> dict:
    """Run a batch of games in a worker process. Returns partial results.

    Each worker loads models independently to avoid cross-process sharing.
    """
    agent_a = create_agent(spec_a, device)
    agent_b = create_agent(spec_b, device)

    import copy
    agents = {0: agent_a, 1: agent_b, 2: copy.copy(agent_a), 3: copy.copy(agent_b)}

    wins = 0
    losses = 0
    draws = 0
    rounds_list = []

    for game_seed in game_seeds:
        result = play_complete_game_agents(agents, seed=game_seed, max_rounds=max_rounds)
        w = result["winner_team"]
        rounds_list.append(result["rounds_played"])
        if w == 0:
            wins += 1
        elif w == 1:
            losses += 1
        else:
            draws += 1

    return {
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "rounds_list": rounds_list,
    }


# ---------------------------------------------------------------------------
# Aggregate evaluation
# ---------------------------------------------------------------------------

def evaluate_complete_games(
    play_fn,
    num_games: int = 100,
    seed: int | None = None,
    verbose: bool = False,
    log_interval: int = 0,
) -> dict:
    """Run multiple complete games serially and aggregate stats."""
    wins = 0
    losses = 0
    draws = 0
    rounds_list = []

    for i in range(num_games):
        game_seed = seed + i * 100_000 if seed is not None else None
        result = play_fn(game_seed)

        w = result["winner_team"]
        r = result["rounds_played"]
        rounds_list.append(r)

        if w == 0:
            wins += 1
            tag = "WIN"
        elif w == 1:
            losses += 1
            tag = "LOSS"
        else:
            draws += 1
            tag = "DRAW"

        if verbose:
            lvl = result["final_levels"]
            print(
                f"  Game {i + 1:4d}: {tag:4s} | "
                f"{r:3d} rounds | levels: {lvl[0]:2d} vs {lvl[1]:2d}"
            )

        played = i + 1
        decided = wins + losses
        if log_interval > 0 and played % log_interval == 0 and decided > 0:
            print(f"  [{played}/{num_games}] game_win_rate={wins / decided:.1%} ({wins}W/{losses}L/{draws}D)")

    decided = wins + losses
    win_rate = wins / decided if decided > 0 else float("nan")

    return {
        "game_win_rate": win_rate,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "num_games": num_games,
        "avg_rounds": np.mean(rounds_list),
        "min_rounds": min(rounds_list),
        "max_rounds": max(rounds_list),
    }


def evaluate_complete_games_parallel(
    spec_a: str,
    spec_b: str,
    device: str,
    max_rounds: int,
    num_games: int = 100,
    seed: int | None = None,
    num_workers: int = 4,
) -> dict:
    """Run multiple complete games in parallel and aggregate stats."""
    game_seeds = [
        seed + i * 100_000 if seed is not None else None
        for i in range(num_games)
    ]

    chunks: list[list[int | None]] = [[] for _ in range(num_workers)]
    for i, s in enumerate(game_seeds):
        chunks[i % num_workers].append(s)

    ctx = mp.get_context("spawn")
    with ctx.Pool(num_workers) as pool:
        results = pool.starmap(
            _eval_worker,
            [
                (chunk, spec_a, spec_b, device, max_rounds)
                for chunk in chunks if chunk
            ],
        )

    wins = sum(r["wins"] for r in results)
    losses = sum(r["losses"] for r in results)
    draws = sum(r["draws"] for r in results)
    rounds_list = []
    for r in results:
        rounds_list.extend(r["rounds_list"])

    decided = wins + losses
    win_rate = wins / decided if decided > 0 else float("nan")

    return {
        "game_win_rate": win_rate,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "num_games": num_games,
        "avg_rounds": np.mean(rounds_list),
        "min_rounds": min(rounds_list),
        "max_rounds": max(rounds_list),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="DanZero complete game evaluation (multi-round with level progression)"
    )
    parser.add_argument("--model", type=str, required=True,
                        help="Agent A: checkpoint path or spec")
    parser.add_argument("--model-b", type=str, default="random",
                        help="Agent B: checkpoint path or spec (default: random)")
    parser.add_argument("--games", type=int, default=100, help="Number of complete games")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-rounds", type=int, default=200,
                        help="Max rounds per game (safety limit)")
    parser.add_argument("--num-workers", type=int, default=1,
                        help="Parallel workers (default: 1 = serial)")
    parser.add_argument("--verbose", action="store_true", help="Print per-game results")
    parser.add_argument("--log-interval", type=int, default=100,
                        help="Print progress every N games (0=off)")
    args = parser.parse_args()

    use_parallel = args.num_workers > 1
    workers_info = f" | Workers: {args.num_workers}" if use_parallel else ""
    print(f"Complete Game Evaluation: {args.model} vs {args.model_b}")
    print(f"  Games: {args.games} | Device: {args.device} | Max rounds: {args.max_rounds}{workers_info}")
    print()

    t0 = time.time()

    if use_parallel:
        if args.verbose:
            print("  (--verbose disabled in parallel mode)")
            print()
        results = evaluate_complete_games_parallel(
            spec_a=args.model,
            spec_b=args.model_b,
            device=args.device,
            max_rounds=args.max_rounds,
            num_games=args.games,
            seed=args.seed,
            num_workers=args.num_workers,
        )
    else:
        agent_a = create_agent(args.model, args.device)
        agent_b = create_agent(args.model_b, args.device)

        import copy
        agents_dict = {0: agent_a, 1: agent_b, 2: copy.copy(agent_a), 3: copy.copy(agent_b)}
        play_fn = lambda seed, a=agents_dict: play_complete_game_agents(
            a, seed=seed, max_rounds=args.max_rounds,
        )
        results = evaluate_complete_games(
            play_fn, num_games=args.games, seed=args.seed, verbose=args.verbose,
            log_interval=args.log_interval,
        )

    elapsed = time.time() - t0

    decided = results["wins"] + results["losses"]
    print()
    draws_note = f", {results['draws']} draws excluded" if results["draws"] > 0 else ""
    print(f"  Game win rate: {results['game_win_rate']:.1%} "
          f"({results['wins']}/{decided}{draws_note})")
    print(f"  Avg rounds/game: {results['avg_rounds']:.1f} "
          f"(min: {results['min_rounds']}, max: {results['max_rounds']})")
    print(f"  Time: {elapsed:.1f}s ({elapsed / args.games:.2f}s/game)")


if __name__ == "__main__":
    main()
