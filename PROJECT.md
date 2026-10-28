# PROJECT — Oracle of Sevens

Source of truth. Other files link here and never restate goals, pins, or modes.
Brief: [docs/_original-brief.txt](docs/_original-brief.txt), [game_description](game_description). Rules for agents: [CLAUDE.md](CLAUDE.md).

## 1. Goal

Ship **Oracle of Sevens** to Stake Engine: a mystic-tarot 7x7 cluster-tumble slot with a charged multiplier grid, 5 frozen bet modes, and a 77,777x max win.
Player-visible name is Oracle of Sevens (Studio: team `dumalex`, game `oracle-of-sevens` on studio.engine.io). Internal ids keep the working name `seventh_veil` / `seventh-veil`.
Our code lives in `game\math\seventh_veil` and `game\web\seventh-veil` (tracked here). `scripts\sync.ps1` copies it into the SDK clones, where it builds and runs.

DONE test: game approved on Stake Engine with ≥2 stars and live. Game Quality Rankings: 1 star = not published (the public checklist's "≥1 star" is outdated).

## 2. Non-Goals

- No stateful mechanics: no cash-out, gamble, continuation, jackpots (Engine rule, [docs/00](docs/00-platform.md)).
- No new or changed modes after approval. The mode set in §4 is frozen at submission.
- No dark patterns. [docs/08](docs/08-compliance.md) is not negotiable.
- No custom backend. No edits to `math-sdk\games\0_0_*` or `web-sdk\packages\*` originals.
- No final art or sound before M6 (placeholder art until then).

DONE test: a task that conflicts with this list is rejected.

## 3. Stack (pinned)

| Tool | Version | Why |
|---|---|---|
| Node | 22.16.0 (via fnm) | web-sdk pin |
| pnpm | 10.5.0 (via corepack) | web-sdk `packageManager` |
| Python | 3.12.9 | math-sdk needs >=3.12 |
| Rust/Cargo | 1.98.1 stable, `x86_64-pc-windows-gnu` override in `math-sdk\optimization_program` | math-sdk optimizer; GNU target avoids the multi-GB MSVC Build Tools install |
| Svelte / PixiJS / TurboRepo | 5 / 8 / from lockfile | web-sdk |

DONE test: `scripts\doctor.ps1` exits 0 (Node, pnpm, Python required; Rust version shown as WARN if different).

## 4. Modes (frozen)

| Mode | Player sees | Cost | Type | Target RTP |
|---|---|---|---|---|
| `base` | Fate: Veil | 1x | spin | 96.50% |
| `omen` | Fate: Omen (more bonuses) | 1.25x | spin, `is_feature` | 96.50% |
| `prophecy` | Fate: Prophecy (most bonuses) | 2x | spin, `is_feature` | 96.50% |
| `star` | Star bonus | 100x | `is_buybonus` | 96.50% |
| `tower` | Tower bonus | 400x | `is_buybonus` | 96.50% |

Max win 77,777x in every mode. Every base pay is at least 1.2x. Base hits 25% of spins; a 100-bet balance lasts a median ~340 spins. Design: [docs/06](docs/06-game-design.md). Math targets and results: [docs/07](docs/07-math-spec.md).

## 5. Repo Layout

```
stake/
├─ PROJECT.md, CLAUDE.md, .env.example
├─ game/        math\seventh_veil, web\seventh-veil — our code; edit here only
├─ scripts/     doctor.ps1 · sync.ps1 · math_stats.py · gen_fe_config.py · books_to_stories.py
│             books_to_mock.py · dev_cert.ps1 · check_external_urls.ps1
├─ docs/        00 platform · 01 math · 02 web · 03 contract · 04 practice · 05 publish
│               06 design · 07 math spec · 08 compliance · _archive/
├─ math-sdk/    clone of StakeEngine/math-sdk (own git, ignored here) — builds our math
└─ web-sdk/     clone of engineio/web-sdk (own git, ignored here) — builds our frontend
```

## 6. Milestones

Open work, scored and prioritized: [TODO.md](TODO.md).

| # | Milestone | DONE test | State |
|---|---|---|---|
| M0 | Toolchain | `scripts\doctor.ps1` exit 0 | done |
| M1 | SDKs cloned, math venv | `Test-Path math-sdk\env, web-sdk\apps\cluster` both True | done |
| M2 | Math prototype | `publish_files\` has index.json + 5 books + 5 lookup CSVs | done |
| M3 | Math tuned (prototype) | `math_stats.py`: all modes RTP 0.9635–0.9665, 3-star fails empty | done |
| M3b | Math final | base "win > cost" ≥ 8%; production run (100k spin / 50k buy sims) passes M3 | done (base win > cost 25.3% after the M5b rebalance; docs/07 Results) |
| M4 | Frontend fork, placeholder art | `pnpm run build --filter=seventh-veil` makes `index.html` | done |
| M5 | Contract + storybook + compliance core | `books_to_stories.py --check` empty; storybook plays base/star/tower books | done; open items in docs/08 |
| M5b | Balance + local play + hardening | `math_stats.py --sessions`: all modes pass, base hit ≥23%, base median session ≥300 spins; `check_external_urls.ps1` exit 0; demo server plays 1 round per mode | done except browser rounds for omen/prophecy/star/tower (their charges and books checked against the mock API only). Base hit 25.3%, median 338 spins; URL check exit 0; base rounds, max win, jurisdiction, social and replay played in the browser 2026-09-19 |
| M6 | Final art, no external URLs, tile, publish | docs/08 all `[x]` (incl. original art, zero external URLs in build, tile ≤3 MB); Developer page plays 1 round per mode; reviewer IDs filled | next |

## 7. Commands

Run from `stake\` in PowerShell.

| Intent | Command |
|---|---|
| Check env | `powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1` |
| Copy game code into SDKs | `powershell -ExecutionPolicy Bypass -File scripts\sync.ps1` |
| Build math | `Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location` |
| Verify math | `math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief --sessions` |
| Retune optimizer only (reuse books) | `$env:SV_SKIP_SIMS='1'; $env:SV_MODES='star'; Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location; Remove-Item Env:SV_SKIP_SIMS, Env:SV_MODES` |
| Math → web config | `math-sdk\env\Scripts\python.exe scripts\gen_fe_config.py` |
| Books → stories + contract check | `math-sdk\env\Scripts\python.exe scripts\books_to_stories.py [--check]` |
| Web install | `Push-Location web-sdk; pnpm install; Pop-Location` |
| Demo data + HTTPS cert (once per math change) | `math-sdk\env\Scripts\python.exe scripts\books_to_mock.py; powershell -ExecutionPolicy Bypass -File scripts\dev_cert.ps1` |
| Demo play, 1,000 USD balance (port 3007) | `Push-Location web-sdk\apps\seventh-veil; pnpm run dev:demo`, open `https://localhost:3007/?sessionID=demo&rgs_url=localhost:3007/rgs&lang=en` |
| Storybook (port 6007) | `Push-Location web-sdk\apps\seventh-veil; pnpm run storybook` |
| Dev against a real RGS session (port 3007) | `Push-Location web-sdk; pnpm run dev --filter=seventh-veil` |
| Build | `Push-Location web-sdk; pnpm run build --filter=seventh-veil; Pop-Location` |
| No external URLs in build | `powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1` |

Details and expected output: [docs/01](docs/01-math-sdk.md), [docs/02](docs/02-web-sdk.md).

## 8. Contract

Books → `bookEventHandlerMap` → EmitterEvents. Event types: `reveal`, `winInfo`, `updateTumbleWin`, `tumbleBoard`, `updateGrid`, `bonusVariant`, `freeSpinTrigger`, `freeSpinRetrigger`, `updateFreeSpin`, `freeSpinEnd`, `setTotalWin`, `setWin`, `wincap`, `finalWin` (+ frontend-only `createBonusSnapshot`). Every type has a handler. Full table: [docs/03](docs/03-contract.md).

## 9. Test Strategy

1. Math: `math_stats.py` — RTP band, 3-star limits, books↔lookup payout match, max win.
2. Contract: `books_to_stories.py --check` — book event types ⊆ handler keys.
3. Frontend: storybook replays loss, win, big win, bonus (star, tower) and max win for base, star, tower (no omen/prophecy stories). Demo play (`dev:demo`) runs real rounds against the mock RGS.
4. Compliance: [docs/08](docs/08-compliance.md) checklist, run before every submission.

## 10. Definition of Ready (for M6)

- [x] M0–M5 core done
- [x] Game code tracked in `game\` (not only in upstream clones)
- [x] Storybook runs on Windows (node wrapper sets `PUBLIC_CHROMATIC`)
- [x] No external URLs in the build (`scripts\check_external_urls.ps1` exit 0)
- [x] Local demo play with a balance (mock RGS)
- [ ] Original art and sound (sample art is rejected)
- [ ] Stake Engine account → §11 Q1

## 11. Open Questions

| # | Question | Owner | Blocking? |
|---|---|---|---|
| Q1 | Create Stake Engine account; read login-gated checklist; confirm RTP range and mode-count rules | project owner | M6 |
| Q2 | Push this repo (with `game\`) to your own GitHub for backup | project owner | M6 |
| Q3 | ~~Ante-mode value~~ closed 2026-09-19: retuned (omen base RTP 0.30 → 0.40) and worded honestly in rules and dialogs | — | no |
| Q4 | ~~Jurisdiction buttons~~ closed 2026-09-19: our `ui/UIDefault.svelte` hides turbo/autoplay/buy; verified in demo (`demo_nobuy_noturbo_noauto`) | — | no |
| Q5 | Replay link: the SDK keeps no round/event ID in state, so the game cannot build a "copy replay link". Replay mode itself works (verified with mock `/bet/replay`). Confirm on Engine whether its UI provides the link | project owner | M6 |
| Q6 | ~~Engine caps~~ closed 2026-09-19: max cost ≤2,000×, max win ≤500,000×; bet-level template set by exposure (2-star tier $15M / $100k bet cost) — studio.engine.io/docs math-verification | — | no |
| Q7 | Tarot theme regional review risk | project owner | M6 |
| Q8 | ~~External URLs~~ closed 2026-09-19: Typekit removed, `webfontloader` stubbed, Inter (OFL) bundled, sample URLs stripped; `check_external_urls.ps1` exit 0 | — | no |
| Q9 | RGS mode names are lower case (`base`), web keys upper case (`BASE`), as in the SDK samples. Confirm RGS matching is case-insensitive | project owner | M6 |
| Q10 | ~~Upload limit~~ closed 2026-09-19: ≤4.2 GB per books file, ≤10M events per mode; ours max 164 MB | — | no |
| Q11 | Buy-mode charging: the client multiplies only `activate` modes; the mock charges `amount × cost` for all modes. Confirm the real RGS does the same for buy modes | project owner | M6 |
| Q12 | Social mode: shared SDK labels outside our code (buy-bonus dialog texts) may still use restricted words; our texts (rules, mode dialogs, error messages) go through `t()`. Check on Engine with `social=true` | agent | M6 |
| Q13 | Once during demo testing the bet read $10 instead of $1 before a forced round; not reproduced in 7 later spins. Watch for it in M6 testing | agent | no |
| Q14 | `jurisdiction.minimumRoundDuration` unit is not in the Engine docs (schema `rgs-fetcher/src/schema.ts` says `number`). `stateSession.svelte.ts` reads it as ms (values under 100 as seconds). Confirm with Engine support or a staging session that sets it | agent | M6 |

## 12. Sources

| URL | Proves | Checked |
|---|---|---|
| https://stake-engine.com/docs/approval-guidelines | stateless rule, no mode/math change after approval, no external sources | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/front-end-communication | UI disclosure, autoplay, spacebar, sound rules | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/game-replay-requirements | replay mode | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/jurisdiction-requirements | no child appeal, social-casino vocabulary | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | index.json, lookup CSV, books format | 2026-09-19 |
| https://stake-engine.com/docs/rgs | RGS flow, money units | 2026-09-19 |
| https://stake-engine.com/ | revenue: 10% GGR or 7.5% expected GGR | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/submission-checklist | full login-gated checklist (incl. no Stake Engine loader) | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/game-quality-rankings | 1 star = not published; AI-asset and shallow-gameplay risks | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/math-verification | critical/non-critical math tests, file limits, bet-level templates | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/general-disclaimer | required rules disclaimer text | 2026-09-19 |
| https://github.com/StakeEngine/math-sdk | math SDK, `0_0_cluster` base, 3-star limits in `utils/rgs_verification.py` | 2026-09-19 |
| https://github.com/engineio/web-sdk | web SDK (moved from StakeEngine/web-sdk), `apps/cluster` base | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/game-quality-rankings | 0–3★ in thirds from 3 reviewers; publish needs ≥6/9 points; fail locks the thread 3 days; only 3★ in New Releases/Slots/Burst; New Releases ordered by team 30-day Insights rank | 2026-10-28 |
| https://studio.engine.io/docs/approval-guidelines/math-verification | one limit set: RTP 96.0–96.7%, max payout 100,000×, exposure $50M, bet cost $500k; penalty schedule by failed classes; max win more frequent than 1 in 10M; 100k–1M sims; intermediate wins expected | 2026-10-28 |
| https://studio.engine.io/docs/ai-review | Engine review prompt, run locally, same guideline IDs as reviewers | 2026-10-28 |
| https://studio.engine.io/docs-content/prompt.md | guideline IDs ([181]…[275]), reviewer sizes 1024×576/400×225/800×450/425×812, test currencies USD EUR CAD MXN JPY XSC XGC | 2026-10-28 |
| https://studio.engine.io/docs/promote | promotion channels: X, Stake followers (~30% email open), giveaways, Stake Challenges ticket, streamer rev-share, Watchtowr, promoteonstake.com | 2026-10-28 |
| https://stake-engine.com/docs/distribution | Only on Stake 10% GGR vs network 5%+5%; fixed at launch | 2026-10-28 |
| https://stake-engine.com/docs/payments | payout 1st of month, USDT/USDC ERC-20, new wallet waits 3 days | 2026-10-28 |
| https://stake-engine.com/docs/approval-guidelines/game-tile-requirements | Media Editor, 3:4 and 16:9, no added words or multipliers on art | 2026-10-28 |
| https://studio.engine.io/teams/dumalex/games/oracle-of-sevens/approval | Readiness: no tile, no cover, math and front not published, 0/1 reviews | 2026-10-28 |
