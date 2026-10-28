# 05 — Publish

## Purpose

Checklist: math files + frontend build → Engine Studio → published → submitted for approval → live.

## Prereq

- Engine Studio team and game (done 2026-09-19: team `dumalex`, game `oracle-of-sevens`, https://studio.engine.io/teams/dumalex/games/oracle-of-sevens).
- Team setup in Studio (owner only): **Payments** method (Guaranteed 7.5% chosen; fixed for new publishers once a game is active), **Settings** provider name + URL slug, **Wallet** for payouts.
- Math tuned and verified ([07](07-math-spec.md)), compliance checked ([08](08-compliance.md)).
- Frontend build ([02](02-web-sdk.md)).

## Steps

- [ ] 1. `scripts\doctor.ps1` exits 0, then `scripts\math_stats.py seventh_veil --brief --sessions` passes.
- [ ] 2. Build the frontend and assemble the upload folder:
  ```powershell
  Push-Location web-sdk; pnpm run build --filter=seventh-veil; Pop-Location
  powershell -ExecutionPolicy Bypass -File scripts\check_external_urls.ps1
  $o = 'web-sdk\apps\seventh-veil\.svelte-kit\output'
  New-Item -ItemType Directory -Force upload\front | Out-Null
  Copy-Item "$o\prerendered\pages\index.html" upload\front
  Copy-Item "$o\client\*" upload\front -Recurse
  ```
  `upload\` is git-ignored. Delete `upload\front` before rebuilding it; leave out `upload\front\.vite`.
- [ ] 3. Studio → game → **Files** → **Import Files** → select `math-sdk\games\seventh_veil\library\publish_files` → **Start Sync**.
- [ ] 4. **Import Files** → select `upload\front` → **Start Sync**.
- [ ] 5. **Publish Game** → Math, then **Publish Game** → Front End.
- [ ] 6. **Start Approval** page, Readiness: math version published, front version published, math validation (RTP, hit rate, max win), betlevel validation (at least one valid betlevel template).
- [ ] 7. **Play Game**: one round per mode, replay, `social=true`.
- [ ] 8. **Media**: 3:4 tile set as cover, 16:9 cover art. Tile assets per the tile requirements page: `GameTitle-BG` (PNG/JPG), `GameTitle-FG.png` (transparent), `ProviderName-Logo.png` (transparent); BG + FG ≤ 3 MB combined.
- [ ] 9. Walk the login-gated submission checklist (stake-engine.com login is separate from Studio), fill the Payment, Distribution, Compliance, Details tabs, then **Submit** (owner clicks).

## Review

- Three independent reviewers rate 0–3 stars within 24 hours.
- Three reviewers × 0–3★ in thirds: the game needs ≥6/9 points to publish. A failed review locks the thread for 3 days. Plan for 3★: only 3★ games enter New Releases, Slots and Burst Games ([00](00-platform.md) steps 11–12).
- First-time publishers: one open review at a time (five once a game is live).
- After approval the game is live on Stake within 24 hours. Payouts on the 1st of each month to the team wallet.

## Verify

- Readiness shows every check passed.
- Game loads from Studio **Play Game**, authenticates, plays and ends a round in every mode, no error code.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://studio.engine.io/teams/dumalex/games/oracle-of-sevens/approval | readiness checks, one open review, go-live and payout timing (its 2-star bar is replaced by the ≥6/9 rule, row below) | 2026-09-19 |
| https://studio.engine.io/teams/dumalex/payments | payment methods, method lock for new publishers, monthly payouts | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/game-tile-requirements | tile assets, names, 3 MB limit | 2026-09-19 |
| https://stake-engine.com/docs/approval-guidelines/submission-checklist | checklist is login-gated | 2026-09-19 |
| https://studio.engine.io/docs/approval-guidelines/game-quality-rankings | ≥6/9 points to publish, 3-day lock, 3★ shelves | 2026-10-28 |
| https://github.com/engineio/web-sdk | upload folder layout (`index.html` + `client\`), Import Files, Publish Game | 2026-09-19 |
| https://stake-engine.com/docs/math/math-file-format | math folder contents | 2026-09-19 |
