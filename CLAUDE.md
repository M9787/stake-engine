# CLAUDE.md — agent rules

Read [PROJECT.md](PROJECT.md) first. It holds goal, pins, commands, open questions. This file holds only rules.

## Read order

1. PROJECT.md §1 Goal → §2 Non-Goals → §4 Modes → §6 Milestones → §11 Open Questions.
2. The one doc in `docs/` for the task: 00 platform, 01 math, 02 web, 03 contract, 04 best practice, 05 publish, 06 design, 07 math spec, 08 compliance.

## Commands

Use the command table in PROJECT.md §7. Do not invent other commands.
Always run `powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1` before any SDK command.

## Do

- Verify before claiming. Run the command, read the output, then report. Quote the exact error on failure.
- Use only APIs, events, and fields that exist in the SDK source or the Stake Engine docs. Cite the file or URL.
- Put any unverified claim in PROJECT.md §11 with owner and blocking flag — never in doc bodies.
- Keep one fact in one file. Link to it from other files. Pins live only in PROJECT.md §3.
- Keep math and web lifecycles separate. Only docs/03-contract.md couples them.
- Write every runnable step as a command, not a description.
- Add a Sources entry (URL + what it proves + date) for every new platform fact.

## Don't

- No invented API names, BookEvent types, EmitterEvent types, or config keys.
- No "latest" versions. No version change without editing PROJECT.md §3 first.
- No installs or new scaffolding outside the current milestone (PROJECT.md §6).
- No edits to `web-sdk\packages\*`, `math-sdk\games\0_0_*`, or `web-sdk\apps\cluster`.
- Math: edit the core in `core\math\cluster_tumble` and game data in `skins\<skin>\` (`game.json`, `math\reels`, `text`), then run `scripts\sync.ps1` (it installs the core and generates one shim per skin in `math-sdk\games\<gameId>`). `game\math\seventh_veil` is the frozen hand-written reference for `tools\golden\compare_config.py`; do not edit it.
- Web: edit the one core app `core\web\cluster-tumble` (skin data only through `$skin` → `build\<gameId>\web`), then run `scripts\sync.ps1` (it syncs to `web-sdk\apps\cluster-tumble`). Direct edits in the SDK clones are overwritten by the next sync.
- Assets: slot catalogue `core\assets\slots.v1.json`; skin style bible and prompts `skins\<skin>\assets.json`; owner files in `skins\<skin>\art_in\{raw,edited}\` (git-ignored).
- Never run `robocopy /MIR` or `Remove-Item -Recurse` on a `node_modules` folder: pnpm links point into `web-sdk\packages`, and both follow them and delete package files. Delete a whole app folder only with `cmd /c rmdir /s /q`, which does not follow junctions (incident 2026-11-07, restored with `git -C web-sdk checkout -- packages`).
- Before and after any core or skin math change: `tools\gamedef\validate.py`, `tools\golden\compare_config.py`, `tools\golden\quick_books.py`, `tools\lint_core.py` (PROJECT.md §7).
- Never hand-edit generated files: everything under `build\<gameId>\` (`web\config.ts`, `skin.generated.ts`, `assets.generated.ts`, `rules.generated.en.json`, `modes.json`, `static\`, `static-gen\`, `prompts.*`), `skins\<skin>\assets.lock.json` and ingested files (`tools\assets\ingest.py`), `core\web\pnpm-lock.yaml` (mirror written by `sync.ps1`), `src\stories\Mode*` and `src\stories\data\*` (`books_to_stories.py`), `math-sdk\games\<gameId>\game_config.py` and `run.py` (`tools\gen\gen_shim.py`).
- No new or changed bet modes for Oracle (`skins\oracle-of-sevens`). The set in PROJECT.md §4 is frozen. Factory games freeze at `mathLocked`.
- No design that breaks docs/08-compliance.md. Those rules are not negotiable.
- After any math change: rerun `run.py`, then `scripts\math_stats.py`, and update docs/07 results.
- No secrets in the repo. `.env` is git-ignored; only `.env.example` is tracked.
- No commits unless the user asks.

## Shell

Windows 11, PowerShell. No `make` (math-sdk Makefile targets have PowerShell equivalents in docs/01-math-sdk.md).

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **stake** (1918 symbols, 2812 relationships, 94 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/stake/context` | Codebase overview, check index freshness |
| `gitnexus://repo/stake/clusters` | All functional areas |
| `gitnexus://repo/stake/processes` | All execution flows |
| `gitnexus://repo/stake/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
