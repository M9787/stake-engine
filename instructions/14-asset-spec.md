# 14 — Asset spec: `docs\09-assets.md`

**Goal:** One document gives the user exact Midjourney and Suno prompts, file names and sizes. The user generates everything in 2–3 short sittings without having to think about design.

**Why:**
- "Over-reliance on generic AI-generated assets", "mismatched art styles" and "standard fonts, gradients, emoji icons" lead to low ratings (https://studio.engine.io/docs/approval-guidelines/game-quality-rankings, 2026-10-28).
- The user can't draw and has <5 h/week (2026-10-28). So the prompts must produce one consistent style without a paint-over.

**Depends on:** 13.

## What the doc must contain
1. **Style bible** (1 page):
   - the theme: mystic tarot, a seventh veil, an oracle;
   - a palette of 6 hex colours (deep indigo, violet, gold, moon-silver, ember red, night black);
   - lighting, line style and texture;
   - what to avoid: no cartoon or child-like look (jurisdiction rule), no Stake branding, no text in images, no real tarot deck copies (Rider-Waite artwork is public domain in the US, but use original designs).
2. **Consistency recipe for Midjourney:**
   - one master prompt suffix;
   - one `--sref` image (the first approved hero image);
   - fixed `--seed`;
   - `--style raw`, `--ar 1:1` for symbols, `--v` set to the current version.
   
   Write the exact text so the user can copy and paste it.
3. **Asset table:** one row per asset the game loads (key from `game\web\seventh-veil\src\game\assets.ts`), with these columns:
   - file name;
   - pixel size (symbols 256×256 for the game, generate at 1024);
   - transparent yes/no;
   - prompt;
   - how many variants to make.

   Include:
   - symbols H1–H4 (four tarot figures: Oracle, Moon, Tower, Star) and L1–L4 (four runes or suits);
   - scatter S (crystal ball);
   - multiplier spot states (marked, x2–x1024 glow levels: these can be one sigil plus code colour);
   - reel frame; base background; bonus background (Star and Tower variants);
   - big-win panel backdrop; bonus intro card; Tower intro card; transition veil;
   - logo (title art, no stock font); UI button set (spin, +/−, menu, auto, sound);
   - provider logo (white on transparent, about 338×134);
   - tile key art for 3:4 and 16:9 (no text, bright, no dark edges).
4. **Batch order:** sitting 1 is the hero image (to set the style) plus symbols. Sitting 2 is backgrounds, frame and UI. Sitting 3 is the logo, tile art and re-dos.
5. **Music (Suno):** prompt text plus length for each track:
   - base loop (2:00, seamless);
   - bonus loop (2:00);
   - big-win sting (8 s);
   - max-win sting (12 s);
   - bonus intro sting (5 s).

   Note: commercial use needs a paid Suno plan at the time of creation. The user has Pro ($10).
6. **Sound effects list** (about 25 names, mapped to the 44 sprite names in `src\game\sound.ts`):
   - which to make with ElevenLabs Sound Effects (Starter plan, commercial licence);
   - which to take from CC0 sources (Kenney.nl, Freesound with a CC0 filter).
7. **Licence log template** for `ASSET_LICENSES.md`: asset, tool, plan, date, prompt, edits.

## Done test
- `docs\09-assets.md` exists, and every key in `assets.ts` that we keep has one row.
- The prompts can be copied and pasted as they are.
- The user can follow sitting 1 in under 1 hour.

## Notes
- Check current Midjourney and Suno licence terms on their sites before writing the doc. Add the URL and date to Sources.
