# 03 — Make the art with Midjourney (3 short sittings)

**Why:** Art decides most of the star rating. Only 3★ games appear in New Releases. Reviewers mark down "generic AI-generated assets" and mixed styles. You don't need to draw: the agent's prompts keep the style the same, and the agent's script cleans every image.

**Before you start:** the agent has written `docs\09-assets.md` (agent task 14).

## Setup (10 min, once)
1. Go to https://www.midjourney.com and subscribe to **Basic** (about $10/month). Check the current price on the site.
2. You need a paid plan for commercial use. Check the current terms page and tell the agent the date.

## Sitting 1 — style + symbols (1 h)
1. Open `docs\09-assets.md` → "Sitting 1".
2. Paste the **hero prompt**. Make 4 versions. Pick the one you like most.
3. Copy that image's URL. All other prompts use it as `--sref <url>` to keep the style.
4. Paste each symbol prompt (H1–H4, L1–L4, S). For each one, pick the best of 4, then **Upscale**.
5. Download each pick. Name it exactly as the table says (for example `H1_oracle.png`). Save it to `C:\Users\User\Desktop\Claude Code\stake\art_in\`.

## Sitting 2 — backgrounds, frame, UI (1 h)
- Same process with the "Sitting 2" rows.

## Sitting 3 — logo, tile art, redo (1 h)
- Same process with the "Sitting 3" rows.
- Redo any image the agent's script flagged as "bad cut-out" or "off-style".

## Rules
- Never put words, numbers or "x1000" in the images.
- No cartoon or child-like faces. No real logos. No copies of famous tarot decks.
- If an image has messy hands or faces, regenerate it (**Vary (Subtle)**). Do not try to fix it yourself.

## Done when
- Every row in docs/09 has a file in `art_in\`. Tell the agent "art sitting N done".
