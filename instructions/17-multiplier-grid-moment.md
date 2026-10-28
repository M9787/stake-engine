# 17 — Signature moment: the multiplier grid

**Goal:** The charged multiplier grid becomes the game's "clip moment": the thing people screenshot and share. Each charge level looks and sounds stronger.

**Why:**
- This is our core mechanic. Today it is only a sample `payframe` loop plus "N X" text (`MultiplierGrid.svelte:44-61`), with no charge-up or doubling animation and no sound (audit 2026-10-28).
- "Shallow gameplay" and "missing engaging features" are the top causes of low ratings.
- Streamer clips need visible huge multipliers (trade press, 2025–2026).

**Depends on:** 16.

## Design
| State | Look | Sound |
|---|---|---|
| Marked (first win) | Faint sigil etched in the cell | Soft chime |
| x2 | Sigil lights violet, small pulse | Chime up 1 step |
| x4–x16 | Brighter, thin rays, colour shifts violet → gold | Rising pitch per level |
| x32–x128 | Gold, orbiting sparks, cell border burns | Deeper hit + shimmer |
| x256–x1024 | White-gold flare, screen shake (small), lightning to neighbours | Big impact + choir hit |
| Applied to a win | Beams fly from each charged cell into the win counter, counter multiplies with a slam | Whoosh then slam |

## Steps
1. Rewrite `MultiplierGrid.svelte` to use the states above with code tweens and particles. Read the values from the existing `updateGrid` events (docs/03 contract). Do not invent events.
2. Add a "grid total" readout that shows the sum of charged spots during bonuses.
3. Add pitch-stepped chimes: one base sound, played at a higher rate per level. This needs only 1–2 new sound effects.
4. Respect turbo: shorten the animations, but always show the final value.
5. Respect `minimumRoundDuration` (task 10).

## Done test
- In storybook, the max-win story shows every state from marked to x1024.
- A 10-second screen recording of a bonus with x256+ is saved to `docs\clips\grid-*.mp4` for task 24.
- FPS stays ≥50 on a mid laptop at 1024×576 (Chrome performance panel).
