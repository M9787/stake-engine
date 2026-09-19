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
- Edit game code only in `game\math\seventh_veil` and `game\web\seventh-veil`, then run `scripts\sync.ps1`. Direct edits in the SDK clones are overwritten by the next sync.
- Never hand-edit generated files: `src\game\config.ts` (`gen_fe_config.py`), `src\stories\Mode*` and `src\stories\data\*` (`books_to_stories.py`).
- No new or changed bet modes. The set in PROJECT.md §4 is frozen.
- No design that breaks docs/08-compliance.md. Those rules are not negotiable.
- After any math change: rerun `run.py`, then `scripts\math_stats.py`, and update docs/07 results.
- No secrets in the repo. `.env` is git-ignored; only `.env.example` is tracked.
- No commits unless the user asks.

## Shell

Windows 11, PowerShell. No `make` (math-sdk Makefile targets have PowerShell equivalents in docs/01-math-sdk.md).
