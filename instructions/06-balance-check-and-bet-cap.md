# 06 — Balance check and bet cap

**Goal:** No play request is sent when the balance is below the full cost. This covers Space hold, autoplay and bonus buys. On low balance the bet snaps to the highest valid bet level.

**Why:**
- Guideline [222]: no play request when balance < bet, including space bar, autoplay and bonus buys (https://studio.engine.io/docs-content/prompt.md, 2026-10-28).
- Guideline [242]: bets step only through `betLevels`.

**Depends on:** 02.

## Current problems (audit 2026-10-28)
- `web-sdk\packages\utils-xstate\src\createIntermediateMachineBet.ts:8-18`: `checkSpaceHold` loops back to `fetching` without calling `isBetCostAvailable()`. Autoplay does check (`createIntermediateMachineAutoBet.ts:17`).
- `isBetCostAvailable` ignores the buy cost (`stateBet.svelte.ts:62`). `ButtonBet` stays enabled with a buy mode active even when the balance is too low.
- `correctBetAmount` (`stateBet.svelte.ts:24-31`) caps the bet at `balance/cost`, which is not a bet level. The RGS will likely answer `ERR_VAL`.

## Steps
1. Add a Vite transform for `createIntermediateMachineBet.ts`. In `checkSpaceHold`, stop instead of fetching when the full cost is not available.
2. Add a Vite transform for `stateBet.svelte.ts`:
   - `isBetCostAvailable` uses the full cost of the active mode (amount × mode cost, buys included).
   - `correctBetAmount` picks the highest `betLevels` entry whose full cost fits the balance. If none fits, it keeps the lowest level and disables the button.
3. Show the existing "insufficient balance" message through `t()`. Task 07 adds the social wording.
4. Test with a low mock balance. Find the balance setting in `web-sdk\apps\seventh-veil\dev\mockRgs.js`.

## Done test
Check each case in the browser Network tab:
- Balance 0.50, bet 1.00: holding Space sends **no** `/wallet/play` request.
- Balance 50, Star buy (100x) at bet 1.00: the buy is blocked.
- Balance 3.40: the bet snaps to the highest level that fits, and the mock RGS accepts it.
