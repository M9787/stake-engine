r"""Images for factory TEST assets (tools\assets\test_assets.py). Deterministic, Pillow + numpy only.

Every image is made at its slot size (catalogue px; 1024 wide when px is null), so the bundle stays small:
  symbols  high tier = a distinct gem / crown / shield / cut-diamond shape per symbol, low tier = a rounded
           tile with a large letter (A K Q J, then roman numerals), scatter = a gold star burst; each pay
           symbol gets its own hue (palette hues first, missing ones spread round the colour wheel)
  scenes   backgrounds = soft painted gradient with vignette; tile/cover/hero = bright key art with the
           game's display name large inside the safe area; frame, banner, card, logo, ui buttons styled
TEST mode may show letters in images (low symbols, title); precheck blocks test assets from release.
Alpha images keep every opaque pixel at brightness >= 64, so ingest's black colour key keeps them whole.
"""

import colorsys
import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "core" / "web" / "cluster-tumble" / "fontsrc"
TITLE_FONT = FONT_DIR / "CinzelDecorative-Black.ttf"
LOW_GLYPHS = ["A", "K", "Q", "J", "I", "II", "III", "IV"]
HIGH_SHAPES = ["brilliant", "crown", "shield", "diamond", "hexagon", "heart"]
SCATTER_HUE = 0.13  # gold star burst
SS = 4  # supersampling for small images (symbols, ui)


# ---------------------------------------------------------------- colour

def seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hsv(h, s, v, a=255):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, min(1, max(0, s)), min(1, max(0, v)))
    return (round(r * 255), round(g * 255), round(b * 255), a)


def to_hsv(rgb):
    return colorsys.rgb_to_hsv(*(c / 255 for c in rgb[:3]))


def hue_dist(a, b):
    d = abs(a - b) % 1.0
    return min(d, 1 - d)


class Theme:
    """Palette from game.json theme.palette, plus distinct hues for the pay symbols."""

    def __init__(self, gdef: dict, texts: dict):
        pal = [hex_rgb(v) for v in (gdef.get("theme", {}).get("palette") or {}).values() if isinstance(v, str) and v.startswith("#")]
        self.pal = pal if len(pal) >= 2 else [(16, 24, 38), (224, 160, 48), (31, 122, 122), (216, 226, 234)]
        by_v = sorted(self.pal, key=lambda c: to_hsv(c)[2])
        self.dark, self.light = by_v[0], by_v[-1]
        sat = sorted(self.pal, key=lambda c: -to_hsv(c)[1] * to_hsv(c)[2])
        self.accent_hue = to_hsv(sat[0])[0] if to_hsv(sat[0])[1] > 0.25 else 0.11
        self.base_hue = to_hsv(self.dark)[0] if to_hsv(self.dark)[1] > 0.15 else 0.62
        self.name = gdef.get("identity", {}).get("displayName") or texts.get("game.name", "Game").title()
        syms = gdef.get("symbols", [])
        highs = [s["id"] for s in syms if s.get("role") == "pay" and s.get("tier") == "high"]
        lows = [s["id"] for s in syms if s.get("role") == "pay" and s.get("tier") != "high"]
        hues = self.spread_hues(len(highs) + len(lows))
        self.style = {}
        # highs take every other hue of the wheel, lows the ones in between: same-tier symbols sit far apart
        order = list(range(0, len(hues), 2)) + list(range(1, len(hues), 2))
        for i, sid in enumerate(highs + lows):
            hue = hues[order[i]]
            if i < len(highs):
                self.style[sid] = ("high", hue, HIGH_SHAPES[i % len(HIGH_SHAPES)])
            else:
                self.style[sid] = ("low", hue, LOW_GLYPHS[(i - len(highs)) % len(LOW_GLYPHS)])
        for s in syms:
            if s.get("role") in ("scatter", "wild"):
                self.style[s["id"]] = (s["role"], SCATTER_HUE, None)
        self.highs = highs
        self.variants = [v["id"] for v in gdef.get("features", {}).get("bonusVariants", [])]

    def spread_hues(self, n):
        """n evenly spaced hues (the most distinct set possible), the wheel turned to sit as close as it can
        to the saturated palette hues while staying at least 15 degrees from the scatter's gold."""
        if n <= 0:
            return []
        pal = [to_hsv(c)[0] for c in self.pal if to_hsv(c)[1] > 0.3 and to_hsv(c)[2] > 0.2]
        step = 1 / n

        def ok(off):
            return all(hue_dist(off + k * step, SCATTER_HUE) >= 15 / 360 for k in range(n))

        def fit(off):
            return sum(min(hue_dist(p, off + k * step) for k in range(n)) for p in pal)

        offsets = [i / 360 for i in range(360) if i / 360 < step] or [0.0]
        good = [o for o in offsets if ok(o)] or offsets
        off = min(good, key=lambda o: (round(fit(o), 6), o))
        return [(off + k * step) % 1.0 for k in range(n)]

    def bright(self, rgb, k):
        return tuple(round(c + (255 - c) * k) for c in rgb[:3])


# ---------------------------------------------------------------- drawing helpers

def font(size):
    try:
        return ImageFont.truetype(str(TITLE_FONT), size)
    except OSError:
        return ImageFont.load_default(size=size)


def fit_font(draw, text, max_w, max_h):
    size = max_h
    while size > 8:
        f = font(size)
        box = draw.textbbox((0, 0), text, font=f, stroke_width=max(1, size // 14))
        if box[2] - box[0] <= max_w and box[3] - box[1] <= max_h:
            return f, box
        size = int(size * 0.92)
    f = font(8)
    return f, draw.textbbox((0, 0), text, font=f)


def gradient(w, h, top, bottom, radial=False):
    """RGBA gradient image (vertical, or radial from the upper centre)."""
    if radial:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        t = np.sqrt(((x - w * 0.5) / (w * 0.6)) ** 2 + ((y - h * 0.35) / (h * 0.75)) ** 2).clip(0, 1)[..., None]
    else:
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] * np.ones((1, w, 1), np.float32)
    a, b = np.array(top[:3], np.float32), np.array(bottom[:3], np.float32)
    rgb = a * (1 - t) + b * t
    alpha = np.full((h, w, 1), 255, np.float32)
    return Image.fromarray(np.concatenate([rgb, alpha], axis=2).astype(np.uint8), "RGBA")


def fill_shape(img, mask, top, bottom, radial=False):
    img.paste(gradient(img.width, img.height, top, bottom, radial), (0, 0), mask)


def poly_mask(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def star_points(cx, cy, r_out, r_in, n, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sparkle(draw, cx, cy, r, colour):
    draw.polygon(star_points(cx, cy, r, r * 0.18, 4), fill=colour)


def floor_alpha(img):
    """Opaque pixels at brightness >= 64 so ingest's black colour key keeps them (scripts/assets_build.cut_out)."""
    arr = np.array(img, dtype=np.float32)
    mx = arr[..., :3].max(axis=2)
    low = (arr[..., 3] > 0) & (mx < 64)
    scale = np.where(low, 64 / np.maximum(mx, 1), 1.0)[..., None]
    arr[..., :3] = np.where(low[..., None], np.maximum(arr[..., :3] * scale, 64 * (mx < 1)[..., None]), arr[..., :3])
    arr[..., :3] *= (arr[..., 3:] > 0)  # fully transparent pixels stay black
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")


def shrink(img, size):
    return img.resize(size, Image.LANCZOS) if img.size != tuple(size) else img


# ---------------------------------------------------------------- symbols

def draw_high(S, hue, shape):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base, light, dark = hsv(hue, 0.85, 0.82), hsv(hue, 0.45, 1.0), hsv(hue, 0.95, 0.42)
    line = hsv(hue, 0.9, 0.3)
    lw = int(S * 0.022)
    c = S / 2
    if shape == "brilliant":
        outer = [(c + S * 0.43 * math.cos(math.pi / 8 + i * math.pi / 4), c + S * 0.43 * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        table = [(c + S * 0.22 * math.cos(math.pi / 8 + i * math.pi / 4), c + S * 0.22 * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        fill_shape(img, poly_mask((S, S), outer), light, dark)
        for i in range(8):
            j = (i + 1) % 8
            ang = math.pi / 8 + (i + 0.5) * math.pi / 4
            lit = 0.5 + 0.5 * math.cos(ang - math.pi * 1.25)  # light from the upper left
            d.polygon([outer[i], outer[j], table[j], table[i]], fill=hsv(hue, 0.95 - 0.5 * lit, 0.45 + 0.55 * lit))
        fill_shape(img, poly_mask((S, S), table), light, base)
        d.polygon(outer, outline=line, width=lw)
        d.polygon(table, outline=hsv(hue, 0.3, 1.0), width=lw // 2)
    elif shape == "crown":
        body = [(S * 0.16, S * 0.66), (S * 0.12, S * 0.26), (S * 0.32, S * 0.46), (S * 0.5, S * 0.18),
                (S * 0.68, S * 0.46), (S * 0.88, S * 0.26), (S * 0.84, S * 0.66)]
        fill_shape(img, poly_mask((S, S), body), light, dark)
        d.polygon(body, outline=line, width=lw)
        band = [S * 0.14, S * 0.64, S * 0.86, S * 0.82]
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).rounded_rectangle(band, radius=int(S * 0.04), fill=255)
        fill_shape(img, m, base, dark)
        d.rounded_rectangle(band, radius=int(S * 0.04), outline=line, width=lw)
        for x, y, r in ((0.12, 0.26, 0.05), (0.5, 0.18, 0.06), (0.88, 0.26, 0.05)):
            d.ellipse([S * (x - r), S * (y - r), S * (x + r), S * (y + r)], fill=hsv(hue, 0.15, 1.0), outline=line, width=lw // 2)
        for x in (0.3, 0.5, 0.7):
            r = 0.055
            d.ellipse([S * (x - r), S * (0.73 - r), S * (x + r), S * (0.73 + r)], fill=hsv(hue + 0.5, 0.6, 1.0), outline=line, width=lw // 2)
    elif shape == "shield":
        pts = [(S * 0.18, S * 0.16), (S * 0.82, S * 0.16), (S * 0.82, S * 0.5)]
        for k in range(1, 12):
            a = k / 12 * math.pi / 2
            pts.append((S * (0.5 + 0.32 * math.cos(a)), S * (0.5 + 0.38 * math.sin(a))))
        pts.append((S * 0.5, S * 0.88))
        for k in range(11, 0, -1):
            a = k / 12 * math.pi / 2
            pts.append((S * (0.5 - 0.32 * math.cos(a)), S * (0.5 + 0.38 * math.sin(a))))
        pts.append((S * 0.18, S * 0.5))
        fill_shape(img, poly_mask((S, S), pts), base, dark)
        d.polygon(pts, outline=line, width=lw)
        inner = [((x - c) * 0.72 + c, (y - c * 0.95) * 0.72 + c * 0.95) for x, y in pts]
        fill_shape(img, poly_mask((S, S), inner), light, base)
        d.polygon(star_points(c, S * 0.47, S * 0.2, S * 0.08, 5), fill=hsv(hue, 0.1, 1.0), outline=line)
    elif shape == "diamond":
        crown = [(S * 0.3, S * 0.2), (S * 0.7, S * 0.2), (S * 0.88, S * 0.4), (S * 0.12, S * 0.4)]
        pav = [(S * 0.12, S * 0.4), (S * 0.88, S * 0.4), (S * 0.5, S * 0.88)]
        fill_shape(img, poly_mask((S, S), crown), light, base)
        fill_shape(img, poly_mask((S, S), pav), base, dark)
        for a, b, col in (((0.3, 0.2), (0.38, 0.4), 0.9), ((0.5, 0.2), (0.38, 0.4), 0.7), ((0.5, 0.2), (0.62, 0.4), 0.7),
                          ((0.7, 0.2), (0.62, 0.4), 0.9)):
            d.line([(S * a[0], S * a[1]), (S * b[0], S * b[1])], fill=hsv(hue, 0.4, col), width=lw // 2)
        for x in (0.12, 0.38, 0.62, 0.88):
            d.line([(S * x, S * 0.4), (S * 0.5, S * 0.88)], fill=hsv(hue, 0.9, 0.55), width=lw // 2)
        d.polygon(crown[:2] + [crown[2]] + [pav[2]] + [crown[3]], outline=line, width=lw)
        d.line([(S * 0.12, S * 0.4), (S * 0.88, S * 0.4)], fill=line, width=lw // 2)
    elif shape == "hexagon":
        outer = [(c + S * 0.42 * math.cos(i * math.pi / 3), c + S * 0.42 * math.sin(i * math.pi / 3)) for i in range(6)]
        inner = [(c + S * 0.24 * math.cos(i * math.pi / 3), c + S * 0.24 * math.sin(i * math.pi / 3)) for i in range(6)]
        fill_shape(img, poly_mask((S, S), outer), light, dark)
        for i in range(6):
            j = (i + 1) % 6
            lit = 0.5 + 0.5 * math.cos((i + 0.5) * math.pi / 3 - math.pi * 1.25)
            d.polygon([outer[i], outer[j], inner[j], inner[i]], fill=hsv(hue, 0.95 - 0.5 * lit, 0.45 + 0.55 * lit))
        fill_shape(img, poly_mask((S, S), inner), light, base)
        d.polygon(outer, outline=line, width=lw)
    else:  # heart
        pts = []
        for k in range(120):
            t = k / 120 * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((c + x * S * 0.026, S * 0.47 - y * S * 0.026))
        fill_shape(img, poly_mask((S, S), pts), light, dark, radial=True)
        d.polygon(pts, outline=line, width=lw)
    sparkle(d, S * 0.33, S * 0.3, S * 0.09, (255, 255, 255, 235))
    sparkle(d, S * 0.68, S * 0.62, S * 0.045, (255, 255, 255, 200))
    return img


def draw_low(S, hue, glyph):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = [S * 0.1, S * 0.1, S * 0.9, S * 0.9]
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=int(S * 0.17), fill=255)
    fill_shape(img, m, hsv(hue, 0.5, 0.98), hsv(hue, 0.9, 0.55))
    d.rounded_rectangle(box, radius=int(S * 0.17), outline=hsv(hue, 0.95, 0.33), width=int(S * 0.03))
    inset = [b + (S * 0.045 if i < 2 else -S * 0.045) for i, b in enumerate(box)]
    d.rounded_rectangle(inset, radius=int(S * 0.13), outline=hsv(hue, 0.2, 1.0, 170), width=int(S * 0.012))
    f, bb = fit_font(d, glyph, int(S * 0.62), int(S * 0.56))
    sw = max(2, int(S * 0.028))
    x = (S - (bb[2] - bb[0])) / 2 - bb[0]
    y = (S - (bb[3] - bb[1])) / 2 - bb[1]
    d.text((x + S * 0.015, y + S * 0.02), glyph, font=f, fill=hsv(hue, 0.9, 0.3, 200), stroke_width=sw, stroke_fill=hsv(hue, 0.9, 0.3, 200))
    d.text((x, y), glyph, font=f, fill=(255, 252, 240, 255), stroke_width=sw, stroke_fill=hsv(hue, 0.95, 0.32))
    return img


def draw_scatter(S, hue=0.13):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    for i in range(16):  # rays
        a = i * math.pi / 8
        d.polygon([(c + S * 0.47 * math.cos(a), c + S * 0.47 * math.sin(a)),
                   (c + S * 0.12 * math.cos(a + 0.12), c + S * 0.12 * math.sin(a + 0.12)),
                   (c + S * 0.12 * math.cos(a - 0.12), c + S * 0.12 * math.sin(a - 0.12))], fill=hsv(hue, 0.35, 1.0, 150))
    outer = star_points(c, c, S * 0.44, S * 0.25, 12)
    fill_shape(img, poly_mask((S, S), outer), hsv(hue, 0.25, 1.0), hsv(hue - 0.04, 0.95, 0.85), radial=True)
    d.polygon(outer, outline=hsv(hue - 0.03, 0.95, 0.4), width=int(S * 0.02))
    inner = star_points(c, c, S * 0.26, S * 0.12, 8, rot=-math.pi / 2 + math.pi / 8)
    fill_shape(img, poly_mask((S, S), inner), (255, 255, 255), hsv(hue, 0.6, 1.0), radial=True)
    d.polygon(inner, outline=hsv(hue, 0.9, 0.55), width=int(S * 0.012))
    d.ellipse([c - S * 0.07, c - S * 0.07, c + S * 0.07, c + S * 0.07], fill=(255, 255, 250, 255))
    sparkle(d, S * 0.26, S * 0.24, S * 0.08, (255, 255, 255, 230))
    return img


def draw_wild(S, hue=0.8):
    img = draw_scatter(S, hue)
    d = ImageDraw.Draw(img)
    f, bb = fit_font(d, "W", int(S * 0.3), int(S * 0.3))
    d.text(((S - bb[2] + bb[0]) / 2 - bb[0], (S - bb[3] + bb[1]) / 2 - bb[1]), "W", font=f, fill=hsv(hue, 0.9, 0.45))
    return img


# ---------------------------------------------------------------- scenes

def painted(w, h, th: Theme, key: str, bright=False):
    """Soft painted-look backdrop: blurred colour blobs from the palette on a dark (or bright) wash."""
    rng = np.random.default_rng(seed(key))
    lw, lh = max(8, w // 16), max(8, h // 16)
    y, x = np.mgrid[0:lh, 0:lw].astype(np.float32)
    x, y = x / lw, y / lh
    if bright:
        top, bot = np.array(th.bright(hsv(th.accent_hue, 0.35, 1.0), 0.3), np.float32), np.array(hsv(th.base_hue, 0.55, 0.85)[:3], np.float32)
    else:
        top, bot = np.array(th.bright(th.dark, 0.26), np.float32), np.array(th.bright(th.dark, 0.04), np.float32)
    img = top * (1 - y[..., None]) + bot * y[..., None]
    cols = [c for c in th.pal if to_hsv(c)[1] > 0.2] or th.pal
    for i in range(7):
        cx, cy = rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)
        r = rng.uniform(0.18, 0.4)
        col = np.array(cols[i % len(cols)], np.float32)
        if bright:
            col = col + (255 - col) * 0.35
        k = np.exp(-(((x - cx) ** 2) * (w / h) ** 2 * 0.5 + (y - cy) ** 2) / (2 * r * r))[..., None] * rng.uniform(0.3, 0.55)
        img = img * (1 - k) + col * k
    img += rng.normal(0, 2.0, img.shape).astype(np.float32)  # canvas texture, low so webp stays small
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB").resize((w, h), Image.BICUBIC)
    im = im.filter(ImageFilter.GaussianBlur(max(1, min(w, h) // 300)))
    if not bright:  # vignette, centre kept calm for the board
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r2 = ((xx / w - 0.5) / 0.62) ** 2 + ((yy / h - 0.5) / 0.62) ** 2
        v = (1 - 0.55 * np.clip(r2, 0, 1.6) ** 1.3).clip(0.25, 1)[..., None]
        im = Image.fromarray((np.array(im, np.float32) * v).astype(np.uint8), "RGB")
    return im.convert("RGBA")


def sunburst(img, cx, cy, colour, n=18):
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    R = max(img.size) * 1.2
    for i in range(n):
        a0, a1 = (2 * i) * math.pi / n, (2 * i + 1) * math.pi / n
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=colour)
    return Image.alpha_composite(img, over.filter(ImageFilter.GaussianBlur(max(2, img.width // 200))))


def title(img, text, box):
    """Display name, gold gradient with dark stroke, fitted inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    words = text.upper().split()
    lines = [" ".join(words)] if len(words) < 2 else [" ".join(words[: (len(words) + 1) // 2]), " ".join(words[(len(words) + 1) // 2:])]
    probe = ImageDraw.Draw(img)
    if len(lines) == 2:
        one, _ = fit_font(probe, lines[0] + " " + lines[1], x1 - x0, (y1 - y0) // 2)
        two, _ = fit_font(probe, max(lines, key=len), x1 - x0, (y1 - y0) // 2)
        if one.size >= two.size * 0.8:
            lines = [lines[0] + " " + lines[1]]
    lh = (y1 - y0) // len(lines)
    y = y0
    for ln in lines:
        f, bb = fit_font(probe, ln, x1 - x0, int(lh * 0.9))
        sw = max(2, f.size // 12)
        tw, th_ = bb[2] - bb[0], bb[3] - bb[1]
        tx, ty = x0 + (x1 - x0 - tw) / 2 - bb[0], y + (lh - th_) / 2 - bb[1]
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).text((tx, ty), ln, font=f, fill=255)
        stroke = Image.new("L", img.size, 0)
        ImageDraw.Draw(stroke).text((tx, ty), ln, font=f, fill=255, stroke_width=sw, stroke_fill=255)
        shadow = stroke.filter(ImageFilter.GaussianBlur(sw * 1.5))
        img.paste((40, 20, 8, 160), (int(sw * 0.6), int(sw * 0.9)), shadow)
        img.paste((60, 30, 10, 255), (0, 0), stroke)
        fill_shape(img, mask, (255, 248, 210), (232, 150, 30))
        y += lh
    return img


def gem_row(img, th: Theme, cx, cy, size, count=3):
    gems = [draw_high(512, th.style[s][1], th.style[s][2]) for s in th.highs[:count]] or [draw_scatter(512)]
    n = len(gems)
    for i, g in enumerate(gems):
        k = 1.25 if i == n // 2 else 1.0
        sz = int(size * k)
        g = g.resize((sz, sz), Image.LANCZOS)
        x = int(cx + (i - (n - 1) / 2) * size * 0.95 - sz / 2)
        y = int(cy - sz / 2 - (size * 0.12 if i == n // 2 else 0))
        img.alpha_composite(g, (x, y))
    return img


def key_art(w, h, th: Theme, key, gems=True):
    """Bright key art with the display name inside the safe area. tile.bg leaves the gems to tile.fg."""
    img = painted(w, h, th, key, bright=True)
    img = sunburst(img, w / 2, h * 0.58, (255, 255, 255, 46))
    m = min(w, h)
    if gems:
        img = gem_row(img, th, w / 2, h * (0.68 if h > w else 0.66), m * (0.3 if h > w else 0.26))
    sx, sy = w * 0.1, h * 0.08  # safe area: 10 % sides, 8 % top
    img = title(img, th.name, (int(sx), int(sy), int(w - sx), int(sy + h * (0.28 if h > w else 0.34))))
    return img


def frame(w, h, th: Theme):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    band = int(min(w, h) * 0.055)
    outer = Image.new("L", (w, h), 0)
    od = ImageDraw.Draw(outer)
    od.rounded_rectangle([0, 0, w - 1, h - 1], radius=band * 2, fill=255)
    od.rounded_rectangle([band, band, w - 1 - band, h - 1 - band], radius=band, fill=0)
    fill_shape(img, outer, hsv(th.accent_hue, 0.35, 1.0), hsv(th.accent_hue, 0.9, 0.5))
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=band * 2, outline=hsv(th.accent_hue, 0.9, 0.32), width=max(3, band // 8))
    d.rounded_rectangle([band, band, w - 1 - band, h - 1 - band], radius=band, outline=hsv(th.accent_hue, 0.2, 1.0), width=max(2, band // 10))
    d.rounded_rectangle([band // 2, band // 2, w - 1 - band // 2, h - 1 - band // 2], radius=int(band * 1.5),
                        outline=hsv(th.accent_hue, 0.95, 0.4), width=max(2, band // 12))
    gem = draw_high(256, th.style[th.highs[0]][1] if th.highs else 0.0, "brilliant") if th.highs else draw_scatter(256)
    gs = int(band * 1.6)
    gem = gem.resize((gs, gs), Image.LANCZOS)
    for x, y in ((band / 2, band / 2), (w - band / 2, band / 2), (band / 2, h - band / 2), (w - band / 2, h - band / 2),
                 (w / 2, band / 2), (w / 2, h - band / 2), (band / 2, h / 2), (w - band / 2, h / 2)):
        img.alpha_composite(gem, (int(x - gs / 2), int(y - gs / 2)))
    return img


def banner(w, h, th: Theme):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img = sunburst(img, w / 2, h / 2, hsv(th.accent_hue, 0.3, 1.0, 70), n=14)
    # keep the rays inside an ellipse so the cut-out has a clean edge
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([w * 0.02, h * 0.02, w * 0.98, h * 0.98], fill=255)
    img.putalpha(Image.fromarray(np.minimum(np.array(img.getchannel("A")), np.array(m.filter(ImageFilter.GaussianBlur(w // 40))))))
    d = ImageDraw.Draw(img)
    for side in (-1, 1):  # ribbon tails
        x = w / 2 + side * w * 0.36
        d.polygon([(x, h * 0.36), (x + side * w * 0.12, h * 0.4), (x + side * w * 0.07, h * 0.52), (x + side * w * 0.12, h * 0.66),
                   (x, h * 0.62)], fill=hsv(th.accent_hue, 0.9, 0.6), outline=hsv(th.accent_hue, 0.9, 0.35))
    box = [w * 0.12, h * 0.28, w * 0.88, h * 0.72]
    mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle(box, radius=int(h * 0.08), fill=255)
    fill_shape(img, mk, hsv(th.base_hue, 0.6, 0.5), hsv(th.base_hue, 0.7, 0.3))
    d.rounded_rectangle(box, radius=int(h * 0.08), outline=hsv(th.accent_hue, 0.6, 1.0), width=int(h * 0.025))
    inner = [box[0] + h * 0.035, box[1] + h * 0.035, box[2] - h * 0.035, box[3] - h * 0.035]
    d.rounded_rectangle(inner, radius=int(h * 0.06), outline=hsv(th.accent_hue, 0.8, 0.75), width=int(h * 0.008))
    return img


def card(w, h, th: Theme, variant: str):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    box = [w * 0.06, h * 0.04, w * 0.94, h * 0.96]
    mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle(box, radius=int(w * 0.07), fill=255)
    hue = (th.accent_hue + 0.5) % 1 if (seed(variant) % 2) else th.base_hue
    fill_shape(img, mk, hsv(hue, 0.55, 0.85), hsv(hue, 0.8, 0.35), radial=True)
    img = sunburst(img, w / 2, h * 0.55, (255, 255, 255, 40), n=16)
    img.putalpha(Image.fromarray(np.minimum(np.array(img.getchannel("A")), np.array(mk))))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=int(w * 0.07), outline=hsv(th.accent_hue, 0.5, 1.0), width=int(w * 0.03))
    star = draw_scatter(512).resize((int(w * 0.62), int(w * 0.62)), Image.LANCZOS)
    img.alpha_composite(star, (int(w * 0.19), int(h * 0.55 - w * 0.31)))
    img = title(img, variant.replace("_", " ").title(), (int(w * 0.14), int(h * 0.08), int(w * 0.86), int(h * 0.24)))
    return img


def emblem(S, th: Theme):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], fill=hsv(th.accent_hue, 0.7, 0.75), outline=hsv(th.accent_hue, 0.9, 0.35), width=int(S * 0.02))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([S * 0.12, S * 0.12, S * 0.88, S * 0.88], fill=255)
    fill_shape(img, m, hsv(th.base_hue, 0.5, 0.75), hsv(th.base_hue, 0.8, 0.35), radial=True)
    d.ellipse([S * 0.12, S * 0.12, S * 0.88, S * 0.88], outline=hsv(th.accent_hue, 0.3, 1.0), width=int(S * 0.012))
    for i in range(24):
        a = i * math.pi / 12
        r0, r1 = S * 0.4, S * 0.445
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))], fill=hsv(th.accent_hue, 0.4, 1.0), width=int(S * 0.008))
    crown = draw_high(512, th.accent_hue, "crown").resize((int(S * 0.6), int(S * 0.6)), Image.LANCZOS)
    img.alpha_composite(crown, (int(S * 0.2), int(S * 0.18)))
    return img


def ui_button(S, th: Theme, icon: str):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], fill=255)
    fill_shape(img, m, hsv(th.accent_hue, 0.3, 1.0), hsv(th.accent_hue, 0.9, 0.45), radial=True)
    d.ellipse([S * 0.04, S * 0.04, S * 0.96, S * 0.96], outline=hsv(th.accent_hue, 0.9, 0.3), width=int(S * 0.03))
    d.ellipse([S * 0.14, S * 0.14, S * 0.86, S * 0.86], fill=hsv(th.base_hue, 0.6, 0.38), outline=hsv(th.accent_hue, 0.2, 1.0), width=int(S * 0.015))
    ink, w_ = (255, 250, 235, 255), int(S * 0.07)
    c = S / 2
    if icon == "spin":
        d.arc([S * 0.3, S * 0.3, S * 0.7, S * 0.7], 20, 320, fill=ink, width=w_)
        a = math.radians(320)
        tip = (c + S * 0.2 * math.cos(a), c + S * 0.2 * math.sin(a))
        d.polygon([(tip[0] + S * 0.1, tip[1] - S * 0.02), (tip[0] - S * 0.07, tip[1] - S * 0.08), (tip[0] - S * 0.01, tip[1] + S * 0.1)], fill=ink)
    elif icon in ("plus", "minus"):
        d.rounded_rectangle([S * 0.3, c - w_ / 2, S * 0.7, c + w_ / 2], radius=w_ // 3, fill=ink)
        if icon == "plus":
            d.rounded_rectangle([c - w_ / 2, S * 0.3, c + w_ / 2, S * 0.7], radius=w_ // 3, fill=ink)
    elif icon == "menu":
        for y in (0.36, 0.5, 0.64):
            d.rounded_rectangle([S * 0.3, S * y - w_ / 2.4, S * 0.7, S * y + w_ / 2.4], radius=w_ // 3, fill=ink)
    elif icon == "auto":
        d.ellipse([S * 0.25, S * 0.38, S * 0.5, S * 0.62], outline=ink, width=int(w_ * 0.8))
        d.ellipse([S * 0.5, S * 0.38, S * 0.75, S * 0.62], outline=ink, width=int(w_ * 0.8))
    elif icon == "turbo":
        d.polygon([(S * 0.56, S * 0.24), (S * 0.32, S * 0.54), (S * 0.48, S * 0.54), (S * 0.42, S * 0.78), (S * 0.68, S * 0.44),
                   (S * 0.52, S * 0.44)], fill=ink)
    elif icon == "sound":
        d.polygon([(S * 0.28, S * 0.42), (S * 0.38, S * 0.42), (S * 0.52, S * 0.3), (S * 0.52, S * 0.7), (S * 0.38, S * 0.58), (S * 0.28, S * 0.58)], fill=ink)
        for r in (0.1, 0.17):
            d.arc([S * (0.52 - r), c - S * r, S * (0.52 + r), c + S * r], -50, 50, fill=ink, width=int(w_ * 0.6))
    else:
        d.polygon(star_points(c, c, S * 0.22, S * 0.1, 5), fill=ink)
    return img


def sigil(S, th: Theme):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = hsv(th.accent_hue, 0.55, 1.0)
    c = S / 2
    d.ellipse([S * 0.06, S * 0.06, S * 0.94, S * 0.94], outline=col, width=int(S * 0.08))
    d.polygon(star_points(c, c, S * 0.3, S * 0.13, 6), fill=col)
    return img


def transition(w, h, th: Theme):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(-4, 12):
        x = i * w / 8
        col = hsv(th.accent_hue + (i % 3) * 0.04, 0.4, 1.0, 70 + (i % 3) * 30)
        d.polygon([(x, 0), (x + w / 10, 0), (x + w / 10 - h * 0.6, h), (x - h * 0.6, h)], fill=col)
    return img.filter(ImageFilter.GaussianBlur(max(2, w // 300)))


# ---------------------------------------------------------------- entry

def slot_size(slot: dict):
    if slot.get("px"):
        return tuple(slot["px"])
    a, b = (int(x) for x in (slot.get("aspect") or "1:1").split(":"))
    return 1024, round(1024 * b / a)


def render(th: Theme, slot: dict) -> Image.Image:
    sid = slot["id"]
    w, h = slot_size(slot)
    if sid.startswith("symbol."):
        kind, hue, extra = th.style.get(sid[7:], ("high", 0.0, "brilliant"))
        S = w * SS
        art = {"high": lambda: draw_high(S, hue, extra), "low": lambda: draw_low(S, hue, extra),
               "scatter": lambda: draw_scatter(S, hue), "wild": lambda: draw_wild(S)}[kind]()
        return shrink(art, (w, h))
    if sid == "sigil":
        return shrink(sigil(w * SS, th), (w, h))
    if sid.startswith("ui."):
        return shrink(ui_button(w * SS, th, sid[3:]), (w, h))
    if sid.startswith("bg."):
        img = painted(w, h, th, sid)
        if sid.split(".")[1] != "base":  # bonus backdrops: warmer light from the top
            img = sunburst(img, w / 2, -h * 0.1, hsv(th.accent_hue, 0.5, 1.0, 22), n=12)
        return img
    if sid == "frame.board":
        return frame(w, h, th)
    if sid.startswith("panel."):
        return banner(w, h, th)
    if sid.startswith("card."):
        return card(w, h, th, sid.split(".")[1])
    if sid.startswith("transition."):
        return transition(w, h, th)
    if sid.startswith("logo."):
        return shrink(emblem(w * 2, th), (w, h))
    if sid == "tile.fg":
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        return gem_row(img, th, w / 2, h * 0.74, min(w, h) * 0.36)
    if sid in ("tile.bg", "cover", "hero") or sid.startswith("tile."):
        return key_art(w, h, th, sid, gems=sid != "tile.bg")
    return painted(w, h, th, sid)


def make(th: Theme, slot: dict, raw: Path, edited: Path):
    img = render(th, slot)
    if slot.get("alpha"):
        img = floor_alpha(img.convert("RGBA"))
    else:
        img = img.convert("RGB")
    raw.parent.mkdir(parents=True, exist_ok=True)
    img.save(raw, "PNG", optimize=False)
    # edited differs from raw by one corner pixel only (raw != edited), so nothing visible changes
    ed = img.copy()
    px = ed.getpixel((0, 0))
    ed.putpixel((0, 0), tuple(min(255, v + 1) for v in px[:3]) + ((px[3],) if ed.mode == "RGBA" else ()))
    edited.parent.mkdir(parents=True, exist_ok=True)
    ed.save(edited, "PNG", optimize=False)
