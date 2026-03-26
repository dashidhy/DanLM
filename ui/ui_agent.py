"""UI Agent — manages AI agents for the web game UI.

Wraps the EvalAgent system to provide a unified interface for GameSession.
Supports multiple agent types (V0, V1T, Transformer) with shared model loading.
"""

from __future__ import annotations

import dataclasses
import os

import numpy as np
import torch

from danzero.engine.game import GuanDanRound, Observation
from danzero.engine.tribute import TributeRecord
from danzero.eval.agents import EvalAgent, create_agent_from_model

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENT_REGISTRY = {
    "danzero_v0": {
        "name": "DanZero V0",
        "description": "MLP Q-network, heuristic tribute",
        "path": os.path.join(
            _PROJECT_ROOT, "ckpts", "DanZero_v3",
            "v3_default_param_cycle000007000_int8.onnx",
        ),
        "kind": "mlp",
        "rep": "v0",
    },
    "danzero_v1t": {
        "name": "DanZero V1T",
        "description": "MLP Q-network, model-driven tribute",
        "path": os.path.join(
            _PROJECT_ROOT, "ckpts", "DanZero_v3_rep_v1t",
            "v3_rep_v1t_best_eval_001_int8.onnx",
        ),
        "kind": "v1t",
        "rep": "v1t",
    },
    "danlm_v1": {
        "name": "DanLM V1",
        "description": "TinyLM Q-network, model-driven tribute",
        "path": os.path.join(
            _PROJECT_ROOT, "ckpts", "DanLM_v1",
            "dansformer_v1_best_eval.pt",
        ),
        "kind": "transformer",
        "rep": "transformer",
    },
}


def _load_model(config: dict) -> tuple:
    """Load model from config, return (model, rep, extra_kwargs).

    Returns model object, representation string, and extra kwargs for
    create_agent_from_model (e.g. encode_batch_fn for v0).
    """
    kind = config["kind"]
    path = config["path"]
    rep = config["rep"]

    if kind == "mlp":
        from danzero.encoding import get_encoder
        from danzero.eval.evaluator import OnnxEvalModel

        if path.endswith(".onnx"):
            model = OnnxEvalModel(path)
            encode_fn = get_encoder(rep).encode_batch
            return model, rep, {"encode_batch_fn": encode_fn}

        from danzero.model.network import QNetwork

        ckpt = torch.load(path, weights_only=False, map_location="cpu")
        cfg = ckpt.get("config", {})
        hidden_sizes = tuple(
            cfg.get("hidden_sizes")
            or cfg.get("network_hidden_sizes")
            or (512, 1024, 512, 1024, 512)
        )
        model = QNetwork(
            input_dim=cfg.get("input_dim", 567),
            hidden_sizes=hidden_sizes,
            dropout=cfg.get("dropout", 0.0),
        )
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()
        encode_fn = get_encoder(rep).encode_batch
        return model, rep, {"encode_batch_fn": encode_fn}

    if kind == "v1t":
        if path.endswith(".onnx"):
            from danzero.eval.evaluator import OnnxEvalModel

            model = OnnxEvalModel(path)
            return model, rep, {}

        from danzero.model.network import QNetwork

        ckpt = torch.load(path, weights_only=False, map_location="cpu")
        cfg = ckpt.get("config", {})
        hidden_sizes = tuple(
            cfg.get("hidden_sizes")
            or cfg.get("network_hidden_sizes")
            or (512, 1024, 512, 1024, 512)
        )
        model = QNetwork(
            input_dim=cfg.get("input_dim", 964),
            hidden_sizes=hidden_sizes,
            dropout=cfg.get("dropout", 0.0),
        )
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()
        return model, rep, {}

    if kind == "transformer":
        from danzero.model.transformer import TransformerConfig, TransformerQNetwork

        ckpt = torch.load(path, weights_only=False, map_location="cpu")
        raw_cfg = ckpt.get("model_config") or ckpt.get("config", {})
        valid = {f.name for f in dataclasses.fields(TransformerConfig)}
        tcfg = TransformerConfig(**{k: v for k, v in raw_cfg.items() if k in valid})
        model = TransformerQNetwork(tcfg)
        model.load_state_dict(ckpt.get("model_state_dict") or ckpt["model"])
        model.eval()
        return model, rep, {"max_seq_len": tcfg.max_seq_len}

    raise ValueError(f"Unknown agent kind: {kind}")


class UIAgent:
    """Manages 4 EvalAgent instances (one per seat) sharing a single model.

    Provides a unified interface for GameSession to delegate all AI decisions
    (tribute give/back, play, hints) to the appropriate per-seat agent.
    """

    def __init__(self, agent_key: str = "danzero_v1t") -> None:
        if agent_key not in AGENT_REGISTRY:
            raise ValueError(
                f"Unknown agent: {agent_key}. "
                f"Available: {list(AGENT_REGISTRY.keys())}"
            )
        self.agent_key = agent_key
        config = AGENT_REGISTRY[agent_key]
        self.agent_name = config["name"]

        # Load model once, create 4 agents sharing the same model
        model, rep, extra_kwargs = _load_model(config)
        self._agents: list[EvalAgent] = [
            create_agent_from_model(model, rep, **extra_kwargs)
            for _ in range(4)
        ]

    def reset_round(self, level: int) -> None:
        """Reset all agents for a new round."""
        for seat in range(4):
            self._agents[seat].reset(seat, level)

    # -- Tribute delegation --

    def select_tribute_give(
        self,
        seat: int,
        hand: np.ndarray,
        legal_cards: list[int],
        is_double: bool,
        receiver: int | None,
    ) -> int:
        return self._agents[seat].select_tribute_give(
            hand, legal_cards, is_double, receiver,
        )

    def select_tribute_back(
        self,
        seat: int,
        hand: np.ndarray,
        legal_cards: list[int],
        back_to: int,
        give_records: list[TributeRecord],
    ) -> int:
        return self._agents[seat].select_tribute_back(
            hand, legal_cards, back_to, give_records,
        )

    def notify_tribute(
        self,
        records: list[TributeRecord],
        anti_tribute_abs: np.ndarray | None = None,
    ) -> None:
        for a in self._agents:
            a.notify_tribute(records, anti_tribute_abs)

    # -- Play delegation --

    def select_play(self, obs: Observation, round_obj: GuanDanRound) -> int:
        return self._agents[obs.player].select_play(obs, round_obj)

    def observe_action(
        self, player: int, play: np.ndarray, new_trick_after: bool,
    ) -> None:
        for a in self._agents:
            a.observe_action(player, play, new_trick_after)

    # -- Hint support --

    def get_q_values(self, obs: Observation, round_obj: GuanDanRound) -> np.ndarray:
        return self._agents[obs.player].get_q_values(obs, round_obj)

    def get_top_k(
        self, obs: Observation, round_obj: GuanDanRound, k: int = 3,
    ) -> list[tuple[int, float]]:
        q = self.get_q_values(obs, round_obj)
        k = min(k, len(q))
        top_idx = np.argsort(q)[::-1][:k]
        return [(int(i), float(q[i])) for i in top_idx]

    # -- Registry --

    @staticmethod
    def list_agents() -> list[dict]:
        """Return list of available agents for frontend selection."""
        return [
            {"key": k, "name": v["name"], "description": v["description"]}
            for k, v in AGENT_REGISTRY.items()
        ]
