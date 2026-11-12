r"""Package precheck: refuse to package a game that is not submission-ready (docs/10 plan v3.3 M11, C3/C4, C-r3).

Usage (from stake\, asset venv not needed):  math-sdk\env\Scripts\python.exe tools\assets\precheck.py --game <id> [--mode test|release] [--pre-art] [--json]
Every problem carries a policy rule id and level from core\policy.v1.json (owner decision 2026-11-07):
  stake (FAIL, blocks packaging)
    assets.test      a slot in assets.lock.json has provenance licence 'test' (tools\assets\test_assets.py)
    assets.required  tile.bg, tile.fg or cover not ingested
    sims.min         a lookUpTable_<mode>_0.csv missing or under 100,000 rows, or the last run was the preview tier
    skin.testOnly    identity.testOnly is set
  ours (WARN, reported with the reason, never fails)
    assets.complete  another required slot is unfilled (still on its fallback)
    assets.humanEdit image without a real human edit (edited file missing/identical, or no edit note)
    assets.provenance licence not on the allowlist or source URL missing
    assets.signoff   art sign-off missing or stale (tools\assets\contact_sheet.py --sign)
Factory mode (game.json release.mode, tools\gamedef\mode.py; --mode overrides it): in test mode the rules whose
core\policy.v1.json row has "modes": ["release"] (assets.test, assets.provenance, assets.humanEdit, assets.signoff,
assets.complete) are off and not reported. Every Stake rule (sims, tiles exist - test tiles allowed - testOnly) applies.
--pre-art: art-related Stake rules (assets.required) are reported as WARN but do not fail (Oracle before M6d).
--json prints {"ok", "game", "mode", "preArt", "blockers": [...], "warnings": [...]}; each item {rule, level, message, why}.
Exit 1 only when there is a stake-level blocker.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, Catalog, asset_set_hash  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gamedef"))
from gamectx import game_arg  # noqa: E402
from mode import mode_arg, rule_active  # noqa: E402

MIN_ROWS = 100_000
POLICY = ROOT / "core" / "policy.v1.json"
TILE_SLOTS = ("tile.bg", "tile.fg", "cover")
TEST_LICENCE = "test"
ART_RULES = {"assets.required"}  # relaxed by --pre-art
EXTRA_WHY = {"skin.testOnly": "Test skins exist only to exercise the factory; they are never submitted."}


def policy_rules() -> dict:
    try:
        return {r["id"]: r for r in json.loads(POLICY.read_text(encoding="utf-8"))["rules"]}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def art_problems(cat: Catalog):
    """List of (rule id, message) for the art checks."""
    out = []
    lock_path = cat.game.skin / "assets.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")).get("slots", {}) if lock_path.exists() else {}
    allow = set(cat.core["imageLicences"] + cat.core["audioLicences"] + cat.core["fontLicences"])
    test_slots = sorted(sid for sid, rec in lock.items() if (rec.get("provenance") or {}).get("licence") == TEST_LICENCE)
    if test_slots:
        out.append(("assets.test", f"{len(test_slots)} slot(s) use factory test assets, which can't ship: "
                    f"{', '.join(test_slots[:8])}{' ...' if len(test_slots) > 8 else ''} (tools\\assets\\test_assets.py --clear)"))
    for s in cat.slots:
        if s["required"] != "ship":
            continue
        rec = lock.get(s["id"])
        if not rec:
            rule = "assets.required" if s["id"] in TILE_SLOTS else "assets.complete"
            out.append((rule, f"{s['id']}: not filled (still on its fallback)"))
            continue
        p = rec.get("provenance") or {}
        if p.get("licence") == TEST_LICENCE:
            continue  # reported once above as assets.test
        if s["kind"] == "image" and cat.tool(s).get("humanEdit") == "required":
            if not rec.get("editedSha") or rec.get("editedSha") == rec.get("rawSha"):
                out.append(("assets.humanEdit", f"{s['id']}: no human edit (edited file missing or identical to the AI download)"))
            if not p.get("editNote"):
                out.append(("assets.humanEdit", f"{s['id']}: edit note missing"))
        if p.get("licence") not in allow:
            out.append(("assets.provenance", f"{s['id']}: licence '{p.get('licence')}' not on the allowlist"))
        if not p.get("sourceUrl"):
            out.append(("assets.provenance", f"{s['id']}: source URL missing"))
    signoff = cat.game.skin / "art_signoff.json"
    if not signoff.exists():
        out.append(("assets.signoff", "art sign-off missing (tools\\assets\\contact_sheet.py --sign)"))
    elif json.loads(signoff.read_text(encoding="utf-8")).get("assetSetSha256") != asset_set_hash(cat):
        out.append(("assets.signoff", "art sign-off is stale: assets changed after signing"))
    return out


def math_problems(cat: Catalog):
    """List of (rule id, message) for the math output."""
    out = []
    for m in cat.game.gdef["modes"]:
        lut = cat.game.publish / f"lookUpTable_{m['name']}_0.csv"
        if not lut.exists():
            out.append(("sims.min", f"math: {lut.name} missing (build the math)"))
            continue
        with open(lut, newline="", encoding="utf-8") as f:
            rows = sum(1 for _ in csv.reader(f))
        if rows < MIN_ROWS:
            out.append(("sims.min", f"math: {lut.name} has {rows} rows, Stake needs at least {MIN_ROWS:,} simulations"))
    meta = cat.game.library / "run_meta.json"
    if meta.exists() and json.loads(meta.read_text(encoding="utf-8")).get("tier") == "preview":
        out.append(("sims.min", "math: the last run was the preview tier; run the candidate tier before packaging"))
    return out


def main():
    cat = Catalog(game_arg())
    pre_art = "--pre-art" in sys.argv
    mode = mode_arg(cat.game.gdef)
    rules = policy_rules()
    found = math_problems(cat)
    if cat.game.gdef["identity"].get("testOnly"):
        found.append(("skin.testOnly", "skin is marked identity.testOnly and can never be packaged"))
    found += art_problems(cat)
    blockers, warnings = [], []
    for rule, msg in found:
        r = rules.get(rule, {})
        if not rule_active(r, mode):
            continue  # off in this factory mode (core\policy.v1.json "modes")
        level = r.get("level", "stake")
        item = {"rule": rule, "level": level, "message": msg, "why": r.get("why") or EXTRA_WHY.get(rule) or r.get("rule", "")}
        if level == "stake" and not (pre_art and rule in ART_RULES):
            blockers.append(item)
        else:
            if level == "stake":
                item["note"] = "pre-art: not enforced yet"
            warnings.append(item)
    failed = bool(blockers)
    if "--json" in sys.argv:
        print(json.dumps({"ok": not failed, "game": cat.game.id, "mode": mode, "preArt": pre_art, "blockers": blockers, "warnings": warnings}, indent=2))
    else:
        for tag, items in (("FAIL", blockers), ("WARN", warnings)):
            for i in items:
                extra = f" ({i['note']})" if i.get("note") else ""
                print(f"{tag}  [{i['rule']}] {i['message']}{extra}" + (f" - why: {i['why']}" if i["why"] else ""))
        print(f"{'FAIL' if failed else 'OK'}: precheck {cat.game.id} [{mode} mode] ({len(blockers)} blocker(s) from Stake rules, "
              f"{len(warnings)} warning(s){', art not enforced' if pre_art else ''})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
