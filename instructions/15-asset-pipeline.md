# 15 — Asset pipeline script

**Goal:** One command turns the user's raw downloads into game-ready, consistent, small files. The agent does the "paint-over" work in code.

**Why:** The user can't draw (2026-10-28). Raw AI images vary in edges, colour and size, and mismatched styles lower the rating.

**Depends on:** 14.

## Steps
1. Create `scripts\assets_build.py`. Run it with the math venv Python, or a separate venv if packages are needed. **Ask the user before installing any package** (CLAUDE.md: no installs outside the milestone; M6 covers art).
2. Input folders: `art_in\` and `audio_in\` at the repo root (git-ignored raw files). Output: `game\web\seventh-veil\static\assets\...`.
3. Image steps:
   1. Remove the background: `rembg` (offline model) or a colour key for flat backgrounds.
   2. Trim and centre on a square canvas with even padding.
   3. Colour-match to the palette in docs/09 by adjusting hue and saturation toward the bible colours.
   4. Add a consistent outer glow or outline: the same width, colour and blur for all symbols.
   5. Resize to the target size, plus a 2x version if needed.
   6. Pack symbols into one atlas (PixiJS JSON hash format) and export WebP at quality 85.
   7. Print a report: name, size in KB, alpha yes/no.
4. Font step: render an OFL display font, picked in docs/09, to a bitmap font (`.xml` + `.webp`) with a gold gradient and stroke. Use the glyph set from task 03.
5. Audio steps:
   1. Normalise loudness (about −16 LUFS for music, −12 for effects).
   2. Trim silence.
   3. Build one Howler sprite in ogg + m4a. Keep the sprite names from `src\game\sound.ts`.
6. Write `ASSET_LICENSES.md` rows for every input file found.

## Done test
- `python scripts\assets_build.py --check` runs on a sample folder with 3 test images and 2 sounds, and writes valid outputs.
- The report shows every symbol at the same size with alpha.
