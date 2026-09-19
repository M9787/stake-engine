# 05 — Publish

## Purpose

Checklist: math files + frontend build → Stake Engine → published → submitted for approval.

## Prereq

- Stake Engine account (PROJECT.md §11 Q1).
- Math tuned and verified ([07](07-math-spec.md)), compliance checked ([08](08-compliance.md)).
- Frontend build ([02](02-web-sdk.md)).

## Steps

- [ ] 1. Production math run (100k sims spin modes, 50k buy modes; scale up only if Engine upload limits allow). `scripts\math_stats.py` passes.
- [ ] 2. Upload `math-sdk\games\seventh_veil\library\publish_files\` to Engine. Engine checks format and shows stats.
- [ ] 3. Build frontend: `pnpm run build --filter=seventh-veil`.
- [ ] 4. Combine `prerendered\pages\index.html` and `client\` contents from `apps\seventh-veil\.svelte-kit\output\`.
- [ ] 5. Upload via Engine **Files** page.
- [ ] 6. **Publish Frontend**.
- [ ] 7. Test via **Developer** page: one round per mode, plus replay URL.
- [ ] 8. Fill the reviewer event-ID table in [08](08-compliance.md), walk the login-gated checklist, submit.

Exact Engine UI labels for steps 2 and 8: unverified → PROJECT.md §11 Q1.

## Verify

- Game loads from Engine URL, authenticates, plays and ends a round in every mode, no error code.
- Review result: average ≥1 star.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://github.com/engineio/web-sdk | steps 3–7 | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | steps 1–2 | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/submission-checklist | step 8 | 2026-09-19 |
