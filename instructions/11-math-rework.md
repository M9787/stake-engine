# 11 — Math rework (before submission; math freezes after approval)

**Goal:** Math that makes good stream clips and passes every Engine check:
- 500x–5,000x wins show up often enough to be seen on stream;
- the max win is reachable (better than 1 in 10M in every mode);
- buy modes never feel like a scam at the low end;
- every mode has 100k+ simulations.

**Why:**
- Math verification (https://studio.engine.io/docs/approval-guidelines/math-verification, read 2026-10-28):
  - "Maximum win should be realistically obtainable (typically more frequent than 1 in 10,000,000)";
  - "100,000–1,000,000 simulations";
  - "intermediate wins should exist between small payouts and the maximum win".
- Viral clips come from big multipliers and buy-bonus hits (trade press, see task 24).
- User decision 2026-10-28: tune for big mid wins.

**Depends on:** nothing. Do this early, because tasks 09 and 22 need the final numbers.

## Problems now (audit 2026-10-28)
| Mode | Problem |
|---|---|
| base | ≥500x is 1 in 848k spins; 1000x+ (below max) is 1 in 2.6M. Max win is 1 in 19.4M. |
| omen | Loses on 98.2% of spins. Max win is 1 in 15.6M. |
| prophecy | Natural bonus pays about 54x on average, less than a Star buy (96.5x). |
| star (100x) | 48% of buys return <50x; the lowest is 1.2x. |
| tower (400x) | 76.7% of buys return <400x; the lowest is 1.2x. |

## Targets
Fill the "Before" column from `stats_summary.json` before you change anything.

| Metric | Before | Target |
|---|---|---|
| RTP every mode | 96.50% | 96.40–96.60% (band 96.0–96.7) |
| Max win odds, every spin mode | base 1/19.4M | better than 1/10M (aim 1/5M–1/8M) |
| base P(≥1000x) | 1/2.6M | about 1/150k–1/300k |
| base P(≥100x) | p99.9=137x | about 1/1,500 |
| star min result | 1.2x | ≥10x (floor) |
| star P(<20x) | 12.5% | ≤5% |
| tower min result | 1.2x | ≥40x (floor) |
| sims | 100k / 50k buys | 100k every mode (buy modes can go to 200k) |
| Non-critical failed classes | ? | 0 (exposure $50M) |

## Steps
1. Read `game\math\seventh_veil\game_optimization.py` and `run.py`. Copy the current values into a "Before" table in `docs\07-math-spec.md`.
2. Max win: raise the wincap share in `game_optimization.py:16-18` (base ≥0.008, omen ≥0.0065, prophecy ≥0.006). Lower the bonus share by the same amount, so each tuple still sums to 0.965.
3. Mid wins: relax the damping in `game_optimization.py:88-90` (base 20–1000x ×0.5, bonus 150–1000x ×0.7, bonus 5k–20k ×0.8). Add a scaling rule that lifts 500x–5,000x. Make one change at a time.
4. Buy floor: add an optimizer condition, or a minimum in the scaling, that gives near-zero weight to results below the floor for star and tower.
   - If the optimizer cannot do this, add a math rule instead. Example: Tower starts with more charged spots, or a guaranteed charged spot per spin.
   - That is a **mechanic** change. Update `docs\06-game-design.md`. Modes stay the same (PROJECT.md §4 is frozen); only the inside of a feature changes.
5. Sims: set `run.py:27-28` (star, tower) to `int(1e5)`. Don't set `SV_SKIP_SIMS`.
6. Run the full pipeline (PROJECT.md §7):
   - `Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location`
   - `math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief --sessions`
   - `math-sdk\env\Scripts\python.exe scripts\gen_fe_config.py`
   - `math-sdk\env\Scripts\python.exe scripts\books_to_stories.py --check`
   - `math-sdk\env\Scripts\python.exe scripts\books_to_mock.py`
7. Check the result against the Engine non-critical limits (math-verification page):
   - P(≥5,000×) ≤0.05, P(≥10,000×) ≤0.01, P(≥25,000×) ≤0.005, P(≥50,000×) ≤0.001;
   - CVaR per-stake ≤700, absolute ≤50,000;
   - ETL>40× ≤0.9, ETL>10,000× ≤0.8, sum ≤1.5;
   - std dev ≤60 in every mode.

   Extend `math_stats.py` to print these checks if it does not already.
8. Update `docs\07-math-spec.md` Results with before/after. Update PROJECT.md M3b's done-test text: "50k buy" becomes "100k".

## Done test
- `math_stats.py --sessions`: all modes pass, base hit ≥23%, base median session ≥300 spins (M5b test still holds).
- Every target in the table above is met, or the gap is written in docs/07 with a reason.
- `books_to_stories.py --check` prints nothing.
- Total books size is <4.2 GB per file.

## Notes
- Run long jobs in the background. One full run takes a while (base, omen and prophecy at 100k, buys at 100k).
- Watch the "Gotcha": `math_stats.py:74-78` reads the raw lookup if it is newer than the publish one. Always finish with the optimizer step.
