"""Hyperparameter configuration for DanZero V3 training (cycle-based, deterministic pool diversity).

Key design: replay buffer diversity k is a direct hyperparameter, not a derived value.
Each cycle = concurrent (actors collect N/k samples || learner trains S steps) + barrier + sync.
Hardware speed only affects wall-clock time, not training behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class DanZeroV3Config:
    """V3 training config: cycle-based with deterministic replay buffer diversity.

    Core hyperparameters (N, k, S) fully determine training behavior:
    - N (replay_buffer_size): replay buffer size in samples
    - k (replay_buffer_diversity): number of historical weight versions in the buffer
    - S (train_steps_per_cycle): gradient steps per sync cycle
    - budget_per_cycle = N // k (derived): samples collected per cycle
    """

    # Network architecture
    representation: str = "v0"           # encoding version: v0 (567-dim) or v1t (964-dim)
    input_dim: int = 567
    network_hidden_sizes: tuple[int, ...] = (512, 1024, 512, 1024, 512)

    # Optimization
    lr: float = 1e-4
    optimizer: str = "adam"         # adam, adamw, rmsprop
    rmsprop_eps: float = 1e-5
    dropout: float = 0.0              # dropout rate between hidden layers (0 = off)
    onnx_mode: str = "none"          # actor inference: none, fp32, int8
    ring_size: int = 1               # games per actor (1 = no interleaving)

    # Dual Q-network (teammate cooperation reward)
    dual_q: bool = False             # enable dual Q-network (Q_s + Q_t)
    shared_q: bool = False           # True=shared backbone, False=decoupled
    teammate_loss_weight: float = 0.5  # c in dual loss: L = L_s + c*(1-d)*L_t

    # Dueling Q-network (V(s) + A(s,a) decomposition)
    dueling: bool = False            # enable Dueling DQN
    dueling_v_loss_weight: float = 1.0  # λ for auxiliary V loss
    state_dim: int = 0               # filled from encoder (0 = auto)
    action_dim: int = 0              # filled from encoder (0 = auto)

    # Distributional Q-network (C51-style multi-bin)
    distributional: bool = False     # mutually exclusive with dual_q
    dist_num_bins: int = 51          # number of value bins
    dist_v_min: float = -3.5         # minimum bin center
    dist_v_max: float = 3.5          # maximum bin center
    dist_loss: str = "ce"            # loss type: ce, two_hot_ce, hl_gauss, mse_ent
    dist_hl_sigma: float = 0.75      # HL-Gauss sigma as multiple of bin width
    dist_entropy_weight: float = 0.01  # entropy weight λ for mse_ent loss

    # TD bootstrapping (convex MC/TD target)
    td_bootstrap: bool = False       # enable TD targets (mutually exclusive with dual_q)
    td_beta: float = 0.95            # MC weight: β^(T-1-t)*R + (1-β^(T-1-t))*maxQ  (1=DMC, <1=more TD)

    # V3 core: directly controllable hyperparameters
    replay_buffer_size: int = 524_288     # N: replay buffer size in samples
    replay_buffer_diversity: int = 2      # k: weight versions in buffer
    train_steps_per_cycle: int = 16       # S: gradient steps per cycle
    batch_size: int = 32768
    exploration: str = "eps_greedy"  # eps_greedy, boltzmann
    eps_greedy: float = 0.02
    eps_greedy_schedule: str = "cosine"   # constant, linear, cosine
    eps_min: float = 0.0
    eps_top_k: int = 0                    # top-k ε-greedy: 0=standard, >0=explore among top-k
    boltzmann_temp: float = 0.1           # Boltzmann sampling temperature (max)
    boltzmann_temp_min: float = 0.01      # min temperature for schedule
    boltzmann_schedule: str = "cosine"    # constant, linear, cosine

    # Logging
    steps_per_log: int = 16

    # Actors
    num_actors: int = 30

    # Checkpointing (freq in cycles)
    ckpt_cycles: int = 20             # save every N cycles (0 = final only)
    ckpt_dir: str = "checkpoints"
    max_recent_ckpts: int = 10        # keep last X ckpts (0 = keep all, no cleanup)
    max_best_ckpts: int = 10          # keep top Y by eval win rate (0 = keep all evaluated)

    # Evaluation (async, polls checkpoints)
    eval_num_games: int = 500
    eval_cycles: int = 20             # eval every N cycles (0 = every ckpt)
    first_eval_cycle: int = 20        # first eval at this cycle (0 = eval_cycles)
    eval_baselines: tuple[str, ...] = ()
    reg_eval_cycles: int = 0             # regression eval every N cycles: all bots + random (0=off)
    shadow_eval_cycles: tuple[int, ...] = ()  # relative offsets, e.g. (1000,) = vs self 1000 cycles ago
    eval_vs_model: str = ""              # path to opponent ONNX model for eval (empty = disabled)

    # Device
    device: str = "cuda"

    def __post_init__(self) -> None:
        if self.exploration not in ("eps_greedy", "boltzmann"):
            raise ValueError(
                f"exploration must be eps_greedy or boltzmann, got '{self.exploration}'"
            )
        if self.distributional and self.dual_q:
            raise ValueError(
                "distributional and dual_q are mutually exclusive"
            )
        if self.td_bootstrap and self.dual_q:
            raise ValueError(
                "td_bootstrap is mutually exclusive with dual_q"
            )
        if self.dist_loss not in ("ce", "two_hot_ce", "hl_gauss", "mse_ent"):
            raise ValueError(
                f"dist_loss must be one of ce/two_hot_ce/hl_gauss/mse_ent, got '{self.dist_loss}'"
            )
        if self.eval_cycles > 0 and self.ckpt_cycles > 0:
            if self.eval_cycles % self.ckpt_cycles != 0:
                raise ValueError(
                    f"eval_cycles ({self.eval_cycles}) must be a multiple of "
                    f"ckpt_cycles ({self.ckpt_cycles})"
                )
        if self.first_eval_cycle > 0 and self.ckpt_cycles > 0:
            if self.first_eval_cycle % self.ckpt_cycles != 0:
                raise ValueError(
                    f"first_eval_cycle ({self.first_eval_cycle}) must be a multiple of "
                    f"ckpt_cycles ({self.ckpt_cycles})"
                )
        if self.reg_eval_cycles > 0:
            if self.eval_cycles > 0 and self.reg_eval_cycles % self.eval_cycles != 0:
                raise ValueError(
                    f"reg_eval_cycles ({self.reg_eval_cycles}) must be a multiple of "
                    f"eval_cycles ({self.eval_cycles})"
                )
            if self.ckpt_cycles > 0 and self.reg_eval_cycles % self.ckpt_cycles != 0:
                raise ValueError(
                    f"reg_eval_cycles ({self.reg_eval_cycles}) must be a multiple of "
                    f"ckpt_cycles ({self.ckpt_cycles})"
                )
        if self.shadow_eval_cycles and self.ckpt_cycles > 0:
            for offset in self.shadow_eval_cycles:
                if offset % self.ckpt_cycles != 0:
                    raise ValueError(
                        f"shadow_eval_cycles offset {offset} must be a multiple of "
                        f"ckpt_cycles ({self.ckpt_cycles})"
                    )

    @property
    def budget_per_cycle(self) -> int:
        """Derived: samples to collect per cycle = N // k."""
        return self.replay_buffer_size // self.replay_buffer_diversity

    def to_dict(self) -> dict:
        """Serialize config to a plain dict (safe for torch.save)."""
        d = asdict(self)
        d["network_hidden_sizes"] = list(d["network_hidden_sizes"])
        d["eval_baselines"] = list(d["eval_baselines"])
        d["shadow_eval_cycles"] = list(d["shadow_eval_cycles"])
        return d

    @classmethod
    def from_dict(cls, d: dict) -> DanZeroV3Config:
        """Reconstruct config from a dict (e.g. loaded from checkpoint)."""
        d = dict(d)
        if "network_hidden_sizes" in d:
            d["network_hidden_sizes"] = tuple(d["network_hidden_sizes"])
        if "eval_baselines" in d:
            d["eval_baselines"] = tuple(d["eval_baselines"])
        if "shadow_eval_cycles" in d:
            d["shadow_eval_cycles"] = tuple(d["shadow_eval_cycles"])
        # Drop unknown keys (forward compatibility)
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        d = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**d)
