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
| Buy floor | Star buys never pay below 10x, Tower below 40x: a bought bonus under the floor is re-simulated (task 11) | `game_config.py` `buy_floor`, `game_override.py` `check_repeat` |
| Reels | BR0 base, FR0 bonus (no wild), WCAP max-win forcing (H1-heavy) | `reels\*.csv` |

### Optimizer targets (`game_optimization.py`)

RTP shares are fractions of mode cost. Each mode sums to 0.965.

| Mode | Cost | Wincap RTP | Bonus RTP | Bonus 1 in | Base-game RTP | Base hit 1 in |
|---|---|---|---|---|---|---|
| base | 1 | 0.010 | 0.324 | 400 | 0.631 | 4.0 |
| omen | 1.25 | 0.008 | 0.557 | 150 | 0.400 | 5.0 |
| prophecy | 2 | 0.006 | 0.559 | 80 | 0.400 | 3.0 |
| star | 100 | 0.005 | 0.960 | 1 | — | — |
| tower | 400 | 0.0004 | 0.9646 | 1 | — | — |

Max-win odds = wincap RTP × cost / 77,777 (base 0.010 → 1 in 7.8M).

Scaling: spin modes lift base wins 1–3x (4.0) and 3–6x (2.0), lift bonus 500–1,000x and 1,000–5,000x (`MID_WIN_LIFT`: base 4.0 / 15.0, omen and prophecy 2.0 / 4.0) and damp bonus 5,000–20,000x (0.8). Buy modes damp 5,000–77,776x (0.5); star also damps 10–20x (0.15) and 20–50x (0.5) and lifts 50–200x (4.0); tower damps 20–50x (0.9). `min_m2m`: spin modes 1.1, star 1.0, tower 4 (`BUY_SHAPES`).

Keep the base-game average win (base-game RTP × hit 1-in-N × mode cost, in base bets) at 2.3 or more (base 2.52, omen 2.5, prophecy 2.4): lower targets sit below the raw median and the optimizer fails with "create_ancestors failed to converge".

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

### Engine non-critical limits (math-verification page, 2026-10-28)

One limit set for every game. `scripts\math_stats.py` checks them and counts failure classes.

| Check | Limit | Unit |
|---|---|---|
| Std dev (any mode) | 60 | std ÷ cost (Engine does not say; PROJECT.md §11 Q15) |
| CVaR per-stake / absolute | 700 / 50,000 | mean of the top 0.1%, ÷ cost / raw |
| P(≥5k / 10k / 25k / 50k / 100k ×) | 0.05 / 0.01 / 0.005 / 0.001 / 0.0005 | raw, not scaled by cost |
| ETL >40× cost, ETL >10,000×, sum | 0.9 / 0.8 / 1.5 | RTP share ÷ cost |
| ETL absolute sum | 10,000 | not ÷ cost |

The 6 failure classes are max payout, cost multiplier, volatility, CVaR, ETL and tail probability. **0 failed classes = $50M exposure / $500k bet cost**; 1 = $25M / $500k; 2 = $15M / $250k; 3 = $10M / $100k. The old SDK "3-star" set in `rgs_verification.py` (run by `run.py` format checks) is obsolete. Its `etl40b` warning on prophecy (1.004, not ÷ cost) is not an Engine failure: ÷ cost it is 0.502.

## Results (production: 100k sims in every mode, 2026-10-28, task 11)

| Mode | RTP | Hit rate | Win > cost | Bonus 1 in | Max win 1 in | p90 / p99 / p99.9 (x) | Min win | Std ÷ cost | CVaR ÷ cost | ETL40 ÷ cost |
|---|---|---|---|---|---|---|---|---|---|---|
| base | 0.96500 | 25.3% | 25.3% | 400 | 7.8M | 1.2 / 14.5 / 137 | 0 | 29.4 | 180 | 0.530 |
| omen | 0.96500 | 20.7% | 1.6% | 150 | 7.8M | 1.2 / 29.3 / 136 | 0 | 24.1 | 150 | 0.643 |
| prophecy | 0.96500 | 34.6% | 2.7% | 80 | 6.5M | 1.2 / 56.1 / 161 | 0 | 16.8 | 113 | 0.502 |
| star | 0.96500 | 100% | 35.1% (median 43x) | 1 | 155,554 | 261 / 341 / 419 | 10x | 2.2 | 12.4 | 0.005 |
| tower | 0.96500 | 100% | 34.9% (median 172x) | 1 | 486,106 | 935 / 1,667 / 2,383 | 40x | 1.0 | 7.5 | 0.000 |

Engine failed classes: **0**. Books match lookups in every mode. Raw std: star 219, tower 398 (Q15).

Mid wins, 1 in N spins (or buys):

| Mode | ≥100x | ≥500x | ≥1,000x |
|---|---|---|---|
| base | 399 | 79,874 | 139,383 |
| omen | 245 | 58,567 | 129,964 |
| prophecy | 170 | 37,234 | 81,354 |
| star | 3 | 1,983 | 6,103 |
| tower | 1 | 3 | 12 |

Sessions (`--sessions`: 100 base bets, bet = mode cost, 20,000 sessions):

| Mode | Median spins | P(survive 200) | Dead run in 200 (median / p90) |
|---|---|---|---|
| base | 317 | 66.3% | 14 / 20 |
| omen | 223 | 53.2% | 16 / 24 |
| prophecy | 138 | 40.1% | 9 / 14 |

Book sizes (bytes ÷ 10⁶ = MB): base 46.7 MB, omen 73.1 MB, prophecy 100.1 MB, star 287.5 MB, tower 352.7 MB (860 MB total). The limit is 4.2 GB per file.

### Task 11: before → after (targets from instructions/11)

| Metric | Before (2026-09-19) | After (2026-10-28) | Target | Met |
|---|---|---|---|---|
| RTP every mode | 96.50% | 96.50% | 96.40–96.60% | yes |
| Max win odds (base / omen / prophecy) | 1/19.4M / 1/15.6M / 1/9.7M | 1/7.8M / 1/7.8M / 1/6.5M | better than 1/10M | yes |
| base P(≥1000x) | 1/2.28M | 1/139k | ~1/150k–300k | yes (slightly more often) |
| base P(≥100x) | 1/421 | 1/399 | ~1/1,500 | already more often; the target was misread from p99.9 |
| prophecy natural bonus avg | ~54x (1 in 60) | ~89x (1 in 80) | near a Star buy (96.5x) | yes (owner decision 2026-10-28) |
| star min / P(<20x) | 1.2x / 12.5% | 10x / 4.8% | ≥10x / ≤5% | yes |
| tower min | 1.2x | 40x | ≥40x | yes |
| sims | 100k / 50k buys | 100k every mode | 100k | yes |
| Engine failed classes | 0 | 0 | 0 | yes (std ÷ cost, Q15) |
| base hit / median session | 25.3% / 338 | 25.3% / 317 | ≥23% / ≥300 | yes |

### Known gaps

1. **Ante modes pay above cost less often.** Omen 1.6% and prophecy 2.7% of spins pay more than their cost: their base hits (≥1.2x) are often below the 1.25x / 2x price. They trade base value for bonus frequency. This is stated in the rules screen and the mode dialogs (owner decision 2026-09-19: retune + honest wording).
2. **Prophecy sessions are shorter.** Median 138 spins (was 184): more RTP sits in the rarer, bigger bonus (owner decision 2026-10-28). No session target applies to prophecy.
3. **Star median fell 56x → 43x.** The floor removes results under 10x, and the optimizer then spreads weight over the 20–50x range. Star buys paying more than their price fell from 43.6% to 35.1%. A retune that lifted 50–200x harder raised P(<20x) to 7.1%, so it was reverted. Star's low end is now safe; its middle is weaker.
4. **Tower is swingier than Star.** 34.9% of Tower buys return more than 400x (median 172x). Accepted: Tower is the high-volatility choice, and the dialog says a bonus can pay less than its price.
5. **Sample size.** 100k sims cannot resolve 1-in-10M events. Max-win odds come from optimizer weights on forced max-win books.
6. **Optimizer runs vary.** The same settings gave star P(<20x) 3.9% and 4.8% in two runs. Recheck `math_stats.py` after every optimizer run.

## Verify

```powershell
math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief --sessions
```

Pass = every mode RTP 0.9635–0.9665, `fails {}`, `match True`, `engine failed classes 0`; base hit ≥23% and median session ≥300 spins (PROJECT.md §6 M5b); star min ≥10x, tower min ≥40x.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://github.com/StakeEngine/math-sdk/blob/main/utils/rgs_verification.py | old SDK 3-star limits (obsolete) | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/math-verification | Engine non-critical limits, failure classes, penalty schedule, 1-in-10M max win, 100k–1M sims | 2026-10-28 |
| https://github.com/StakeEngine/math-sdk/blob/main/docs/math_docs/optimization_section/optimization_algorithm.md | optimizer conditions | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | upload format | 2026-09-19 |
