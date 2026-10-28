# 13 — Track assets in `game\` and remove dead files

**Goal:** Assets live in our tracked folder and sync into the SDK copy. About 35 MB of unused files are gone.

**Why:**
- Today every asset exists only in `web-sdk\apps\seventh-veil\static`, which is ignored by our git. `scripts\sync.ps1:11` skips `static`, so a re-clone loses everything.
- 3★ needs an "optimised bundle size" (https://studio.engine.io/docs/approval-guidelines/game-quality-rankings, 2026-10-28).

**Depends on:** nothing.

## Dead files found (audit 2026-10-28)
- About 22 MB of `.png` files whose atlas or XML points to the `.webp` sibling.
- `audio\sounds.mp3` and `sounds.ac3`, about 9.7 MB. Keep ogg and m4a, and check that the Howler config lists only those two.
- `spines\bonusButton` (991 KB), `spines\winMeterExplosion` (633 KB), `sprites\uiSlotsAssetsBespoke` (135 KB), the `index.ts` stubs.
- `loader.gif` (78 KB). The Stake loader gif is already removed in task 01.

## Steps
1. Copy `web-sdk\apps\seventh-veil\static` to `game\web\seventh-veil\static`.
2. Change `scripts\sync.ps1` so it also mirrors `static`. Keep the rest of its behaviour.
3. For each `.png`, check whether any `.atlas`, `.json` or `.xml` references that exact file name. Delete it only if nothing does. Write the deleted list to `docs\cleanup-2026-10.md`.
4. Delete the unused spines and sprites listed above. First confirm with `Select-String -Path game\web\seventh-veil\src -Pattern 'bonusButton|winMeterExplosion|uiSlotsAssetsBespoke' -Recurse` that nothing loads them.
5. Remove the mp3 and ac3 files. Keep the source list in `sounds.json` to `ogg` and `m4a`. Safari uses m4a.
6. Run sync and build, then play one round per mode in demo play.

## Done test
- `git status` shows `game\web\seventh-veil\static\` tracked.
- The build folder is ≤25 MB and the game plays without missing-texture errors in the console.

## Notes
- Large binary files: if the repo will be pushed to GitHub (human task 12), consider Git LFS for `static\`. Ask the user before setting it up.
