# Agent instructions — Oracle of Sevens

The agent does these tasks, in number order. Lower number = higher priority.
Each file has: Goal, Why, Depends on, Steps, Done test, Notes.
Human-only tasks are in [../instructions_human](../instructions_human/README.md).

Written 2026-10-28 from a full audit (code, math, Studio docs read while logged in, web research).

## Why this order
1. **Phase A** fixes what reviewers test with fixed checklist IDs. If a check fails, the review stalls.
2. **Phase B** decides the star rating. Only **3★** games appear in New Releases, Slots and Burst Games, so a game needs 3★ to have a real chance of going viral. 2★ is published but hidden from those lists.
3. **Phase C** covers staging and submission.
4. **Phase D** covers launch and growth.

Math, modes and mechanics freeze after approval. So task 11 (math) must be done before 21.

| No. | Task | Phase | Depends on | Status |
|---|---|---|---|---|
| 01 | [Remove Engine loader](01-remove-engine-loader.md) | A | — | done 2026-10-28 |
| 02 | [Run Engine AI review](02-run-engine-ai-review.md) | A | 01 | done 2026-10-28 |
| 03 | [Currency and sub-cent amounts](03-currency-and-sub-cent.md) | A | 02 | done 2026-10-28 |
| 04 | [Mobile zoom and screen sizes](04-mobile-zoom-and-screen-sizes.md) | A | 02 | done 2026-10-28 |
| 05 | [Language fallback](05-language-fallback.md) | A | 02 | done 2026-10-28 |
| 06 | [Balance check and bet cap](06-balance-check-and-bet-cap.md) | A | 02 | done 2026-10-28 |
| 07 | [Social mode](07-social-mode.md) | A | 05 | done 2026-10-28 |
| 08 | [Replay](08-replay.md) | A | 03, 05 | done 2026-10-28 |
| 09 | [Rules and disclaimer](09-rules-and-disclaimer.md) | A | 11 (numbers) | done 2026-10-28 |
| 10 | [Jurisdiction flags](10-jurisdiction-flags.md) | A | 02 | done 2026-10-28 |
| 11 | [Math rework](11-math-rework.md) | A | — | todo |
| 12 | [Docs refresh](12-docs-refresh.md) | A | — | todo |
| 13 | [Track assets and remove dead files](13-track-assets-and-clean.md) | B | — | todo |
| 14 | [Asset spec docs/09](14-asset-spec.md) | B | 13 | todo |
| 15 | [Asset pipeline script](15-asset-pipeline.md) | B | 14 | todo |
| 16 | [Replace sample art with static sprites](16-replace-sample-art.md) | B | 15, human 03 | todo |
| 17 | [Signature moment: multiplier grid](17-multiplier-grid-moment.md) | B | 16 | todo |
| 18 | [Game feel](18-game-feel.md) | B | 16 | todo |
| 19 | [UI skin](19-ui-skin.md) | B | 16 | todo |
| 20 | [Bundle and load time](20-bundle-and-load-time.md) | B | 16–19 | todo |
| 21 | [Build, package, final AI review](21-build-package-review.md) | B | 01–20 | todo |
| 22 | [Staging test on Studio](22-staging-test.md) | C | 21, human 06 | todo |
| 23 | [Submission text](23-submission-text.md) | C | 22 | todo |
| 24 | [Launch kit](24-launch-kit.md) | D | 21 | todo |
| 25 | [After launch](25-after-launch.md) | D | live | todo |

## Rules for every task
- Follow [CLAUDE.md](../CLAUDE.md). Edit game code only in `game\math\seventh_veil` and `game\web\seventh-veil`. Then run `powershell -ExecutionPolicy Bypass -File scripts\sync.ps1`.
- Never edit `web-sdk\packages\*` in place. To change shared code, use one of the three override tools that already exist:
  1. A Vite `transform` plugin (`game\web\seventh-veil\vite.config.js:13-20`, `stripSampleUrls`).
  2. `resolve.alias` (`vite.config.js:31`).
  3. A local copy of the component.
- Run `powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1` before any SDK command.
- After a task: run its Done test, set Status here to `done`, and note the evidence.
