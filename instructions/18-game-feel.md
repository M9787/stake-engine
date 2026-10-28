# 18 — Game feel ("juice")

**Goal:** Every event has clear, satisfying feedback. Players want "one more spin" instead of stopping after 1–2 bets.

**Why:** Reviewers name "players typically place only 1–2 bets before losing interest" as the top cause of low ratings (https://studio.engine.io/docs/approval-guidelines/game-quality-rankings, 2026-10-28).

**Depends on:** 16.

## Checklist
1. **Tumble:** winning cells flash, then shatter. New symbols fall with a stagger (column by column, 30 ms) and a small bounce. The tumble count steps up in the corner.
2. **Win counter:** the count-up speed depends on the size of the win. Show the cluster total next to the cluster ("+12.40"). No celebration when win ≤ cost (docs/08 rule, `presentedWinLevel`).
3. **Anticipation:** when 2 crystal balls are on the board and a tumble or drop is still coming, dim the board slightly, add a heartbeat sound and make the balls glow.
   - Only show it when a 3rd ball is really possible, from the book data. **No fake near-miss** (docs/08 honest anticipation).
4. **Big-win tiers:** big / super / mega / epic / max. Each tier has its own colour, a particle shower made of our art and a music sting. Tap to skip.
5. **Bonus intros:**
   - Star: a moon veil opens and 5 sigils pre-charge one by one.
   - Tower: lightning strikes the tower and 12 sigils pre-charge in a wave.

   They must clearly look different, so the 400x buy looks worth it.
6. **Bonus end:** a total-win screen with a spin count and the highest multiplier reached. That is good clip content.
7. **Retrigger:** +5 spins flies into the counter with a sound.
8. **Idle:** after 10 s idle, symbols do a subtle shimmer wave.
9. **Sound mix:** music ducks under big hits. Every effect has a volume that fits the mix; nothing clips.

## Done test
- A 60-second demo recording, `docs\clips\feel-demo.mp4`, shows a tumble chain, anticipation, a big win and a bonus intro.
- docs/08 "celebrate only above cost" is checked with the star `win_below_cost` story.
