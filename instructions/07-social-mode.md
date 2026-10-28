# 07 — Social mode (Stake.us)

**Goal:** With `social=true`, or when the jurisdiction sets `socialCasino`:
- no restricted word appears anywhere;
- SC and GC show with no `$`;
- the language is English;
- mode names are clean and the same everywhere.

**Why:**
- Guidelines [77], [78], [225], [188] (https://studio.engine.io/docs-content/prompt.md, 2026-10-28).
- The restricted word list and the common misses ("Bet", "Auto Bet", "Total Bet", and "Buy" on bonus buttons and dialogs) are on https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements (2026-10-28).

**Depends on:** 05.

## Current problems (audit 2026-10-28)
- Shared labels check only the URL (`web-sdk\packages\components-ui-pixi\src\i18n\i18nDerived.ts:7,9`). Our `ButtonBet.svelte:10` imports it.
- `LoadI18n.svelte:31-32` does not force `en`.
- Shared ui-html still has "BET MENU", "SELECT YOUR BET" and "INSUFFICIENT FUNDS … ADD FUNDS".
- The `LabelBet` label is not social-safe.
- `game\src\game\wording.ts:51` `isSocial()` exists, but only our own texts use it.

## Steps
1. Make one source of truth: `isSocial()` in `wording.ts` returns true for `?social=true` **or** `jurisdiction.socialCasino`.
2. Add a Vite transform on both shared `i18nDerived.ts` files (ui-pixi and ui-html) so their social switch calls our `isSocial()`.
3. Give every shared label a social replacement taken from the jurisdiction page. Examples: bet → "Play", bet amount → "Play amount", buy bonus → "Get bonus", funds → "Coins".
4. Force `en` when social, in the local `LoadI18n` from task 05.
5. Check that no mode name, internal or player-visible, contains: buy, bet, pay, stake, wager, cash, money, credit, purchase, deposit, withdraw.
6. Grep the build: `Select-String -Path web-sdk\apps\seventh-veil\build\index.html -Pattern '\b(bet|buy|wager|cash|money|credit|purchase|deposit|withdraw|stake)\b' -AllMatches`. Each hit must be code or sit behind the social switch.

## Done test
- Run demo play with `&social=true&currency=XSC`, then again with the mock jurisdiction set to `socialCasino`.
- Open every screen: main, rules, buy dialog, autoplay, replay, insufficient balance. None shows a restricted word.
- The balance shows "SC" with no `$`.
- Screenshots are saved to `docs\screens\social-*.png`.
