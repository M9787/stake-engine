 Context

 information.txt (13 lines) is the whole project. Folder empty otherwise. Current text is a wish list:
 "Docs needed. Kit needed. Best practice needed. Env must be simple, structured, hierarchy of ideas.
 Final output must be ready-to-develop environment."

 Problem: no target platform facts, no acceptance criteria, no order of work, no ownership of unknowns.
 Any agent reading it invents scope. Next iteration needs a schema — a filled-in, structured brief
 that an agent can execute without guessing.

 Grounding facts found (used to make schema concrete, not speculative):

 - Stake Engine = game dev + monetization platform; publish via ACP (Admin Control Panel), games run on RGS.
 - math-sdk (StakeEngine/math-sdk): Python ≥3.12 + PIP, Rust/Cargo for optimizer, make setup.
   Emits backend config, lookup tables, simulation books.
 - web-sdk (StakeEngine/web-sdk): Svelte 5 + PixiJS 8 + TurboRepo. Node v22.16.0, pnpm v10.5.0.
   Fork-to-own model. /apps = games (lines, cluster, ways, scatter), /packages = shared modules.
   Commands: pnpm run storybook|dev|build --filter=<MODULE>.
 - Contract between halves: BookEvents (from RGS/math) → bookEventHandlers → EmitterEvents (animation).
   Event order is the game behavior.
 - Ship flow: build → output folder → upload to Stake Engine → publish → launch.

 Deliverable

 Replace information.txt with a hierarchy of instruction files. Schema = the shape below.

 stake/
 ├─ PROJECT.md            # tier 1 — what/why, one screen, source of truth
 ├─ CLAUDE.md             # tier 1 — agent rules, commands, do/don't
 ├─ docs/
 │  ├─ 00-platform.md     # Stake Engine, ACP, RGS — verified links only
 │  ├─ 01-math-sdk.md     # python side: setup, run, outputs
 │  ├─ 02-web-sdk.md      # svelte/pixi side: setup, storybook, build
 │  ├─ 03-contract.md     # BookEvents → handlers → EmitterEvents
 │  ├─ 04-best-practice.md
 │  └─ 05-publish.md      # upload → publish → launch checklist
 └─ .env.example + setup script

 PROJECT.md schema (the "better instruction")

 Each section has fixed heading, fixed field types, and a DONE test. No prose paragraphs.

 ┌─────┬─────────────────────┬──────────────────────────────────────────────────────────┬───────────────────────────────────┐
 │  #  │       Section       │                          Fields                          │             DONE test             │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 1   │ Goal                │ one sentence, one game type (lines/ways/cluster/scatter) │ reader names the artifact shipped │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 2   │ Non-Goals           │ bullet list                                              │ ambiguity killed                  │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 3   │ Stack (pinned)      │ tool → exact version → why                               │ node -v, python -V, pnpm -v match │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 4   │ Repo Layout         │ tree, ≤2 levels                                          │ every dir has one owner concept   │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 5   │ Environments        │ local / storybook / RGS-mock / published                 │ each has run command              │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 6   │ Commands            │ table: intent → command → expected output                │ copy-paste runs clean             │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 7   │ Contract            │ BookEvent list → handler → emitter event                 │ one table row per event           │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 8   │ Definition of Ready │ checkbox list                                            │ all boxes = env is dev-ready      │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 9   │ Open Questions      │ question → owner → blocking?                             │ none blocking before build        │
 ├─────┼─────────────────────┼──────────────────────────────────────────────────────────┼───────────────────────────────────┤
 │ 10  │ Sources             │ URL → what it proves → date checked                      │ no unverified claim               │
 └─────┴─────────────────────┴──────────────────────────────────────────────────────────┴───────────────────────────────────┘

 Ordering rule (the "hierarchy of ideas" the file asks for): Goal → Constraints → Stack → Layout →
 Commands → Contract → Verification. Facts before instructions, instructions before commands,
 commands before checklists. Nothing forward-references.

 Rules baked into the schema

 - Every claim about the platform carries a source URL + date. Unverified → goes in Open Questions, not body.
 - Version pins are exact (Node 22.16.0, pnpm 10.5.0, Python ≥3.12) — no "latest".
 - One fact lives in one file. Other files link, never restate.
 - Math and web are separate lifecycles; only docs/03-contract.md couples them.
 - Anything runnable is a command, not a description.

 Steps

 1. Write PROJECT.md from the schema table above, filled with the grounding facts.
 2. Write CLAUDE.md: pinned versions, command table, "verify before claiming", no-invented-API rule.
 3. Write docs/00..05 stubs — each opens with Purpose / Prereq / Steps / Verify / Sources.
 4. Keep information.txt as docs/_original-brief.txt (traceability), pointer from PROJECT.md.
 5. Re-verify the two SDK READMEs live; anything that 404s → Open Questions.

 Verification

 - PROJECT.md §8 checklist has zero unchecked boxes, or each unchecked one maps to §9 with an owner.
 - Every command in §6 pasted into PowerShell either runs or names its missing prereq.
 - Grep for un-sourced version numbers / URLs → none outside §10 and Sources blocks.
 - Fresh-agent test: hand only PROJECT.md to a new session, ask "what do I build first" — answer must be
   unambiguous and match §1.

 Not in this iteration

 Cloning math-sdk / web-sdk, installing Node/Python/Rust, scaffolding a game app. That is iteration 3,
 gated on this schema being approved.