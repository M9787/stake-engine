# 03 — Currency and sub-cent amounts

**Goal:** Every amount shows correctly in USD, EUR, CAD, MXN, JPY, XSC and XGC. Payouts under 0.01 do not show as 0.00 or 0.01.

**Why:** Two guidelines (source: https://studio.engine.io/docs-content/prompt.md, 2026-10-28):
- [219]: each currency formats correctly (symbol, decimals, position) everywhere.
- [273]: sub-cent payouts display accurately.

**Depends on:** 02 (check the report for extra currency findings).

## Current problems (audit 2026-10-28)
- `web-sdk\packages\utils-shared\amount.ts:37-43` forces 2 decimals, so 0.012 shows as 0.01.
- `Intl` currency style throws on codes that are not 3 letters (USDT, DOGE). Only XGC and XSC are handled (`amount.ts:6-9`).
- The bitmap font `goldFont/mm_gold.xml` has only 58 glyphs: no `£`, and the only lowercase letters are `z` and `ł`. Big-win, tumble and free-spin numbers use it (`Win.svelte`).

## Steps
1. Make a local copy: `game\web\seventh-veil\src\overrides\amount.ts`, starting from the shared `amount.ts`.
2. Point every importer at the copy with `resolve.alias` in `game\web\seventh-veil\vite.config.js`, the same way `webfontloader` is aliased at line 31. Match the exact import specifier the shared code uses. Find it with `Select-String -Path web-sdk\packages -Pattern "utils-shared/amount" -Recurse`.
3. In the copy:
   - Show up to 4 decimals when the value has sub-cent digits. Otherwise keep the currency's normal decimals (JPY 0, others 2).
   - Wrap `Intl.NumberFormat` in try/catch. On error, format the number and add the code as a suffix, for example `12.50 USDT`.
   - Keep the XSC → "SC" and XGC → "GC" handling, with no `$`.
4. Fonts: task 19 makes the new bitmap font. Its glyph set must include `0-9 . , $ € £ ¥ A-Z a-z x X + - space`.
5. Add a check script `game\web\seventh-veil\src\overrides\amount.check.ts` that prints sample values for every currency in the list.

## Done test
- The check script prints correct strings for 0.004, 0.012, 1 and 1234.5 in USD, EUR, CAD, MXN, JPY, XSC, XGC and USDT.
- Demo play with `&currency=JPY` and with `&currency=XSC`: balance, bet and win all look right.

## Notes
- Money units: 1,000,000 = 1.00 (RGS micro-units).
