# 10 — Jurisdiction flags

**Goal:** The game obeys every jurisdiction flag the RGS sends in `authenticate`, so operators in strict regions can run it.

**Why:** The flags exist in the SDK config schema, but nothing in our game reads them. Audit 2026-10-28: a grep found no use outside `stateConfig` and the schema. Rules: https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements (2026-10-28).

**Depends on:** 02.

## Flags to support
| Flag | What the game must do |
|---|---|
| `minimumRoundDuration` | One round, from bet to result, lasts at least this long. Turbo and space-hold cannot make it shorter. |
| `displayRTP` | Show RTP in the rules only when true. |
| `displaySessionTimer` | Show the elapsed session time. |
| `displayNetPosition` | Show net win or loss for the session. |
| `disabledSlamstop` | Hide or disable stopping the reels early. |
| `disabledSuperTurbo` | Hide super turbo. |
| `disabledTurbo`, `disabledAutoplay`, `disabledBuyFeature` | Already handled in `ui/UIDefault.svelte` (Q4, closed). Re-check that they still work. |

## Steps
1. Find the exact flag names in the SDK schema: `Select-String -Path web-sdk\packages -Pattern 'minimumRoundDuration|displaySessionTimer|displayNetPosition|disabledSlamstop|disabledSuperTurbo|displayRTP' -Recurse`. Use only names that exist there (CLAUDE.md rule).
2. Read them from `stateConfig` in our code. Add a small `JurisdictionHud.svelte` for the session timer and net position.
3. `minimumRoundDuration`: wait before `endRound` / unlock until the duration has passed.
   - `src\game\actor.ts` uses shared machines. Add the wait in our book handler that finishes the round, or wrap the machine with a local copy.
   - Space-hold forces turbo (`EnableSpaceHold.svelte:11`). The minimum duration must still apply.
4. Add a jurisdiction switch to the mock RGS (`dev\mockRgs.js`) so each flag can be tested.

## Done test
- With each flag set in the mock, the matching behaviour is visible.
- With `minimumRoundDuration=3000`, 10 rounds under space-hold each take ≥3 s, measured from the request timestamps in the Network tab.
