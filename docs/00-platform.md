# 00 — Platform (Stake Engine, RGS)

## Purpose

Facts about the platform the game runs on. Read before 01..05.

## Prereq

None.

## Steps (what the platform does)

1. **Stake Engine** hosts games and the RGS (Remote Game Server). The developer uploads static math files and a frontend build. No developer-run backend.
2. **Math on RGS.** RGS stores pre-simulated rounds ("books"). A play returns one book, picked by lookup-table weights. File format: [01-math-sdk.md](01-math-sdk.md#outputs).
3. **Game URL.** The game loads from the Engine CDN with query params:

   | Param | Meaning |
   |---|---|
   | `sessionID` | player session, required on every request |
   | `lang` | ISO 639-1 language code |
   | `device` | `mobile` or `desktop` |
   | `rgs_url` | RGS base URL — never hardcode, it can change |

4. **RGS API flow.** Call `/wallet/authenticate` on load. Then per round: `/wallet/play` → animate → `/wallet/end-round`. `/wallet/balance` reads balance. Without authenticate, calls fail with `400 ERR_VAL`. A round with no win is closed by `/wallet/play` (`round.active` false); `/wallet/play` during an open round fails with `400 ERR_VAL`.
5. **Resume.** During a multi-step round, `POST /bet/event {sessionID, event}` records progress. On reload, `round.event` in the authenticate response holds the last recorded value.
6. **Money.** Integers with 6 decimal places: `1000000` = 1 unit. Currency affects display only.
7. **Bets.** Bet must lie in `minBet..maxBet` and divide by `stepBet` (from authenticate). Debit = base bet × bet-mode cost multiplier. `config.gameModes` lists `{mode, costMultiplier, maxBet}`: each mode has its own maxBet.
8. **Error codes.** 400: `ERR_VAL`, `ERR_IPB`, `ERR_GLE`. 429: `ERR_ACT` (retry shortly). 500: `ERR_GEN`. Without an `ERR_*` body: plain-text 400 (malformed request), 423 on `/wallet/play` (new bets paused), 429 on demo (IP rate limit).
9. **Stateless only.** Each bet is independent. No jackpots, gamble features, continuation, or early cash-out. Player choices happen before the spin, as bet modes. Math and modes cannot change after approval.
10. **Revenue.** 10% of GGR, or a guaranteed 7.5% of expected GGR, chosen per team.
11. **Approval.** Three reviewers each rate 0–3 stars in thirds (9 points total). A game needs **≥6/9 points** to publish. A failed review locks the thread for 3 days. The platform was renamed **Engine** (studio.engine.io) in Sep 2026.
12. **Shelves.** Only **3★ games** enter the New Releases, Slots and Burst Games sections. New Releases are ordered by the team's 30-day Engine Insights rank.

## Verify

- Each step above maps to a Sources row below.
- Rating rules: Sources row `game-quality-rankings` (2026-10-28).

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://stake-engine.com/docs/rgs | steps 1, 3–7; currency table + CurrencyMeta | 2026-11-06 |
| https://stake-engine.com/docs/rgs/wallet | step 8 response codes; `gameModes`; `/bet/event` | 2026-11-06 |
| https://stake-engine.com/docs/math/math-file-format | step 2 | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines | step 9 | 2026-09-19 |
| https://stake-engine.com/ | step 10 | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/game-quality-rankings | steps 11–12: 3 × 0–3★ in thirds, ≥6/9 to publish, 3-day lock, only 3★ on shelves | 2026-10-28 |
| https://stake-engine.com/docs/approval-guidelines/submission-checklist | step 11 | 2026-09-19 |
| https://github.com/engineio/ts-client | Engine npm client for RGS calls | 2026-09-19 |
