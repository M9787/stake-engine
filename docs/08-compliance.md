# 08 — Compliance and ethics

## Purpose

Rules the game must meet before submission. Engine rules come from the approval guidelines. Ethics rules are ours; they also match UK and GLI standards. None are negotiable.

## Prereq

[06-game-design.md](06-game-design.md), [07-math-spec.md](07-math-spec.md).

## Steps (checklist — run before every submission)

Status 2026-10-28: `[x]` verified, `[ ]` open. `(code)` = implemented, not yet verified on screen. `[NNN]` = guideline ID in Engine's AI review prompt (`ai-review/prompt.md`); evidence in [ai-review-report.md](ai-review-report.md) Run 2.

### Math
- [x] Every mode passes `scripts\math_stats.py`: RTP 0.9635–0.9665, Engine non-critical limits empty (0 failed classes), books match lookup.
- [x] Every mode has at least one max-win book (reviewer event ID).
- [ ] Math frozen. No change after approval.

### Disclosure (UI)
- [ ] [25] RTP of the game and of each mode shown. (code: `GameInfo.svelte` rules screen)
- [ ] [26] Max win of each mode shown. (code: rules screen + bet-mode dialogs)
- [ ] [27] Cost of each mode shown before purchase. (code: rules screen; SDK buy dialog shows price)
- [ ] [28] Every symbol pay and every multiplier value (x2 … x1024) shown in the paytable. (code: pays from generated `config.ts`)
- [ ] [29] Bonus trigger rules (3–4 balls = Star, 5+ = Tower) shown. (code)

- [x] [235] Button guide: what each button does, incl. Stop, Settings, Replay (`GameInfo.svelte` "Buttons" table; AI review Run 2).
- [x] [185] General disclaimer: Engine template verbatim (`GameInfo.svelte`).
- [ ] Ante and buy trade-offs stated plainly: ante wins often return less than the spin price; a bonus can pay less than its price. (code: rules screen + bet-mode dialogs)

### Bets and balance (RGS)
- [x] [219] Balance and wins formatted per currency: all 85 codes of the Engine table (symbol, decimals, placement), unknown codes as `10.00 ABC` (`src/overrides/formatAmount.ts`; `scripts\check_amount.ts` OK 97 checks, 2026-11-06; SC/GC suffix [78]).
- [x] [242] Only bet levels from `authenticate`; min and max reachable (interception test 1.00–2.00, Run 2).
- [x] [222] No play request without balance for the real mode cost; message shown (`game/actor.ts` guard).
- [x] Starting bet = `defaultBetLevel`; if `betLevels` is missing, levels follow `minBet`..`maxBet` in `stepBet` steps. (our `Authenticate.svelte`; demo starts at $1.00)
- [x] [273] Sub-cent wins keep their digits ($0.004, $0.012 in `check_amount.ts`). Recheck on Engine with the real levels.
- [x] RGS errors show a player message, never raw JSON: `ERR_VAL`, `ERR_IPB`, `ERR_GLE`, `ERR_ACT` (retried 3× first), `ERR_GEN`, plain 400, 423 paused, 429, no connection. (code: `ModalError.svelte`, `src/overrides/rgsFetcher.ts`; mock tokens `paused`, `act<n>`, `gen`, `gle`) (e2e `tools\e2e\tests\m6c.spec.ts` pass 2026-11-06)
- [x] Per-mode `maxBet` from `config.gameModes`: a mode offers only levels up to its maxBet. (code: `Authenticate.svelte`, `EnableJurisdiction.svelte`; mock token `maxbuy<dollars>`) (e2e `tools\e2e\tests\m6c.spec.ts` pass 2026-11-06)
- [x] Bonus resume: `/bet/event` records each free spin; a reload mid-bonus resumes from it. (code: `src/game/roundProgress.ts`) (e2e `tools\e2e\tests\m6c.spec.ts` pass 2026-11-06)
- [x] `social=true` forces English (`vite.patches.js` lang patch). (e2e `tools\e2e\tests\m6c.spec.ts` pass 2026-11-06)
- [x] Board bottom row clear of the HUD at 1280x720, 1200x675, 400x225, 425x812 (`tools\e2e\tests\shots.spec.ts`, 2026-11-06).
- [x] `prefers-reduced-motion` starts in turbo, unless `disabledTurbo` (`EnableJurisdiction.svelte`; e2e pass 2026-11-06).
- [x] Only `rgs_url` from the query string is called. No other host (`check_external_urls.ps1` exit 0).
- [x] [274] Invalid `rgs_url` shows "Connection problem. Please reload the game." (Run 2).
- [x] [240] Unsupported `lang` (`xx`, `en_US`, empty, `zh`) falls back to English, 0 console errors (`vite.patches.js`).

### Controls
- [ ] Spacebar places a bet, except when `disabledSpacebar`. (code: our `ui/ButtonBet.svelte`)
- [ ] Sound on/off toggle.
- [ ] Autoplay needs explicit confirmation. No one-click consecutive bets.
- [x] Turbo, autoplay and buy-bonus buttons hidden when `disabledTurbo`, `disabledAutoplay`, `disabledBuyFeature` (verified in demo `demo_nobuy_noturbo_noauto` 2026-09-19); space-hold turbo off when `disabledSpacebar` or `disabledTurbo`. Our `ui/UIDefault.svelte`, modals guarded in `GameModals.svelte`, `EnableJurisdiction.svelte` as backstop. In fast play, wins stay legible.
- [x] Fullscreen respects `disabledFullscreen`: N/A, the game has no fullscreen control (`OnPressFullScreen` is only a click area).
- [x] Super turbo respects `disabledSuperTurbo`: N/A, only one turbo speed (`stateBet.svelte.ts` `timeScale` 1 or 2).
- [x] `disabledSlamstop`: Stop does not skip the round; stopping autoplay still works (`ui/ButtonBet.svelte` guard).
- [x] `minimumRoundDuration`: each round waits out the minimum before the next (`game/actor.ts` `onPlayGame`); demo with `minround3000` measured 3,000-3,500 ms between rounds, 2026-10-28. Unit open: PROJECT.md Q14.
- [x] `displaySessionTimer`, `displayNetPosition`, `displayRTP`: `components/JurisdictionHud.svelte` top-left line, hidden unless set; verified in demo 2026-10-28.
- [x] [223] No pinch or double-tap zoom (`app.html` viewport, `touch-action: manipulation`).
- [x] [227] Page never scrolls at 1024×576, 400×225, 800×450, 425×812 (scrollHeight = innerHeight, Run 2).
- [ ] [193][194][195] Works on mobile and in the mini-player: every control usable; mobile WIN label covers the bottom row (fix with the final UI, instruction 19).

### Win presentation
- [ ] Win total counts up to the final payout.
- [ ] Celebration (sound, animation, big-win panel) only when the round pays **more than the total cost**. A 100x buy returning 80x shows a plain "80x". (code: `presentedWinLevel` in `bookEventHandlerMap.ts`; test with star `win_below_cost` story)
- [ ] Anticipation (slow reveal) only when a real trigger is possible on the drawn board. No fake near-miss.

### Player protection (ours)
- [ ] No prompts to chase losses or raise the bet after a loss.
- [ ] No countdowns, streak rewards, or "almost won" messages.
- [ ] RTP and rules reachable in one tap from the main screen.
- [ ] [217] No child-like art. Mature theme.

### Social casino (URL `social=true` or `jurisdiction.socialCasino`)
- [x] [77] No restricted term in our text (demo `social=true`: rules screen scanned, 0 hits). The full list (about 40 phrases, e.g. bet, buy, pay, paid, stake, cash, money, credit, currency, fund, purchase, wager, gamble, deposit, withdraw, "cost of", "win feature", "bonus buy") and replacements are in `src/game/wording.ts`, applied by `t()` in the rules screen, bet-mode texts and `ModalError.svelte`.
- [x] [77][225] Shared SDK labels use social words too (PLAY, PLAY BONUS, PLAY MENU, SELECT YOUR PLAY), also when social comes from `jurisdiction.socialCasino` (`vite.patches.js` i18n patches; Run 2). Recheck on Engine: PROJECT.md §11 Q12.

### Replay
- [x] [171][172] Query params `replay`, `game`, `version`, `mode`, `event`, `rgs_url` load `GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}`; `amount`, `currency`, `lang`, `social` honoured, bad values fall back (Run 2).
- [ ] Loader while fetching; the round starts from a Play button (SDK loader and "press anywhere" start seen in demo; check against Engine's replay page). A clear message when replay data fails to load: verified ("This replay could not be loaded."). (code: error path in our `Authenticate.svelte`)
- [x] [174] No authenticated calls in replay (demo: only `GET /bet/replay/...`). Real cost and multiplier shown: "TOWER BONUS ×400 · €2.00 · REAL COST €800.00" (`ui/UIReplay.svelte`).
- [x] [173] Replay can be watched again (REPLAY button, twice in Run 2).
- [x] [188] No restricted words in replay with `social=true`.
- [x] [243] Replay fits at 400×225.
- [ ] Betting disabled in replay. No path from replay to real play except "Play Again".

### Assets
- [x] [275] No Stake Engine loader (removed in instruction 01).
- [ ] [253] No web-sdk sample art or Stake branding. (placeholder sample art in use — replace at M6, instructions 14–16)
- [x] No external requests: `scripts\check_external_urls.ps1` exits 0 on the build. (code: Typekit link removed, `webfontloader` aliased to a stub, Inter font bundled under OFL, sample S3/twist-game.app URLs stripped at build)
- [ ] [217][253] Original design, no copied IP. Unique audio and visuals.
- [ ] Game tile: `GameTitle-BG` (background) + `GameTitle-FG.png` (transparent foreground) ≤3 MB combined, plus transparent `Provider-Logo.png`; high-res PNG/JPG.

### Submission
- [ ] Short blurb: theme and mechanics.
- [ ] Game finalized: no debug UI, no console noise, version number shown (`package.json` version via `GameVersion`).

### Reviewer event IDs (fill at M6)

| Mode | Loss | Normal win | Big win | Bonus trigger | Max win |
|---|---|---|---|---|---|
| base | | | | | |
| omen | | | | | |
| prophecy | | | | | |
| star | n/a | | | n/a | |
| tower | n/a | | | n/a | |

## Verify

All boxes checked. Any unchecked box → PROJECT.md §11 row with owner.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://stake-engine.com/docs/approval-guidelines | stateless, math frozen, no sample assets | 2026-09-19 |
| https://stake-engine.com/docs/rgs | currency table, sub-cent win decimals, resume via `/bet/event` | 2026-11-06 |
| https://stake-engine.com/docs/rgs/wallet | response codes, `gameModes[].maxBet` | 2026-11-06 |
| https://stake-engine.com/docs/approval-guidelines/front-end-communication | disclosure, controls, win count-up | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/game-replay-requirements | replay | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/game-tile-requirements | tile | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements | child appeal, social-casino words | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/rgs-communication | bet levels, `minStep`, static files only, `rgs_url`, `lang` fallback | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/submission-checklist | blurb, finalized game (public part only; full list login-gated) | 2026-09-19 |
| https://stake-engine.com/docs/rgs/wallet | `disabledTurbo`, `socialCasino`, `disabledFullscreen` | 2026-09-19 |
| https://studio.engine.io/docs-content/prompt.md | guideline IDs `[NNN]` used by reviewers and the AI review | 2026-10-28 |
| https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-14-responsible-product-design | no celebrating returns ≤ stake, no loss-chasing design | 2026-09-19 |
