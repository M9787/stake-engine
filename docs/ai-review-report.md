# Engine AI review report — Oracle of Sevens

**Prompt:** [ai-review/prompt.md](../ai-review/prompt.md), downloaded 2026-10-28 from https://studio.engine.io/docs-content/prompt.md.

## Run 2 — after instructions 01–10, 2026-10-28

**Summary:** 33 PASS · 0 FAIL · 1 AT RISK · 5 NEEDS A HUMAN · 1 N/A.
- **How:** code was read and the game was run. The run used the local mock RGS (`dev/mockRgs.js`, real books) in headless Chromium (Playwright), at `https://localhost:3007`.
- **Evidence:** screenshots are in `docs/screens/` (`t06-*`, `t07-*`, `t08-*`, `t10-*`, `run2-*`).
- **Other checks:** `node --experimental-strip-types scripts/check_amount.ts` → `OK all values`; `scripts/check_external_urls.ps1` → exit 0.

### At risk

**[253] Distinct from existing titles and [217] content: AT RISK until the final art**
- **Found:** the art and the loading logo are still the SDK `cluster` sample: "MINING MAYHEM" (`docs/screens/t08-replay-start.png`).
- **Fix:** instructions 14–16.

### Interception tests (the prompt's procedures)

| Test | Result |
|---|---|
| #242 rewritten bet levels (1.00/1.40/1.60/2.00) | `+` stops at 2.00 and greys out; `−` stops at 1.00 and greys out (`run2-betlevels-*.png`) |
| #187 interrupted round | bet 1.60, payout 1.2x, end-round aborted, reload → authenticate `round.active=true amount=1600000` → resumes, then the next `/wallet/play` has `amount: 1600000` |
| #221 zero-win end-round | 0x rounds sent no end-round; the first end-round came only after a 1.2x win |
| #222 insufficient balance | $0.50: BET and Space send 0 `/wallet/play`. $1 with Space held 25 s, 3 runs: 1–2 plays, 0 `ERR_IPB`, message "Insufficient balance…" (`t06-demo_b1_t8-hold.png`) |
| #274 invalid rgs_url (`example.com`) | "Connection problem. Please reload the game."; no RGS request succeeded |
| #240 lang `xx`, `en_US`, empty, `zh` | loads in English, 0 console errors |
| #227 / sizes | scrollHeight = innerHeight at 1024×576, 400×225, 800×450 and 425×812 (fixed a 2–4 px overflow: `canvas{display:block}`) |
| #77 / #78 social (`socialCasino` from jurisdiction, XSC) | PLAY, PLAY BONUS, SPIN, PLAY MENU, SELECT YOUR PLAY, PLAY on bonus cards, "1,000.00 SC" |
| #171–#174 replay (Tower, EUR, 2.00) | "TOWER BONUS ×400 · €2.00 · REAL COST €800.00", win €2,288.00 (1144x × 2), REPLAY works twice, 0 wallet calls |
| #172 bad values | `currency=JPY&amount=bad&lang=xx` → "¥1", English |
| #243 replay at 400×225 | fits; title overlap fixed (`run2-*`, `t08-replay-400x225.png` taken before the fix) |
| Jurisdiction | `minround3000`: 3.0–3.5 s between Space-hold rounds; HUD "Session 00:00:46 · Net −$7.80 · RTP 96.50%" |

### Full table (changed rows only; all other rows as in Run 1)

| ID | Verdict | Evidence |
|---|---|---|
| 275 | PASS | no loader in `src/` or the build |
| 242 | PASS | interception test above; `vite.patches.js` stateBet snap |
| 219 | PASS | `src/overrides/formatAmount.ts`; JPY ¥1, EUR €, CA$, MX$ (`check_amount.ts`) |
| 273 | PASS | `$0.004`, `$0.012` (`check_amount.ts`) |
| 222 | PASS | `src/game/actor.ts` guard; tests above |
| 223 | PASS | `src/app.html` viewport `user-scalable=no`, `touch-action: manipulation` |
| 193 / 195 / 194 | NEEDS A HUMAN (layout works) | `run2-size-*.png`: every control visible and usable. Mobile: the WIN label covers the bottom row of the board; revisit with the final UI (instructions 19) |
| 227 | PASS | scroll check above |
| 240 | PASS | `vite.patches.js` stateUrl lang |
| 77 / 188 / 225 | PASS | `vite.patches.js` i18n patches, `wording.ts` |
| 78 | PASS | "1,000.00 SC" |
| 171 / 172 / 173 / 174 / 243 | PASS | `src/components/ui/UIReplay.svelte`, `Authenticate.svelte` replay |
| 185 | PASS | template verbatim, `GameInfo.svelte` |
| 235 | PASS | the button guide adds Stop, Settings and Replay |
| 217 / 253 | AT RISK / NEEDS A HUMAN | sample art (instructions 14–16) |

### For a person to check
- **Final look at the four sizes** (after the new art): no overlaps, text readable at 400×225.
- **Sound:** mute, then play a bonus and a big win; nothing should be audible.
- **Art originality and content** ([217], [253]) once the sample art is replaced.

## Run 1 — baseline, 2026-10-28 (before fixes 03–10, after fix 01)

**Summary:** 19 PASS · 13 FAIL · 2 AT RISK · 5 NEEDS A HUMAN · 1 N/A. Code was read only; the game was not run (the build was in progress).
The game will be run in Run 2, after tasks 03–10, with the prompt's interception tests.

### Failures

**[219] Currency display: FAIL**
- **Found:** `web-sdk/packages/utils-shared/amount.ts:37-43` always uses 2 decimals, so JPY shows `¥10.00`. `amount.ts:34` puts XSC/XGC first (`SC 10.00`), but the table expects `10.00 SC`. Codes that are not ISO (USDT) throw inside `Intl`. Replay never reads `currency` (`src/components/Authenticate.svelte:136-161`).
- **Fix:** add a local `formatAmount` and alias `utils-shared/amount` to it. In replay, read `currency`. Task 03 (replay: 08).

**[273] Sub-cent payouts: FAIL**
- **Found:** `amount.ts:38-39` sets `maximumFractionDigits: 2`, so 0.004 shows as 0.00 and 0.012 as 0.01.
- **Fix:** allow up to 4 decimals for values with sub-cent digits. Task 03.

**[222] Insufficient balance sends no play request: FAIL**
- **Found:** with Space hold, `createIntermediateMachineBet.ts:8-18` `checkSpaceHold` loops to `fetching` with no funds check, so `/wallet/play` goes out and relies on `ERR_IPB`. `stateBet.svelte.ts:57-62` ignores the cost of buy modes.
- **Fix:** add a central guard in `src/game/actor.ts` `onNewGameStart` that uses the mode's real cost. Task 06.

**[242] Bet levels only: FAIL**
- **Found:** `stateBet.svelte.ts:24-31` `correctBetAmount` caps a bet at `balance/cost`, which is not a bet level. The mock rejects it with `ERR_VAL` (`dev/mockRgs.js:94`).
- **Fix:** snap to the highest level that fits. Task 06.

**[223] Double-tap zoom disabled: FAIL**
- **Found:** `src/app.html:6` is `<meta name="viewport" content="width=device-width" />` only.
- **Fix:** add `initial-scale=1, maximum-scale=1, user-scalable=no` and `touch-action: manipulation`. Task 04.

**[240] Invalid language falls back: FAIL**
- **Found:** `state-shared/src/stateUrl.svelte.ts:27-28` passes any code through. `LoadI18n.svelte:23-33` falls back only when an error is thrown. `?lang=zz` then asks for sprite frames that don't exist: `FreeSpinIntro.svelte:51`, `FreeSpinOutro.svelte:63,70`, `PressToContinue.svelte:19`.
- **Fix:** check `lang` against our supported list (`en`). Task 05.

**[77] Social wording: FAIL**
- **Found:** the shared labels below skip our `t()`, and `components-ui-pixi/src/i18n/i18nDerived.ts:7,9` checks only `?social=true`, not `jurisdiction.socialCasino`. Restricted words:
  - "BET": the amount label, `LabelBet.svelte:16`, which reads "SPIN" under `social=true`;
  - "BET MENU", "SELECT YOUR BET": `ModalBetMenu.svelte:25,28`;
  - "BUY BONUS": `ButtonBuyBonus.svelte:74`, when social comes from the jurisdiction;
  - "FUNDS", "BET": the autoplay insufficient-funds message, `components-ui-html/src/i18n/i18nDerived.ts:20`;
  - "PAYTABLE": `components-ui-pixi/src/i18n/i18nDerived.ts:18`.
- **Fix:** add Vite transforms that route both i18n files through `t()` and `isSocial()`. Task 07.

**[188] Replay has no restricted words: FAIL**
- **Found:** the replay UI renders the shared `LabelBet` ("BET"/"SPIN") and the menu "PAYTABLE" (`UIReplay.svelte`).
- **Fix:** task 07 transforms, plus a local UIReplay. Task 08.

**[172] Replay optional parameters: FAIL**
- **Found:** `currency` is not read. A missing or invalid `amount` gives a 0.00 bet (`Authenticate.svelte:137`).
- **Fix:** task 08.

**[173] Replay can be watched again: FAIL**
- **Found:** the shared `UIReplay.svelte` has no replay-again control.
- **Fix:** task 08.

**[174] Replay shows cost and multiplier: FAIL**
- **Found:** `LabelBet.svelte:17` uses `betCost()`, which counts buy modes as 1x. No multiplier is shown.
- **Fix:** tasks 06 and 08.

**[78] SC/GC display: FAIL**
- **Found:** the format is `SC 10.00`, but the prompt table expects `10.00 SC`. XEC is not mapped.
- **Fix:** task 03.

**Extra: jurisdiction flags not honoured: FAIL** (not a numbered guideline)
- **Found:** a grep finds no reader of `minimumRoundDuration`, `displaySessionTimer`, `displayNetPosition`, `displayRTP` or `disabledSlamstop`. `Authenticate.svelte:81-84` replaces the default flags, so flags the RGS leaves out become `undefined`.
- **Fix:** task 10.

### At risk

**[185] General disclaimer: AT RISK**
- **Found:** `src/components/GameInfo.svelte:142` says "Malfunction voids all pays and plays." The template says "wins". The other points have not been compared yet.
- **Fix:** task 09.

**[243] Replay at 400×225: AT RISK**
- Not run yet. Task 08 will check it.

### Full table

| ID | Guideline | Verdict | Evidence |
|---|---|---|---|
| 181 | Authenticates on launch | PASS | `src/components/Authenticate.svelte:34-38` uses `stateUrlDerived.rgsUrl()`; no hardcoded host (`scripts/check_external_urls.ps1` exit 0, 2026-09-19) |
| 274 | Invalid rgs_url | PASS | error modal on failure, `Authenticate.svelte:131-133`; checked 2026-09-19. Re-run in Run 2 |
| 183 | Bet sends play | PASS | `createPrimaryMachines.ts:11-17`; demo rounds played 2026-09-19 |
| 275 | No Stake Engine loader | PASS | removed in task 01; grep finds no hit in `src/` |
| 213 | Title unique / restricted terms | PASS | "ORACLE OF SEVENS" contains no listed term (`Game.svelte:95`) |
| 217 | Offensive content | NEEDS A HUMAN | sample art still in place (task 16) |
| 253 | Distinct from existing titles | NEEDS A HUMAN | sample art from SDK `cluster` (task 16) |
| 242 | Bet levels from authenticate | FAIL | see above |
| 187 | Active round restores bet | PASS | `Authenticate.svelte:113-129` sets `betAmount` and `wageredBetAmount` from `round.amount` |
| 219 | Currency display | FAIL | see above |
| 273 | Sub-cent payouts | FAIL | see above |
| 221 | Zero-win no end-round | PASS | `createPrimaryMachines.ts` `noWin` sends no end-round |
| 222 | Insufficient balance | FAIL | see above |
| 228 | Space bar bets | PASS | `ui/ButtonBet.svelte:23` `OnHotkey Space`; `EnableHotkey.svelte:19` calls `preventDefault` |
| 227 | No scroll | PASS | `app.html:9` body `overflow: hidden`. Re-check sizes in Run 2 |
| 104 | Autoplay confirmation | PASS | autoplay opens a settings modal (audit 2026-09-19) |
| 31 | High-cost modes confirmed | PASS | `ModalBuyBonusConfirm.svelte:68-79` shows the cost before buying |
| 107 | Sound off | PASS | sound toggle (audit 2026-09-19). Re-check in Run 2 |
| 25 | RTP and max win per mode | PASS | `GameInfo.svelte:112-119` from `config.ts` |
| 24 | Symbol payouts | PASS | `GameInfo.svelte:20-25`, H1–H4 and L1–L4 from `config.ts` |
| 26 | Win combinations | PASS | cluster, tumble and multiplier text in `GameInfo.svelte` |
| 27 | Mode descriptions and costs | PASS | mode table plus `betModes.ts:299-327` |
| 29 | Free games and re-triggers | PASS | 12/15, 15-18 and +5 retrigger text in `GameInfo.svelte` |
| 235 | Every control explained | AT RISK → task 09 | check `BUTTONS` in `GameInfo.svelte:47-58` against the UI |
| 185 | General disclaimer | AT RISK | see above |
| 266 | Mystery Mode | N/A | no mode shows probabilities. The mode dialogs give bonus frequencies ("about 1 in 400"); task 09 checks them against the math |
| 193 | Laptop 1024×576 | NEEDS A HUMAN | Run 2 screenshot |
| 195 | Popout S/L | NEEDS A HUMAN | Run 2 screenshot |
| 194 | Mobile 425×812 | NEEDS A HUMAN | Run 2 screenshot |
| 223 | Double-tap zoom | FAIL | see above |
| 239 | English | PASS | `en` messages; shared keys are English text |
| 240 | Invalid language | FAIL | see above |
| 77 | Social wording | FAIL | see above |
| 78 | SC/GC | FAIL | see above |
| 225 | Mode names | PASS | Fate: Veil / Omen / Prophecy, Star bonus, Tower bonus; `betModes.ts` |
| 188 | Replay restricted words | FAIL | see above |
| 171 | Replay loads | PASS | mock `/bet/replay` verified 2026-09-19; no wallet calls (`createPrimaryMachines.ts:43`) |
| 172 | Replay params | FAIL | see above |
| 173 | Replay again | FAIL | see above |
| 174 | Replay cost | FAIL | see above |
| 243 | Replay 400×225 | AT RISK | see above |

### Mapping
- Task 03: [219], [273], [78].
- Task 04: [223], [193], [194], [195].
- Task 05: [240].
- Task 06: [222], [242].
- Task 07: [77], [188].
- Task 08: [172], [173], [174], [243].
- Task 09: [185], [235], [266].
- Task 10: jurisdiction flags.
- Extra: none beyond the above.
