# 09 — Rules and disclaimer

**Goal:** The rules screen is complete and matches the final math exactly.

**Why:** Guidelines (https://studio.engine.io/docs-content/prompt.md, 2026-10-28):
- [25]: RTP and max win per mode.
- [24]: every symbol's pays.
- [26]: win combinations.
- [27]: mode descriptions and costs that match `index.json`.
- [29]: free games and retriggers.
- [235]: every control explained.
- [185]: general disclaimer.
- [266]: any probabilities shown match the math.

Disclaimer template: https://stake-engine.com/docs/approval-guidelines/general-disclaimer.

**Depends on:** 11. The rules must show the final math numbers.

## Steps
1. In `game\web\seventh-veil\src\components\GameInfo.svelte:142`, change "Malfunction voids all **pays** and plays." to the template wording "… all **wins** and plays." Then compare the whole disclaimer with the template, word by word.
2. Make sure the rules say that outcomes are pre-calculated and come only from the RGS response.
3. Generate the numbers, don't type them. Pays, RTP, max win and costs come from `src\game\config.ts`, which `scripts\gen_fe_config.py` writes after task 11.
4. Explain these items in plain words:
   - clusters (5+), tumble, the multiplier grid (mark → x2 → doubles up to x1024);
   - Star (3–4 balls, 12/15 spins) and Tower (5+ balls);
   - retrigger (+5);
   - each Fate mode: what it changes and its cost;
   - buy costs 100x and 400x;
   - max win 77,777x.
5. Check that the button guide covers every control: spin, bet +/−, autoplay, turbo, menu, sound, rules, buy, Fate selector.
6. Remove symbols the math doesn't have (H5, W, M) from the pay table if they appear.

## Done test
- A script or manual check compares every number in the rules with `math-sdk\games\seventh_veil\library\publish_files\index.json`, `docs\07-math-spec.md` and `config.ts`. Zero differences.
- The disclaimer matches the template text.
