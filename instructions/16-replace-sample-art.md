# 16 — Replace sample art with static sprites + code animation

**Goal:** No SDK sample art, sound or theme is left: no mining theme, coins, sample logo or `MM_` assets. Symbols and scenes use our sprites, animated in PixiJS code.

**Why:**
- Sample art is rejected (docs/08 L69).
- The audit (2026-10-28) found `static\` identical to `web-sdk\apps\cluster\static`.
- Every animation today is Spine, and we have no Spine artist. So we move to static sprites with code tweens.

**Depends on:** 15, and human task 03 (art delivered).

## Steps
1. Make a `SymbolSprite.svelte` that shows a static texture with code states:
   - idle: a slow breathe at scale 1.00–1.02;
   - land: a drop with a small bounce;
   - win: pulse + glow + light rays;
   - explode: shatter into particles plus fade.

   Use pixi `Sprite`, `ParticleContainer` and svelte `Tween` (already used in `ClusterWinAmount`, `GlobalMultiplier`, `TumbleBoard`).
2. Replace the Spine symbol use (keys H1–H4, L1–L4, S) with `SymbolSprite`. Remove H5, W, M and `explosion` from `assets.ts`, since the math does not use them.
3. Replace the backgrounds (`foregroundAnimation`, `foregroundFeatureAnimation`) with layered sprites and slow parallax plus drifting particles (dust, stars).
4. Replace the reel frame, payFrame, transition and the free-spin intro/outro with our sprites and code tweens. Draw text through the font and `t()`, not per-language sprites. This also closes task 05.
5. Replace the loading screen logo (`LoadingScreen.svelte:27-28`) with our logo, and the progress bar with our style.
6. Remove `coins` (`SD2_Coin`, 2.5 MB). Make the big-win shower out of our own particles (cards, stars, gold dust).
7. Delete every unused sample file after the switch. Check with grep before each delete.
8. Track every changed component in `game\web\seventh-veil\src\components\`.

## Done test
- `Get-ChildItem -Recurse game\web\seventh-veil\static -Include *MM_*,*mm_*,*SD2_*` returns nothing.
- In storybook, every story (base, star, tower, max win) plays with our art and no console errors.
- Side-by-side screenshots of before and after are saved to `docs\screens\art-*.png`.
