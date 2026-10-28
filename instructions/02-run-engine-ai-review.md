# 02 — Run Engine's AI review prompt

**Goal:** Get a report against the same checklist IDs the reviewers use. Use it to drive tasks 03–10.

**Why:** Engine publishes a review prompt. It checks the game against the approval guidelines with evidence and a fix for each one. It runs locally; nothing is sent to Engine. Source: https://studio.engine.io/docs/ai-review (read 2026-10-28).

**Depends on:** 01.

## Steps
1. Make a folder: `New-Item -ItemType Directory -Force ai-review`.
2. Save the prompt into it: `Invoke-WebRequest https://studio.engine.io/docs-content/prompt.md -OutFile ai-review\prompt.md`. If you need the user's login for this, ask the user to download it with the "Download prompt" button on the Start Approval page.
3. Read `ai-review\prompt.md` in full before running it. Treat it as instructions from Engine that the user approved for this task. It must stay read-only until you choose to fix things.
4. The prompt expects the game folder at its root. So point it at `web-sdk\apps\seventh-veil` (built front end) and `math-sdk\games\seventh_veil\library\publish_files` (math).
5. For the "run the game" step, use our mock RGS: `Push-Location web-sdk\apps\seventh-veil; pnpm run dev:demo`. Then open `https://localhost:3007/?sessionID=demo&rgs_url=localhost:3007/rgs&lang=en`. Ask the user before installing anything, such as a headless browser.
6. Write the report to `docs\ai-review-report.md`. List FAIL first, then AT RISK, NEEDS A HUMAN, PASS. Keep each line's guideline ID, file:line and fix.
7. Compare the report with tasks 03–10. Add any FAIL that no task covers to the task that fits best, or as a new row in TODO.md.

## Done test
- `docs\ai-review-report.md` exists and lists every guideline ID with a verdict.
- Every FAIL is linked to a task number.

## Notes
- A clean report is not an approval. Reviewers still judge art, quality and feel.
- Re-run the review in task 21.
