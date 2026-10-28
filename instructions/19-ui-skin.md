# 19 — UI skin

**Goal:** Buttons, panels and fonts look made for this game, not like a stock template.

**Why:**
- The UI today is plain rounded rectangles. The shared `UiSprite.svelte` is an "ADD YOUR DESIGN" stub, and the title is plain text (`Game.svelte:95,100`) (audit 2026-10-28).
- Reviewers penalise "standard fonts, gradients, emoji icons, and border effects".

**Depends on:** 16.

## Steps
1. Skin these with the UI art from docs/09 (9-slice sprites where they need to stretch):
   - spin button;
   - bet +/−, autoplay, turbo, menu, sound, rules;
   - Fate selector;
   - bonus cards.
2. Put the logo art in place of the plain title text in `Game.svelte`.
3. HTML panels (rules, menus, dialogs): use our display font (OFL, bundled, no external URL) for headings, keep Inter for body text, and use our palette. No default browser buttons.
4. Every button has a hover, a press (scale 0.95) and a disabled state.
5. Check that touch targets are ≥44 px at 425×812.

## Done test
- Screenshots at all four reviewer sizes show the skinned UI (`docs\screens\ui-*.png`).
- `scripts\check_external_urls.ps1` exits 0. The fonts are bundled.
