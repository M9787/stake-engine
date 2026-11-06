r"""Contact sheet + art sign-off for one game (docs/10 plan v3.3 sections 12-14).

Usage (from stake\, asset venv):
  .venv-assets\Scripts\python.exe tools\assets\contact_sheet.py --game seventh_veil
      writes build\<id>\contact_land.png, contact_port.png (symbols at 128 px on the base background)
      and contact_all.png (every image slot with its id), then runs check_art_in
  .venv-assets\Scripts\python.exe tools\assets\contact_sheet.py --game seventh_veil --sign "Owner Name"
      records the art sign-off with the current asset-set hash in skins\<skin>\art_signoff.json
      (package.ps1 refuses a stale hash). Only signs when check_art_in --gate passes.

Uses the edited file when present, else the raw download, else a placeholder tile.
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, Catalog, asset_set_hash, best_file  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402

CHECKLIST = [
    "Every symbol reads clearly at 128 px on the background (shape and colour, not detail)",
    "All images look like one set (same light, line and palette)",
    "No text, letters or numbers inside any image",
    "No child appeal: no cartoon, chibi or child-like faces",
    "No real brand, logo or copied artwork",
    "Each image was edited by hand (edit note filled)",
]


def palette(cat: Catalog):
    pal = cat.game.gdef.get("theme", {}).get("palette", {})
    return list(pal.values()) or ["#202030", "#404060"]


def placeholder(size, label, colour):
    im = Image.new("RGBA", size, colour)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#ffffff80")
    d.text((6, 6), label, fill="#ffffff")
    return im


def load(path, size, label, colour):
    if path is None:
        return placeholder(size, label, colour)
    with Image.open(path) as im:
        return im.convert("RGBA").resize(size, Image.LANCZOS)


def symbol_sheet(cat: Catalog, bg_slot: str, size, cols):
    pal = palette(cat)
    bg_s = next((s for s in cat.slots if s["id"] == bg_slot), None)
    sheet = load(best_file(cat, bg_s) if bg_s else None, size, bg_slot + " (missing)", pal[0])
    syms = [s for s in cat.slots if s["id"].startswith("symbol.")]
    cell = 128
    gap = 16
    rows = (len(syms) + cols - 1) // cols
    x0 = (size[0] - cols * (cell + gap)) // 2
    y0 = (size[1] - rows * (cell + gap)) // 2
    for i, s in enumerate(syms):
        tile = load(best_file(cat, s), (cell, cell), s["id"], pal[min(1, len(pal) - 1)] + "c0")
        sheet.alpha_composite(tile, (x0 + (i % cols) * (cell + gap), y0 + (i // cols) * (cell + gap)))
    return sheet


def all_sheet(cat: Catalog):
    imgs = [s for s in cat.slots if s["kind"] == "image"]
    cell, label_h, cols = 220, 22, 6
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * (cell + label_h)), "#14111f")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, s in enumerate(imgs):
        f = best_file(cat, s)
        x, y = (i % cols) * cell, (i // cols) * (cell + label_h)
        if f:
            with Image.open(f) as im:
                im = im.convert("RGBA")
                im.thumbnail((cell - 8, cell - 8))
                sheet.alpha_composite(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        else:
            d.rectangle([x + 4, y + 4, x + cell - 4, y + cell - 4], outline="#5b2a86")
            d.text((x + 10, y + cell // 2), "missing", fill="#e07a6f", font=font)
        tag = "edited" if cat.find("edited", s) else ("raw" if f else "")
        d.text((x + 4, y + cell + 4), f"{s['id']} {tag}", fill="#ece8f6", font=font)
    return sheet


def main():
    gid = game_arg()
    cat = Catalog(gid)
    out = ROOT / "build" / gid
    out.mkdir(parents=True, exist_ok=True)
    if "--sign" in sys.argv:
        name = sys.argv[sys.argv.index("--sign") + 1]
        gate = subprocess.run([sys.executable, str(Path(__file__).with_name("check_art_in.py")), "--game", gid, "--gate"])
        if gate.returncode != 0:
            sys.exit("Not signed: check_art_in --gate must pass first (see the report above).")
        rec = {"game": gid, "signedBy": name, "date": date.today().isoformat(), "assetSetSha256": asset_set_hash(cat), "checklist": CHECKLIST}
        (cat.game.skin / "art_signoff.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print(f"Signed by {name}: asset set {rec['assetSetSha256'][:12]}")
        return
    symbol_sheet(cat, "bg.base.land", (1600, 900), 5).convert("RGB").save(out / "contact_land.png")
    symbol_sheet(cat, "bg.base.port", (900, 1600), 3).convert("RGB").save(out / "contact_port.png")
    all_sheet(cat).convert("RGB").save(out / "contact_all.png")
    print(f"wrote build/{gid}/contact_land.png, contact_port.png, contact_all.png")
    print("Art-direction checklist (answer each before signing):")
    for c in CHECKLIST:
        print(f"  [ ] {c}")
    subprocess.run([sys.executable, str(Path(__file__).with_name("check_art_in.py")), "--game", gid])


if __name__ == "__main__":
    main()
