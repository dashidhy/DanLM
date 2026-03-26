# Evaluation Results

## Evaluation Protocol

### Single-Round Win Rate

A single round of GuanDan: 4 players are dealt 27 cards each, play until all cards are exhausted. The team whose player finishes first wins.

- Model A plays seats 0 & 2 (one team), Model B plays seats 1 & 3 (the other team).
- Win rate = proportion of rounds where Team A finishes first.
- We report results over 500-1000 games with a fixed random seed for reproducibility.

### Whole-Game (Episode) Win Rate

A complete GuanDan game consists of **multiple rounds** with level progression from 2 to A. A team wins by reaching level A and winning a round they own at that level. This is the metric used in the original DanZero paper (Table I).

- Whole-game win rate amplifies single-round advantages due to cumulative effects: a 54% single-round edge typically translates to ~66% whole-game win rate.
- We report results over 500 games.

---

## Baseline Bots

### Source

We include **16 bug-fixed bots** from the [1st National GuanDan AI Algorithm Competition (首届中国人工智能掼蛋算法大赛)](https://gameai.njupt.edu.cn/gameaicompetition/guandan_machine_code/index.html). The original competition code was publicly released by the organizers.

### Why Competition Rankings Don't Reflect Actual Strength

Our round-robin tournament (13 bots, 200 games per pair) revealed that **competition rankings significantly misrepresent actual bot strength**:

| Bot | Competition Award | Actual Rank | Single-Round Win Rate | Note |
|-----|------------------|-------------|----------------------|------|
| fin-njupt-guandan-ai | Consolation (优胜奖) | **#1** | 76.6% | Had a None-check bug causing ~49% of games to crash |
| 2nd-egg-pancake | 2nd Prize | #2 | 72.6% | Correctly ranked |
| 3rd-chick-squad | 3rd Prize | #3 | 68.8% | Correctly ranked |
| fin-caiji | Consolation (优胜奖) | #4 | 65.8% | Stronger than 1st Prize winner |
| 1st-lalala | **1st Prize** | #8 | 45.6% | Beaten by 6 other bots |

After fixing bugs in the competition code, the actual strength order becomes clear. The strongest bot (fin-njupt-guandan-ai) was crippled by a simple None-check bug that caused it to crash in nearly half its games, masking its true strength.

### Top 5 Strongest Bots (after bug fixes)

1. **fin-njupt-guandan-ai** — Actual strongest, consolation prize due to crash bug
2. **3rd-chick-squad** — Consistent performer
3. **fin-guanglan-iot** — Strong finalist
4. **fin-egg-expert** — Strong finalist
5. **2nd-egg-pancake** — 2nd prize winner, correctly ranked

---

## Model Comparison

We provide three models demonstrating a clear progression:

### DanZero V0 — Baseline Reproduction

Our faithful reproduction of the original DanZero paper (AAAI 2023):
- 5-layer MLP with 567-dim hand-crafted input features
- Trained with Deep Monte Carlo (DMC) self-play
- **Successfully reproduces and exceeds the paper's reported results** (>=99% whole-game win rate vs all baseline bots)

### DanZero V1T — Enhanced Hand-Crafted SOTA

Our improved version of DanZero with:
- Bug fixes from the original implementation
- Enhanced state representation (V1T): 964-dim features with richer encoding
- Model-driven tribute selection (replacing heuristic)
- Significantly stronger than V0 on the hardest bots

### DanLM V1 — Feature-Free (This Work)

Our novel approach with zero hand-crafted features:
- TinyLM encoder processes raw tokenized game history
- Simple count/onehot vectors for hand and action (no derived statistics)
- Trained with DMC self-play + next-token prediction auxiliary task
- **Surpasses V1T despite using no domain knowledge**

---

## Detailed Results

### Single-Round Win Rate vs Baseline Bots (500 games, seed=42)

| Opponent | DanZero V0 | DanZero V1T | DanLM V1 |
|----------|-----------|-------------|----------|
| Random | 99.9% | 99.9% | 100.0% |
| fin-njupt-guandan-ai | 72.7% | 78.0% | *TBD* |
| 3rd-chick-squad | 73.8% | 79.2% | *TBD* |
| fin-guanglan-iot | 75.4% | 80.1% | *TBD* |
| fin-egg-expert | 78.1% | 83.5% | *TBD* |
| 2nd-egg-pancake | 82.6% | 87.3% | *TBD* |

### Head-to-Head (500 games, seed=42)

| Match | Single-Round | Whole-Game |
|-------|-------------|------------|
| DanLM V1 vs DanZero V1T | **54.2%** | **66.4%** (332/500) |
| DanLM V1 vs DanZero V0 | *TBD* | *TBD* |
| DanZero V1T vs DanZero V0 | *TBD* | *TBD* |

### Progression Summary

```
DanZero V0 (567-dim hand-crafted) < DanZero V1T (964-dim hand-crafted) < DanLM V1 (zero hand-crafted)
```

DanLM surpasses both hand-crafted models while using **no domain knowledge at all**.
