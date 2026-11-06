# Plan v2: Oracle of Sevens → state of the art → Core extraction → Stake Game Factory

## Context

The owner has a Stake Engine account, a logo, a wallet and AI-generated assets. The goal is a "game factory": one verified core plus data-only skins, edited in a local UI, shipping new Stake Engine games on a regular cadence.

Owner decisions (AskUserQuestion, 2026-11-06):
- **Order:** A) polish Oracle of Sevens to state of the art and submit it; B) extract the core, with Oracle as skin #1 and identical output; C) build the factory editor.
- **Core scope:** one mechanic family first: cluster pays, tumble, grid multipliers, free spins, bonus variants, ante and buy modes. Lines/ways come later as a second core behind the same interfaces.
- **Editor:** local web app (SvelteKit on 127.0.0.1, inside this repo). It runs the Python math locally. It must serve **non-developers**.
- **Oracle math:** one final UX retune, then freeze.
- **Art gate:** every asset needs a recorded human edit, plus a named sign-off. Raw AI output is blocked, with no waivers.
- **Originality:** each game needs ≥2 mechanic differences from every earlier factory game, plus one signature moment.
- **Cadence:** 1 game per 2 weeks for the first 8 weeks after the factory is ready (each game adds a module), then weekly.

Why this shape: Stake rates originality. It penalises generic AI art, shallow gameplay and large bundles. Only 3★ games get New Releases placement. Math is frozen after approval. You get 1 open review until the first game is live, then 5, and a failed review locks for 3 days. So the factory is a **mechanic library plus original art direction**, not a reskin mill.

Review history:
- v1 scored 7.6 (product), 6.7 (compliance/math) and 6.6 (engineering).
- v2 applied every finding (tagged [P#], [C#], [E#] for reviewers 1–3) and scored 8.7, 8.2 and 8.2.
- v2.1 applied all round-2 items (tagged "round 2"). Round 3 final scores:

| Reviewer | Score |
|---|---|
| Product / non-dev UX | 8.7 |
| Stake compliance / math | 8.6 |
| Engineering | 8.4 |
| **Mean** | **8.57** |

None of the reviewers reported blockers. Engineering's one residual risk (Vite/SvelteKit serving files outside the workspace root) is now de-risked by an early spike in M6a.

## Research inputs (condensed; full agent reports are in the session)

- **R1, current code.**
  - Math `game\math\seventh_veil` (7 py, 682 LOC) is a fork of `0_0_cluster`.
  - Web `game\web\seventh-veil`: 38 components byte-identical to `apps\cluster`. Skin values are hardcoded in `assets.ts`, `constants.ts`, `winLevelMap.ts`, `sound.ts`, `bookEventHandlerMap.ts`, `betModes.ts:42-68` and `GameInfo.svelte:10-41`; the last two hand-copy math numbers.
  - The `seventh_veil` path is hardcoded in every script. `assets_build.py` output `static\assets\sv\` is not wired in.
  - GitNexus index is broken: "Database file version: 42, Current build storage version: 40".
- **R2, Stake gaps.**
  - P0: sample art/audio still present ("MINING MAYHEM"); `formatAmount.ts` wrong for BTC/USDT/XRC/WRW/DKK/NOK/PLN/IDR; reviewer event IDs empty; never staged; tiles missing.
  - P1: stale error map; `gameModes[].maxBet` ignored; HUD overlaps the bottom row at 1280×720; docs/08 items "code only"; bundle 24 MB.
  - P2: resume, mock divergence, no FE tests, EN only, reduced motion.
- **R3, best practice.**
  - mechanic library
  - one JSON-Schema game definition driving generators and forms (`@sjsf/form`, MIT)
  - Stake critical tests as hard gates
  - provenance ledger
  - AssetPack/Howler pipeline
  - book-replay e2e
  - license audit (no copyleft)
  - manual submission
- **Verified math facts.**
  - Sims are seeded per sim (`math-sdk\src\state\state.py:88-93`).
  - Output depends on `num_threads`, `batching_size` and thread×repeat concatenation (`write_data.py:139-145`).
  - Force-key sets become lists in string-hash order (`write_data.py:69-75`).
  - The `fixed_amt` path is unseeded (`run_sims.py:191-193`).
  - The Rust optimizer is non-deterministic: `thread_rng()` at `main.rs:537,950,1502,1553`, plus rayon. docs/07:128 shows run-to-run variance.
  - `executables.py:74,83` indexes `freespin_triggers[gametype][count]` directly; Oracle's keys stop at 8.
  - `math_stats.py:24-47` has only non-critical limits.

## 1. Architecture (v2: one app per core, not a copy per game) [E1, E2, E3]

```
stake\
├─ core\                         # tag core-vX.Y.Z
│  ├─ schema\game-definition.v1.schema.json      # JSON Schema 2020-12; x-range / x-frozen / x-unit / plain descriptions
│  ├─ presets\volatility\{low,medium,high}.json  # targets + ConstructParameters (full and "preview" reduced)
│  ├─ presets\templates\{oracle_like,compact_6x6}.game.json
│  ├─ math\cluster_tumble\       # gamestate, calculations, executables, events, config_builder.py,
│  │                             # optimization_builder.py, run_core.py, features\{grid_multiplier,precharge,
│  │                             # bonus_variants,buy_floor,retrigger,ante_modes}.py
│  ├─ web\cluster-tumble\        # ONE SvelteKit app; skin via $skin alias; src\compliance\, src\features\<module>\,
│  │                             # sdk-adapter\vite.patches.js (fail-loud, kept)
│  └─ CONTRACT.md                # events per module + 12 jurisdiction flags + endRound note
├─ skins\<game_id>\              # DATA ONLY
│  game.json  text\en.json  text\en.social.json  math\reels\*.csv  math\lookups\*.csv (frozen weights)
│  art_in\ audio_in\ fonts\ tiles\  provenance.csv  golden.lock.json  .history\  releases\<ver>.manifest.json
├─ tools\                        # all take --game <id>; old scripts\ paths become wrappers
├─ factory\                      # SvelteKit editor (own package.json + lockfile), 127.0.0.1
├─ build\<game_id>\              # generated, git-ignored: game.resolved.json, web\ ($skin target), reports\, jobs\, dist\
└─ release\<game_id>\<ver>\      # git-ignored except manifest.json + submission.md; zipped to backup
```

**Web.**
- `core\web\cluster-tumble` syncs to `web-sdk\apps\cluster-tumble\`. That is one app and one lockfile entry, so a new game causes no lockfile churn.
- `svelte.config.js` extends the shared `config-svelte`, which returns a plain object (`web-sdk\packages\config-svelte\index.js:5-15`), with `kit.alias['$skin'] = <repo>\build\<GAME>\web`. No package edits.
- Static assets come from the skin [E round 2 #1]: `kit.files.assets = <repo>\build\<GAME>\web\static` in the app's `svelte.config.js`.
- Vite dev server: add `server.fs.allow: [repoRoot]` in `core\web\cluster-tumble\vite.config.js`. `stake\build\` sits outside the `web-sdk` workspace root, and Vite blocks it by default. Same place as today's aliases, `vite.config.js:31-39`.
- Build (PowerShell): `$env:GAME='seventh_veil'; Push-Location web-sdk; pnpm --filter cluster-tumble exec vite build; Pop-Location`. This bypasses turbo, because `turbo.json` does not hash `GAME` and its cache would be stale.
  - adapter-static writes to the app's `build\` for every game, so `package.ps1` immediately moves the output to `build\<id>\dist`.
  - Never build two games at the same time.
- Storybook: the app's `.storybook\main.ts` spreads the shared config (`config-storybook\src\main.ts:4,10`) and adds two things. Story globs are paths, not Vite aliases, so `$skin/...` would not work.
  - a story glob `path.relative('.storybook', '<repo>\build\<GAME>\web\stories') + '/**/*.stories.svelte'`
  - `build\<GAME>\web\static` appended to `staticDirs`
- All three (assets, `fs.allow`, Storybook) are part of the M10 exit.

**Math.**
- Core syncs to `math-sdk\games\core_cluster_tumble\`.
- Each game gets a thin shim, `math-sdk\games\<id>\{game_config.py, run.py, reels\}`. In `game_config.py`: `from games.core_cluster_tumble.config_builder import build; GameConfig = build("<id>")`.
- The shim is needed because `output_filenames.py:25` and `rgs_verification.py:324-326` resolve `games.<game_id>`. No edits to `0_0_*`.
- `build("<id>")` must return a **class**, not an instance. `rgs_verification.py:328` calls `getattr(module, "GameConfig")`, and `run.py:41` calls `GameConfig()` [E round 2 #2].
- M8 rewrites the core's bare imports (e.g. `gamestate.py:1-2` `from game_override import …`) as package imports (`games.core_cluster_tumble.*`). `games\__init__.py` exists, and the editable `.pth` covers it.

**SDK upgrade.**
- Pin SHAs in PROJECT.md §3. `vite.patches.js` already fails loudly (`:105-107`).
- To upgrade: branch, bump the SHA, build, then run the full gate against every golden. `sdk.lock.json` and `UPSTREAM.md` are cut [P8, E11].

**Git.**
- `main` holds core plus skins.
- Tags: `core-vX.Y.Z` and `<game>-v<ver>` when packaging.
- The manifest records both tags, both SDK SHAs and the pins.
- An approved game is rebuilt with `git worktree add ..\<game>-v<ver> <tag>` [E9].
- **Disk:** Oracle `library\` is about 1 GB. After the golden lock, zip `publish_files` to `release\` and back it up (Q2). Delete `optimization_files` [E10].

## 2. CORE vs SKIN boundary

| Class | Lives in | Skin can edit | Frozen at approval |
|---|---|---|---|
| Game loop, cluster eval, tumble, event emission, RNG call order | core math | no | — |
| Feature module code (grid doubling, precharge, variant select, buy floor, retrigger, ante) | core math + web features | on/off + params | — |
| Feature params (grid cap, scope, precharge spots/value per variant, scatter→variant map, fs counts, buy floor) | `game.json features` | yes, within x-range | math |
| Board 5–8 × 5–8; symbols (H/L/S/W, tiers); paytable bands + pays + minPay | `game.json` | yes | math |
| Reel strips | `skins\<id>\math\reels` or `reels.generate{weights,length,seed}` | yes | math |
| Modes: name (= web key = replay name) [C6], cost, kind, variant, quotas | `game.json modes[]` | yes | math |
| Math targets per mode: RTP 96.0–96.7, hit rate, bonus 1-in-N, max win ≤100,000×, mid-win lift, buy shape | `game.json math` + preset | yes | math |
| Optimizer internals (ConstructParameters) | core presets | preset choice | math |
| Frozen weights | `skins\<id>\math\lookups` | written by "Freeze math" only | math |
| Compliance (replay, social, currency, errors, jurisdiction flags, maxBet, lang fallback, disclaimer, autoplay/>2× confirm, Space, resume) | core web `compliance\` | no | — |
| Texts (name, symbol names, mode titles, rules prose with `{placeholders}`, win-level names) | `skins\<id>\text\*.json` | yes; lint: no literal numbers, restricted words | visual |
| Theme, presentation timings, win-level thresholds, sound-slot mapping, art/audio/fonts, tiles | `game.json` + skin folders | yes (sound slots fixed by core) | visual |
| Budgets (bundle ≤10 MB, tex ≤5, audio ≤2.5, JS ≤1.5) | core default | tighten only | — |
| Generated (config.ts, skin.generated.ts, rules.generated.json, stories, mock, game.resolved.json) | `build\` | never | — |

**Enforcement** (trimmed [E11]):
- `tools\lint_skin.py` checks an extension allowlist: no `.ts/.js/.svelte/.py/.css` under `skins\`.
- The schema sets `additionalProperties:false`.
- `tools\lint_core.py` fails on skin literals in `core\`: `seventh`, `oracle`, `star`, `tower`, palette hex.
- ESLint `no-restricted-imports`: skin data may only come through `$skin/*`.
- `tools\gen\check_generated.py` regenerates and diffs.
- `mathLocked:true` in the release manifest makes `tools\gamedef\diff.py` refuse changes to `x-frozen:math` fields.

## 3. GameDefinition v1 and semantic validation

**Fields:**
- `schemaVersion`
- `core{family,version}`
- `identity{gameId,displayName,version}`
- `board{reels,rows}`
- `symbols[]{id,tier|role,nameKey}`
- `paytable{bands,pays,minPay}`
- `reels`
- `features{gridMultiplier, bonusVariants[]{id,scatterMin,scatterMax,spins,precharge{spots,value},buyFloor}, retrigger}`
- `modes[]{name,cost,kind,variant,quotas?,scatterTriggers}`
- `math{rtp,wincap,preset,targets{<mode>}, sims, run{threads,batching}}`
- `theme`, `presentation`, `audio.map`, `text`
- `review{signatureMoment, originality[], artSignoff}`

**`tools\gamedef\validate.py`** returns plain-language messages that the editor shows next to the field. It checks:
- Every symbol is paid and appears on a reel.
- The top paytable band equals reels×rows [C4].
- `freespin_triggers` has a key for **every** scatter count from the minimum up to reels×rows [C4].
- Variant scatter ranges are disjoint and reachable.
- Mode names [C6, round 2]:
  - ≤32 chars, `[A-Za-z0-9_-]`, unique ignoring case.
  - Checked against the **full** social restricted-phrase list from `wording.ts` (~35 phrases, including stake, cash, wager, buy, bet, pay). This always applies, because mode names are shared between social and normal play.
  - cost ≥1.
- Cheapest mode cost = 1.0 [C3].
- wincap ≤100,000.
- `fixed_amt` is forbidden [C2].
- Quotas [C5, round 2]:
  - Quotas set pool composition, not probabilities. Oracle deliberately over-samples winners: `q_zero` 0.45 vs a 75% zero-win probability.
  - Explicit quotas are allowed. When a template omits them, a derived default is used as a heuristic only.
  - **Hard rule:** a minimum book count per criterion at the chosen sim count (e.g. wincap ≥100 books at 100k sims, ≥10 at 10k preview).
  - **Hard rule:** target hit rate ≤ share of paying books in the pool.
- Text placeholders resolve.

## 4. Determinism and frozen weights [C1, C2, E4]

- **Books are reproducible under pins.** Pins: `PYTHONHASHSEED=0`, Python 3.12.9, zstandard 0.23.0, fixed `threads`/`batching`. `snapshot.py` sorts force-option lists and compares *decompressed* books. All pins go into `golden.lock.json` and the manifest.
- **Weights are not reproducible**, because the optimizer is non-deterministic. So weights are **captured, not recomputed**:
  - The candidate run is done 2–3× and the owner keeps the best report.
  - "Freeze math" copies `publish_files\lookUpTable_*_0.csv` into `skins\<id>\math\lookups\` and records the sha in `golden.lock.json`.
  - From then on `CT_REUSE_WEIGHTS=1` is mandatory, and no gate re-runs cargo.
  - Each gate checks that the lookup payout column equals the regenerated books (Engine's publish hash rule).
- **Open question Q27:** may we keep a seeded optimizer copy in `core\math\optimizer_seeded\`? It would be built from the pinned math-sdk SHA, not by editing `math-sdk\`. That would make weights reproducible. Default if unanswered: capture.
- **Wincap hang guard:** `run_core.py` wraps the run with a max-repeat abort. The preview tier runs a "wincap reachable" smoke test first [C4].

## 5. Phase A — Oracle state of the art + submit-ready (≈16 agent-days + owner art)

First, edit PROJECT.md: §6 M6a–M6f replace M6. §3 pins Playwright and the SDK SHAs.

**M6a. Baseline + determinism (2d)** [E4]
1. Run `node .gitnexus/run.cjs analyze`.
2. Record SDK SHAs: `git -C web-sdk rev-parse HEAD; git -C math-sdk rev-parse HEAD`.
3. Record wall time per mode (sims and optimizer separately) in docs/07.
4. Add env switches to `game\math\seventh_veil\run.py` first [C round 2 #1]:
   - `SV_SKIP_OPT`: `run.py:34` currently hardcodes `"run_optimization": True`.
   - `SV_REUSE_WEIGHTS`: copies the frozen `lookUpTable_*_0.csv` into `publish_files` **before** the second `generate_configs` (`run.py:57-61`), so `index.json` and `config_fe` reflect the frozen weights.
   - `snapshot.py` asserts `sys.flags.hash_randomization == 0`.
   - `snapshot.py` records `num_threads` and `batching_size`, and `--verify` compares them. Book order depends on them (`write_data.py:139-145`).
5. Run the determinism proof:
   ```
   $env:PYTHONHASHSEED='0'; $env:SV_SKIP_OPT='1'
   Push-Location math-sdk; .\env\Scripts\python.exe games\seventh_veil\run.py; Pop-Location
   math-sdk\env\Scripts\python.exe tools\golden\snapshot.py seventh_veil --write build\seventh_veil\det1.json
   ```
   Run it again with `--verify`.
6. **Skin-alias spike (0.5d, throwaway branch)** [E round 3]:
   - In a scratch copy of the app, point `kit.files.assets` and one `$skin` import at `stake\build\spike\`, and add `server.fs.allow`.
   - Run dev, build and Storybook once.
   - This proves the Phase B web approach early, before M10 depends on it.
- Exit: identical books hash; the spike loads an asset from outside `web-sdk\` in dev, build and Storybook. If the hash differs, find the cause before anything else.

**M6b. Final retune, then freeze (2–3d)**
- Raise the star median (now 43× on a 100× buy) and the omen/prophecy value through `BUY_SHAPES` / `SPIN_TARGETS` / `MID_WIN_LIFT` (`game_optimization.py:12-39`).
- Split `star_precharge_value`. This is output-neutral, which M6a's hash proves.
- Add Stake **critical tests** to `math_stats.py` [C3]:
  - cheapest mode = 1.0×
  - raw std ≥0.6 for every 1.0× mode (at cost 1.0, raw std equals std per unit of cost)
  - max win ≤1,000,000×
  - cost ≤50,000×
- Add soft gates: hit rate ≥1 in 50, non-paying share, single-book dominance, mid-range gaps.
- Add a `--json` output.
- Commands: PROJECT.md §7 "Build math", then `math-sdk\env\Scripts\python.exe scripts\math_stats.py seventh_veil --brief --sessions --json`, `scripts\gen_fe_config.py`, `scripts\books_to_stories.py --check`.
- Exit:
  - RTP 0.9635–0.9665 in every mode
  - 0 failed classes; critical tests pass
  - star median ≥ the target the owner picks at the M6b review
  - docs/07 updated
- Then freeze: copy the weights and write the golden lock.

**M6c. Compliance code (4d)**

| Gap | Fix | Verify |
|---|---|---|
| Currency | Port Engine's CurrencyMeta into `formatAmount.ts`. **Win decimals per bet level** [C7, round 2]: decimals = max(2, decimals needed to show `bet × minPay` exactly), capped at the currency's maximum. This only goes above 2 for base bets below $0.10. Balance stays 2 dp. | `node --experimental-strip-types scripts\check_amount.ts`, with BTC/USDT/XRC/WRW/DKK/NOK/PLN/IDR and sub-cent cases |
| Errors | `ModalError.svelte`: current codes are `ERR_VAL/IPB/GLE` (400), `ERR_ACT` (429, retry with backoff), `ERR_GEN` (500), plain-text 400, 423 paused, plus a generic fallback. Drop `ERR_IS/ATE/LOC/MAINTENANCE`. Fix `docs/00-platform.md:24,28` [C8] | `tools\e2e\errors.spec.ts` |
| maxBet | Read `gameModes[].maxBet` from the raw authenticate response, matching mode names case-insensitively. Cap bet levels per mode. Mock returns `gameModes` | e2e + staging check |
| Resume | Implement `/bet/event`: store the last processed bookEvent index (≤32 bytes) and resume from `round.event`. Raised from P2 [C10] | e2e: reload mid-bonus resumes |
| Social | Force EN when `social=true`. Restricted-phrase scan covers UI labels and the replay window [C9] | e2e DOM scan |
| HUD overlap, reduced motion, mock parity (reset session, plain replay 404, ERR_ACT, 423) | — | e2e + bbox check |

**M6d. Art, audio, feel, bundle (5d agent + owner sittings)**
- Instructions 16–20.
- Wire `static\assets\sv\` into `assets.ts`. Remove MINING MAYHEM and the mining fonts.
- Fill `provenance.csv` (batch rows: tool, model, prompt file, human edit, licence, sha). Each asset needs a human-edit entry (owner decision).
- Owner signs art direction.
- Omen/prophecy stories: fix `books_to_stories.py:25`.
- Install Playwright (pinned) in `tools\e2e\`.
- Add `tools\check_sample_assets.ps1`: sha256 against `web-sdk\apps\cluster\static\**`, plus a "MINING" text scan.
- Exit:
  - build ≤10 MB
  - first spin ≤4 s on Fast 4G with 4× CPU throttle
  - `check_external_urls.ps1` exits 0; sample-asset check exits 0
  - Q16 closed, or CC0 SFX used

**M6e. Verification (3d)**
- `tools\e2e\replay.spec.ts` replays loss/win/big/bonus/max for all 5 modes. It checks that the final win equals the book payout and that there are 0 console/network errors.
- Screenshots at 1200×675, 400×225 and 425×812, plus the in-game **Popout S/L** [C9].
- Also run `social=true` and an unsupported `lang`.
- docs/08 "(code)" items become `[x]` with evidence.
- `tools\pick_event_ids.py` reuses `categorize()` from `books_to_stories.py:57` and fills the reviewer IDs.
- Run the Engine AI review.
- Exit: docs/08 all `[x]` except Engine-only items; AI review shows 0 FAIL.

**M6f. Package, staging, submit (1d + owner)**
- Instructions 21–23.
- Tiles via Studio "Media" [C11].
- Publish math, then FE. Use Studio "Play Game" for 1 round per mode.
- Close Q2/5/7/9/11/12/14/15.
- Golden lock:
  ```
  math-sdk\env\Scripts\python.exe tools\golden\snapshot.py seventh_veil --write skins\oracle-of-sevens\golden.lock.json
  ```
- Tag `seventh_veil-v1.0.0`.
- Submit (manual).

## 6. Phase B — core extraction, Oracle = skin #1 (≈20 agent-days; overlaps Oracle review)

First, edit CLAUDE.md and PROJECT.md explicitly [E5]:
- `CLAUDE.md:12`: §7 gains the `tools\` commands.
- `:28-29`: pin jsonschema in §3 before M8.
- `:31`: edit `core\` and `skins\`, then `scripts\sync.ps1 -Game <id>`.
- `:32`: add to the generated list: `skin.generated.ts`, `rules.generated.json`, `game.resolved.json`, mock, stories.
- `:33`: "§4 frozen modes = Oracle; factory games freeze at mathLocked".
- PROJECT.md `:10` and §5 layout.
- `.gitignore`: add `build/`; `release/**` except `manifest.json` and `submission.md`; `skins/*/art_in/` and `skins/*/audio_in/` raw sources (backed up per Q2).

**M7. Schema v1 + Oracle game.json (3d)**
- Hand-write `game.json` once, from `game_config.py:21-212` and `game_optimization.py:12-39`.
- Write `text\en.json` from `betModes.ts` and `GameInfo.svelte`, with placeholders.
- `tools\golden\compare_config.py seventh_veil` diffs `vars(GameConfig())` between the fork and the builder.
- Exit: `math-sdk\env\Scripts\python.exe tools\gamedef\validate.py skins\oracle-of-sevens\game.json` exits 0; config diff is empty.

**M8. Math core + shim (4d)**
- Move the code to `core\math\cluster_tumble\`. star/tower become `features\bonus_variants.py`.
- **RNG rule:** same `random.*` calls, same args, same order. Same dict insertion order in events (`write_data.py:299`, no `sort_keys`).
- Board generalised (`num_rows`/`num_reels` from game.json).
- Exit: `snapshot.py --verify` passes against the golden; `math_stats --json` output is identical.

**M9. Generators (3d)**
- `--game` on `gen_fe_config`, `books_to_stories` (modes from the definition, robust handler parse), `books_to_mock`, `check_external_urls`, `assets_build` (palette from theme).
- New: `gen_skin_ts.py`, `gen_rules.py` (numbers only from `math.json` + `config_fe`).
- Exit: `math-sdk\env\Scripts\python.exe tools\gen\check_generated.py --game seventh_veil` shows 0 diff; `config.ts` is byte-identical.

**M6a spike results (2026-11-06).** Test setup: a git worktree of web-sdk, with an app that reads its skin from `stake\build\spike\web`, outside the workspace.

Proven:
- **Build:** a `kit.alias.$skin` import compiles into the bundle, and `kit.files.assets` serves the static files from the skin folder.
- **Dev server:** with `server.fs.allow`, the skin module and its static files are served. Paths outside the allow list return 403.
- **Storybook:** `staticDirs` can point into the skin folder, and an in-app story that imports `$skin` builds.

Rules for M10 that follow from these results:
1. **Merge core static files into the skin's `static`.** With `kit.files.assets` on the skin folder, a skin without `favicon.svg` failed prerender (`404 /favicon.svg`). The generator must write the core's own static files there too.
2. **Write generated stories inside the app**, at `src\stories\generated\` (git-ignored). A story file outside the app fails with `Rollup failed to resolve import "@storybook/addon-svelte-csf"`. Only data and static files may live outside.
3. **Never add a second app to the main `web-sdk` checkout and run a filtered `pnpm install`.** The first spike attempt did that, and pnpm pruned the store, which broke `apps\seventh-veil\node_modules\vite`. Repair: restore the lockfile, then `pnpm install --frozen-lockfile`. This confirms the one-app design. Run experiments in a worktree.
4. **A fresh checkout needs the workspace packages built** before the app builds: `pnpm exec turbo run build --filter="<app>^..." --no-daemon`. Otherwise the build fails with `Failed to resolve entry for package "pixi-svelte"`. Add this to doctor and the job runner.
5. **On Windows, a vite build may keep running after it prints `✔ done`.** The job runner treats `✔ done` plus the output files as success, then kills the process tree. Separately, `pnpm run build --filter=seventh-veil` through turbo once hung for 20 min, so call vite directly.
6. **Deleting a worktree under `build\` hits "Filename too long".** Unregister it with `git worktree remove`, then clear the folder with `robocopy <empty> <dir> /MIR`.

**M10. Web core (7d)** [E7]
- One app with `$skin`.
- `constants.ts`: INITIAL_BOARD, layout and symbol sizes derived from the board (5–8).
- Sound slots. GameInfo/betModes render generated data only. Delete leftover H5/W/M.
- Exit:
  - `$env:GAME='seventh_veil'; Push-Location web-sdk; pnpm --filter cluster-tumble exec vite build; Pop-Location` succeeds
  - assets are served from `build\seventh_veil\web\static`; dev server and Storybook load the skin
  - e2e frames vs golden ≤0.1% pixel diff
  - bundle ±2%
  - lints pass

**M11. Gates + packaging + smoke skin (5d)**
- `tools\gates\gate.ps1 -Game <id> [-Fast]` and `tools\package.ps1 -Game <id>`.
- Manifest contents: gameDef sha, `git describe` core tag, SDK SHAs, pins, publish/front/asset sha256, provenance, gate report.
- `skins\zz_smoke` (6×6, one variant, palette art) builds with zero code changes.
- Exit: `powershell -ExecutionPolicy Bypass -File tools\gates\gate.ps1 -Game seventh_veil` and `-Game zz_smoke` both exit 0. Delete `game\`.

## 7. Phase C — factory editor (≈26 agent-days)

Pin `@sjsf/form`, ajv and SvelteKit in §3 before M12.

**Runtime [P5, E6].** Jobs are spawned with `spawn(python, args, {detached:true, windowsHide:true})`. Each job gets a PID file and a state file, `build\<id>\jobs\<ts>.json`, polled through `status.json`. Cancel = `taskkill /PID <pid> /T /F`. A failed job leaves the previous build intact. Errors map to plain language, e.g. "create_ancestors failed to converge for mode X → lower bonus 1-in-N or choose preset Y".

**M12. Shell, onboarding, history (4d)** [P4, P6]
- Doctor panel: `doctor.ps1`, ffmpeg/rembg/Rust, SDK SHAs, free disk.
- Game list. "New from template". "Save as copy".
- Templates ship with a small golden book set and mock data in `core\presets\templates\<name>\books\`. Preview and Storybook then work at minute zero; the first preview run replaces them [P round 2 #1].
- Auto-snapshot on every save to `skins\<id>\.history\<ts>\`, with a Restore list.
- Job panel: log, progress (sims per mode), cancel, retry.
- Exit: the owner creates a game that passes validation without touching any file.

**M13. Skin screens (6d)** [P1, P10]. These are purpose-built screens, not raw schema trees:
- (a) **Symbol roster:** per row: art drop and thumbnail, tier, name, inline pay band.
- (b) **Paytable grid:** bands × symbols; validation errors shown on the cell.
- (c) **Mode cards:** cost, kind, variant, triggers and per-mode targets (hit rate, bonus 1-in-N, mid-win). The generated player-facing text ("1 in N") previews live.
- (d) **Sound slots:** the fixed core slot list; drop, play, duration/size.
- (e) **Text editor:** `en.json` and `en.social.json` side by side, placeholder chips, restricted-word lint, social preview.
- (f) `@sjsf/form` only for theme, presentation and feature params.

**M14. Assets, provenance, art gate, tiles (4d)** [P7, P8]
- Drag-drop per slot.
- **Draft lane:** raw PNG/OGG through a dev manifest, with hot reload in under 1 s. The full `assets_build --skin` (cut-out, atlas, bitmap font, Howler sprite) runs only on Build.
- Provenance per import batch with per-file override. A human-edit field is required.
- Art sign-off records the asset-set hash. Budget meter.
- **Tile composer:** hero + logo + title → 3:4 and 16:9 exports, with safe-zone overlay and size check.
- Exit: Oracle assets rebuilt through the UI give identical hashes.

**M15. Math tuning (6d)** [C5, P2]
- Preset picker and per-mode targets.
- **Preview tier:** 10k sims/mode, reduced ConstructParameters preset, changed modes only (`CT_MODES`). Results are labelled "estimate".
- **Candidate tier:** 100k sims, full optimizer, overnight, 2–3 runs, pick the best.
- Shows the compute estimate from M6a timings (no quota).
- Hard-gate red/green: RTP band, critical tests, 0 failed classes, books↔lookup match, max-win book per mode, max-win odds better than 1 in 10M, mode limits.
- Soft panel: hit rate, win>cost %, median session, p90/p99/p99.9, CVaR, ETL, buy min/median, Q15 dual readout.
- **Two states** [P round 2 #2]:
  - **Frozen** ("Freeze math" button, around day 4): captures weights. The owner can still unfreeze, which creates a new version.
  - **Locked**: set only when the board card moves to "Live" (Engine approved). This writes `mathLocked:true`, and `diff.py` enforces only Locked.

**M16. Preview, diff, pipeline board, one-click (6d)** [P3]
- Iframe preview of the core app with `$skin`. It replays real books through the production replay path, with a category picker per mode.
- `gamedef\diff.py` semantic diff vs the last release.
- **Pipeline board** per game: draft → tuning → math frozen → packaged → submitted → in review → live / failed (locked until a date). Shows open-review slots (1, then 5) and release history from the manifests.
- Queue-stall warning: starting art for game N+2 before game N is submitted shows a warning [P round 2 #3].
- **Build → Verify → Package** button streams the gate report.
- Exit:
  - Oracle round trip gives a manifest equal to the release, except timestamps.
  - **Usability test** [P12]: a non-developer builds `zz_smoke` end to end in under 2 h with no agent help.

**M17. Pilot game #2 (6d)**
- One new module (multiplier symbol or sticky wild): schema fragment, Python feature, web handler/component, CONTRACT row, golden story, e2e.
- Game #2 is built in the editor on the cadence below.
- Exit: gates pass, ≥2 mechanic differences plus a signature moment (checklist in `game.json.review`, auto-filled diff axes, owner confirms), art sign-off.

## 8. Gates

`gate.ps1 -Fast` runs in GitHub Actions after Q2. The full gate runs locally, because CI cannot run 100k sims or cargo [E8].

| Gate | Tool | Tier |
|---|---|---|
| Schema + semantics | `validate.py` | fast |
| Skin data-only, core literal-free, generated untouched | `lint_skin`, `lint_core`, `check_generated` | fast |
| Math critical + non-critical, books↔lookup | `math_stats.py --json`, golden verify | full |
| Contract | `books_to_stories.py --check --game` | fast |
| Book replay (all modes × 5 categories), errors, maxBet, resume, social, lang fallback, Popout | `tools\e2e\*` against committed golden books/mock | fast |
| Screenshots 1200×675, 400×225, 425×812 vs approved baseline | e2e + pixelmatch | fast |
| Bundle budget, external URLs, sample assets | size walk, `check_external_urls.ps1`, `check_sample_assets.ps1` | fast |
| Licence audit | `pnpm licenses list --prod --json`: no GPL/AGPL/LGPL; fonts OFL/own; provenance licence allowlist | fast |
| Currency | `check_amount.ts` | fast |
| Provenance complete + human edit + art sign-off hash | `package.ps1` precheck | full |
| Originality checklist | `game.json.review` | full |
| Engine AI review | manual | before submit |

## 9. Cadence (after M17)

Owner time is about 10–12 h per game [P9]. Ramp target in PROJECT.md §6: 1 game per 2 weeks for 8 weeks, then weekly.

| Day | Owner | Agent / automation |
|---|---|---|
| 1 | Concept, module combo, style bible; generate art and music | Template, modules, validate, preview math |
| 2–3 | Curate and **edit** art; provenance; SFX | Preview tuning; candidate runs overnight (2–3) |
| 4 | Pick candidate; **freeze math**; art sign-off | Full asset build, timings, texts, stories |
| 5 | Play preview, mobile check, tiles | `gate.ps1` full; fix loop |
| 6 | Read AI review; manual upload + submit if a slot is free, else queue | `package.ps1` → release + `submission.md` (blurb, event IDs); tag |

## 10. Risks

| Risk | Mitigation |
|---|---|
| Books not reproducible | M6a proof + pins |
| Weights not reproducible | Capture + reuse; Q27 seeded optimizer |
| KeyError or hang from new boards | Validate trigger keys and bands; max-repeat abort; wincap smoke |
| Quota/target mismatch | Derive quotas; plain convergence errors |
| Reskin penalty | Originality checklist, signature moment, human-edited art, module per early game |
| SDK drift | SHA pins, fail-loud patches, golden on upgrade |
| Turbo stale cache | Bypass turbo |
| Compute | Tiers, per-mode reruns, overnight |
| Non-dev mistakes | Data-only skins, ranges, history, write-protected releases (tag + manifest) |
| AI licensing | Provenance + human edit + licence allowlist |
| Review throughput | Pipeline board, queue, quality first |
| Disk | Zip + backup, prune optimization files |

## 11. Open questions (add to PROJECT.md §11)

| Q | Question |
|---|---|
| Q2 | GitHub push + backup target (CI, release zips, raw art) |
| Q19 | Approve installs per milestone: Playwright (M6c/d), jsonschema (M7), `@sjsf/form` + ajv (M12) |
| Q20 | Bundle ≤10 MB / first spin ≤4 s as core default |
| Q21 | Languages beyond EN at launch |
| Q24 | Hardware for overnight runs |
| Q26 | Observed Engine review turnaround (sets the real cadence ceiling) |
| Q27 | Seeded optimizer copy in `core\` (reproducible weights) vs capture-only |
| Q28 | Star median target for the M6b retune |

## 12. Effort

| Phase | Agent-days |
|---|---|
| A | ≈16 |
| B | ≈20 |
| C | ≈26 |
| **Total** | **≈62** (one agent at a time; some of B overlaps Oracle's review) |

Per game in steady state: ≈10–12 owner hours + ≈2 agent-days.

## Verification (end to end)

1. Phase A: `tools\e2e` replay suite green; docs/08 all `[x]`; AI review 0 FAIL; staging round per mode; submitted.
2. Phase B: `snapshot.py --verify` against the Oracle golden; `check_generated` 0 diff; `gate.ps1 -Game seventh_veil` and `-Game zz_smoke` exit 0.
3. Phase C: Oracle round-trip manifest equals the release; a non-developer builds `zz_smoke` in under 2 h; game #2 passes all gates and is submitted.

## Critical files

- `game\math\seventh_veil\{game_config,game_override,game_optimization,run}.py`
- `scripts\{math_stats,books_to_stories,gen_fe_config,books_to_mock,assets_build}.py`
- `scripts\sync.ps1`, `scripts\check_amount.ts`
- `game\web\seventh-veil\{vite.config.js,vite.patches.js}`
- `game\web\seventh-veil\src\overrides\formatAmount.ts`, `src\components\{ModalError,Authenticate,GameInfo}.svelte`, `src\game\{assets,constants,betModes,bookEventHandlerMap}.ts`
- `math-sdk\src\{state\run_sims.py,write_data\write_data.py,executables\executables.py,config\output_filenames.py}`
- `math-sdk\optimization_program\src\main.rs`
- `web-sdk\turbo.json`, `web-sdk\packages\config-svelte\index.js`
- `CLAUDE.md`, `PROJECT.md`, `.gitignore`
