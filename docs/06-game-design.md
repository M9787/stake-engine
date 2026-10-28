# 06 — Game design: Oracle of Sevens

Player-visible name: Oracle of Sevens. The veil motif stays in play ("Fate: Veil", "THE VEIL TEARS"): the oracle lifts the veil. Internal ids keep `seventh_veil`.

## Purpose

What the player experiences, and why each element earns its place. Math numbers live in [07](07-math-spec.md). Rules that limit design live in [08](08-compliance.md).

## Prereq

[00-platform.md](00-platform.md): Engine games are stateless. Every player choice happens before the spin, as a bet mode.

## Steps (design)

### Fantasy

An oracle's reading room. Each spin draws cards through seven veils. Winning clusters burn sigils into the table. Struck sigils glow, charge, and double. Tone: mature, candle-lit, gold on deep violet. No child-like characters, no religious iconography.

### Core loop (one spin, 3–8 s)

1. Choose a Fate (`base` / `omen` / `prophecy`) or buy a bonus (`star` / `tower`).
2. Cards drop on a 7x7 grid.
3. 5+ touching identical symbols form a cluster. The cluster pays, then explodes.
4. Each exploded spot gets a **sigil** (marked, no multiplier yet).
5. A win on a marked spot **charges** it to x2. Each later win there doubles it: x4, x8 … **x1024**.
6. A cluster's pay is multiplied by the sum of charged spots under it.
7. New cards fall in (tumble). Repeat until no cluster. Base game: sigils clear after the spin.
8. 3+ Crystal Balls trigger a bonus.

### Symbols

| Id | Name | Tier |
|---|---|---|
| H1 | The High Priestess | high |
| H2 | The Tower | high |
| H3 | The Moon | high |
| H4 | The Magician | high |
| L1–L4 | Runes: Fehu, Ansuz, Raido, Kenaz (Kenaz on bonus reels only) | low |
| S | Crystal Ball | scatter |

No wild in v1. Clusters stay easy to read.

### "Every win beats your bet" (Fate: Veil only)

The lowest pay is 1.2x (a 5-cluster of Raido). In the base mode (Fate: Veil) every hit returns more than the stake: no "wins" that are really losses. Base hits land about 1 in 4 spins (25%), and each one is real. This is the game's player promise and a marketing line.

Scope: the promise holds only in Fate: Veil. In Omen (1.25x price) a 1.2x hit is below the spin price, and in Prophecy (2x) most hits are. Those modes trade base wins for more frequent bonuses, and the rules screen and mode dialogs say so plainly. Bonus buys can pay less than their price; the dialogs say that too.

### Playtime balance (iteration 4)

Target: a 100-bet balance should last a normal session. Before the rebalance the base game hit 14% of spins, 62% of RTP sat in a 1-in-350 bonus, and a 100-bet balance lasted a median 163 spins. RTP moved from the bonus into base hits: base now hits 25% of spins with a bonus about 1 in 400, and the median session is about 340 spins (338 measured) with a longest dead run of about 14 spins. Numbers: [07](07-math-spec.md).

### Bonuses (the "pick your bonus" hook)

| Bonus | How to get it | Rule |
|---|---|---|
| **Star** | 3–4 Crystal Balls, or buy `star` | 12 spins (3 balls) / 15 spins (4 balls). Starts with 5 random spots pre-charged at x2. Sigils persist for the whole bonus. |
| **Tower** | 5+ Crystal Balls, or buy `tower` | 15–18 spins. Sigils persist. Starts with 12 random spots pre-charged at x2. |

Retrigger: 3+ Crystal Balls during a bonus add 5 spins. The player picks the bonus by picking the buy mode; natural triggers map by ball count, shown in the paytable.

### Fate tiers (the "choose your risk" hook)

Same rules, same RTP. Higher Fate costs more per spin and triggers bonuses more often. The mode dialogs show cost, RTP, max win and bonus frequency for each Fate before the player commits; the rules screen lists cost, RTP and max win per mode. This is the legal form of Plinko/Mines-style risk choice.

### Signature moment

Max win 77,777x ends the round (`wincap`). The max-win panel plays, relabelled "THE VEIL TEARS" (implemented; a dedicated 6-second cinematic comes with final art in M6). Replay sharing depends on Engine's UI (PROJECT.md §11 Q5); the game has no copy-link button.

### What we took from top performers, and what we left out

| Taken | From |
|---|---|
| Visible, persistent, escalating multipliers | Sugar Rush 1000, Gates of Olympus |
| Short, readable rounds | Crash, Plinko |
| Player chooses risk before the round | Plinko rows, Mines count |
| Choice of bonus | Hacksaw (Le Bandit, Wanted) |
| Round, memorable max win | Waylanders Forge (80,085x) |
| Strong theme and mascot potential | Big Bass, Le Bandit |

| Left out | Why |
|---|---|
| Cash-out, gamble, jackpots | Engine rule; stateless only |
| 5+ buy tiers | Waylanders complexity complaint; 2 buys cover the choice |
| Many tiny sub-stake "wins" | Gates of Olympus / Sugar Rush complaint; every base pay ≥1.2x instead |
| Rare, invisible bonuses | Fate tiers make bonus odds a visible choice (1 in 400 / 150 / 80) |
| Loss-disguised-as-win, fake near-miss | [08](08-compliance.md) |

## Verify

- Every mechanic above maps to code in `game\math\seventh_veil` (source; `scripts\sync.ps1` copies it into math-sdk) (grid: `game_executables.py`, Star/Tower pre-charge and bonus variant: `game_override.py`).
- Every symbol and bonus rule appears in the in-game paytable (M5).

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://stake-engine.com/docs/approval-guidelines | stateless-only rule | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements | no child appeal | 2026-09-19 |
| https://github.com/StakeEngine/math-sdk | `0_0_cluster` grid-multiplier base | 2026-09-19 |
