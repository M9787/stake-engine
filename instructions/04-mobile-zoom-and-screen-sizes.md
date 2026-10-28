# 04 — Mobile zoom and the four reviewer screen sizes

**Goal:** Double-tap zoom is off. The game fits at all four reviewer sizes, with nothing cut off and no scrolling.

**Why:** Guidelines (https://studio.engine.io/docs-content/prompt.md, 2026-10-28):
- [223]: double-tap zoom disabled. `width=device-width` alone fails.
- [193]: laptop 1024×576.
- [195]: popout S 400×225 and popout L 800×450.
- [194]: mobile 425×812 with touch input.
- [227]: the main frame never scrolls.

**Depends on:** 02.

## Steps
1. In `game\web\seventh-veil\src\app.html:6`, set the viewport to `width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no`.
2. In the body style (`app.html:10`), add `touch-action: manipulation; overscroll-behavior: none;`. Add the same `touch-action` to the canvas.
3. Run `scripts\sync.ps1` and start demo play (PROJECT.md §7).
4. In browser dev tools, device mode, check each size: 1024×576, 400×225, 800×450, 425×812.
5. At each size, check that:
   - spin, bet +/− and menu are visible and clickable;
   - the rules open and close;
   - nothing scrolls.
6. Save one screenshot per size to `docs\screens\size-<w>x<h>.png`.

## Done test
- All four screenshots show the full game with usable buttons.
- `Select-String game\web\seventh-veil\src\app.html -Pattern 'user-scalable=no'` finds a match.

## Notes
- Repeat this check in task 21, because new art can change the layout.
