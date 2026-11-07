r"""Factory TEST assets: fill a game's empty asset slots with labelled placeholders, or remove them again.

Usage (from stake\, asset venv: Pillow, numpy, ffmpeg on PATH):
  .venv-assets\Scripts\python.exe tools\assets\test_assets.py --game <id>            fill slots without a raw file
  .venv-assets\Scripts\python.exe tools\assets\test_assets.py --game <id> --force    also redo slots whose files are test files
  .venv-assets\Scripts\python.exe tools\assets\test_assets.py --game <id> --clear    remove every test file and record

Create writes into skins\<skin>\art_in (git-ignored):
  images  raw\<slot>.png at 2x the slot px (1024 wide when px is null) in a palette gradient
          (game.json theme.palette) with a simple shape and the slot id + "TEST"; edited\<slot>.png is
          the raw with a border, so raw != edited
  audio   raw\<slot>.wav: music = 8 s loopable two-note pattern, sfx = 0.3-1.5 s chirp; pitch varies by slot
  fonts   raw\<slot>.ttf copied from the core app's fonts (Inter TTF if present, else core\web\cluster-tumble\fontsrc)
  provenance.json lines with licence 'test', sourceUrl 'factory:test_assets', editNote 'factory test placeholder'
then runs tools\assets\ingest.py --all, tools\assets\audio.py, tools\gen\gen_assets_ts.py, tools\gen\gen_web_static.py.
Slots with a real (non-test) provenance line are never touched, also not with --force.

--clear removes only what has provenance licence 'test': art_in raw/edited files and provenance lines,
assets.lock.json records and their ingested finals (assets\slots, tiles, assets\fonts, audio), then
reruns gen_assets_ts.py, gen_web_static.py and audio.py.

Test assets can never ship: tools\assets\precheck.py blocks any 'test' licence (rule assets.test,
core\policy.v1.json). Output is deterministic (seeded by slot id, no timestamps or metadata).
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import EXT, ROOT, Catalog  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402

TEST_LICENCE = "test"
SOURCE = "factory:test_assets"
NOTE = "factory test placeholder"
FONT_DIRS = [ROOT / "core" / "web" / "cluster-tumble" / "src" / "assets" / "fonts", ROOT / "core" / "web" / "cluster-tumble" / "fontsrc"]
BITEXACT = ["-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact"]


def seed(slot_id: str) -> int:
    return int(hashlib.sha256(slot_id.encode("utf-8")).hexdigest()[:8], 16)


def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette(cat: Catalog):
    pal = [hex_rgb(v) for v in (cat.game.gdef.get("theme", {}).get("palette") or {}).values() if isinstance(v, str) and v.startswith("#")]
    return pal if len(pal) >= 2 else [(16, 24, 38), (224, 160, 48), (31, 122, 122), (216, 226, 234)]


def image_size(slot: dict):
    if slot.get("px"):
        return slot["px"][0] * 2, slot["px"][1] * 2
    a, b = (int(x) for x in (slot.get("aspect") or "1:1").split(":"))
    return 1024, round(1024 * b / a)


def shape_of(sid: str) -> str:
    if sid.startswith("frame."):
        return "frame"
    if sid.startswith("panel."):
        return "banner"
    if sid.startswith("card."):
        return "card"
    if sid.startswith(("bg.", "cover", "tile.bg", "hero", "transition.")):
        return "scene"
    return "circle"  # symbols, sigil, ui buttons, logo, tile.fg


def make_image(cat: Catalog, slot: dict, raw: Path, edited: Path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    w, h = image_size(slot)
    pal = palette(cat)
    s = seed(slot["id"])
    c1, c2 = pal[s % len(pal)], pal[(s // 7 + 1 + s % len(pal)) % len(pal)]
    if c1 == c2:
        c2 = pal[(pal.index(c1) + 1) % len(pal)]
    t = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    grad = (np.array(c1, np.float32) * (1 - t) + np.array(c2, np.float32) * t)
    grad = np.broadcast_to(grad, (h, w, 3)).astype(np.uint8)
    full = Image.fromarray(np.ascontiguousarray(grad), "RGB").convert("RGBA")
    accent = pal[(s // 13 + 2) % len(pal)]
    shape = shape_of(slot["id"])
    alpha_bg = bool(slot.get("alpha")) and shape != "scene"
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)) if alpha_bg else full.copy()
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    m = min(w, h)
    if shape == "circle":
        r = int(m * 0.42)
        md.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill=255)
    elif shape == "frame":
        bw = int(m * 0.08)
        md.rectangle([0, 0, w - 1, h - 1], fill=255)
        md.rectangle([bw, bw, w - 1 - bw, h - 1 - bw], fill=0)
    elif shape == "banner":
        md.rounded_rectangle([int(w * 0.05), int(h * 0.2), int(w * 0.95), int(h * 0.8)], radius=int(m * 0.1), fill=255)
    elif shape == "card":
        md.rounded_rectangle([int(w * 0.08), int(h * 0.06), int(w * 0.92), int(h * 0.94)], radius=int(m * 0.08), fill=255)
    else:  # scene: full gradient with a horizon band and a sun disc
        md.rectangle([0, int(h * 0.62), w, int(h * 0.7)], fill=255)
        r = int(m * 0.18)
        md.ellipse([w // 2 - r, int(h * 0.45) - r, w // 2 + r, int(h * 0.45) + r], fill=255)
    if shape == "scene":
        img.paste(Image.new("RGBA", (w, h), accent + (255,)), (0, 0), mask)
    else:
        img.paste(full, (0, 0), mask)
        outline = ImageDraw.Draw(img)
        if shape == "circle":
            r = int(m * 0.42)
            outline.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], outline=accent + (255,), width=max(2, m // 60))
    draw = ImageDraw.Draw(img)
    size = max(12, min(int(m * 0.11), int(w * 1.6 / max(6, len(slot["id"])))))
    font = ImageFont.load_default(size=size)
    ink, shadow = (255, 255, 255, 255), (0, 0, 0, 255)
    for text, dy in ((slot["id"], -0.6), ("TEST", 0.7)):
        box = draw.textbbox((0, 0), text, font=font, stroke_width=max(1, size // 12))
        x = (w - (box[2] - box[0])) // 2 - box[0]
        y = int(h / 2 + dy * size) - (box[3] - box[1]) // 2 - box[1]
        draw.text((x, y), text, font=font, fill=ink, stroke_width=max(1, size // 12), stroke_fill=shadow)
    if not slot.get("alpha"):
        img = img.convert("RGB")
    raw.parent.mkdir(parents=True, exist_ok=True)
    img.save(raw, "PNG", optimize=False)
    ed = img.copy()
    ImageDraw.Draw(ed).rectangle([0, 0, w - 1, h - 1], outline=(255, 0, 255, 255) if ed.mode == "RGBA" else (255, 0, 255),
                                 width=max(4, m // 40))
    edited.parent.mkdir(parents=True, exist_ok=True)
    ed.save(edited, "PNG", optimize=False)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def make_audio(slot: dict, out: Path):
    s = seed(slot["id"])
    out.parent.mkdir(parents=True, exist_ok=True)
    if slot["kind"] == "music":
        f1 = 196 + (s % 12) * 22  # two-note pattern, 0.5 s per note, each note faded so the 8 s loop is click-free
        f2 = round(f1 * (1.25 if s % 2 else 1.5))
        expr = f"0.35*sin(PI*mod(t\\,0.5)/0.5)*sin(2*PI*t*if(lt(mod(t\\,1)\\,0.5)\\,{f1}\\,{f2}))"
        dur = 8
    else:
        f0 = 400 + (s % 17) * 60
        dur = round(0.3 + (s % 13) / 12 * 1.2, 3)
        k = (s % 5 + 1) * 300 * (1 if s % 2 else -0.5)
        expr = f"0.5*sin(PI*t/{dur})*sin(2*PI*({f0}*t+{k}*t*t/2))"
    ffmpeg("-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d={dur}", "-ac", "2", *BITEXACT, "-c:a", "pcm_s16le", str(out))


def font_source() -> Path:
    for d in FONT_DIRS:
        for pat in ("Inter*.ttf", "inter*.ttf", "*.ttf", "*.otf"):
            hits = sorted(d.glob(pat)) if d.exists() else []
            if hits:
                return hits[0]
    sys.exit("No TTF/OTF font found in " + ", ".join(str(d.relative_to(ROOT)) for d in FONT_DIRS))


def run_tool(*args):
    print(f"run   {' '.join(str(a) for a in args)}")
    r = subprocess.run([sys.executable, *[str(a) for a in args]], cwd=ROOT)
    if r.returncode:
        sys.exit(f"FAIL: {args[0]} exited {r.returncode}")


def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def is_test(rec: dict) -> bool:
    return (rec or {}).get("licence") == TEST_LICENCE


def create(cat: Catalog, force: bool):
    prov_path = cat.art_in / "provenance.json"
    prov = load_json(prov_path, {"slots": {}})
    prov.setdefault("slots", {})
    made = kept = 0
    font = None
    for slot in sorted(cat.slots, key=lambda x: x["id"]):
        sid = slot["id"]
        line = prov["slots"].get(sid)
        if line and not is_test(line):
            kept += 1
            continue  # real provenance: never touched
        raw_existing = cat.find("raw", slot)
        if raw_existing and not (force and is_test(line)):
            kept += 1
            continue
        raw = cat.art_in / "raw" / (sid + {"image": ".png", "font": ".ttf"}.get(slot["kind"], ".wav"))
        if slot["kind"] == "image":
            make_image(cat, slot, raw, cat.art_in / "edited" / f"{sid}.png")
        elif slot["kind"] in ("music", "sfx"):
            make_audio(slot, raw)
        elif slot["kind"] == "font":
            font = font or font_source()
            raw.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(font, raw)
        else:
            continue
        prov["slots"][sid] = {"licence": TEST_LICENCE, "sourceUrl": SOURCE, "editNote": NOTE, "promptSha": slot["promptSha"]}
        made += 1
    prov["slots"] = dict(sorted(prov["slots"].items()))
    write_json(prov_path, prov)
    print(f"test assets: {made} made, {kept} left alone (existing file or real provenance)"
          + (f"; fonts from {font.relative_to(ROOT)}" if font else ""))
    run_tool(ROOT / "tools" / "assets" / "ingest.py", "--game", cat.game.id, "--all")
    run_tool(ROOT / "tools" / "assets" / "audio.py", "--game", cat.game.id)
    run_tool(ROOT / "tools" / "gen" / "gen_assets_ts.py", "--game", cat.game.id)
    run_tool(ROOT / "tools" / "gen" / "gen_web_static.py", "--game", cat.game.id)


def remove(path: Path, removed: list):
    if path.exists() and path.is_file():
        path.unlink()
        removed.append(path)


def prune(folder: Path, stop: Path):
    """Remove empty folders from folder up to (not including) stop."""
    while folder != stop and folder.exists() and folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
        folder = folder.parent


def clear(cat: Catalog):
    skin = cat.game.skin
    removed = []
    prov_path = cat.art_in / "provenance.json"
    prov = load_json(prov_path, {"slots": {}})
    test_ids = {sid for sid, line in prov.get("slots", {}).items() if is_test(line)}
    by_id = {s["id"]: s for s in cat.slots}
    for sid in sorted(test_ids):
        slot = by_id.get(sid, {"id": sid, "fileStem": sid, "kind": None})
        for lane in ("raw", "edited"):
            exts = EXT.get(slot["kind"]) or tuple(e for v in EXT.values() for e in v)
            for ext in exts:
                remove(cat.art_in / lane / f"{slot['fileStem']}{ext}", removed)
        del prov["slots"][sid]
    lock_path = skin / "assets.lock.json"
    lock = load_json(lock_path, None)
    if lock is not None:
        for sid, rec in list(lock.get("slots", {}).items()):
            if is_test(rec.get("provenance")):
                if rec.get("file"):
                    f = (skin / rec["file"]).resolve()
                    if skin.resolve() in f.parents:
                        remove(f, removed)
                        prune(f.parent, skin)
                del lock["slots"][sid]
        if not lock.get("slots") and set(lock) <= {"slots"}:
            remove(lock_path, removed)
        else:
            write_json(lock_path, lock)
    if prov_path.exists():
        if not prov.get("slots") and set(prov) <= {"slots"}:
            remove(prov_path, removed)
        else:
            write_json(prov_path, prov)
    for lane in ("raw", "edited"):
        prune(cat.art_in / lane, skin)
    prune(cat.art_in, skin)
    print(f"cleared {len(test_ids)} test slot(s), {len(removed)} file(s) removed")
    run_tool(ROOT / "tools" / "gen" / "gen_assets_ts.py", "--game", cat.game.id)
    run_tool(ROOT / "tools" / "gen" / "gen_web_static.py", "--game", cat.game.id)
    run_tool(ROOT / "tools" / "assets" / "audio.py", "--game", cat.game.id)


def main():
    if "--game" not in sys.argv:
        sys.exit(__doc__)
    cat = Catalog(game_arg())
    if "--clear" in sys.argv:
        clear(cat)
    else:
        create(cat, "--force" in sys.argv)


if __name__ == "__main__":
    main()
