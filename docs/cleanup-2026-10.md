# Asset cleanup 2026-10-28 (instruction 13)

Assets now live in the tracked folder `game\web\seventh-veil\static`; `scripts\sync.ps1` mirrors it into the web-sdk app.

The files below were removed because nothing loads them. The check: a file-name search over every text file in `static` and `src` (atlas, JSON, XML, TS, Svelte). `bonusButton`, `winMeterExplosion` and `uiSlotsAssetsBespoke` have no hits in `src`.

A copy of every removed file is kept in the git-ignored `art_in\_removed_2026-10\` folder.

Static size: 53 MB before, 21 MB after. Build output (`web-sdk\apps\seventh-veil\build`): 24 MB.

Kept on purpose: `H5`, `M`, `W`, `explosion` and `coins` are still loaded by `assets.ts`, although the math has no such symbols. Instruction 16 removes them with the art swap.

| Removed (58 entries) | Size | Why |
|---|---|---|
| `loader.gif` | 77 KB | old loader, not referenced |
| `assets/audio/sounds.mp3` | 4,759 KB | Howler loads ogg + m4a only (`sounds.json` `src` trimmed to those two) |
| `assets/audio/sounds.ac3` | 4,758 KB | Howler loads ogg + m4a only (`sounds.json` `src` trimmed to those two) |
| `assets/spines/bonusButton` | 968 KB | folder not referenced in `src` or any asset file |
| `assets/spines/winMeterExplosion` | 618 KB | folder not referenced in `src` or any asset file |
| `assets/sprites/uiSlotsAssetsBespoke` | 132 KB | folder not referenced in `src` or any asset file |
| `assets/fonts/goldBlur/miningfont_gold_blur.png` | 376 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/fonts/goldFont/mm_gold.png` | 317 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/anticipation/anticipation.png` | 774 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/bigwin/big_wins.png` | 643 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/bonusButton/2.0/buy_button.png` | 141 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/bonusButton/buy_button.png` | 659 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/clusterWin/clusterpay.png` | 9 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/foregroundAnimation/mm_bg.png` | 2,331 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/foregroundFeatureAnimation/mm_bg_feature.png` | 1,953 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/fsIntro/fs_screen.png` | 646 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/globalMultiplier/multiframe.png` | 60 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/loader/loader.png` | 2,177 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/reelhouse/reelhouse_glow.png` | 180 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/symbols/symbols.png` | 1,035 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/symbols2/symbols2.png` | 2,877 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/symbols3/symbols3.png` | 2,438 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/transition/transition.png` | 1,475 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/spines/tumbleWin/tumble_win.png` | 1,019 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/freeSpins/freeSpins.png` | 1,163 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/pressToContinueText/MM_pressanywhere.png` | 109 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/progressBar/progressBar.png` | 43 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/symbolsStatic/symbolsStatic.png` | 878 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/uiSlotsAssetsBespoke/autospin_active.png` | 6 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/uiSlotsAssetsBespoke/autospin_active_hover.png` | 5 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/uiSlotsAssetsBespoke/turbo_active.png` | 5 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/uiSlotsAssetsBespoke/turbo_active_hover.png` | 4 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/sprites/winSmall/MM_Localisation_winsmall.png` | 396 KB | atlas, sheet or font uses the `.webp` sibling |
| `assets/fonts/goldBlur/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/fonts/goldFont/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/fonts/purpleFont/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/fonts/silverFont/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/anticipation/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/bigwin/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/clusterWin/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/foregroundAnimation/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/foregroundFeatureAnimation/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/fsIntro/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/globalMultiplier/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/loader/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/reelhouse/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/symbols/index.ts` | 1 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/symbols2/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/symbols3/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/transition/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/spines/tumbleWin/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/freeSpins/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/payFrame/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/pressToContinueText/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/progressBar/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/reelsFrame/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/symbolsStatic/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
| `assets/sprites/winSmall/index.ts` | 0 KB | Vite import stub; `assets.ts` loads by URL |
