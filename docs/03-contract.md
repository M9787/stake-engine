# 03 — Contract (math ↔ web)

## Purpose

Only file that couples math and web. Every BookEvent in the books must have a handler in `web-sdk\apps\seventh-veil\src\game\bookEventHandlerMap.ts`.

## Prereq

[01-math-sdk.md](01-math-sdk.md) outputs, [02-web-sdk.md](02-web-sdk.md) app layout.

## Steps (data flow)

1. RGS `/wallet/play` returns one book. `book.events` = ordered BookEvents.
2. The frontend plays each BookEvent in order through `bookEventHandlerMap`.
3. Each handler updates state and broadcasts EmitterEvents (`eventEmitter.broadcast` / `broadcastAsync`).
4. Components react via `eventEmitter.subscribeOnMount()`.

Event order = game behavior.

### Seventh Veil BookEvent table

Handler column = base `apps/cluster` behavior we forked. **ours** = written for Seventh Veil in `game\web\seventh-veil\src\game\bookEventHandlerMap.ts`. All handlers exist (`books_to_stories.py --check` → no missing handlers). Bonus intros no longer show the cluster global-multiplier orb.

| BookEvent | Emitted by (math) | Key fields | EmitterEvents (cluster base) |
|---|---|---|---|
| `reveal` | draw board | `board`, `gameType`, `anticipation` | `stopButtonEnable`, `soundScatterCounterClear`, `tumbleWinAmountReset` |
| `winInfo` | cluster win | `wins[]{symbol, clusterSize, win, positions, meta{clusterMult}}` | `showClusterWinAmounts`, `soundOnce` |
| `updateTumbleWin` | after win | `amount` | `tumbleWinAmountShow`, `tumbleWinAmountUpdate` |
| `tumbleBoard` | tumble | new symbols, exploded positions | `tumbleBoard*`, `boardSettle`, `soundOnce` |
| `updateGrid` | grid change (base + bonus) | `gridMultipliers[7][7]`: 0 empty, 1 sigil, ≥2 charged | `multiplierGridShow`, `multiplierGridUpdate` |
| `bonusVariant` | bonus start | `variant`: `star` \| `tower` | **ours**: sets `stateGame.bonusVariant` (intro/frame skin per variant: M6 art) |
| `freeSpinTrigger` | bonus trigger | `totalFs`, `positions` | intro + counter + `transition`, `uiHide/uiShow` |
| `freeSpinRetrigger` | retrigger | `totalFs` | counter update, intro |
| `updateFreeSpin` | each bonus spin | `amount`, `total` | `freeSpinCounterShow`, `freeSpinCounterUpdate` |
| `freeSpinEnd` | bonus end | `amount`, `winLevel` | outro count-up, `transition` |
| `setTotalWin` | round total | `amount` | state only |
| `setWin` | win panel | `amount`, `winLevel` | `winShow`, `winUpdate`, `winHide` — **ours**: `presentedWinLevel` celebrates only if win > mode cost ([08](08-compliance.md)); same in `freeSpinEnd` |
| `wincap` | 77,777x reached | `amount` | **ours**: sets `stateGame.veilTorn`; next win panel shows max level as "THE VEIL TEARS" |
| `finalWin` | round end | `amount` | grid/multiplier hide |
| `createBonusSnapshot` | frontend only | `bookEvents` | resume a bonus after reload |

Cluster-base handler `updateGlobalMult` stays for compatibility; Seventh Veil math does not emit it.

## Mock RGS

`game\web\seventh-veil\dev\mockRgs.js` answers the calls the SDK makes (`rgs-requests/src/rgs-requests.ts`), under `/rgs` on the dev server. Amounts are API units (1,000,000 = $1, `constants-shared/bet.ts`).

| Call | Request | Mock response |
|---|---|---|
| `POST /wallet/authenticate` | `sessionID`, `language` | `balance {amount, currency}`, `config {betLevels, defaultBetLevel, minBet, maxBet, stepBet, gameModes [{mode, costMultiplier, maxBet}], jurisdiction (all 12 flags)}`, open `round` if any |
| `POST /wallet/play` | `sessionID`, `mode` (any case), `currency`, `amount` | debits `amount × mode cost` (all modes); `round {roundID, amount, payout, payoutMultiplier, costMultiplier, active, mode, event, state}`; `ERR_IPB` if balance is short, `ERR_VAL` for unknown mode, bet level not offered, bet above the mode's maxBet, a round already open, or buy while `disabledBuyFeature`. Session tokens force errors: `paused` (423, no body), `act<n>` (429 `ERR_ACT` n times), `gen` (500 `ERR_GEN`), `gle` (`ERR_GLE`) |
| `POST /wallet/end-round` | `sessionID` | credits payout, `balance`; `ERR_VAL` if no round is open |
| `POST /mock/force` | `sessionID`, `next` | next play in that session uses the forced book of the played mode: `maxwin`, `bonus`, `loss`, `win`, `big` (`.mock-rgs/<mode>.json` `forced`, from `scripts\books_to_mock.py`; buy modes have no `loss`). Unknown key: random draw |
| `POST /mock/reset` | `sessionID` | forgets the session (fresh balance, no open round) |
| `POST /bet/event` | `sessionID`, `event` | `{event}`; stored as `round.event` (the game sends the book event index of each free spin) |
| `GET /bet/replay/{game}/{version}/{mode}/{event}` | round ID as `event` | `{amount, payout, payoutMultiplier, costMultiplier, state}`; 404 `ERR_BNF` if unknown |

Malformed JSON gets a plain-text `400 Bad Request`, like the RGS.

Real-RGS points still unverified (need an Engine account): mode-name case matching (PROJECT.md §11 Q9), whether the client or server multiplies buy-mode cost.

## Verify

- `scripts\math_stats.py seventh_veil` prints `event_types` per mode. Every type must be in the table above.
- M5: diff that set against the keys of `bookEventHandlerMap.ts`. Diff must be empty.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://github.com/engineio/web-sdk/blob/main/apps/cluster/src/game/bookEventHandlerMap.ts | cluster handlers + EmitterEvents | 2026-09-19 |
| https://github.com/engineio/web-sdk/blob/main/apps/cluster/src/game/typesBookEvent.ts | cluster BookEvent types | 2026-09-19 |
| https://github.com/StakeEngine/math-sdk/blob/main/src/events/event_constants.py | math event names | 2026-09-19 |
