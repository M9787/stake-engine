"""Turn the owner's raw art and audio downloads into game-ready files (instruction 15, spec in docs/09-assets.md).

Usage (from stake\\, asset venv: see scripts\\assets_requirements.txt):
  .venv-assets\\Scripts\\python.exe scripts\\assets_build.py            build art_in\\ + audio_in\\ into static\\assets\\sv\\
  .venv-assets\\Scripts\\python.exe scripts\\assets_build.py --check    self-test on generated samples in a temp folder
Options: --art DIR --audio DIR --out DIR --font TTF --fallback-font TTF --no-rembg

Stages:
  images  cut-out (rembg, or a black colour key with --no-rembg), trim, square pad, palette pull, shared glow,
          resize, symbol atlas (PixiJS JSON hash) as WebP q85, report (size, KB, alpha, flags)
  font    bitmap font (BMFont .xml + .webp): gold gradient fill, dark stroke
  audio   ffmpeg: trim silence (SFX), loudnorm (-16 LUFS music, -12 SFX), one Howler sprite in ogg + m4a
  log     one ASSET_LICENSES.md row per new input file
Outputs go to a separate folder (static\\assets\\sv\\); instruction 16 wires them into assets.ts.
"""

import argparse
import colorsys
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import date

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "game", "web", "seventh-veil", "static")
SOUNDS_JSON = os.path.join(STATIC, "assets", "audio", "sounds.json")
FONT_DIR = os.path.join(ROOT, "game", "web", "seventh-veil", "fontsrc")

# docs/09 section 1. The palette pull moves hue and saturation toward the nearest of these.
PALETTE = {
    "deep_indigo": "#1B1446",
    "veil_violet": "#5B2A86",
    "antique_gold": "#D4A845",
    "moon_silver": "#C9CED6",
    "ember_red": "#B3362C",
    "night_black": "#0A0812",
}
GLOW = {"color": "#D4A845", "radius": 6, "strength": 0.55}  # one glow for every cut-out asset
PALETTE_PULL = 0.35  # 0 = keep colours, 1 = snap hue to the palette
OFF_STYLE_LIMIT = 0.30  # mean hue distance (0..0.5) above this prints "off-style"
BAD_CUTOUT_LIMIT = 0.25  # share of half-transparent pixels in the alpha area above this prints "bad cut-out"

# docs/09 section 3: file-name pattern -> (group, size in px (w, h), alpha). First match wins.
IMAGE_SPEC = [
    (r"^hero$", None, None, False),
    (r"^(H[1-4]|L[1-4]|S)_", "symbols", (256, 256), True),
    (r"^sigil$", "symbols", (128, 128), True),
    (r"^bg_.*_land$", "backgrounds", (2560, 1440), False),
    (r"^bg_.*_port$", "backgrounds", (1440, 2560), False),
    (r"^frame_reels$", "frames", (1600, 1600), True),
    (r"^panel_bigwin$", "panels", (1400, 800), True),
    (r"^card_.*_intro$", "panels", (1200, 1600), True),
    (r"^veil_transition$", "panels", (2560, 1440), True),
    (r"^ui_spin$", "ui", (256, 256), True),
    (r"^ui_", "ui", (128, 128), True),
    (r"^logo_emblem$", "logo", (1024, 1024), True),
    (r"^tile_bg_3x4$", "tile", (1200, 1600), False),
    (r"^tile_fg_3x4$", "tile", (1200, 1600), True),
    (r"^cover_16x9$", "tile", (1920, 1080), False),
]

# docs/09 section 6: SFX source file -> game sound names. Names ending _1.._5 get rising pitch steps.
SFX_MAP = {
    "click": ["sfx_btn_general"],
    "spin": ["sfx_btn_spin"],
    "stone_drop": [f"sfx_reel_stop_{i}" for i in range(1, 6)] + ["sfx_symbols_landing", "sfx_royals_landing"],
    "crystal_land": [f"sfx_scatter_stop_{i}" for i in range(1, 6)] + ["sfx_scatter_reveal"],
    "crystal_win": ["sfx_scatter_win", "sfx_scatter_win_v2"],
    "riser": ["sfx_anticipation", "sfx_anticipation_start"],
    "chime_1": ["tumble_win_1"],
    "chime_2": ["tumble_win_2"],
    "chime_3": ["tumble_win_3"],
    "chime_4": ["tumble_win_4"],
    "chime_5": ["tumble_win_5"],
    "sigil_mark": ["sfx_multiplier_landing", "sfx_multiplier_update"],
    "sigil_up": ["sfx_multiplier_up", "sfx_multiplier_combine_a", "sfx_multiplier_combine_b"],
    "sigil_burst": ["sfx_multiplier_explosion_a", "sfx_multiplier_explosion_b", "sfx_multiplier_explosion_c", "sfx_wild_explode"],
    "sigil_win": ["sfx_multiplier_win"],
    "sigil_reset": ["sfx_multiplier_reset"],
    "retrigger": ["sfx_fs_respins", "sfx_superfreespin"],
    "coins": ["sfx_bigwin_coinloop"],
    "win_small": ["sfx_winlevel_small", "sfx_winlevel_nice"],
    "win_mid": ["sfx_winlevel_standard", "sfx_winlevel_substantial"],
    "win_end": ["sfx_winlevel_end", "sfx_youwon_panel"],
}
MUSIC_MAP = {
    "bgm_main": ["bgm_main"],
    "bgm_freespin": ["bgm_freespin"],
    "sting_bigwin": ["bgm_winlevel_big", "bgm_winlevel_mega", "bgm_winlevel_epic", "bgm_winlevel_superwin"],
    "sting_maxwin": ["bgm_winlevel_max"],
    "sting_bonus_intro": ["jng_intro_fs"],
}
PITCH_STEP = 1.06  # ~1 semitone per _N step
SPRITE_GAP_MS = 500
LUFS = {"music": -16, "sfx": -12}

# Glyphs of the sample bitmap fonts (gold + silver) plus the formatAmount output (task 03).
GLYPHS = (
    " !\"#$%&()*+,-./0123456789:;=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ~×"
    "€¥£₹₩₱₽₺₫"
)
FONT_PX = 96
FONT_STROKE = 4
GOLD_GRADIENT = ["#F6E3A1", "#D4A845", "#8A6420"]
STROKE_COLOR = "#2A1A08"

AUDIO_EXT = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aiff")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def palette_hues():
    hues = []
    for h in PALETTE.values():
        r, g, b = (c / 255 for c in hex_rgb(h))
        hh, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s > 0.15:  # greys and black carry no useful hue
            hues.append((hh, s))
    return hues


# ---------------------------------------------------------------- images


def spec_for(stem):
    for pattern, group, size, alpha in IMAGE_SPEC:
        if re.match(pattern, stem):
            return group, size, alpha
    return "misc", None, False


def cut_out(img, session):
    """RGBA with the background removed: rembg if available, else a near-black colour key."""
    if session is not None:
        from rembg import remove

        return remove(img.convert("RGBA"), session=session)
    rgba = np.array(img.convert("RGBA"), dtype=np.float32)
    lum = rgba[..., :3].max(axis=2)
    alpha = np.clip((lum - 18) / 40, 0, 1)  # <18 transparent, >58 opaque, soft edge between
    rgba[..., 3] = alpha * 255
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def trim_square(img, pad=0.08):
    bbox = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    side = int(max(img.size) * (1 + 2 * pad))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return canvas


def cover(img, size):
    """Scale and centre-crop to fill `size` (backgrounds, tile art)."""
    w, h = size
    scale = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * scale)), max(h, round(img.height * scale))), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def palette_pull(img, strength=None):
    """Move each pixel's hue toward the nearest palette hue. Returns (image, mean hue distance before)."""
    strength = PALETTE_PULL if strength is None else strength
    arr = np.array(img.convert("RGBA"), dtype=np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3:]
    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    delta = mx - mn
    s = np.where(mx > 0, delta / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(delta, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    targets = np.array([h for h, _ in palette_hues()], dtype=np.float32)
    diff = (targets[None, None, :] - hue[..., None] + 0.5) % 1 - 0.5  # signed shortest hue distance
    nearest = np.take_along_axis(diff, np.abs(diff).argmin(axis=2)[..., None], axis=2)[..., 0]
    mask = (s > 0.12) & (a[..., 0] > 0.05)
    distance = float(np.abs(nearest[mask]).mean()) if mask.any() else 0.0
    hue = np.where(mask, (hue + nearest * strength) % 1, hue)
    # HSV -> RGB
    v = mx
    i = np.floor(hue * 6).astype(int) % 6
    f = hue * 6 - np.floor(hue * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    choices = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]
    out = np.zeros_like(rgb)
    for k, (cr, cg, cb) in enumerate(choices):
        sel = i == k
        out[..., 0][sel], out[..., 1][sel], out[..., 2][sel] = cr[sel], cg[sel], cb[sel]
    merged = np.concatenate([out, a], axis=2)
    return Image.fromarray((merged * 255).clip(0, 255).astype(np.uint8), "RGBA"), distance


def add_glow(img, scale=1.0):
    radius = max(1, round(GLOW["radius"] * scale))
    alpha = img.getchannel("A").filter(ImageFilter.MaxFilter(radius * 2 + 1)).filter(ImageFilter.GaussianBlur(radius))
    alpha = alpha.point(lambda x: int(x * GLOW["strength"]))
    glow = Image.new("RGBA", img.size, hex_rgb(GLOW["color"]) + (0,))
    glow.putalpha(alpha)
    return Image.alpha_composite(glow, img)


def cutout_quality(img):
    a = np.array(img.getchannel("A"))
    area = (a > 8).sum()
    partial = ((a > 16) & (a < 240)).sum()
    return partial / area if area else 1.0


def process_image(path, out_dir, session):
    stem = os.path.splitext(os.path.basename(path))[0]
    group, size, alpha = spec_for(stem)
    if group is None:
        return None  # style source only (hero.png)
    img = Image.open(path)
    flags = []
    if alpha:
        img = trim_square(cut_out(img, session))
        if cutout_quality(img) > BAD_CUTOUT_LIMIT:
            flags.append("bad cut-out")
    else:
        img = img.convert("RGBA")
    img, dist = palette_pull(img)
    if dist > OFF_STYLE_LIMIT:
        flags.append("off-style")
    if size:
        if alpha and size[0] == size[1]:
            img = img.resize(size, Image.LANCZOS)
            img = add_glow(img, size[0] / 256)
        else:
            img = cover(img, size)
    if not alpha:
        img = img.convert("RGB")
    os.makedirs(os.path.join(out_dir, group), exist_ok=True)
    dst = os.path.join(out_dir, group, stem + ".webp")
    img.save(dst, "WEBP", quality=85, method=6)
    return {"name": stem, "group": group, "file": dst, "size": img.size, "kb": round(os.path.getsize(dst) / 1024, 1),
            "alpha": img.mode == "RGBA", "flags": flags, "image": img}


def pack_atlas(items, out_dir, name="symbols"):
    """Grid-pack equal-height items into one WebP + PixiJS JSON-hash atlas."""
    if not items:
        return None
    cell = max(max(i["size"]) for i in items)
    cols = math.ceil(math.sqrt(len(items)))
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (0, 0, 0, 0))
    frames = {}
    for k, it in enumerate(items):
        x, y = (k % cols) * cell, (k // cols) * cell
        w, h = it["size"]
        sheet.paste(it["image"], (x, y))
        frames[it["name"] + ".png"] = {
            "frame": {"x": x, "y": y, "w": w, "h": h},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
            "sourceSize": {"w": w, "h": h},
        }
    img_name = f"{name}.webp"
    sheet.save(os.path.join(out_dir, img_name), "WEBP", quality=85, method=6)
    meta = {"image": img_name, "format": "RGBA8888", "size": {"w": sheet.width, "h": sheet.height}, "scale": "1"}
    json_path = os.path.join(out_dir, f"{name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"frames": frames, "meta": meta}, f, indent=1)
    return json_path


def build_images(art_dir, out_dir, use_rembg=True):
    files = sorted(f for f in os.listdir(art_dir) if f.lower().endswith(IMAGE_EXT)) if os.path.isdir(art_dir) else []
    session = None
    if files and use_rembg:
        try:
            from rembg import new_session

            session = new_session("u2net")
        except ImportError:
            print("warn  rembg not installed: using the black colour key (--no-rembg)")
    results = []
    for f in files:
        r = process_image(os.path.join(art_dir, f), os.path.join(out_dir, "images"), session)
        if r:
            r["source"] = os.path.join(art_dir, f)
            results.append(r)
    atlas = pack_atlas([r for r in results if r["group"] == "symbols"], os.path.join(out_dir, "images"))
    print(f"\nimages ({len(results)}){'  cut-out: rembg u2net' if session else ''}")
    print(f"  {'name':<20}{'group':<12}{'size':<12}{'KB':>8}  alpha  flags")
    for r in results:
        print(f"  {r['name']:<20}{r['group']:<12}{'%dx%d' % r['size']:<12}{r['kb']:>8}  {'yes' if r['alpha'] else 'no ':<5}  {', '.join(r['flags']) or '-'}")
    if atlas:
        print(f"  atlas {os.path.relpath(atlas, ROOT)}")
    return results, atlas


# ---------------------------------------------------------------- font


def vertical_gradient(size, colors):
    w, h = size
    stops = [np.array(hex_rgb(c), dtype=np.float32) for c in colors]
    ys = np.linspace(0, len(stops) - 1, h)
    rows = np.array([stops[int(min(y, len(stops) - 2))] * (1 - (y - int(min(y, len(stops) - 2)))) +
                     stops[int(min(y, len(stops) - 2)) + 1] * (y - int(min(y, len(stops) - 2))) for y in ys])
    return Image.fromarray(np.repeat(rows[:, None, :], w, axis=1).astype(np.uint8), "RGB")


def has_glyph(font, ch):
    """True unless Pillow draws the font's .notdef box for `ch` (no fontTools needed)."""
    if ch == " ":
        return True
    notdef = font.getmask("􏿽")
    mask = font.getmask(ch)
    return mask.size != notdef.size or bytes(mask) != bytes(notdef)


def build_font(font_path, out_dir, name="sv_gold", fallback=None):
    font = ImageFont.truetype(font_path, FONT_PX)
    fb = ImageFont.truetype(fallback, FONT_PX) if fallback else None
    ascent, descent = font.getmetrics()
    pad = FONT_STROKE + 2
    cell_h = ascent + descent + 2 * pad
    glyphs, missing = [], []
    for ch in GLYPHS:
        use = font if has_glyph(font, ch) else (fb if fb and has_glyph(fb, ch) else None)
        if use is None:
            missing.append(ch)
            continue
        adv = use.getlength(ch)
        l, t, r, b = use.getbbox(ch, stroke_width=FONT_STROKE)
        w = max(1, int(math.ceil(r - l)) + 2 * pad) if ch != " " else 1
        img = Image.new("RGBA", (w, cell_h), (0, 0, 0, 0))
        if ch != " ":
            ox, oy = pad - l, pad
            stroke = Image.new("L", img.size, 0)
            ImageDraw.Draw(stroke).text((ox, oy), ch, font=use, fill=255, stroke_width=FONT_STROKE, stroke_fill=255)
            fill = Image.new("L", img.size, 0)
            ImageDraw.Draw(fill).text((ox, oy), ch, font=use, fill=255)
            img.paste(Image.new("RGBA", img.size, hex_rgb(STROKE_COLOR) + (255,)), (0, 0), stroke)
            img.paste(vertical_gradient(img.size, GOLD_GRADIENT).convert("RGBA"), (0, 0), fill)
            xoffset = int(l) - pad
        else:
            xoffset = 0
        glyphs.append((ch, img, xoffset, int(round(adv)) + FONT_STROKE))
    # shelf pack into a 1024-wide page
    page_w, x, y, row_h, placed = 1024, 0, 0, 0, []
    for ch, img, xo, adv in glyphs:
        if x + img.width > page_w:
            x, y = 0, y + row_h + 2
            row_h = 0
        placed.append((ch, img, x, y, xo, adv))
        x += img.width + 2
        row_h = max(row_h, img.height)
    page_h = 2 ** math.ceil(math.log2(y + row_h + 1))
    page = Image.new("RGBA", (page_w, page_h), (0, 0, 0, 0))
    for ch, img, px, py, _, _ in placed:
        page.paste(img, (px, py))
    os.makedirs(out_dir, exist_ok=True)
    page_file = f"{name}.webp"
    page.save(os.path.join(out_dir, page_file), "WEBP", quality=90, method=6)
    root = ET.Element("font")
    ET.SubElement(root, "info", face=os.path.splitext(os.path.basename(font_path))[0], size=str(FONT_PX), bold="0",
                  italic="0", charset="", unicode="1", stretchH="100", smooth="1", aa="1", padding="0,0,0,0", spacing="2,2")
    ET.SubElement(root, "common", lineHeight=str(cell_h), base=str(ascent + pad), scaleW=str(page_w),
                  scaleH=str(page_h), pages="1", packed="0")
    pages = ET.SubElement(root, "pages")
    ET.SubElement(pages, "page", id="0", file=page_file)
    chars = ET.SubElement(root, "chars", count=str(len(placed)))
    for ch, img, px, py, xo, adv in placed:
        ET.SubElement(chars, "char", id=str(ord(ch)), x=str(px), y=str(py), width=str(img.width), height=str(img.height),
                      xoffset=str(xo), yoffset="0", xadvance=str(adv), page="0", chnl="15")
    xml_path = os.path.join(out_dir, f"{name}.xml")
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    print(f"\nfont  {os.path.relpath(xml_path, ROOT)}: {len(placed)} glyphs, page {page_w}x{page_h}"
          + (f"; missing (add --fallback-font): {''.join(missing)}" if missing else ""))
    return xml_path, missing


# ---------------------------------------------------------------- audio


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg failed: {r.stderr.strip()[:300]}")


def duration_ms(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip()) * 1000


def prepare_clip(src, dst, kind, pitch=1.0):
    filters = []
    if kind == "sfx":
        filters.append("silenceremove=start_periods=1:start_threshold=-50dB:stop_periods=-1:stop_threshold=-50dB:stop_duration=0.15")
    if pitch != 1.0:
        filters.append(f"asetrate=44100*{pitch:.4f},aresample=44100")
    filters.append(f"loudnorm=I={LUFS[kind]}:TP=-1.5:LRA=11")
    ffmpeg("-i", src, "-af", ",".join(filters), "-ar", "44100", "-ac", "2", dst)


def build_audio(audio_dir, out_dir, static_root):
    loops = {}
    if os.path.exists(SOUNDS_JSON):
        with open(SOUNDS_JSON, encoding="utf-8") as f:
            sample = json.load(f)
        loops = {k: bool(v[2]) for k, v in sample["sprite"].items() if len(v) > 2}
        volume_config = sample.get("config", {})
    else:
        volume_config = {}
    work = tempfile.mkdtemp(prefix="sv_audio_")
    segments, sprite, found = [], {}, []
    for kind, mapping in (("music", MUSIC_MAP), ("sfx", SFX_MAP)):
        folder = os.path.join(audio_dir, kind)
        files = {os.path.splitext(f)[0]: os.path.join(folder, f) for f in sorted(os.listdir(folder))
                 if f.lower().endswith(AUDIO_EXT)} if os.path.isdir(folder) else {}
        for stem, path in files.items():
            if stem not in mapping:
                print(f"warn  {kind}/{os.path.basename(path)} is not in the docs/09 table, skipped")
                continue
            found.append((kind, path))
            names = mapping[stem]
            stepped = all(re.search(r"_[1-5]$", n) for n in names[:5]) and len(names) >= 5
            variants = {}
            for i, n in enumerate(names):
                pitch = PITCH_STEP ** i if stepped and i < 5 else 1.0
                key = round(pitch, 4)
                if key not in variants:
                    clip = os.path.join(work, f"{stem}_{len(variants)}.wav")
                    prepare_clip(path, clip, kind, pitch)
                    variants[key] = clip
                    segments.append(clip)
                sprite[n] = variants[key]
    if not segments:
        print("\naudio: no input files")
        shutil.rmtree(work, ignore_errors=True)
        return None, found
    # concatenate with gaps; Howler sprite = [start_ms, duration_ms, loop]
    offsets, t = {}, 0.0
    concat_list = os.path.join(work, "list.txt")
    silence = os.path.join(work, "gap.wav")
    ffmpeg("-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", "-t", f"{SPRITE_GAP_MS / 1000}", silence)
    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in segments:
            d = duration_ms(clip)
            offsets[clip] = (round(t), round(d, 3))
            f.write(f"file '{clip}'\nfile '{silence}'\n")
            t += d + SPRITE_GAP_MS
    os.makedirs(out_dir, exist_ok=True)
    joined = os.path.join(work, "sprite.wav")
    ffmpeg("-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", joined)
    ffmpeg("-i", joined, "-c:a", "libvorbis", "-q:a", "4", os.path.join(out_dir, "sounds.ogg"))
    ffmpeg("-i", joined, "-c:a", "aac", "-b:a", "128k", os.path.join(out_dir, "sounds.m4a"))
    rel = "./" + os.path.relpath(out_dir, static_root).replace(os.sep, "/")
    data = {
        "sprite": {n: [offsets[c][0], offsets[c][1], *([True] if loops.get(n) else [])] for n, c in sorted(sprite.items())},
        "src": [f"{rel}/sounds.ogg", f"{rel}/sounds.m4a"],
        "config": {n: volume_config.get(n, {"volume": 1}) for n in sorted(sprite)},
    }
    json_path = os.path.join(out_dir, "sounds.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    shutil.rmtree(work, ignore_errors=True)
    kb = sum(os.path.getsize(os.path.join(out_dir, x)) for x in ("sounds.ogg", "sounds.m4a")) / 1024
    print(f"\naudio  {len(found)} files -> {len(sprite)} sprite names, {len(segments)} clips, ogg+m4a {kb:.0f} KB")
    print(f"  {os.path.relpath(json_path, ROOT)}")
    return json_path, found


# ---------------------------------------------------------------- licence log

LICENSE_HEADER = """# Asset licences — Oracle of Sevens

Template and rules: docs/09-assets.md section 7. `scripts/assets_build.py` adds a row per new input file; fill in Plan, Prompt and Created.

| Asset (game file) | Source file | Tool / source | Plan / licence | Created | Prompt or source URL | Edits |
|---|---|---|---|---|---|---|
"""


def log_licences(path, images, audio_found):
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else LICENSE_HEADER
    added = 0
    rows = []
    for r in images:
        src = os.path.relpath(r["source"], ROOT).replace(os.sep, "/")
        rows.append((src, f"| {os.path.relpath(r['file'], ROOT).replace(os.sep, '/')} | {src} | Midjourney | TODO | TODO | TODO | "
                          f"{'cut-out, ' if r['alpha'] else ''}palette pull, {r['size'][0]}x{r['size'][1]} WebP |"))
    for kind, p in audio_found:
        src = os.path.relpath(p, ROOT).replace(os.sep, "/")
        tool = "Suno" if kind == "music" else "TODO (Kenney / Freesound CC0 / ElevenLabs)"
        rows.append((src, f"| audio sprite | {src} | {tool} | TODO | TODO | TODO | {LUFS[kind]} LUFS{', silence trim' if kind == 'sfx' else ''} |"))
    for src, row in rows:
        if f"| {src} |" not in text:
            text += row + "\n"
            added += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\nlicences  {os.path.relpath(path, ROOT) if path.startswith(ROOT) else path}: {added} new rows")


# ---------------------------------------------------------------- self-test


def make_samples(art, audio):
    os.makedirs(art)
    for name, color, r in (("H1_test", (200, 150, 60), 300), ("L1_test", (90, 50, 140), 220), ("S_test", (150, 160, 190), 360)):
        img = Image.new("RGB", (1024, 1024), (2, 2, 4))
        d = ImageDraw.Draw(img)
        d.ellipse((512 - r, 512 - r, 512 + r, 512 + r), fill=color)
        d.ellipse((512 - r // 3, 512 - r // 3, 512 + r // 3, 512 + r // 3), fill=(240, 230, 200))
        img.save(os.path.join(art, f"{name}.png"))
    os.makedirs(os.path.join(audio, "music"))
    os.makedirs(os.path.join(audio, "sfx"))
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=4", os.path.join(audio, "music", "bgm_main.wav"))
    ffmpeg("-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=0.3", "-f", "lavfi", "-i", "sine=frequency=880:duration=0.4",
           "-filter_complex", "[0][1]concat=n=2:v=0:a=1", os.path.join(audio, "sfx", "stone_drop.wav"))


def check(args):
    tmp = tempfile.mkdtemp(prefix="sv_assets_check_")
    art, audio, out = os.path.join(tmp, "art_in"), os.path.join(tmp, "audio_in"), os.path.join(tmp, "static", "assets", "sv")
    make_samples(art, audio)
    images, atlas = build_images(art, out, use_rembg=not args.no_rembg)
    font_xml, _ = build_font(args.font, os.path.join(out, "fonts"), fallback=args.fallback_font)
    sounds, found = build_audio(audio, os.path.join(out, "audio"), os.path.join(tmp, "static"))
    log_licences(os.path.join(tmp, "ASSET_LICENSES.md"), images, found)
    errors = []
    syms = [r for r in images if r["group"] == "symbols"]
    if len(syms) != 3:
        errors.append(f"expected 3 symbols, got {len(syms)}")
    if len({r["size"] for r in syms}) != 1:
        errors.append(f"symbol sizes differ: {[r['size'] for r in syms]}")
    for r in syms:
        im = Image.open(r["file"])
        if im.mode != "RGBA" or im.getpixel((0, 0))[3] != 0:
            errors.append(f"{r['name']}: no transparent corner")
    with open(atlas, encoding="utf-8") as f:
        a = json.load(f)
    if len(a["frames"]) != 3 or not os.path.exists(os.path.join(os.path.dirname(atlas), a["meta"]["image"])):
        errors.append("atlas frames or image missing")
    chars = ET.parse(font_xml).getroot().find("chars")
    if int(chars.get("count")) < 60:
        errors.append(f"font has only {chars.get('count')} glyphs")
    with open(sounds, encoding="utf-8") as f:
        s = json.load(f)
    want = {"bgm_main", *SFX_MAP["stone_drop"]}
    if set(s["sprite"]) != want:
        errors.append(f"sprite names {sorted(s['sprite'])}")
    if not s["sprite"]["bgm_main"][2:] == [True]:
        errors.append("bgm_main must loop")
    if any(v[1] <= 0 for v in s["sprite"].values()):
        errors.append("empty sprite clip")
    if len({v[0] for k, v in s["sprite"].items() if k.startswith("sfx_reel_stop")}) != 5:
        errors.append("reel stops 1-5 should be 5 pitch steps")
    for ext in ("ogg", "m4a"):
        if duration_ms(os.path.join(out, "audio", f"sounds.{ext}")) < 4000:
            errors.append(f"sounds.{ext} too short")
    print(f"\ncheck output kept in {tmp}")
    if errors:
        print("CHECK FAILED:\n  " + "\n  ".join(errors))
        return 1
    print("CHECK OK")
    return 0


def apply_theme(game_id):
    """Take palette, glow and font colours from skins/<skin>/game.json "theme" (docs/10 section 2).
    Fields the theme leaves out keep the defaults above (the Oracle style bible, docs/09)."""
    global PALETTE, GLOW, PALETTE_PULL, GOLD_GRADIENT, STROKE_COLOR
    sys.path.insert(0, os.path.join(ROOT, "tools", "gamedef"))
    from gamectx import Game

    theme = Game(game_id).gdef.get("theme", {})
    PALETTE = theme.get("palette", PALETTE)
    GLOW = theme.get("glow", GLOW)
    PALETTE_PULL = theme.get("palettePull", PALETTE_PULL)
    GOLD_GRADIENT = theme.get("fontGradient", GOLD_GRADIENT)
    STROKE_COLOR = theme.get("fontStroke", STROKE_COLOR)
    print(f"theme {game_id}: {len(PALETTE)} palette colours, pull {PALETTE_PULL}, glow {GLOW['color']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", default="seventh_veil", help="game id whose game.json theme sets palette, glow and font colours")
    ap.add_argument("--check", action="store_true", help="self-test on generated samples (writes only to a temp folder)")
    ap.add_argument("--art", default=os.path.join(ROOT, "art_in"))
    ap.add_argument("--audio", default=os.path.join(ROOT, "audio_in"))
    ap.add_argument("--out", default=os.path.join(STATIC, "assets", "sv"))
    ap.add_argument("--font", default=os.path.join(FONT_DIR, "CinzelDecorative-Bold.ttf"))
    ap.add_argument("--fallback-font", default=None, help="TTF for glyphs the main font lacks (e.g. ₹ ₩ ₱ ₽ ₺ ₫)")
    ap.add_argument("--no-rembg", action="store_true", help="black colour key instead of rembg")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # glyph lists hold symbols cp1252 lacks
    apply_theme(args.game)
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("FAIL  ffmpeg/ffprobe not on PATH")
        return 1
    if args.check:
        return check(args)
    images, _ = build_images(args.art, args.out, use_rembg=not args.no_rembg)
    build_font(args.font, os.path.join(args.out, "fonts"), fallback=args.fallback_font)
    _, found = build_audio(args.audio, os.path.join(args.out, "audio"), STATIC)
    log_licences(os.path.join(ROOT, "ASSET_LICENSES.md"), images, found)
    flagged = [r["name"] for r in images if r["flags"]]
    if flagged:
        print(f"\nre-do in Midjourney (Vary Subtle): {', '.join(flagged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
