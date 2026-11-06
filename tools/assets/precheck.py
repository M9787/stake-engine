r"""Package precheck: refuse to package a game that is not submission-ready (docs/10 plan v3.3 M11, C3/C4, C-r3).

Usage (from stake\, asset venv not needed):  math-sdk\env\Scripts\python.exe tools\assets\precheck.py --game <id> [--pre-art]
Checks, in plain language:
  art     every required slot ingested (assets.lock.json), images with a real human edit (edited file
          differs from the AI download, edit note filled), licence on the allowlist with a source URL,
          art sign-off present and matching the current asset-set hash (tools\assets\contact_sheet.py --sign)
  math    every lookUpTable_<mode>_0.csv has at least 100,000 rows; run_meta.json not from the preview tier
  skin    identity.testOnly is not set
--pre-art reports the art checks but does not fail on them (Oracle before M6d).
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import Catalog, asset_set_hash  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gamedef"))
from gamectx import game_arg  # noqa: E402

MIN_ROWS = 100_000


def art_problems(cat: Catalog):
    out = []
    lock_path = cat.game.skin / "assets.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")).get("slots", {}) if lock_path.exists() else {}
    allow = set(cat.core["imageLicences"] + cat.core["audioLicences"] + cat.core["fontLicences"])
    for s in cat.slots:
        if s["required"] != "ship":
            continue
        rec = lock.get(s["id"])
        if not rec:
            out.append(f"{s['id']}: not filled (still on its fallback)")
            continue
        p = rec.get("provenance") or {}
        if s["kind"] == "image" and cat.tool(s).get("humanEdit") == "required":
            if not rec.get("editedSha") or rec.get("editedSha") == rec.get("rawSha"):
                out.append(f"{s['id']}: no human edit (edited file missing or identical to the AI download)")
            if not p.get("editNote"):
                out.append(f"{s['id']}: edit note missing")
        if p.get("licence") not in allow:
            out.append(f"{s['id']}: licence '{p.get('licence')}' not on the allowlist")
        if not p.get("sourceUrl"):
            out.append(f"{s['id']}: source URL missing")
    signoff = cat.game.skin / "art_signoff.json"
    if not signoff.exists():
        out.append("art sign-off missing (tools\\assets\\contact_sheet.py --sign)")
    elif json.loads(signoff.read_text(encoding="utf-8")).get("assetSetSha256") != asset_set_hash(cat):
        out.append("art sign-off is stale: assets changed after signing")
    return out


def math_problems(cat: Catalog):
    out = []
    for m in cat.game.gdef["modes"]:
        lut = cat.game.publish / f"lookUpTable_{m['name']}_0.csv"
        if not lut.exists():
            out.append(f"math: {lut.name} missing (build the math)")
            continue
        with open(lut, newline="", encoding="utf-8") as f:
            rows = sum(1 for _ in csv.reader(f))
        if rows < MIN_ROWS:
            out.append(f"math: {lut.name} has {rows} rows, Stake needs at least {MIN_ROWS:,} simulations")
    meta = cat.game.library / "run_meta.json"
    if meta.exists() and json.loads(meta.read_text(encoding="utf-8")).get("tier") == "preview":
        out.append("math: the last run was the preview tier; run the candidate tier before packaging")
    return out


def main():
    cat = Catalog(game_arg())
    pre_art = "--pre-art" in sys.argv
    art = art_problems(cat)
    hard = math_problems(cat)
    if cat.game.gdef["identity"].get("testOnly"):
        hard.append("skin is marked identity.testOnly and can never be packaged")
    for p in hard:
        print(f"  FAIL  {p}")
    for p in art:
        print(f"  {'TODO' if pre_art else 'FAIL'}  {p}")
    failed = bool(hard) or (bool(art) and not pre_art)
    print(f"{'FAIL' if failed else 'OK'}: precheck {cat.game.id} ({len(hard)} math/skin, {len(art)} art problem(s){', art not enforced' if pre_art else ''})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
