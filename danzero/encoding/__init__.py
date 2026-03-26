"""Encoding module with versioned state/action encoders."""

from __future__ import annotations

from types import SimpleNamespace


def get_encoder(version: str = "v0") -> SimpleNamespace:
    """Get encoder module for the given representation version.

    Returns a namespace with: DIM_STATE, DIM_ACTION, DIM_INPUT,
    encode_observation, encode_batch.
    """
    if version == "v0":
        from .encoder import (
            DIM_ACTION,
            DIM_INPUT,
            DIM_STATE,
            encode_batch,
            encode_observation,
        )
    elif version == "v1t":
        from .encoder_v1 import (
            DIM_ACTION,
            DIM_INPUT_V1T as DIM_INPUT,
            DIM_STATE_V1T as DIM_STATE,
            encode_batch_v1t as encode_batch,
            encode_observation_v1t as encode_observation,
        )
    else:
        raise ValueError(f"Unknown representation version: {version}")
    return SimpleNamespace(
        DIM_STATE=DIM_STATE,
        DIM_ACTION=DIM_ACTION,
        DIM_INPUT=DIM_INPUT,
        encode_observation=encode_observation,
        encode_batch=encode_batch,
    )
