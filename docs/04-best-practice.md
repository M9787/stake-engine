# 04 — Best practice

## Purpose

Rules that keep the environment reproducible and the game approvable.

## Prereq

[00-platform.md](00-platform.md), [03-contract.md](03-contract.md).

## Steps (rules)

### Environment
1. Pin exact versions (PROJECT.md §3). Run `scripts\doctor.ps1` before work.
2. Use the SDK's own package manager version (corepack reads `packageManager`).
3. Keep secrets out of git. Copy `.env.example` to `.env`; `.env` is ignored.

### Math
4. Change math only in `math-sdk\games\seventh_veil` (never the `0_0_*` originals). Re-run simulation after every change.
5. Never hand-edit books or lookup tables. Regenerate them.
6. `payoutMultiplier` in lookup CSV must equal books — upload rejects mismatch.

### Frontend
7. Change only `web-sdk\apps\seventh-veil`. Shared `packages\` stay upstream-clean.
8. One handler per BookEvent type. New math event type → add row to docs/03 first, then the handler.
9. Read `rgs_url` from the URL. Never hardcode RGS host.
10. Show exact win amounts; small bets need extra decimal precision on wins.
11. Support resume: handle `round.event` from authenticate.

### Process
12. Math and web are separate lifecycles. Coordinate only through docs/03.
13. Unknown → PROJECT.md §11 with owner. Do not guess.
14. Build and test via Developer page before submitting. Incomplete submissions delay review.

## Verify

- `scripts\doctor.ps1` exit code 0.
- `git status` shows no `.env`, `env\`, `node_modules\`, build outputs.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://stake-engine.com/docs/rgs | rules 9–11 | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | rule 6 | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/submission-checklist | rule 14 | 2026-09-19 |
