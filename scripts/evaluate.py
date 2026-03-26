#!/usr/bin/env python3
"""DanZero single-round evaluation CLI.

All evaluation uses the unified pluggable eval engine (play_round + evaluate).
Both --model and --model-b accept any agent spec or bare checkpoint path.

Agent specs:
    random                          Random agent
    <path>.pt                       Auto-detect from checkpoint (mlp/v1t/transformer)
    <path>.onnx                     Auto-detect MLP ONNX
    mlp:<path>                      MLP Q-network
    v1t:<path>                      MLP with model-driven tribute
    transformer:<path>              Transformer Q-network
    bot:<name>                      Baseline competition bot

Examples:
    # MLP vs random (default opponent)
    uv run python scripts/evaluate.py --model ckpts/DanZero_v3/v3_default_param_cycle000007000.pt

    # Transformer vs MLP v1t ONNX
    uv run python scripts/evaluate.py \
        --model ckpts/Dansformer_v1/dansformer_v1_best_eval.pt \
        --model-b ckpts/DanZero_v3_rep_v1t/v3_rep_v1t_best_eval_001_int8.onnx

    # MLP vs baseline bot
    uv run python scripts/evaluate.py \
        --model ckpts/DanZero_v3/v3_default_param_cycle000007000.pt \
        --model-b bot:fin-njupt-guandan-ai
"""

from __future__ import annotations

import argparse
import time

from danzero.eval.agents import create_agent
from danzero.eval.evaluator import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate DanZero agent (single-round)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--model", type=str, required=True,
                        help="Agent A: checkpoint path or spec")
    parser.add_argument("--model-b", type=str, default="random",
                        help="Agent B: checkpoint path or spec (default: random)")
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed (default: None for non-deterministic)")
    parser.add_argument("--log-interval", type=int, default=100,
                        help="Print progress every N games (0=off)")
    args = parser.parse_args()

    agent_a = create_agent(args.model, args.device)
    agent_b = create_agent(args.model_b, args.device)

    print(f"Evaluating {args.model} vs {args.model_b} ({args.games} games)...")
    t0 = time.time()
    results = evaluate(agent_a, agent_b, num_games=args.games, seed=args.seed,
                       log_interval=args.log_interval)
    elapsed = time.time() - t0
    print(f"  Agent A win rate: {results['win_rate_a']:.1%}")
    print(f"  Avg reward A: {results['avg_reward_a']:.3f}, B: {results['avg_reward_b']:.3f}")
    print(f"  Time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
