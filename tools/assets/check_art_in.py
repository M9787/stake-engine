r"""Check the owner's asset drop folder for one game, in plain language (docs/10 plan v3.3 section 14).

Usage (from stake\, asset venv for image sizes):
  .venv-assets\Scripts\python.exe tools\assets\check_art_in.py --game seventh_veil          report
  .venv-assets\Scripts\python.exe tools\assets\check_art_in.py --game seventh_veil --gate   exit 1 unless every
                                                                                             required slot is complete (M6d entry)
Folder: skins\<skin>\art_in\raw\<slot>.<ext> (AI download), art_in\edited\<slot>.<ext> (your edit),
art_in\provenance.json (saved from build\<id>\prompts.html).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import EXT, ROOT, Catalog, sha256_file  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402

try:
    from PIL import Image
except ImportError:  # sizes are skipped without Pillow
    Image = None

ASPECT_TOL = 0.03


def aspect_of(text: str):
    a, b = text.split(":")
    return int(a) / int(b)


def check_slot(cat: Catalog, s: dict, prov: dict, allow: set, current_sha: str):
    """Return (complete: bool, issues: list[str])."""
    issues = []
    tool = cat.tool(s)
    raw, edited = cat.find("raw", s), cat.find("edited", s)
    need_edit = s["kind"] == "image" and tool.get("humanEdit") == "required"
    if not raw:
        return False, ["no file yet"]
    if need_edit and not edited:
        issues.append("edited file missing: open the raw file in Photopea, follow the edit recipe, save to art_in\\edited\\")
    if need_edit and edited and sha256_file(raw) == sha256_file(edited):
        issues.append("edited file is identical to the download: a real human edit is required")
    if s["kind"] == "image" and Image and s.get("aspect"):
        for lane, f in (("raw", raw), ("edited", edited)):
            if not f:
                continue
            with Image.open(f) as im:
                w, h = im.size
            want = aspect_of(s["aspect"])
            if abs(w / h - want) / want > ASPECT_TOL:
                issues.append(f"{lane} file is {w}x{h}, expected aspect {s['aspect']}: regenerate with --ar {s['aspect']} or crop")
            if s.get("px") and (w < s["px"][0] or h < s["px"][1]):
                issues.append(f"{lane} file is {w}x{h}, smaller than the game size {s['px'][0]}x{s['px'][1]}: upscale first")
    p = prov.get(s["id"], {})
    lic = p.get("licence", "")
    if not lic:
        issues.append("provenance: licence not filled")
    elif lic not in allow:
        issues.append(f"provenance: licence '{lic}' is not allowed (allowed: {', '.join(sorted(allow))})")
    if not p.get("sourceUrl"):
        issues.append("provenance: source URL not filled")
    if need_edit and not p.get("editNote"):
        issues.append("provenance: edit note not filled (say what you changed)")
    if p.get("promptSha") and p["promptSha"] != current_sha:
        issues.append("prompt changed since this file was made (style bible edited): check it still fits, or regenerate")
    if p.get("redo"):
        issues.append(f"marked for redo: {p['redo']}")
    return not issues, issues


def unknown_files(cat: Catalog):
    stems = {s["fileStem"] for s in cat.slots}
    exts = {e for v in EXT.values() for e in v}
    out = []
    for lane in ("raw", "edited"):
        folder = cat.art_in / lane
        if not folder.exists():
            continue
        for f in sorted(folder.iterdir()):
            if f.is_file() and (f.stem not in stems or f.suffix.lower() not in exts):
                out.append(f"art_in\\{lane}\\{f.name}")
    return out


def main():
    gid = game_arg()
    cat = Catalog(gid)
    prov = cat.provenance()
    allow = set(cat.core["imageLicences"] + cat.core["audioLicences"] + cat.core["fontLicences"])
    if cat.core.get("testLicence"):
        allow.add(cat.core["testLicence"])  # factory test placeholders (tools\assets\test_assets.py); precheck blocks them
    required = [s for s in cat.slots if s["required"] == "ship"]
    done = 0
    by_sitting = {}
    for s in cat.slots:
        ok, issues = check_slot(cat, s, prov, allow, s["promptSha"])
        if ok and s["required"] == "ship":
            done += 1
        by_sitting.setdefault(s["sitting"], []).append((s, ok, issues))
    if "--json" in sys.argv:
        out = {
            "required": {"filled": done, "total": len(required)},
            "unknownFiles": unknown_files(cat),
            "slots": {s["id"]: {"complete": ok, "issues": issues} for rows in by_sitting.values() for s, ok, issues in rows},
        }
        print(json.dumps(out))
        return
    titles = {x["id"]: x["title"] for x in cat.core["sittings"]}
    for sid in sorted(by_sitting):
        rows = by_sitting[sid]
        n_ok = sum(1 for _, ok, _ in rows if ok)
        print(f"\nSitting {sid} - {titles.get(sid, '')}: {n_ok}/{len(rows)} complete")
        for s, ok, issues in rows:
            if ok:
                continue
            tag = "required" if s["required"] == "ship" else s["required"]
            print(f"  {s['id']} ({tag}): " + "; ".join(issues))
    extra = unknown_files(cat)
    if extra:
        print("\nFiles with an unknown name (rename to a slot id from prompts.html):")
        for f in extra:
            print(f"  {f}")
    minutes = json.loads((cat.art_in / "provenance.json").read_text(encoding="utf-8")).get("minutes", {}) if (cat.art_in / "provenance.json").exists() else {}
    spent = sum(float(v) for v in minutes.values() if str(v).replace(".", "", 1).isdigit())
    print(f"\nRequired slots complete: {done}/{len(required)}. Owner minutes logged: {spent:g}.")
    if "--gate" in sys.argv:
        ok = done == len(required) and not extra
        print("GATE " + ("PASS" if ok else "FAIL: every required slot must be complete and every file name known"))
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
