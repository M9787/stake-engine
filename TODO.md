# TODO — Oracle of Sevens to live on Stake

Updated 2026-09-19. Verified against Studio (studio.engine.io, team `dumalex`, game `oracle-of-sevens`), Studio docs and code.
Score = Impact (1–5) × Urgency (1–5), out of 25. Priority: P0 blocks everything, P1 blocks submission, P2 affects the star rating, P3 nice to have.
Owner: **You** = project owner, **Me** = agent.

Key rules learned today:
- **1 star = not published.** We need **≥2 stars** (Game Quality Rankings).
- Common low-rating causes: "over-reliance on generic AI-generated assets", mismatched art styles, shallow gameplay.
- Math critical tests: our game passes all of them (see Math).

## Next 5 actions
1. Me: code fixes C1–C6 (checklist failures), rebuild, re-package `upload\front`.
2. You: add the wallet and confirm the provider name and slug.
3. You: upload math, then frontend (Import Files → Start Sync). Me: publish, with your OK.
4. Me: write `docs/09-assets.md` (art and sound spec with prompts). You: start generating.
5. Me: math fixes M1–M2 (max-win odds, buy-mode simulation count), then re-upload the math.

## 1. Studio setup (You)
| Status | Task | Owner | P | Score | Evidence |
|---|---|---|---|---|---|
| ✅ | Payment method Guaranteed 7.5% | You | — | — | payments page, selected |
| ❌ | Wallet: ERC-20 address, home/work address, USDT or USDC (failed payouts can't be recovered) | You | P1 | 4×3=12 | wallet page empty; with no wallet, the balance carries over to the next month |
| ❓ | Provider Name and URL Slug saved (shows in stake.com URLs) | You | P1 | 3×3=9 | settings page; value not confirmed |
| ❌ | Provider logo: white on transparent, about 338×134, `DumaLex-Logo.png` | You | P1 | 3×2=6 | settings plus tile rules |

## 2. Upload and staging test
| Status | Task | Owner | P | Score | Evidence |
|---|---|---|---|---|---|
| ✅ | Frontend builds with "ORACLE OF SEVENS" (Node 22.16.0, doctor exits 0) | Me | — | — | build log `✔ done` |
| ❌ | Re-package `upload\front` from the new build (current folder holds the old build and the Stake loader gif) | Me | P0 | 5×5=25 | after C1 |
| ❌ | Upload math: Files → Import Files → `math-sdk\games\seventh_veil\library\publish_files` → Start Sync | You | P0 | 5×5=25 | Files: "No files uploaded yet" |
| ❌ | Upload frontend: `upload\front` → Start Sync | You | P0 | 5×5=25 | same |
| ❌ | Publish Game → Math, then Front End (I ask first) | Me+You | P0 | 5×5=25 | Readiness: both "Not published" |
| ❌ | Readiness: math validation and bet-level template valid | Me | P0 | 5×4=20 | template sized by exposure: 77,777 × max bet ≤ $15M means max bet ≤ $192 |
| ❌ | Staging play: 1 round per mode; loss sends no end-round; low-balance play is blocked; reload mid-bonus restores the bet; `social=true`; replay | Me | P1 | 4×4=16 | checklist PreChecks and RGS items |
| ❌ | Test on popout S/L, mobile, older Android/iOS | Me+You | P1 | 4×3=12 | checklist Responsive |
| ✅ | Q10 upload size closed: limit is 4.2 GB per books file and 10M events per mode; ours is 164 MB max | — | — | — | math-verification page |

## 3. Code fixes from the submission checklist (Me; web-sdk packages are read-only, so fix via our copies or a Vite rewrite like the existing constants.ts one)
| Status | Task | Owner | P | Score | Evidence |
|---|---|---|---|---|---|
| ❌ C1 | Remove the Stake Engine loader: `LoaderStakeEngine` in `src/routes/+layout.svelte:4,16,29` plus `stake-engine-loader.gif` | Me | P0 | 5×5=25 | checklist: "Game should not contain the Stake Engine Loader" |
| ❌ C2 | Sub-cent payouts: `utils-shared/amount.ts` forces 2 decimals (0.012 shows as 0.01); non-ISO codes may throw in Intl | Me | P1 | 4×4=16 | checklist Currency Support |
| ❌ C3 | Mobile double-tap zoom: viewport `maximum-scale=1,user-scalable=no`, `touch-action:manipulation` on body and canvas | Me | P1 | 4×4=16 | checklist Responsive; `app.html:6` |
| ❌ C4 | Replay: read `currency`; add a Replay-again button; show the full cost (100x/400x buys show 1x today) and the multiplier | Me | P1 | 4×4=16 | checklist Replay; `stateBet.svelte.ts:56-60`, `UIReplay.svelte` |
| ❌ C5 | Social mode: force `en`; shared SPIN/BUY labels must also follow `jurisdiction.socialCasino`, not only `?social=true` | Me | P1 | 4×4=16 | checklist Stake.US; `i18nDerived.ts:7,9` |
| ❌ C6 | Space-hold loop: add a balance check (`isBetCostAvailable`) before the next play request | Me | P1 | 4×3=12 | checklist "Insufficient balance bets do not send a play request" |
| ❌ C7 | Invalid `lang` (`?lang=xx`) must fall back to `en`, not throw in Intl | Me | P1 | 3×3=9 | checklist Language |
| ❌ C8 | Bet cap on low balance: snap to the highest valid bet level | Me | P2 | 3×2=6 | `stateBet.svelte.ts:24-31` |
| ❓ C9 | General disclaimer: compare `GameInfo.svelte:140-142` to Stake's template text ("Malfunction voids all wins and plays…") | Me | P1 | 3×3=9 | general-disclaimer page |
| ❌ C10 | Update docs/08 with the full Studio checklist (50+ items); fix rows wrongly marked [x] (replay cost display, social labels) | Me | P1 | 3×3=9 | audit |
| ✅ | Already passing: bet levels from authenticate, restored round bet, no end-round on a loss, Space = bet, no scroll, rules content (pays, clusters, retrigger, modes, RTP, max win), autoplay confirm, buy/ante confirm, button guide, sound toggle | — | — | — | audit |

## 4. Math (engine math verification)
| Status | Task | Owner | P | Score | Evidence |
|---|---|---|---|---|---|
| ✅ | Critical tests pass: base 1.0× is cheapest; base SD 19.47 (≥0.6); RTP 96.50% in all modes (90–96.7, spread 0); max 77,777× (≤500k); max cost 400× (≤2000×); hit ≥1 in 50 in every mode (base 1/4.0) | — | — | — | own metrics, math-verification page |
| ✅ | Non-critical: fails only "max payout multiplier" at the 2-star tier (77,777 > 50,000), which is 1 failed class, so caps stay $15M / $100k. 3-star tier: 0 failures | — | — | — | P≥5k 0.00008 max, ETL40 ≤0.654, CVaR per-stake ≤178, absolute ≤3,692 |
| ❌ M1 | Max win odds should be better than 1 in 10M: base is 1 in 19.4M, omen 1 in 15.6M. Raise the max-win weight in the optimizer targets, rerun, run `math_stats` | Me | P1 | 4×3=12 | "typically more frequent than 1 in 10,000,000" |
| ❌ M2 | Buy modes have 50k simulations; the guideline is 100k–1M. Rerun star/tower at 100k (books about 600 MB total, OK) | Me | P2 | 3×3=9 | math-verification "Summary statistics" |
| ❌ M3 | After M1/M2: `gen_fe_config.py`, `books_to_stories.py --check`, docs/07, re-upload math | Me | P1 | 4×3=12 | CLAUDE.md math rule |

## 5. Art and sound (biggest gap; decides the star rating)
| Status | Task | Owner | P | Score | Evidence |
|---|---|---|---|---|---|
| ❌ | `docs/09-assets.md`: list of every asset the frontend loads (symbols h1–h5, l1–l4, W, S, M, frame, background, big win, free-spin intro, transition, tumble, fonts, audio sprite), sizes, file names, one style guide, AI prompts per asset, Suno prompts | Me | P0 | 5×5=25 | build log lists the asset keys |
| ❌ | Generate art (Firefly or Midjourney paid), then a **human paint-over** for a consistent style. No raw generic AI look | You | P0 | 5×5=25 | rankings: "over-reliance on generic AI-generated assets" leads to a low rating |
| ❌ | Music with Suno Pro/Premier (base loop, bonus loop, big-win and max-win stings); sound effects from stock or ElevenLabs | You | P1 | 4×4=16 | Suno paid plans give a commercial licence |
| ❌ | `ASSET_LICENSES.md`: tool, plan, date, licence, edits for each asset | Me+You | P1 | 3×4=12 | IP rule: infringement means rejection |
| ❌ | Integrate: replace sample art, static sprites plus code tweens where there is no Spine; keep the bundle small | Me | P0 | 5×4=20 | 3-star needs an "optimised bundle size" |
| ❌ | Gameplay depth: the bonus and multiplier grid must feel rich (a common low-rating cause is "shallow gameplay") | Me | P2 | 4×2=8 | rankings page |

## 6. Submission
| Status | Task | Owner | P | Score | Evidence |
|---|---|---|---|---|---|
| ✅ | Checklist behind the login found and read (studio.engine.io/docs) | — | — | — | submission-checklist |
| ❌ | Media: 3:4 tile set as cover; 16:9 cover art; `OracleOfSevens-BG` (PNG/JPG) + `OracleOfSevens-FG.png` ≤3 MB combined | You+Me | P1 | 5×3=15 | Readiness; tile requirements |
| ❌ | Blurb: short theme and mechanics text for promotion | Me | P1 | 3×3=9 | approval guidelines "must be accompanied by a short blurb" |
| ❌ | Title uniqueness: no "Oracle of Sevens" slot found online (The Oracle by Cryptologic, Book of Sevens exist). Also check the Stake lobby | Me | P2 | 3×2=6 | web search |
| ❌ | Fill the Payment, Distribution, Compliance, Details tabs; You click **Submit** | You | P1 | 5×2=10 | approval page |
| ❌ | Review: 3 reviewers within 24 hours; ≥2 stars → live within 24 hours; below that, fix and resubmit within 3 days. One open review for first-time publishers | You+Me | P1 | 5×1=5 | approval page |
| ⚠ | After approval only minor visual fixes are allowed. Math, modes and mechanics freeze, so finish M1–M2 **before** submitting | — | — | — | approval guidelines |

Progress: about 45% overall. Code and math about 85% (checklist fixes open); art 5%; Studio/upload 15%.
