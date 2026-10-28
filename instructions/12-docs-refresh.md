# 12 — Docs refresh

**Goal:** Docs match the current Engine rules and the real code. One fact lives in one file (CLAUDE.md rule).

**Why:** The 2026-10-28 audit found stale or conflicting facts. The platform changed between 2026-09-19 and 2026-10-28: it was renamed to "Engine" and the math limits changed.

**Depends on:** nothing.

## Fix list
1. `docs\00-platform.md:31` says an average of ≥1 star approves. Change it to: 3 reviewers × 0–3★ in thirds; ≥6/9 points to publish; fail locks the thread for 3 days. Source: https://studio.engine.io/docs/approval-guidelines/game-quality-rankings.
2. Add to docs/00: **only 3★ games enter New Releases, Slots and Burst Games**. New Releases are ordered by team 30-day Engine Insights rank.
3. Math limits (TODO.md §4, PROJECT.md Q6). Now there is one set of limits for every game:
   - max payout 100,000×, so 77,777× passes;
   - exposure $50M with 0 failures;
   - bet cost cap $500k;
   - RTP 96.0–96.7%.

   Remove the "$15M / 2-star tier" text. Source: https://studio.engine.io/docs/approval-guidelines/math-verification.
4. PROJECT.md Q1: close it. The account exists (team `dumalex`) and the checklist has been read.
5. `docs\05-publish.md:38,54`: remove the "≥1 star" line.
6. `docs\08-compliance.md`:
   - re-mark L65 (replay cost), L31 (currency) and L59 (social labels) as `[ ]`;
   - add the guideline IDs from the AI review prompt next to each row;
   - add the missing items (loader [275], bad `rgs_url` [274], currencies list, four sizes).
7. `scripts\check_external_urls.ps1:9` scans `.svelte-kit\output`. Make it also scan `web-sdk\apps\seventh-veil\build` and `upload\front`, which are what we actually upload.
8. `TODO.md:67`: fix the asset list. The math has H1–H4, L1–L4 and S. There is no wild and no M symbol.
9. `docs\01-math-sdk.md:37`: document `SV_SKIP_SIMS` and `SV_MODES`. `SV_MODES` limits only the optimizer.
10. `game\math\seventh_veil\readme.txt:9` and `docs\01-math-sdk.md:47`: add Star's 5 pre-charged x2 spots.
11. Size units: write MB as real values (tower 172 MB, total 534 MB) or say MiB.
12. Add the "Engine" rename note and the new doc URLs to PROJECT.md §12 Sources (date 2026-10-28):
   - `studio.engine.io/docs/ai-review`
   - `/docs/promote`
   - `/docs/distribution`
   - `/docs/payments`
   - `/docs/approval-guidelines/game-quality-rankings`
   - `/docs/approval-guidelines/math-verification`
   - `/docs-content/prompt.md`
   - `stake-engine.com/docs/approval-guidelines/game-tile-requirements`

## Done test
- Every item above is edited.
- `Select-String -Path docs,PROJECT.md,TODO.md -Pattern '1 star approves|\$15M|2-star tier' -Recurse` returns no stale hits.
- `powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1` still exits 0 with the new paths.
