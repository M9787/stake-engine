r"""Factory TEST assets: fill a game's empty asset slots with labelled placeholders, or remove them again.

Usage (from stake\, asset venv: Pillow, numpy, ffmpeg on PATH):
  .venv-assets\Scripts\python.exe tools\assets\test_assets.py --game <id>            fill slots without a raw file
  .venv-assets\Scripts\python.exe tools\assets\test_assets.py --game <id> --force    also redo slots whose files are test files
  .venv-assets\Scripts\python.exe tools\assets\test_assets.py --game <id> --clear    remove every test file and record

Create writes into skins\<skin>\art_in (git-ignored), all at the slot size (1024 wide when px is null):
  images  raw\<slot>.png from tools\assets\test_art.py: per pay symbol a distinct shape and hue (high = gem,
          crown, shield or cut diamond; low = rounded tile with a large letter; scatter = star burst),
          painted backgrounds with vignette, bright tile/cover key art with the display name, styled frame,
          banner, cards, logo and buttons; edited\<slot>.png differs from raw by one corner pixel (raw != edited)
  audio   raw\<slot>.wav from tools\assets\test_sound.py: an 8-bar loop per music slot, arpeggio/chord stings,
          short tonal sfx; one key per game
  fonts   raw\<slot>.ttf copied from core\web\cluster-tumble\fontsrc (Cinzel Decorative, OFL)
  provenance.json lines with licence 'test', sourceUrl 'factory:test_assets', editNote 'factory test placeholder';
          fonts: licence 'ofl', the font's URL and editNote 'factory test_assets: ...' (a real OFL font)
then runs tools\assets\ingest.py --all --no-rembg (test images already have clean alpha; when the game also has
real images, test images are ingested one by one with --no-rembg and the rest with rembg), tools\assets\audio.py,
tools\gen\gen_assets_ts.py, tools\gen\gen_web_static.py.
Slots with a real (non-test) provenance line are never touched, also not with --force.

--clear removes only what this tool made (licence 'test', or its font edit note): art_in raw/edited files and
provenance lines, assets.lock.json records and their ingested finals (assets\slots, tiles, assets\fonts, audio), then
reruns gen_assets_ts.py, gen_web_static.py and audio.py.

Test assets can never ship: tools\assets\precheck.py blocks any 'test' licence (rule assets.test,
core\policy.v1.json). Output is deterministic (seeded by slot id, no timestamps or metadata).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import EXT, ROOT, Catalog  # noqa: E402
import test_art  # noqa: E402
import test_sound  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402

TEST_LICENCE = "test"
SOURCE = "factory:test_assets"
NOTE = "factory test placeholder"
# Fonts are real OFL fonts (core\web\cluster-tumble\fontsrc\OFL.txt), so their provenance says 'ofl'; the
# edit note marks them as made by this tool, so --force and --clear still treat them as test assets.
FONT_DIR = ROOT / "core" / "web" / "cluster-tumble" / "fontsrc"
FONT_FILES = {"font.display": "CinzelDecorative-Black.ttf", "font.ui": "CinzelDecorative-Bold.ttf"}
FONT_LICENCE = "ofl"
FONT_URL = "https://fonts.google.com/specimen/Cinzel+Decorative"
FONT_NOTE = "factory test_assets: core OFL font copy (fontsrc/OFL.txt), unchanged"
OURS = ("factory test", NOTE)  # edit-note prefixes written by this tool


def make_image(cat: Catalog, slot: dict, raw: Path, edited: Path, theme=None):
    test_art.make(theme or test_art.Theme(cat.game.gdef, cat.text), slot, raw, edited)


def make_audio(cat: Catalog, slot: dict, out: Path):
    test_sound.make(slot, out, cat.game.id)


def font_source(slot_id: str) -> Path:
    path = FONT_DIR / FONT_FILES.get(slot_id, FONT_FILES["font.display"])
    if not path.exists():
        sys.exit(f"Font not found: {path.relative_to(ROOT)}")
    return path


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
    """Made by this tool: licence 'test', or an OFL font line with this tool's edit note."""
    rec = rec or {}
    return rec.get("licence") == TEST_LICENCE or str(rec.get("editNote") or "").startswith(OURS)


def create(cat: Catalog, force: bool):
    prov_path = cat.art_in / "provenance.json"
    prov = load_json(prov_path, {"slots": {}})
    prov.setdefault("slots", {})
    made = kept = 0
    theme = test_art.Theme(cat.game.gdef, cat.text)
    images = []
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
        line = {"licence": TEST_LICENCE, "sourceUrl": SOURCE, "editNote": NOTE, "promptSha": slot["promptSha"]}
        if slot["kind"] == "image":
            make_image(cat, slot, raw, cat.art_in / "edited" / f"{sid}.png", theme)
            images.append(sid)
        elif slot["kind"] in ("music", "sfx"):
            make_audio(cat, slot, raw)
        elif slot["kind"] == "font":
            raw.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(font_source(sid), raw)
            line.update(licence=FONT_LICENCE, sourceUrl=FONT_URL, editNote=FONT_NOTE)
        else:
            continue
        prov["slots"][sid] = line
        made += 1
    prov["slots"] = dict(sorted(prov["slots"].items()))
    write_json(prov_path, prov)
    print(f"test assets: {made} made, {kept} left alone (existing file or real provenance)")
    # Test images already have clean alpha: ingest them with the deterministic black colour key, not rembg.
    ingest = ROOT / "tools" / "assets" / "ingest.py"
    real_images = [s for s in cat.slots if s["kind"] == "image" and s["id"] not in images and not is_test(prov["slots"].get(s["id"]))
                   and (cat.find("raw", s) or cat.find("edited", s))]
    if not real_images:
        run_tool(ingest, "--game", cat.game.id, "--all", "--no-rembg")
    else:
        for sid in images:
            run_tool(ingest, "--game", cat.game.id, "--slot", sid, "--no-rembg")
        run_tool(ingest, "--game", cat.game.id, "--all")
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
