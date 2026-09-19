# 01 — Math SDK (Python side)

## Purpose

Set up math-sdk on Windows without `make`, build Seventh Veil math, know what it emits.

## Prereq

- Python and Rust per [PROJECT.md §3](../PROJECT.md#3-stack-pinned). Check: `scripts\doctor.ps1`.
- math-sdk cloned to `stake\math-sdk` (PROJECT.md §6 M1).

## Steps

One-time venv (PowerShell equivalent of `make setup`):

```powershell
cd math-sdk
python -m venv env
.\env\Scripts\python.exe -m pip install --upgrade pip
.\env\Scripts\python.exe -m pip install -r requirements.txt
.\env\Scripts\python.exe -m pip install -e .
```

Build the game (equivalent of `make run GAME=seventh_veil`):

```powershell
.\env\Scripts\python.exe games\seventh_veil\run.py
```

Optimizer one-time setup (no MSVC Build Tools needed):

```powershell
rustup toolchain install stable-x86_64-pc-windows-gnu --profile minimal
cd optimization_program; rustup override set stable-x86_64-pc-windows-gnu; cargo build --release; cd ..
```

`run.py` switches: `num_sim_args` (sims per mode), `run_optimization` (Rust optimizer), `run_analysis`, `run_format_checks` (SDK "3-star" volatility checks).

### Game files (`games\seventh_veil\`)

| File | Owns |
|---|---|
| `game_config.py` | ids, 7x7 board, paytable, scatter triggers, x1024 cap, Tower settings, 5 bet modes |
| `gamestate.py` | spin loop: draw → clusters → tumble → charge grid; bonus loop |
| `game_executables.py` | charged-grid update (mark → x2 → double) |
| `game_calculations.py` | cluster pay × sum of charged spots |
| `game_override.py` | per-spin reset, Star/Tower choice, Tower pre-charge |
| `game_events.py` | custom events `updateGrid`, `bonusVariant` |
| `game_optimization.py` | optimizer RTP / hit-rate targets per mode |
| `reels\*.csv` | BR0 (base), FR0 (bonus), WCAP (max-win forcing) |

### Outputs

`games\seventh_veil\library\publish_files\` holds the upload set:

| File | Format |
|---|---|
| `index.json` | `{"modes":[{"name","cost","events","weights"}]}` |
| `lookUpTable_<mode>_0.csv` | rows `id, weight, payout` — all uint64; payout = multiplier × 100 |
| `books_<mode>.jsonl.zst` | zstd JSON lines; each has `id`, `events`, `payoutMultiplier` |

Books `events` feed the frontend: [03-contract.md](03-contract.md).

## Verify

```powershell
math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief
```

Per mode: RTP, hit rate, win > cost rate, max win, quantiles, 3-star failures, books↔lookup match. Targets: [07-math-spec.md](07-math-spec.md).

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://raw.githubusercontent.com/StakeEngine/math-sdk/main/Makefile | setup/run steps | 2026-09-19 |
| https://github.com/StakeEngine/math-sdk/blob/main/docs/math_docs/overview_section/game_struct.md | game file roles | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | output formats | 2026-09-19 |
