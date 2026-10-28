# 01 — Remove the Engine loader

**Goal:** The old "Powered by Stake Engine" loader never shows, and its gif is not in the build.

**Why:** Guideline [275] says the old "Powered by Stake Engine" loader must never appear. A game that shows it fails pre-checks. Source: https://studio.engine.io/docs-content/prompt.md (read 2026-10-28).

**Depends on:** nothing.

## Steps
1. Open `game\web\seventh-veil\src\routes\+layout.svelte`.
2. Delete the `LoaderStakeEngine` import (line 4), the gif URL (line 16), and the component (line 29). Keep the rest of the layout as it is.
3. Search for any other use: `Select-String -Path game\web\seventh-veil\src -Pattern 'LoaderStakeEngine|stake-engine-loader' -Recurse`. Expected result: no matches.
4. Delete `web-sdk\apps\seventh-veil\static\stake-engine-loader.gif`. It is 1.3 MB. Task 13 moves `static` into `game\` later; do not copy the gif there.
5. Run `scripts\sync.ps1`, then build: `Push-Location web-sdk; pnpm run build --filter=seventh-veil; Pop-Location`.

## Done test
- `Get-ChildItem -Recurse web-sdk\apps\seventh-veil\build -Filter *loader*.gif` returns nothing.
- Open demo play (PROJECT.md §7). The game loads with no Engine logo or gif.

## Notes
- The SDK's own `loader.gif` (78 KB) is unused. Task 13 deletes it.
