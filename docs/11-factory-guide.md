# 11 — Factory guide (owner, hands-on)

## Purpose

Make one game in the factory editor, from a new idea to a game submitted in Stake Studio. Plain steps, in order. Page names are the tabs at the top of the editor: **Overview**, **Setup**, **Asset desk**, **Preview**, **Build & package**, **Submit**.

What the editor never does: upload to Stake, publish, or submit. You do those steps in Stake Studio (part E).

## Prereq

- Windows 11 with the tools from PROJECT.md §3. The editor checks them on start (`scripts\doctor.ps1`).
- A Stake Studio team and the game created in Studio ([05-publish.md](05-publish.md) Prereq).
- Accounts for the art and music tools named on the Asset desk cards.

## Steps

### A. Start the editor and make a game

1. Double-click `factory\start.cmd`. Or run:
   ```powershell
   Push-Location factory; pnpm exec vite dev; Pop-Location
   ```
   The browser opens `http://127.0.0.1:5174`. Keep the window open; closing it stops the editor.
2. Page **Your games** → **Computer check**: every row must be PASS. A FAIL row says how to fix it.
3. **New game**: pick a template, type a game id (lower case, e.g. `moon_tide`) and a display name. Press create.
4. The game opens on **Overview**: name and version, colours, texts, history. You can come back here any time.

### B. Setup

5. Tab **Setup**: choose a preset (board size, volatility, max win, bonus about 1 in N spins, modes: base, ante, buy). Press **Apply preset**. Oracle of Sevens is frozen: its modes and math cannot change.
6. Check the title on **Overview**. It must not contain a restricted term: Megaways, XWays, Enhanced, Boosted, RTP, "Gates of", Bonanza, Olympus, Rush, Kraken, Waylanders.

### C. Asset desk (art and sound)

7. Tab **Asset desk**. Each card is one slot (a symbol, a background, a sound). Cards are grouped in sittings, so you can work in short sessions.
8. Optional, to see the game early: press **Fill empty slots with test assets**. Test assets are labelled placeholders. They are fine for Preview but **block** packaging; remove them before you submit.
9. Make the **hero** image first (sitting 1). Copy its image address into **Hero image link**. That link becomes the style reference for every other prompt, and the other image cards unlock.
10. For each card: copy the prompt, make the file in the named tool, do the human edit the card asks for, then upload the raw download and your edited file on the card. Fill **licence**, **source link** and **edit note**.
11. Press **Ingest all** (or ingest one slot). The desk cuts, sizes and records each file in `assets.lock.json`.
12. Make the three tile sources too: `tile.bg` (3:4 background), `tile.fg` (3:4 transparent foreground), `cover` (16:9). Stake needs them for the Media Editor.
13. Press **Contact sheet** and look at the sheets: one style, readable symbols, no child-like art.
14. Press **Sign off** with your name. If you change any art later, sign again (the sign-off records the exact files).

### D. Build & package (steps 1–10)

Tab **Build & package**. Run the steps top to bottom. Each step shows a log; when a step fails, the box above the log says why in plain words.

15. **1 Prepare**: copies your changes into the game.
16. **2 Math estimate**: 10,000 test spins, a few minutes. For tuning only.
17. **3 Prepare again + preview data**: game rules and sample spins for **Preview**. Now open tab **Preview** and play.
18. **4 Build web**: builds the playable files.
19. **5 Quick check**: the fast automatic checks.
20. **6 Final math**: 100,000 test spins per mode with the full optimizer, about 40 minutes. Stake needs 100,000 to 1,000,000 per mode.
21. **7 Freeze math**: keeps these weights, so the game never changes by accident.
22. **8 Full check**: every automatic check, about 45 minutes. It must end with 0 failures.
23. **9 Documents**: writes the submission documents (same as the Submit page, part E).
24. **10 Package**: makes `release\<game>\<version>\` with the math, the front end, the tiles and the documents. It refuses when a Stake-level rule fails, and tells you which.

### E. Submit page (documents)

25. Tab **Submit**.
26. **Take screenshots**: the game at the four reviewer sizes (stop a running Preview first; both use port 3007).
27. **Build submission pack**. The page shows:
    - a red list: problems Stake would reject. Fix them first.
    - a yellow list: our own quality rules, each with a **Why**. You may still submit.
    - the **Studio form fields**, each with a **Copy** button.
    - links: **Submission pack (printable)** opens the full document in a new tab. Print it or keep it beside Studio.
28. After step 32 below (math published), come back, type the **Studio math version** and press **Pick event IDs** again, then **Build submission pack** again. Now the replay links are complete.

### F. Stake Studio

29. Studio → your game → **Files** → **Import Files** → folder `release\<game>\<version>\math` → **Start Sync**.
30. **Import Files** → folder `release\<game>\<version>\front` → **Start Sync**.
31. Check the upload list in section 8 of the pack: same files, same sizes.
32. **Publish Game → Math**, then **Publish Game → Front End**. Note the math version number (used in step 28).
33. **Media**: open the Media Editor. Make the 3:4 tile from `tiles\tile.bg.png` + `tiles\tile.fg.png` and the 16:9 cover from `tiles\cover.png`. Set the studio logo in team settings (once per team).
34. **Play Game**: play one round in every mode, watch one replay, and open the game once with `social=true`. Tick these boxes in section 5 of the pack.
35. Run Stake's AI review prompt (https://stake-engine.com/docs-content/prompt.md) on the final build: [instructions/02-run-engine-ai-review.md](../instructions/02-run-engine-ai-review.md). Fix every FAIL.
36. Submission form: paste the **description (blurb)** and features, tick the two confirmations (general disclaimer in the rules; social mode has no restricted phrases; the pack shows the evidence), choose **distribution** (Only on Stake, or the network). Distribution is fixed at launch.
37. Walk the Studio submission checklist, then the owner presses **Submit**.

### G. After review

38. If a reviewer asks for event IDs (loss, normal win, big win, bonus trigger, max win per mode): copy them from section 4 of the pack. Each line has its replay link.
39. Three reviewers rate 0–3 stars; the game needs 6 of 9 points. A failed review locks the thread for 3 days ([05-publish.md](05-publish.md) Review).
40. After approval nothing changes: the math is frozen. A fix is a new version: raise the version on **Overview**, then repeat parts D–F.

## What blocks vs what warns

The rule list with levels is [core/policy.v1.json](../core/policy.v1.json) (owner decision 2026-11-07). The full checklist is [08-compliance.md](08-compliance.md).

- **Blocks (level `stake`)**: Stake would reject the game. Examples: RTP outside 96.0–96.7% in any mode, max win above 1,000,000x or rarer than 1 in 10,000,000, cheapest mode not 1.0x (or its std dev below 0.6), a mode costing more than 50,000x, more than 20 modes, fewer than 100,000 simulations, a restricted title term, restricted social words in mode names, web-sdk sample assets, factory test assets, missing tile or cover art, a test skin.
- **Warns (level `ours`)**: our quality rules; each shows its reason. Examples: RTP outside our 96.15–96.55% margin, max win above 100,000x, empty art slots, no human edit, missing licence or source link, art not signed off, bundle above 10 MB, empty description, no distribution chosen, missing event IDs.

## Verify

- The Submit page says **Ready** and the pack's section 5 has no BLOCKS row.
- `release\<game>\<version>\` holds `math\`, `front\`, `tiles\`, `manifest.json`, `submission.html`, `submission.md`, `pack.json`.
- Studio **Start Approval** readiness shows every check passed.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://stake-engine.com/docs/approval-guidelines/math-verification | critical math tests (RTP band, max win, cheapest mode, cost, simulations) | 2026-11-07 |
| https://stake-engine.com/docs-content/prompt.md | AI review prompt; restricted title terms [213] | 2026-11-07 |
| https://stake-engine.com/docs/approval-guidelines/game-tile-requirements | 3:4 tile and 16:9 cover | 2026-11-07 |
