# 07 — Math spec: Seventh Veil

## Purpose

Math targets per mode, the knobs that set them, and the latest measured results. Design intent: [06](06-game-design.md). Limits: [08](08-compliance.md).

## Prereq

[01-math-sdk.md](01-math-sdk.md) setup, including the optimizer.

## Steps

### Fixed rules (all modes)

| Rule | Value | Where |
|---|---|---|
| Board | 7x7, clusters ≥5, tumbles | `game_config.py` |
| RTP | 0.9650 (tolerance ±0.0015) | `game_config.py`, `game_optimization.py` |
| Max win | 77,777x (lookup payout `7777700`) | `game_config.py` `wincap` |
| Grid | mark → x2 → double per hit, cap x1024; cluster pay × sum of charged spots | `game_executables.py`, `game_calculations.py` |
| Bonus | 3 balls = Star 12 spins, 4 = Star 15, 5+ = Tower 15–18 spins; retrigger +5 | `game_config.py` `freespin_triggers` |
| Pre-charge | Star 5, Tower 12 random spots charged at x2 at bonus start | `game_config.py` `star_precharge_spots`, `tower_precharge_*` |
| Reels | BR0 base, FR0 bonus (no wild), WCAP max-win forcing (H1-heavy) | `reels\*.csv` |

### Optimizer targets (`game_optimization.py`)

RTP shares are fractions of mode cost. Each mode sums to 0.965.

| Mode | Cost | Wincap RTP | Bonus RTP | Bonus 1 in | Base-game RTP | Base hit 1 in |
|---|---|---|---|---|---|---|
| base | 1 | 0.004 | 0.330 | 400 | 0.631 | 4.0 |
| omen | 1.25 | 0.004 | 0.561 | 150 | 0.400 | 5.0 |
| prophecy | 2 | 0.004 | 0.450 | 60 | 0.511 | 3.0 |
| star | 100 | 0.005 | 0.960 | 1 | — | — |
| tower | 400 | 0.0004 | 0.9646 | 1 | — | — |

Scaling: spin modes lift base wins 1–3x (4.0) and 3–6x (2.0), damp base 20–1000x (0.5), damp bonus 150–1000x (0.7) and 5,000–20,000x (0.8). Buy modes damp 5,000–77,776x (0.5); star also damps 0–20x (0.3) and 20–50x (0.5) and lifts 50–200x (4.0); tower damps 20–50x (0.9). `min_m2m`: spin modes 1.1, star 1.0, tower 4 (`BUY_SHAPES`).

Keep the base-game average win (base-game RTP × hit 1-in-N × mode cost, in base bets) at 2.3 or more (base 2.52, omen 2.5, prophecy 3.07): lower targets sit below the raw median and the optimizer fails with "create_ancestors failed to converge".

### Why every base pay is ≥1.2x

With the SDK default `min_m2m=4`, the optimizer pins the base median to 0.16–0.32x, so 93% of base hits paid below the stake (2.2% of spins paid more than 1x). Scaling hints did not change this: the optimizer scores candidates on RTP only. The fix is in the paytable: the lowest pay is 1.2x, so every base hit beats the stake.

### Iteration 4 rebalance (playtime)

Before: base hit 14.2%, 62% of base RTP in a 1-in-350 bonus, 100-bet balance lasted a median 163 spins. After: RTP moved from the bonus into base hits (base-game RTP 0.360 → 0.631, hit 1 in 7.2 → 1 in 4.0, bonus 1 in 400). Omen got the same shift (0.300 → 0.400), which also lowered its `etl40b`. Star got 5 pre-charged spots, because the optimizer could not lift its median above the raw pool's (~40x).

Session check (`math_stats.py --sessions`: 100 base bets start, bet = mode cost, 20,000 sessions, cap 2,000 spins):

| Mode | Median spins | P(survive 200) | Longest dead run in 200 spins (median / p90) |
|---|---|---|---|
| base | 338 (was 163) | 68.5% (was 42.4%) | 14 / 20 (was 24 / 35) |
| omen | 218 | 52.5% | 16 / 24 |
| prophecy | 184 | 47.6% | 9 / 14 |

### 3-star volatility limits (from `math-sdk\utils\rgs_verification.py`)

`prob5k` ≤ 1%, `prob10k` ≤ 0.5%, `etl40b` ≤ 0.9, `etl10k` ≤ 0.8, `cvar` ≤ 800 (per cost), `rtp` ≤ 0.967. Units: base-bet multiples. They cap how much RTP sits in huge wins.

## Results (production: 100k sims spin modes, 50k buy modes, 2026-09-19)

| Mode | RTP | Hit rate | Win > cost | Bonus 1 in | Max win 1 in | p90 / p99 / p99.9 (x) | etl40b | 3-star |
|---|---|---|---|---|---|---|---|---|
| base | 0.96500 | 25.3% | 25.3% | 400 | 19.4M | 1.2 / 15.2 / 137 | 0.508 | pass |
| omen | 0.96500 | 20.7% | 1.8% | 150 | 15.6M | 1.2 / 25.2 / 156 | 0.789 | pass |
| prophecy | 0.96500 | 35.0% | 5.0% | 60 | 9.7M | 1.4 / 51.5 / 134 | 0.715 | pass |
| star | 0.96500 | 100% | 43.6% (median 56x) | 1 | 155,554 | 193 / 253 / 320 | 0.520 | pass |
| tower | 0.96500 | 100% | 23.3% (median 210x) | 1 | 486,106 | 1,037 / 1,749 / 2,589 | 0.259 | pass |

Book sizes: base 45 MB, omen 70 MB, prophecy 96 MB, star 136 MB, tower 165 MB (518 MB on disk).

Books match lookups in every mode. Event types seen: `reveal`, `winInfo`, `updateTumbleWin`, `tumbleBoard`, `updateGrid`, `bonusVariant`, `freeSpinTrigger`, `freeSpinRetrigger`, `updateFreeSpin`, `freeSpinEnd`, `setTotalWin`, `setWin`, `wincap`, `finalWin` — all in [03](03-contract.md).

### Known gaps

1. **Ante modes pay above cost less often.** Omen 1.8%, prophecy 5.0% of spins pay more than their cost: their base hits (≥1.2x) are often below the 1.25x / 2x price. They trade base value for bonus frequency. Stated in the rules screen and mode dialogs (owner decision 2026-09-19: retune + honest wording).
2. **Tower is swingier than Star.** Only 23.3% of Tower buys return more than 400x (median 210x). Accepted: Tower is the high-volatility choice; the dialog says a bonus can pay less than its price.
3. **Sample size.** 100k sims cannot resolve 1-in-10M events; max-win odds come from optimizer weights on forced max-win books. Scale up if Engine's upload limits allow (books grow ~linearly).

## Verify

```powershell
math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief --sessions
```

Pass = every mode RTP 0.9635–0.9665, `fails {}`, `match True`; base hit ≥23% and median session ≥300 spins (PROJECT.md §6 M5b).

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://github.com/StakeEngine/math-sdk/blob/main/utils/rgs_verification.py | 3-star volatility limits | 2026-09-19 |
| https://github.com/StakeEngine/math-sdk/blob/main/docs/math_docs/optimization_section/optimization_algorithm.md | optimizer conditions | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | upload format | 2026-09-19 |
