# 21 — Build, package, final AI review

**Goal:** `upload\front` holds the final build and passes every local check. The Engine AI review comes back with no FAIL.

**Why:**
- Reviewers see the latest published build (Studio Start Approval page, 2026-10-28).
- Today `upload\front` is stale: old bundle, no "ORACLE OF SEVENS", and it includes the Stake loader gif.

**Depends on:** 01–20.

## Steps
1. `powershell -ExecutionPolicy Bypass -File scripts\doctor.ps1`
2. `powershell -ExecutionPolicy Bypass -File scripts\sync.ps1`
3. `Push-Location web-sdk; pnpm run build --filter=seventh-veil; Pop-Location`
4. `powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1`, which must exit 0.
5. Look at `upload\front` before replacing it. It is regenerated from the build, so it is safe to replace. Then: `Remove-Item -Recurse -Force upload\front; Copy-Item -Recurse web-sdk\apps\seventh-veil\build upload\front`.
6. Check the package:
   - it contains `index.html` with "ORACLE OF SEVENS";
   - it has no `*loader*.gif`;
   - its size is ≤10 MB.
7. Re-run the AI review (task 02) on the final build. Fix every FAIL, then run it again until it is clean. Save the report as `docs\ai-review-report.md` (overwrite it; git keeps the history).
8. Repeat the four reviewer sizes (task 04), social mode (07) and replay (08) checks on the final build.
9. Tell the user that `upload\front` and `math-sdk\games\seventh_veil\library\publish_files` are ready for human task 06.

## Done test
- AI review: 0 FAIL. Every NEEDS A HUMAN item is listed for the user.
- All checks in steps 4–8 pass.
