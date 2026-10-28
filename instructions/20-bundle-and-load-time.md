# 20 — Bundle size and load time

**Goal:** The build is under 10 MB, and the first playable frame shows in under 4 s on a mid phone over 4G.

**Why:** 3★ needs an "optimised bundle size — avoid large assets; games that take a long time to load create poor experiences" (https://studio.engine.io/docs/approval-guidelines/game-quality-rankings, 2026-10-28). Today the build is 58.7 MB; the real payload is about 10–12 MB.

**Depends on:** 16–19.

## Steps
1. Measure: `Get-ChildItem -Recurse web-sdk\apps\seventh-veil\build | Sort-Object Length -Descending | Select-Object -First 20 FullName, Length`.
2. Budget:
   - textures ≤5 MB total WebP;
   - audio ≤2.5 MB (ogg + m4a at 96 kbps for music, mono effects);
   - JS ≤1.5 MB.
3. Preload only what the first screen needs: loader, background, symbols, UI, base music. Lazy-load the bonus and big-win assets after the first spin.
4. `bundleStrategy:'inline'` makes `index.html` 1.35 MB and also writes a duplicate `_app\immutable\bundle.*.js`. Check whether the duplicate is used. If not, exclude it from `upload\front` in task 21.
5. Test the load with Chrome DevTools: Network "Fast 4G", CPU 4× slowdown.

## Done test
- The build folder is ≤10 MB.
- The first spin is possible in ≤4 s under Fast 4G and 4× CPU. Record the numbers in `docs\02-web-sdk.md`.
