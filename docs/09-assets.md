# 09 — Assets: style bible, prompts, file list

## Purpose

This doc is for the owner. It lists every image, music track and sound the game needs, with copy-paste prompts.
- The owner makes the raw files in Midjourney, Suno, ElevenLabs and CC0 libraries, in 3 short sittings.
- The owner drops the raw files into `art_in\` and `audio_in\`.
- `scripts\assets_build.py` (instruction 15) cuts out, recolours, sizes and packs them.

Nobody has to draw.

Symbol names and tiers come from [06-game-design.md](06-game-design.md). Asset keys come from `game\web\seventh-veil\src\game\assets.ts`; sound names come from `static\assets\audio\sounds.json`.

## Prereq

- A Midjourney paid plan (Basic is enough, see Licences).
- A Suno Pro plan.
- Optional: an ElevenLabs Starter plan.
- An empty `art_in\` and `audio_in\` at the repo root. Both are git-ignored.

## 1. Style bible

**Theme:** a mystic tarot reading behind the seventh veil. An oracle's table at night, with candle smoke, a moonlit sky and gilded cards. The mood is mature and elegant: quiet mystery, not horror.

**Palette.** Every image should sit on these 6 colours. The build script pulls hue and saturation toward them.

| Name | Hex | Use |
|---|---|---|
| Deep indigo | `#1B1446` | backgrounds, card faces |
| Veil violet | `#5B2A86` | veils, glows, low symbols |
| Antique gold | `#D4A845` | frames, linework, wins, logo |
| Moon silver | `#C9CED6` | moon, highlights, runes |
| Ember red | `#B3362C` | Tower, big-win accents (use sparingly) |
| Night black | `#0A0812` | deepest shadows, cut-out background |

**Light:** soft candle light from below plus cool moonlight from above. Gold catches the light; there are no hard white highlights.

**Line and texture:** engraved gold linework, like a gilded card edge, with fine painterly detail and a faint paper and velvet grain. Shapes are bold and readable at 128 px.

**Avoid:**
- cartoon, chibi or child-like faces and proportions (jurisdiction rule: no child appeal);
- Stake or Engine logos and any real brand;
- text, letters or numbers in any image (the game draws all text itself);
- copies of real tarot decks. Rider-Waite art is public domain in the US, but the reviewers check originality, so make **original** designs only;
- photo realism, neon "cyber" looks, emoji-like icons and stock gradients. The rankings page names these as low-rating causes.

## 2. Midjourney consistency recipe

Use the same 4 things on every image:

1. **Suffix.** Paste this after every prompt, unchanged:

   ```
   , original mystic tarot artwork, engraved antique gold linework, deep indigo and veil violet with moon silver accents, soft candlelight and moonlight rim light, painterly fine detail, elegant mature mood, no text, no letters, no numbers --raw --v 8.2 --s 150 --seed 7777
   ```

2. **Style reference.** After sitting 1 step 2, add `--sref <URL of your chosen hero image>` to every later prompt.
3. **Aspect ratio:** `--ar 1:1` for symbols and icons, `--ar 16:9` for landscape art, `--ar 9:16` for portrait art, `--ar 3:4` for the tile.
4. **Cut-out background.** Symbols, icons and the logo get this sentence before the suffix: `isolated object centered on a plain flat black background, whole object visible, no glow, no shadow, no frame`. The script removes the black background and adds one shared glow, so all symbols match.

Notes:
- `--raw` is the V8 name for less automatic styling, and V8.2 is the current default model (Sources). If Midjourney changes the default model, keep `--v 8.2` for every asset, so the whole set uses one model.
- Make 4 images per prompt. Pick 1, then **Upscale (Subtle)**. Download as PNG.
- Name each file exactly as in the table, then drop it into `art_in\`.

## 3. Asset table

Size = the size in the game. The script makes it from the upscaled download (about 2048 px). "Alpha" means a transparent background.

### Sitting 1 — hero and symbols (about 1 hour)

| File name (`art_in\`) | Game key | Size | Alpha | Variants | Prompt (add the cut-out sentence and the suffix) |
|---|---|---|---|---|---|
| `hero.png` | — (style source) | — | no | 4, pick 1 | `an oracle's round table at night under a veil of violet silk, seven tarot cards fanned out, a crystal ball glowing softly, a full moon through tall arched windows --ar 16:9` (no cut-out sentence) |
| `H1_priestess.png` | H1 | 256×256 | yes | 4 | `tarot card emblem of The High Priestess, a veiled woman's serene face in profile, crescent moon crown, holding a scroll, framed by two pillars` |
| `H2_tower.png` | H2 | 256×256 | yes | 4 | `tarot card emblem of The Tower, a tall dark stone tower struck by a golden lightning bolt, ember red flames at the windows` |
| `H3_moon.png` | H3 | 256×256 | yes | 4 | `tarot card emblem of The Moon, a large silver full moon with a calm face, two small towers and drops of light falling below` |
| `H4_magician.png` | H4 | 256×256 | yes | 4 | `tarot card emblem of The Magician, a raised hand holding a gold wand, infinity symbol floating above, cup sword and coin at the base` |
| `L1_fehu.png` | L1 | 256×256 | yes | 4 | `carved rune stone with the Elder Futhark rune Fehu, moon silver stone, rune inlaid with antique gold` |
| `L2_ansuz.png` | L2 | 256×256 | yes | 4 | `carved rune stone with the Elder Futhark rune Ansuz, moon silver stone, rune inlaid with veil violet enamel` |
| `L3_raido.png` | L3 | 256×256 | yes | 4 | `carved rune stone with the Elder Futhark rune Raido, moon silver stone, rune inlaid with deep indigo enamel` |
| `L4_kenaz.png` | L4 | 256×256 | yes | 4 | `carved rune stone with the Elder Futhark rune Kenaz, moon silver stone, rune inlaid with ember red enamel` |
| `S_crystal.png` | S | 256×256 | yes | 4 | `a crystal ball on a small gold claw stand, swirling violet mist and tiny stars inside` |
| `sigil.png` | multiplier spot (all states) | 128×128 | yes | 4 | `a flat round occult sigil medallion, seven-pointed star inside a circle of small engraved symbols, single colour gold` |

**Rune shapes:** Midjourney often draws runes wrong. If a rune shape is wrong, keep the stone anyway. The agent can overlay the correct glyph in code from a font.

**Multiplier spot states:** one sigil only. The game tints it per state, so there is nothing more to generate:

| State | Tint |
|---|---|
| marked | `#C9CED6` at 40% |
| x2–x8 | `#D4A845` |
| x16–x64 | `#5B2A86` + gold rim |
| x128–x512 | `#B3362C` + gold rim |
| x1024 | white-gold pulse |

### Sitting 2 — backgrounds, frame, panels, UI (about 1 hour)

| File name | Game key | Size | Alpha | Variants | Prompt (add `--sref`; cut-out sentence only where Alpha = yes) |
|---|---|---|---|---|---|
| `bg_base_land.png` | foregroundAnimation (base) | 2560×1440 | no | 4 | `the oracle's chamber at night, tall arched windows with a full moon, violet veils hanging, candles, empty center space for a game board --ar 16:9` |
| `bg_base_port.png` | foregroundAnimation (mobile) | 1440×2560 | no | 4 | same as above `--ar 9:16` |
| `bg_star_land.png` | foregroundFeatureAnimation (Star) | 2560×1440 | no | 4 | `the oracle's chamber opened to a starry night sky, a bright seven-pointed star above, silver star dust, empty center space --ar 16:9` |
| `bg_star_port.png` | — (mobile) | 1440×2560 | no | 4 | same as above `--ar 9:16` |
| `bg_tower_land.png` | foregroundFeatureAnimation (Tower) | 2560×1440 | no | 4 | `a dark stone tower interior during a storm, golden lightning outside the windows, ember red glow, empty center space --ar 16:9` |
| `bg_tower_port.png` | — (mobile) | 1440×2560 | no | 4 | same as above `--ar 9:16` |
| `frame_reels.png` | reelsFrame / reelhouse | 1600×1600 | yes | 4 | `an ornate square frame of engraved antique gold with small moon and star ornaments at the corners, empty transparent center, front view, flat --ar 1:1` |
| `panel_bigwin.png` | bigwin | 1400×800 | yes | 4 | `a wide ornate gold cartouche banner with violet velvet inside, rays of light behind, empty center for text --ar 16:9` |
| `card_star_intro.png` | fsIntro (Star) | 1200×1600 | yes | 4 | `a single large tarot card back showing a seven-pointed star, gold border, glowing softly --ar 3:4` |
| `card_tower_intro.png` | fsIntro (Tower) | 1200×1600 | yes | 4 | `a single large tarot card back showing a lightning-struck tower, gold border, ember glow --ar 3:4` |
| `veil_transition.png` | transition | 2560×1440 | yes | 2 | `a sheer violet silk veil flowing across the whole frame, translucent, folds catching gold light --ar 16:9` |
| `ui_spin.png` | bet button | 256×256 | yes | 4 | `a round gold medallion button with a circular arrow made of a crescent moon` |
| `ui_plus.png`, `ui_minus.png` | bet + / − | 128×128 | yes | 4 each | `a small round gold button with an engraved plus sign` / `… minus sign` |
| `ui_menu.png` | menu | 128×128 | yes | 4 | `a small round gold button with three horizontal engraved lines` |
| `ui_auto.png` | autoplay | 128×128 | yes | 4 | `a small round gold button with an engraved infinity loop` |
| `ui_turbo.png` | turbo | 128×128 | yes | 4 | `a small round gold button with an engraved lightning bolt` |
| `ui_sound.png` | sound | 128×128 | yes | 4 | `a small round gold button with an engraved bell` |

### Sitting 3 — logo, tile, re-dos (about 1 hour)

| File name | Use | Size | Alpha | Variants | Prompt |
|---|---|---|---|---|---|
| `logo_emblem.png` | loader + title emblem | 1024×1024 | yes | 4 | `a gold emblem of seven small stars arched over a veiled eye, ornate engraved` + cut-out sentence. The words "ORACLE OF SEVENS" are added by the script with the game font, never by Midjourney. |
| `tile_bg_3x4.png` | Engine tile BG (`OracleOfSevens-BG`) | 1200×1600 | no | 4 | `bright mystic key art, a glowing crystal ball and fanned tarot cards in front of a radiant full moon, rich violet and gold, well lit, no dark edges --ar 3:4` |
| `tile_fg_3x4.png` | Engine tile FG (`OracleOfSevens-FG.png`) | 1200×1600 | yes | 4 | `the High Priestess figure holding a crystal ball, half-length, facing the viewer` + cut-out sentence `--ar 3:4` |
| `cover_16x9.png` | 16:9 cover art | 1920×1080 | no | 4 | the tile BG prompt with `--ar 16:9` |
| `provider_logo.png` | Provider logo (`ProviderName-Logo.png`) | 338×134 | yes | — | made by the script: white provider name in the game font on a transparent background. No Midjourney needed. |

Tile rules (Engine tile requirements): no added words, prices or multipliers on the art. BG + FG ≤3 MB together. The art must stay bright at the edges.

Re-dos: the build script prints `bad cut-out` (alpha edge noise) or `off-style` (palette distance too high) per file. Regenerate those with **Vary (Subtle)**.

### Keys we keep from the sample for now

The math has no wild and no M symbol. Keys `H5`, `M`, `W`, `explosion` and `coins` stay as sample art until instruction 16 removes them from `assets.ts`. Do not generate art for them.

Fonts `goldFont`, `goldBlur`, `silverFont` and `purpleFont` are rebuilt by the script from **Cinzel Decorative** (OFL), so nothing needs generating.

## 4. Batch order

| Sitting | What | Done when |
|---|---|---|
| 1 | hero → pick → copy its URL into `--sref`; then the 9 symbols and the sigil | 11 files in `art_in\` |
| 2 | 6 backgrounds, frame, big-win panel, 2 intro cards, veil, 7 UI buttons | 18 files in `art_in\` |
| 3 | logo emblem, tile BG and FG, cover, plus re-dos the script flagged | 4 files + re-dos |

After each sitting, tell the agent "art sitting N done". The agent runs `scripts\assets_build.py` and shows the report.

## 5. Music (Suno Pro)

Settings: **Instrumental** on, plus the model Suno marks as current. Download as WAV if offered, otherwise MP3. Save to `audio_in\music\` with the file name shown.

| File | Game sound | Length | Prompt |
|---|---|---|---|
| `bgm_main.wav` | `bgm_main` | 2:00, loop | `dark ambient mystical underscore, slow 70 bpm, soft hand drums, low strings drone, celesta and harp motifs, whispered choir pads, calm and hypnotic, seamless loop, no vocals` |
| `bgm_freespin.wav` | `bgm_freespin` | 2:00, loop | `mystical cinematic build, 100 bpm, pulsing taiko, rising strings, shimmering bells, choir oohs, hopeful tension, seamless loop, no vocals` |
| `sting_bigwin.wav` | `bgm_winlevel_big` … `bgm_winlevel_superwin` | 8 s | `short triumphant orchestral sting, harp glissando into gold brass chord and choir, mystical, ends on sustained chord` |
| `sting_maxwin.wav` | `bgm_winlevel_max` | 12 s | `epic mystical victory fanfare, full choir and orchestra, timpani roll, bells, huge final chord, 12 seconds` |
| `sting_bonus_intro.wav` | `jng_intro_fs` | 5 s | `short magical reveal sting, rising shimmer, crystal chimes, deep boom, 5 seconds` |

Suno makes full songs, so expect 2–4 minute files. The script cuts the loops at the best bar and crossfades the loop point. For the short stings, generate a short clip and the script trims it.

Suno Pro allows **20 downloads per month**. This list needs 5 downloads plus re-dos, so keep re-dos under 15.

## 6. Sound effects (CC0 first, ElevenLabs optional)

Save to `audio_in\sfx\` with the file name shown. One source file can feed several game sound names; the script maps them and varies pitch where needed.

| Source file | Game sound names it feeds | Source | Search or prompt |
|---|---|---|---|
| `click.wav` | `sfx_btn_general` | Kenney "Interface Sounds" (CC0) | soft click |
| `spin.wav` | `sfx_btn_spin` | Kenney "Interface Sounds" | confirmation |
| `stone_drop.wav` | `sfx_reel_stop_1`–`_5`, `sfx_symbols_landing`, `sfx_royals_landing` | Kenney "Impact Sounds" (CC0) | light stone impact (script pitches 1–5) |
| `crystal_land.wav` | `sfx_scatter_stop_1`–`_5`, `sfx_scatter_reveal` | Freesound, CC0 filter | "crystal glass chime" |
| `crystal_win.wav` | `sfx_scatter_win`, `sfx_scatter_win_v2` | Freesound CC0, or ElevenLabs | `magical crystal ball activation, rising shimmer and chime` |
| `riser.wav` | `sfx_anticipation`, `sfx_anticipation_start` | ElevenLabs or Freesound CC0 | `slow mystical riser, swelling strings and shimmer, 3 seconds` |
| `chime_1.wav` … `chime_5.wav` | `tumble_win_1`–`_5` | Freesound CC0 | "bell chime" at 5 rising pitches |
| `sigil_mark.wav` | `sfx_multiplier_landing`, `sfx_multiplier_update` | ElevenLabs | `soft magical glyph appearing, airy whoosh with a tiny bell` |
| `sigil_up.wav` | `sfx_multiplier_up`, `sfx_multiplier_combine_a`, `_b` | ElevenLabs | `magic power-up, bright ascending sparkle` |
| `sigil_burst.wav` | `sfx_multiplier_explosion_a`, `_b`, `_c`, `sfx_wild_explode` | ElevenLabs or Kenney "Sci-fi Sounds" | `golden magic burst, short and punchy` |
| `sigil_win.wav` | `sfx_multiplier_win` | ElevenLabs | `rich magical chord hit with sparkle tail` |
| `sigil_reset.wav` | `sfx_multiplier_reset` | Kenney "Interface Sounds" | soft descending tone |
| `retrigger.wav` | `sfx_fs_respins`, `sfx_superfreespin` | ElevenLabs | `mystic gong with rising choir, 2 seconds` |
| `coins.wav` | `sfx_bigwin_coinloop` | Kenney "Casino Audio" (CC0) | coin loop (the script loops it) |
| `win_small.wav` | `sfx_winlevel_small`, `sfx_winlevel_nice` | Kenney "Casino Audio" | short positive jingle |
| `win_mid.wav` | `sfx_winlevel_standard`, `sfx_winlevel_substantial` | Kenney "Casino Audio" | longer positive jingle |
| `win_end.wav` | `sfx_winlevel_end`, `sfx_youwon_panel` | Freesound CC0 | "harp resolve" |

That is 21 source files feeding 44 SFX names. The other 8 names are the music tracks and stings in section 5, so all 52 names in `sounds.json` are covered.

- **Kenney.nl** packs are CC0: no credit needed, commercial use OK. Download each pack's zip from kenney.nl (the agent asks before downloading).
- **Freesound:** tick the "Creative Commons 0" licence filter, and copy each sound's page URL into the licence log.
- **ElevenLabs:** commercial use needs a paid plan (Starter or higher). Its music terms exclude "Studio Games" on self-serve plans. Whether the same applies to sound effects is open: PROJECT.md §11 Q16. **Use CC0 sources until Q16 is closed.**

## 7. Licence log (`ASSET_LICENSES.md` at the repo root)

`scripts\assets_build.py` adds one row per input file it finds. The owner fills in Prompt and Plan.

```markdown
# Asset licences — Oracle of Sevens

| Asset (game file) | Source file | Tool / source | Plan / licence | Created | Prompt or source URL | Edits |
|---|---|---|---|---|---|---|
| assets/spines/symbols/symbols.webp (H1) | art_in/H1_priestess.png | Midjourney V8.2 | Basic, paid (ToS 2026-05-27) | 2026-11-02 | "tarot card emblem of The High Priestess…" | cut-out, palette match, glow, 256 px |
| assets/audio/sounds.ogg (bgm_main) | audio_in/music/bgm_main.wav | Suno | Pro, paid at creation | 2026-11-03 | "dark ambient mystical underscore…" | loop cut, −16 LUFS |
| assets/audio/sounds.ogg (sfx_btn_general) | audio_in/sfx/click.wav | Kenney Interface Sounds | CC0 1.0 | 2026-11-03 | https://kenney.nl/assets/interface-sounds | −12 LUFS |
```

## Licences (checked 2026-10-28)

| Tool | Rule that matters | Source |
|---|---|---|
| Midjourney | You own the images you make. A company with more than $1M a year in revenue needs Pro or Mega. Images are **public by default**; Stealth needs Pro or Mega, so the art is visible on Midjourney before launch. Terms effective 2026-05-27. | Midjourney ToS |
| Suno | Songs downloaded on a paid plan (Pro/Premier) are yours to use commercially. Pro has 20 downloads/month (from 2026-09-03). Free downloads are personal use only. | Suno blog 2026-08-10, suno.com/terms |
| ElevenLabs | Paid plans include a commercial licence. Its music terms exclude Studio Games on self-serve plans; the SFX rule is open (Q16). | ElevenLabs pricing, music terms |
| Kenney | CC0 1.0 public domain. | kenney.nl |
| Cinzel Decorative | SIL Open Font License 1.1: free to embed in a game, and the font may not be sold on its own. | github.com/google/fonts `ofl/cinzeldecorative` |

## Verify

- Every key in `assets.ts` that we keep has a row in section 3, or is listed under "Keys we keep from the sample for now".
- Every name in `sounds.json` `sprite` maps to a row in section 5 or 6.
- Every prompt pastes into Midjourney or Suno unchanged.

## Sources

| URL | Proves | Checked |
|---|---|---|
| https://docs.midjourney.com/hc/en-us/articles/32083055291277-Terms-of-Service | ownership, $1M revenue rule, public by default, Stealth on Pro/Mega, effective 2026-05-27 | 2026-10-28 |
| https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version | V8.2 default since 2026-07-24, seeds ~identical | 2026-10-28 |
| https://suno.com/blog/suno-updates-tos | paid-plan downloads usable commercially, Pro 20 downloads/month from 2026-09-03 | 2026-10-28 |
| https://elevenlabs.io/music-terms | self-serve music excludes Studio Games | 2026-10-28 |
| https://elevenlabs.io/pricing | Starter includes a commercial licence | 2026-10-28 |
| https://studio.engine.io/docs/approval-guidelines/game-quality-rankings | generic AI assets, mismatched styles, stock fonts and emoji icons lower the rating | 2026-10-28 |
| https://stake-engine.com/docs/approval-guidelines/game-tile-requirements | tile BG/FG, 3 MB, no added words | 2026-10-28 |
