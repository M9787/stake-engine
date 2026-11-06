# PROJECT — Oracle of Sevens

Source of truth. Other files link here and never restate goals, pins, or modes.
Brief: [docs/_original-brief.txt](docs/_original-brief.txt), [game_description](game_description). Rules for agents: [CLAUDE.md](CLAUDE.md).

## 1. Goal

Ship **Oracle of Sevens** to Stake Engine: a mystic-tarot 7x7 cluster-tumble slot with a charged multiplier grid, 5 frozen bet modes, and a 77,777x max win.
Player-visible name is Oracle of Sevens (Studio: team `dumalex`, game `oracle-of-sevens` on studio.engine.io). Internal ids keep the working name `seventh_veil` / `seventh-veil`.
Our code lives in `core\` (one math core, one web app) and game data in `skins\<skin>\` (tracked here). `scripts\sync.ps1` copies the core into the SDK clones and generates one shim and one `build\<gameId>\web` data folder per skin.

DONE test: game approved on Engine (≥6/9 review points) and live; target 3★, because only 3★ games enter New Releases, Slots and Burst Games ([docs/00](docs/00-platform.md) steps 11–12).

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
| pixi.js (direct dep of the core app) | 8.8.1, same version pixi-svelte locks; added 2026-11-07 | runtime bitmap fonts from the skin font (`src\slots\fonts.ts`, plan v3.3 10.6b); no new download |
| web-sdk clone | `1843d60cedb94b390e641b563f32ad64353bec5e` | SDK pin; upgrade only on a branch + full golden gate (docs/10) |
| math-sdk clone | `307e6812b38489e212f835001f21e9f7d4c18a4d` | SDK pin; same rule |
| @playwright/test | 1.65.0 (own `tools\e2e\package.json` + lockfile, pnpm) | e2e gate: book replay, errors, maxBet, resume, social, screenshots (docs/10 M6c/M6e) |
| jsonschema (Python) | 4.26.0 in `math-sdk\env` | game-definition validation (`tools\gamedef\validate.py`, docs/10 M7) |
| Math run pins | `PYTHONHASHSEED=0`, zstandard 0.23.0, 10 threads, batching 50,000 | reproducible books (docs/07 Determinism) |
| Asset pipeline (`.venv-assets`) | Pillow 13.0.0, numpy 2.5.4, rembg 2.0.86, onnxruntime 1.31.1; ffmpeg 8.1.1 full_build (gyan.dev, winget) | byte-stable ingest, contact sheet, audio (docs/10 v3.3 slice 0); recorded as found 2026-11-07, no install |

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
├─ core/        math\cluster_tumble · web\cluster-tumble (one app) · schema\ · assets\ (slot catalogue) — edit here
├─ skins/       <skin>\game.json, text\, math\{reels,lookups}, assets.json, art_in\ (ignored) — data only
├─ tools/       gamedef · gen · golden · assets · e2e · web_build.ps1 (all take --game / -Game)
├─ build/       generated per game (ignored): web\ ($skin target), dist\, prompts.html, contact sheets
├─ game/        math\seventh_veil — frozen hand-written math reference for tools\golden (do not edit)
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
| M3b | Math final | base "win > cost" ≥ 8%; production run (100k sims in every mode, since task 11 2026-10-28) passes M3 | done (base win > cost 25.3% after the M5b rebalance; docs/07 Results) |
| M4 | Frontend fork, placeholder art | `pnpm run build --filter=seventh-veil` makes `index.html` | done |
| M5 | Contract + storybook + compliance core | `books_to_stories.py --check` empty; storybook plays base/star/tower books | done; open items in docs/08 |
| M5b | Balance + local play + hardening | `math_stats.py --sessions`: all modes pass, base hit ≥23%, base median session ≥300 spins; `check_external_urls.ps1` exit 0; demo server plays 1 round per mode | done except browser rounds for omen/prophecy/star/tower (their charges and books checked against the mock API only). Base hit 25.3%, median 338 spins; URL check exit 0; base rounds, max win, jurisdiction, social and replay played in the browser 2026-09-19 |
| M6a | Baseline + determinism | GitNexus re-indexed; SDK SHAs and math wall time per mode recorded; `snapshot.py --verify` gives the same books hash twice (PYTHONHASHSEED=0, sims only); skin-alias spike loads an asset from outside `web-sdk\` in dev, build and Storybook | done 2026-11-06: books identical across 2 runs (docs/07 Determinism); spike passed dev, build and Storybook with 6 rules for M10 (docs/10) |
| M6b | Final math retune, then freeze | `math_stats.py --json`: RTP 0.9635–0.9665 all modes, 0 failed classes, Engine critical tests pass, star median ≥ Q28 target; weights frozen, golden lock written | done 2026-11-06: all modes RTP 0.965, 0 failed classes, critical PASS, star median 64.1x (Q28 ~60x); weights in `skins\oracle-of-sevens\math\lookups`; star_precharge_value split proven output-neutral (40 files IDENTICAL); `golden.lock.json` written; FE config, contract check, mock data regenerated |
| M6c | Compliance code | `check_amount.ts` (BTC, USDT, XRC, WRW, DKK, NOK, PLN, IDR, sub-cent) exit 0; e2e: current error codes, maxBet per mode, `/bet/event` resume, social EN, no HUD overlap | done 2026-11-06: `check_amount.ts` OK 97 checks (85 Engine currencies); e2e 14/14 (errors 423/500/ERR_GLE, ERR_ACT retry, maxBet per mode, bonus resume via `/bet/event`, social EN, reduced motion, 4 screen sizes) |
| M6d | Original art, audio, bundle | no sample assets (`check_sample_assets.ps1` exit 0); build ≤10 MB; first spin ≤4 s on Fast 4G; provenance with human edit per asset; art sign-off | |
| M6e | Verification | e2e replay of loss/win/big/bonus/max in all 5 modes; screenshots at reviewer sizes + Popout; docs/08 all `[x]`; reviewer IDs filled; AI review 0 FAIL | |
| M6f | Package, staging, submit | Studio plays 1 round per mode; tile + cover; golden lock in `skins\oracle-of-sevens`; tag `seventh_veil-v1.0.0`; submitted | |
| M7–M11 | Core extraction (Phase B) | Oracle rebuilt from `core\` + `skins\oracle-of-sevens` with identical books and config; `gate.ps1 -Game seventh_veil` and `-Game zz_smoke` exit 0 | M7 done 2026-11-06: schema `core\schema\game-definition.v1.schema.json`; `skins\oracle-of-sevens\game.json` + `text\en.json`; `validate.py` 0 errors (11 broken cases caught); `compare_config.py` IDENTICAL (config + optimizer setup + reshape). M8 done 2026-11-07: core in `core\math\cluster_tumble`, shims via `sync.ps1`; `quick_books.py` 320/320 identical; full shim run with frozen weights gives `snapshot.py --verify` IDENTICAL (40 files) against `golden.lock.json` and byte-identical `math_stats --json` (docs/07 "Core rebuild"). M9 done 2026-11-06 except the M10-dependent part: every generator takes `--game` (`tools\gamedef\gamectx.py` maps id to paths); `gen_rules.py` + `gen_skin_ts.py` write `build\<id>\web\`; `check_generated.py` 5/5 current; config.ts, stories and mock byte-identical; `game.json theme` drives `assets_build.py` |
| M12–M17 | Factory editor (Phase C) | a non-developer builds `zz_smoke` in under 2 h; game #2 passes all gates and is submitted | |

Plan v3.3 (2026-11-07, docs/10 end section) re-sequences: Slice 0 (asset catalogue + prompts) → M10 rest → M11 → M6d (CLI ingest) → M6e → M6f submit → M12–M17 during Oracle's review.

Plan for M6a–M17: [docs/10-factory-plan.md](docs/10-factory-plan.md) — Phase A (Oracle state of the art), B (core + skins), C (factory editor). Cadence after M17: 1 game per 2 weeks for 8 weeks, then weekly.

## 7. Commands

Run from `stake\` in PowerShell.

| Intent | Command |
|---|---|
| Check env | `powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1` |
| Copy game code into SDKs | `powershell -ExecutionPolicy Bypass -File scripts\sync.ps1` |
| Build math | `Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location` (since M8 a generated shim: core + `skins\oracle-of-sevens\game.json`; switches `CT_SKIP_SIMS`, `CT_SKIP_OPT`, `CT_REUSE_WEIGHTS`, `CT_MODES`, old `SV_*` names still work) |
| Validate a game definition | `math-sdk\env\Scripts\python.exe tools\gamedef\validate.py skins\oracle-of-sevens\game.json` |
| Core config = hand-written config | `math-sdk\env\Scripts\python.exe tools\golden\compare_config.py seventh_veil` |
| Core books = hand-written books (fast, in memory) | `Push-Location math-sdk; $env:PYTHONHASHSEED='0'; .\env\Scripts\python.exe ..\tools\golden\quick_books.py seventh_veil 20; Pop-Location` |
| No skin literals in core | `math-sdk\env\Scripts\python.exe tools\lint_core.py` |
| Verify math | `math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief --sessions` |
| Retune optimizer only (reuse books) | `$env:SV_SKIP_SIMS='1'; $env:SV_MODES='star'; Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location; Remove-Item Env:SV_SKIP_SIMS, Env:SV_MODES` |
| Build math, sims only (no optimizer) | `$env:PYTHONHASHSEED='0'; $env:SV_SKIP_OPT='1'; Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location; Remove-Item Env:PYTHONHASHSEED, Env:SV_SKIP_OPT` |
| Build math with frozen weights | `$env:PYTHONHASHSEED='0'; $env:SV_REUSE_WEIGHTS="$PWD\skins\oracle-of-sevens\math\lookups"; Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location; Remove-Item Env:PYTHONHASHSEED, Env:SV_REUSE_WEIGHTS` |
| Asset prompts (owner sheet) | `math-sdk\env\Scripts\python.exe tools\assets\prompts.py --game <id>` → `build\<id>\prompts.html` + `prompts.json` · `--check` lints prompts (exit 1 on a problem) |
| Asset drop check / contact sheet / art sign-off | `.venv-assets\Scripts\python.exe tools\assets\check_art_in.py --game <id> [--gate]` · `.venv-assets\Scripts\python.exe tools\assets\contact_sheet.py --game <id> [--sign "<name>"]` |
| Ingest owner assets into a skin | `.venv-assets\Scripts\python.exe tools\assets\ingest.py --game <id> --all` (or `--slot <slotId> [<file>]`; `--force`) → `skins\<skin>\assets\`, `tiles\`, `audio\`, `assets.lock.json`; then `scripts\sync.ps1 -Game <id>` |
| Skin slot manifest / static folder | `math-sdk\env\Scripts\python.exe tools\gen\gen_assets_ts.py --game <id>` · `... tools\gen\gen_web_static.py --game <id> [--check]` (both run by `sync.ps1`) |
| Snapshot math hashes / verify | `math-sdk\env\Scripts\python.exe tools\golden\snapshot.py seventh_veil --write <file>` · `... --verify <file>` (exit 1 on any difference) |
| Math → web config | `math-sdk\env\Scripts\python.exe scripts\gen_fe_config.py [--game <gameId>]` |
| Skin → web data (`build\<id>\web\`) | `math-sdk\env\Scripts\python.exe tools\gen\gen_rules.py --game <gameId>` · `... tools\gen\gen_skin_ts.py --game <gameId>` |
| Generated files current (exit 1 if stale) | `math-sdk\env\Scripts\python.exe tools\gen\check_generated.py --game <gameId>` |
| Books → stories + contract check | `math-sdk\env\Scripts\python.exe scripts\books_to_stories.py [--game <gameId>] [--check]` |
| Web install | `Push-Location web-sdk; pnpm install; Pop-Location` |
| Demo data + HTTPS cert (once per math change) | `math-sdk\env\Scripts\python.exe scripts\books_to_mock.py [--game <gameId>]; powershell -ExecutionPolicy Bypass -File scripts\dev_cert.ps1` |
| Demo play, 1,000 USD balance (port 3007) | `$env:GAME='<gameId>'; Push-Location web-sdk\apps\cluster-tumble; pnpm run dev:demo`, open `https://localhost:3007/?sessionID=demo&rgs_url=localhost:3007/rgs&lang=en` |
| Storybook (port 6007) | `$env:GAME='<gameId>'; Push-Location web-sdk\apps\cluster-tumble; pnpm run storybook` |
| Dev against a real RGS session (port 3007) | `$env:GAME='<gameId>'; Push-Location web-sdk\apps\cluster-tumble; pnpm exec vite dev --port 3007` |
| Build (one game at a time) | `powershell -ExecutionPolicy Bypass -File tools\web_build.ps1 -Game <gameId>` → `build\<gameId>\dist` |
| Workspace packages (fresh checkout, before the first build) | `Push-Location web-sdk; pnpm exec turbo run build --filter="cluster-tumble^..." --no-daemon; Pop-Location` |
| Install order (any web install) | `Push-Location web-sdk; pnpm install; Pop-Location` → `scripts\sync.ps1` (mirrors the lockfile to `core\web\pnpm-lock.yaml`) → `scripts\doctor.ps1` |
| e2e gate (starts dev server with mock RGS) | `$env:GAME='<gameId>'; Push-Location tools\e2e; pnpm exec playwright test; Pop-Location` |
| Screenshot baselines (deterministic frames) | verify: `$env:GAME='<gameId>'; Push-Location tools\e2e; pnpm exec playwright test baseline; Pop-Location` · capture: add `--update-snapshots` (owner-approved re-baseline only) |
| Currency check | `node --experimental-strip-types scripts\check_amount.ts` |
| No external URLs in build | `powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1 [-Game <gameId>]` |

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
| Q1 | ~~Account and checklist~~ closed 2026-10-28: team `dumalex` exists; checklist, RTP band (96.0–96.7%) and mode limit (≤20) read in Studio docs | — | no |
| Q2 | Push this repo (with `game\`) to your own GitHub for backup | project owner | M6 |
| Q3 | ~~Ante-mode value~~ closed 2026-09-19: retuned (omen base RTP 0.30 → 0.40) and worded honestly in rules and dialogs | — | no |
| Q4 | ~~Jurisdiction buttons~~ closed 2026-09-19: our `ui/UIDefault.svelte` hides turbo/autoplay/buy; verified in demo (`demo_nobuy_noturbo_noauto`) | — | no |
| Q5 | Replay link: the SDK keeps no round/event ID in state, so the game cannot build a "copy replay link". Replay mode itself works (verified with mock `/bet/replay`). Confirm on Engine whether its UI provides the link | project owner | M6 |
| Q6 | ~~Engine caps~~ closed 2026-10-28: one limit set for every game — RTP 96.0–96.7%, max payout 100,000× (77,777× passes), exposure $50M and bet cost $500k at 0 failed classes; penalty schedule in [docs/07](docs/07-math-spec.md) — studio.engine.io/docs math-verification | — | no |
| Q7 | Tarot theme regional review risk | project owner | M6 |
| Q8 | ~~External URLs~~ closed 2026-09-19: Typekit removed, `webfontloader` stubbed, Inter (OFL) bundled, sample URLs stripped; `check_external_urls.ps1` exit 0 | — | no |
| Q9 | RGS mode names are lower case (`base`), web keys upper case (`BASE`), as in the SDK samples. Confirm RGS matching is case-insensitive | project owner | M6 |
| Q10 | ~~Upload limit~~ closed 2026-09-19: ≤4.2 GB per books file, ≤10M events per mode; ours max 352.7 MB (tower, 100k sims, 2026-10-28) | — | no |
| Q11 | Buy-mode charging: the client multiplies only `activate` modes; the mock charges `amount × cost` for all modes. Confirm the real RGS does the same for buy modes | project owner | M6 |
| Q12 | Social mode: shared SDK labels outside our code (buy-bonus dialog texts) may still use restricted words; our texts (rules, mode dialogs, error messages) go through `t()`. Check on Engine with `social=true` | agent | M6 |
| Q13 | Once during demo testing the bet read $10 instead of $1 before a forced round; not reproduced in 7 later spins. Watch for it in M6 testing | agent | no |
| Q14 | `jurisdiction.minimumRoundDuration` unit is not in the Engine docs (schema `rgs-fetcher/src/schema.ts` says `number`). `stateSession.svelte.ts` reads it as ms (values under 100 as seconds). Confirm with Engine support or a staging session that sets it | agent | M6 |
| Q15 | Engine "Maximum Std Dev (any mode) 60.0" does not say if std is divided by the mode cost. Raw std: star 212, tower 444 (fail if raw); per cost 2.1 / 1.1. `math_stats.py` passes on std ÷ cost. If raw, Volatility is 1 failed class: exposure $25M. Confirm in Studio readiness after math upload | agent | M6 |
| Q17 | ~~Oracle math~~ closed 2026-11-06: one final UX retune (M6b), then freeze | — | no |
| Q18 | ~~Art gate~~ closed 2026-11-06: every asset needs a recorded human edit and a named sign-off; raw AI output blocked, no waiver | — | no |
| Q19 | Approve installs per milestone: Playwright (M6c/d), jsonschema (M7), `@sjsf/form` + ajv (M12) | project owner | closed 2026-11-06: approved, each pinned in §3 before install |
| Q20 | Bundle ≤10 MB and first spin ≤4 s as the core default budget | project owner | M6d |
| Q21 | Languages beyond EN at launch (Engine supports 17; only EN required) | project owner | no |
| Q22 | ~~Originality~~ closed 2026-11-06: each factory game differs from earlier ones on ≥2 mechanic axes + one signature moment | — | no |
| Q23 | ~~Factory modes~~ closed 2026-11-06: §4 frozen modes apply to Oracle; factory games freeze their own modes at approval | — | no |
| Q24 | Hardware for overnight 100k-sim runs (dedicated or this PC) | project owner | M15 |
| Q25 | ~~Cadence~~ closed 2026-11-06: 1 game per 2 weeks for 8 weeks after M17, then weekly | — | no |
| Q26 | Observed Engine review turnaround (sets the real cadence ceiling) | project owner | no |
| Q27 | Seeded copy of the optimizer in `core\` (reproducible weights) vs capture-only weights | project owner | M8 |
| Q28 | ~~Retune targets~~ closed 2026-11-06: star buy median ~60× (now 43×); omen/prophecy get more frequent mid wins (more spins pay above cost), bonus stays the main draw | — | no |
| Q29 | ~~Final asset storage~~ closed 2026-11-07: edited finals tracked in git (≤10 MB per game); raw AI output in `art_in\` (ignored), zipped per Q2 | — | no |
| Q30 | Distribution per factory game. Default: every cluster-tumble game ships Only on Stake; network only for a second core (network forbids reskins, stake-engine.com/docs/distribution) | project owner | M16 |
| Q31 | ~~Human-edit tool~~ closed 2026-11-07: images edited in Photopea; art sign-off in the owner's name | — | no |
| Q32 | ~~Art privacy~~ closed 2026-11-07: Midjourney Pro (Stealth) | — | no |
| Q33 | ~~Spine~~ closed 2026-11-07: Oracle ships with code-driven motion on flat images; Spine stays an optional per-slot upgrade. Audio needs licence + source only (no human edit) | — | no |
| Q16 | ElevenLabs self-serve **music** terms exclude "Studio Games"; whether its **sound effects** terms allow a commercial online slot on Starter is not confirmed. docs/09 uses CC0 SFX until this is closed. Check elevenlabs.io/terms-of-use and the SFX terms, or ask support | project owner | M6 |

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
| https://studio.engine.io/docs/approval-guidelines/math-verification | Non-critical limits: std ≤60, CVaR per-stake ≤700 / absolute ≤50,000, raw P(≥5k/10k/25k/50k/100k) ≤0.05/0.01/0.005/0.001/0.0005, ETL>40× ≤0.9, ETL>10k ≤0.8, sum ≤1.5, absolute sum ≤10,000; 6 failure classes; penalty schedule 0→$50M/$500k … 6→$0.5M/$10k | 2026-10-28 |
| https://studio.engine.io/docs | Platform renamed "Stake Engine" → "Engine" (studio.engine.io, docs under /docs); older stake-engine.com URLs still resolve | 2026-10-28 |
