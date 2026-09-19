# 08 — Compliance and ethics

## Purpose

Rules the game must meet before submission. Engine rules come from the approval guidelines. Ethics rules are ours; they also match UK and GLI standards. None are negotiable.

## Prereq

[06-game-design.md](06-game-design.md), [07-math-spec.md](07-math-spec.md).

## Steps (checklist — run before every submission)

Status 2026-09-19: `[x]` verified, `[ ]` open. `(code)` = implemented, not yet verified on screen.

### Math
- [x] Every mode passes `scripts\math_stats.py`: RTP 0.9635–0.9665, 3-star limits empty, books match lookup.
- [x] Every mode has at least one max-win book (reviewer event ID).
- [ ] Math frozen. No change after approval.

### Disclosure (UI)
- [ ] RTP of the game and of each mode shown. (code: `GameInfo.svelte` rules screen)
- [ ] Max win of each mode shown. (code: rules screen + bet-mode dialogs)
- [ ] Cost of each mode shown before purchase. (code: rules screen; SDK buy dialog shows price)
- [ ] Every symbol pay and every multiplier value (x2 … x1024) shown in the paytable. (code: pays from generated `config.ts`)
- [ ] Bonus trigger rules (3–4 balls = Star, 5+ = Tower) shown. (code)

- [ ] Button guide: what each button does. (code: `GameInfo.svelte` "Buttons" table)
- [ ] Ante and buy trade-offs stated plainly: ante wins often return less than the spin price; a bonus can pay less than its price. (code: rules screen + bet-mode dialogs)

### Bets and balance (RGS)
- [x] Balance shown, formatted per currency. (SDK `LabelBalance`; USD verified in demo, other currencies at M6)
- [ ] Every bet level from `authenticate` selectable; min and max reachable. (SDK bet menu)
- [x] Starting bet = `defaultBetLevel`; if `betLevels` is missing, levels follow `minBet`..`maxBet` in `stepBet` steps. (our `Authenticate.svelte`; demo starts at $1.00)
- [ ] Wins at the smallest bet show enough decimals (1.2x of the lowest level). Check on Engine with the real levels.
- [ ] RGS errors show a player message, never raw JSON: `ERR_IPB`, `ERR_IS`, `ERR_ATE`, `ERR_GLE`, `ERR_VAL`. (code: our `ModalError.svelte`)
- [ ] Only `rgs_url` from the query string is called. No other host.
- [ ] Text does not break when an unsupported `lang` is passed (English fallback).

### Controls
- [ ] Spacebar places a bet, except when `disabledSpacebar`. (code: our `ui/ButtonBet.svelte`)
- [ ] Sound on/off toggle.
- [ ] Autoplay needs explicit confirmation. No one-click consecutive bets.
- [x] Turbo, autoplay and buy-bonus buttons hidden when `disabledTurbo`, `disabledAutoplay`, `disabledBuyFeature` (verified in demo `demo_nobuy_noturbo_noauto` 2026-09-19); space-hold turbo off when `disabledSpacebar` or `disabledTurbo`. Our `ui/UIDefault.svelte`, modals guarded in `GameModals.svelte`, `EnableJurisdiction.svelte` as backstop. In fast play, wins stay legible.
- [ ] Fullscreen respects `disabledFullscreen`.
- [ ] Works on mobile and in the mini-player.

### Win presentation
- [ ] Win total counts up to the final payout.
- [ ] Celebration (sound, animation, big-win panel) only when the round pays **more than the total cost**. A 100x buy returning 80x shows a plain "80x". (code: `presentedWinLevel` in `bookEventHandlerMap.ts`; test with star `win_below_cost` story)
- [ ] Anticipation (slow reveal) only when a real trigger is possible on the drawn board. No fake near-miss.

### Player protection (ours)
- [ ] No prompts to chase losses or raise the bet after a loss.
- [ ] No countdowns, streak rewards, or "almost won" messages.
- [ ] RTP and rules reachable in one tap from the main screen.
- [ ] No child-like art. Mature theme.

### Social casino (URL `social=true` or `jurisdiction.socialCasino`)
- [x] No restricted term in our text (demo `social=true`: rules screen scanned, 0 hits). The full list (about 40 phrases, e.g. bet, buy, pay, paid, stake, cash, money, credit, currency, fund, purchase, wager, gamble, deposit, withdraw, "cost of", "win feature", "bonus buy") and replacements are in `src/game/wording.ts`, applied by `t()` in the rules screen, bet-mode texts and `ModalError.svelte`.
- [ ] Shared SDK labels: bet button reads "SPIN" and buy button "PLAY BONUS" when `social=true` (SDK `i18nDerived`). Other shared labels ("BET" amount label, buy dialogs) still use gambling terms → PROJECT.md §11 Q12.

### Replay
- [ ] (SDK built-in) Query params `replay`, `game`, `version`, `mode`, `event`, `rgs_url` load `GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}`. Also honour `amount`, `currency`, `lang`, `social`.
- [ ] Loader while fetching; the round starts from a Play button (SDK loader and "press anywhere" start seen in demo; check against Engine's replay page). A clear message when replay data fails to load: verified ("This replay could not be loaded."). (code: error path in our `Authenticate.svelte`)
- [x] No authenticated calls in replay (demo: only `GET /bet/replay/...`). Bet cost, payout and win shown.
- [ ] Betting disabled in replay. No path from replay to real play except "Play Again".

### Assets
- [ ] No web-sdk sample art or Stake branding. (placeholder sample art in use — replace at M6)
- [x] No external requests: `scripts\check_external_urls.ps1` exits 0 on the build. (code: Typekit link removed, `webfontloader` aliased to a stub, Inter font bundled under OFL, sample S3/twist-game.app URLs stripped at build)
- [ ] Original design, no copied IP. Unique audio and visuals.
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
| https://stake-engine.com/docs/approval-guidelines/front-end-communication | disclosure, controls, win count-up | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/game-replay-requirements | replay | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/game-tile-requirements | tile | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements | child appeal, social-casino words | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/rgs-communication | bet levels, `minStep`, static files only, `rgs_url`, `lang` fallback | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/submission-checklist | blurb, finalized game (public part only; full list login-gated) | 2026-09-19 |
| https://stake-engine.com/docs/rgs/wallet | `disabledTurbo`, `socialCasino`, `disabledFullscreen` | 2026-09-19 |
| https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-14-responsible-product-design | no celebrating returns ≤ stake, no loss-chasing design | 2026-09-19 |
