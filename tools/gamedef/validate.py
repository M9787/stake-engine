r"""Validate a game definition (skins/<id>/game.json): schema, then game-logic checks.

Usage:  math-sdk\\env\\Scripts\\python.exe tools\\gamedef\\validate.py skins\\oracle-of-sevens\\game.json [--json]
Exit:   0 = no errors (warnings allowed), 1 = errors, 2 = file or schema could not be read.

Messages are plain language with a field path, so the factory editor can show each one next to
its field (docs/10 section 3). Rules:
- schema: core/schema/game-definition.v1.schema.json (JSON Schema 2020-12)
- every pay symbol has one pay per band; every pay and scatter symbol is on a reel strip
- bands are contiguous and the last one ends at reels x rows; minPay equals the smallest pay
- free-spin trigger keys cover every scatter count a strip window can show (error) and up to
  reels x rows (warning: tumbles can add scatters)
- bonus variant scatter ranges do not overlap; buy modes name an existing variant
- mode names: unique ignoring case, no restricted social-casino word (Engine [77]); cheapest cost 1.0
- math: one target per mode, of the mode's kind; spin quotas sum to 1; RTP parts sum to the RTP
- enough books per outcome type at the chosen sim count (e.g. wincap >= 100 books)
"""

import csv
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import placeholders  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "core" / "schema" / "game-definition.v1.schema.json"
# Restricted social-casino phrases (Engine jurisdiction requirements), kept in one place: wording.ts.
WORDING_FILES = [
    ROOT / "core" / "web" / "cluster-tumble" / "src" / "game" / "wording.ts",
    ROOT / "game" / "web" / "seventh-veil" / "src" / "game" / "wording.ts",
]
MIN_BOOKS = {"wincap": 100, "freegame": 1000, "zero": 1000, "basegame": 1000}
RTP_TOLERANCE = 0.0005


def restricted_words():
    for path in WORDING_FILES:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            block = text.split("const SWEEPS", 1)[1].split("];", 1)[0]
            return [m[0] or m[1] for m in re.findall(r"\[\s*(?:'([^']+)'|\"([^\"]+)\")\s*,", block)]
    return []


def strip_files(game_path: Path, gdef: dict):
    folder = game_path.parent / "math" / "reels"
    return {rid: folder / name for rid, name in gdef["reels"]["files"].items()}


def read_strip(path: Path):
    rows = [r for r in csv.reader(path.open(encoding="utf-8")) if r]
    return [list(col) for col in zip(*rows)]


def max_window_count(columns, symbol, window):
    total = 0
    for col in columns:
        n = len(col)
        total += max(sum(col[(i + k) % n] == symbol for k in range(window)) for i in range(n))
    return total


def validate(game_path: Path):
    errors, warnings = [], []

    def err(path, msg):
        errors.append({"path": path, "message": msg})

    def warn(path, msg):
        warnings.append({"path": path, "message": msg})

    try:
        gdef = json.loads(game_path.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [{"path": "", "message": f"cannot read: {exc}"}], []

    for e in sorted(Draft202012Validator(schema).iter_errors(gdef), key=lambda e: list(e.absolute_path)):
        err("/".join(str(p) for p in e.absolute_path) or "(root)", e.message)
    if errors:
        return gdef, errors, warnings  # logic checks assume the schema shape

    reels, rows = gdef["board"]["reels"], gdef["board"]["rows"]
    cells = reels * rows
    symbols = {s["id"]: s for s in gdef["symbols"]}
    pay_ids = [s["id"] for s in gdef["symbols"] if s["role"] == "pay"]
    scatter_ids = [s["id"] for s in gdef["symbols"] if s["role"] == "scatter"]

    # symbols
    if len(symbols) != len(gdef["symbols"]):
        err("symbols", "Two symbols share an id.")
    if len(scatter_ids) != 1:
        err("symbols", f"Exactly one scatter symbol is needed; found {len(scatter_ids)}.")
    for s in gdef["symbols"]:
        if s["role"] == "pay" and "tier" not in s:
            err(f"symbols/{s['id']}", "Pay symbols need a tier (high or low).")

    # paytable
    pt = gdef["paytable"]
    bands = pt["bands"]
    for i, (lo, hi) in enumerate(bands):
        if lo > hi:
            err(f"paytable/bands/{i}", f"Band {lo}-{hi} runs backwards.")
        if i and lo != bands[i - 1][1] + 1:
            err(f"paytable/bands/{i}", f"Band starts at {lo}; it must start right after {bands[i - 1][1]}.")
    if bands[-1][1] != cells:
        err("paytable/bands", f"The last band must end at {cells} (reels x rows); it ends at {bands[-1][1]}.")
    for sid in pay_ids:
        pays = pt["pays"].get(sid)
        if pays is None:
            err(f"paytable/pays/{sid}", f"Pay symbol {sid} has no pays.")
        elif len(pays) != len(bands):
            err(f"paytable/pays/{sid}", f"{sid} has {len(pays)} pays; there are {len(bands)} bands.")
        elif any(b < a for a, b in zip(pays, pays[1:])):
            warn(f"paytable/pays/{sid}", f"{sid} pays less for a bigger cluster.")
    for sid in pt["pays"]:
        if sid not in pay_ids:
            err(f"paytable/pays/{sid}", f"{sid} is not a pay symbol.")
    all_pays = [p for sid in pay_ids for p in pt["pays"].get(sid, [])]
    if all_pays and abs(min(all_pays) - pt["minPay"]) > 1e-9:
        err("paytable/minPay", f"minPay is {pt['minPay']}; the smallest pay is {min(all_pays)}.")

    # reel strips
    max_scatter = 0
    on_reels = set()
    for rid, path in strip_files(game_path, gdef).items():
        if not path.exists():
            err(f"reels/files/{rid}", f"Reel strip file not found: {path.relative_to(ROOT)}")
            continue
        cols = read_strip(path)
        if len(cols) != reels:
            err(f"reels/files/{rid}", f"{path.name} has {len(cols)} reels; the board has {reels}.")
        for col in cols:
            on_reels |= set(col)
            unknown = set(col) - set(symbols)
            if unknown:
                err(f"reels/files/{rid}", f"{path.name} uses unknown symbols {sorted(unknown)}.")
        if scatter_ids:
            max_scatter = max(max_scatter, max_window_count(cols, scatter_ids[0], rows))
    for sid in pay_ids + scatter_ids:
        if sid not in on_reels:
            err(f"symbols/{sid}", f"{sid} is on no reel strip, so it can never land.")
    for s in gdef["symbols"]:
        if s["role"] == "wild" and s["id"] not in on_reels:
            warn(f"symbols/{s['id']}", f"Wild {s['id']} is on no reel strip (declared but unused).")

    # free-spin triggers
    for kind, table in gdef["freespinTriggers"].items():
        counts = sorted(int(k) for k in table)
        if not counts:
            err(f"freespinTriggers/{kind}", "No trigger counts.")
            continue
        missing = [c for c in range(counts[0], max(counts[-1], max_scatter) + 1) if str(c) not in table]
        if missing:
            err(f"freespinTriggers/{kind}", f"Missing scatter counts {missing}: a board can show up to {max_scatter} scatters.")
        if counts[-1] < cells:
            warn(f"freespinTriggers/{kind}", f"Counts stop at {counts[-1]}; tumbles could add scatters up to {cells}.")

    # bonus variants
    variants = gdef["features"]["bonusVariants"]
    ids = [v["id"] for v in variants]
    if len(set(ids)) != len(ids):
        err("features/bonusVariants", "Two bonus variants share an id.")
    spans = sorted((v["scatterMin"], v["scatterMax"], v["id"]) for v in variants)
    for i, (lo, hi, vid) in enumerate(spans):
        if lo > hi:
            err(f"features/bonusVariants/{vid}", f"Scatter range {lo}-{hi} runs backwards.")
        if i and lo <= spans[i - 1][1]:
            err(f"features/bonusVariants/{vid}", f"Scatter range overlaps variant {spans[i - 1][2]}.")
    base_min = min(int(k) for k in gdef["freespinTriggers"]["basegame"])
    if spans and spans[0][0] != base_min:
        err("features/bonusVariants", f"The lowest variant starts at {spans[0][0]} scatters; free spins start at {base_min}.")
    for v in variants:
        if v["precharge"]["spots"] > cells:
            err(f"features/bonusVariants/{v['id']}/precharge/spots", f"More pre-charged spots than cells ({cells}).")
        if v["precharge"]["value"] > gdef["features"]["gridMultiplier"]["cap"]:
            err(f"features/bonusVariants/{v['id']}/precharge/value", "Pre-charge value is above the grid cap.")

    # modes
    words = restricted_words()
    names_lower = [m["name"].lower() for m in gdef["modes"]]
    if len(set(names_lower)) != len(names_lower):
        err("modes", "Two modes share a name (ignoring case).")
    for m in gdef["modes"]:
        path = f"modes/{m['name']}"
        hit = [w for w in words if re.search(rf"\b{re.escape(w)}\b", m["name"].replace("_", " ").replace("-", " "), re.I)]
        if hit:
            err(path, f"Mode name uses restricted social-casino words {hit} (Engine [77]); mode names are shared with social play.")
        if m["kind"] == "buy":
            if m.get("variant") not in ids:
                err(f"{path}/variant", f"Buy mode needs an existing bonus variant {ids}.")
            if not m["scatterTriggers"].get("all"):
                err(f"{path}/scatterTriggers/all", "Buy mode needs scatter counts to trigger its bonus.")
            else:
                v = next((v for v in variants if v["id"] == m.get("variant")), None)
                for c in m["scatterTriggers"]["all"]:
                    if v and not v["scatterMin"] <= int(c) <= v["scatterMax"]:
                        err(f"{path}/scatterTriggers/all/{c}", f"{c} scatters start variant outside {v['id']} ({v['scatterMin']}-{v['scatterMax']}).")
        else:
            q = m["quotas"]
            for key in ("freegame", "zero", "basegame"):
                if key not in q:
                    err(f"{path}/quotas/{key}", "Spin modes need this quota.")
            total = sum(q.values())
            if abs(total - 1) > 1e-6:
                err(f"{path}/quotas", f"Quotas add up to {total:.4f}; they must add up to 1.")
        sims = gdef["math"]["sims"].get(m["name"])
        if sims is None:
            err(f"math/sims/{m['name']}", "No sim count for this mode.")
        else:
            q = dict(m["quotas"])
            if m["kind"] == "buy":
                q["freegame"] = 1 - q["wincap"]
            for key, share in q.items():
                need = MIN_BOOKS[key]
                if share * sims < need:
                    err(f"{path}/quotas/{key}", f"Only {share * sims:.0f} {key} books at {sims} sims; at least {need} are needed.")
    costs = [m["cost"] for m in gdef["modes"]]
    if min(costs) != 1.0:
        err("modes", f"The cheapest mode must cost 1.0 (Engine critical test); it costs {min(costs)}.")

    # math targets
    math = gdef["math"]
    for m in gdef["modes"]:
        t = math["targets"].get(m["name"])
        path = f"math/targets/{m['name']}"
        if t is None:
            err(path, "No math target for this mode.")
            continue
        if t["kind"] != m["kind"]:
            err(f"{path}/kind", f"Target kind {t['kind']} does not match mode kind {m['kind']}.")
            continue
        parts = t["wincapRtp"] + t["freegameRtp"] + t.get("basegameRtp", 0)
        if abs(parts - math["rtp"]) > RTP_TOLERANCE:
            err(path, f"RTP parts add up to {parts:.4f}; they must add up to the game RTP {math['rtp']}.")
        if m["kind"] == "spin":
            fg_share = m["quotas"]["freegame"]
            if 1 / t["bonusOneIn"] > fg_share:
                err(f"{path}/bonusOneIn", "Bonus is more frequent than the share of bonus books in the pool.")
            paying = m["quotas"]["freegame"] + m["quotas"]["basegame"] + m["quotas"]["wincap"]
            if 1 / t["hitOneIn"] > paying:
                err(f"{path}/hitOneIn", f"Hit rate 1 in {t['hitOneIn']} needs more paying books than the pool has ({paying:.2f}).")
        elif t["minM2m"] > t["maxM2m"]:
            err(f"{path}/minM2m", "minM2m is above maxM2m.")
        rs = t.get("reshape")
        if rs and not rs["split"] < rs["hiFrom"] < math["wincap"]:
            err(f"{path}/reshape", "Reshape needs split < hiFrom < wincap.")
    for name in math["targets"]:
        if name not in [m["name"] for m in gdef["modes"]]:
            err(f"math/targets/{name}", "Target for a mode that does not exist.")

    check_texts(game_path, gdef, err, warn)
    return gdef, errors, warnings


def check_texts(game_path: Path, gdef: dict, err, warn):
    """text/en.json: every needed key exists, placeholders resolve, numbers come from placeholders."""
    text_path = game_path.parent / "text" / "en.json"
    if not text_path.exists():
        err("text/en.json", "Missing: player texts for English.")
        return
    try:
        texts = json.loads(text_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err("text/en.json", f"Not valid JSON: {exc}")
        return
    needed = ["game.name"] + [s["nameKey"] for s in gdef["symbols"]]
    for m in gdef["modes"]:
        needed += [f"mode.{m['name']}.{f}" for f in ("title", "label", "dialog")]
    for key in needed:
        if key not in texts:
            err(f"text/en.json/{key}", "Missing text.")
    vals = placeholders.values(gdef)
    words = restricted_words()
    for key, text in texts.items():
        if key.startswith("_") or not isinstance(text, str):
            continue
        for name in placeholders.unresolved(text, vals):
            err(f"text/en.json/{key}", f"Unknown placeholder {{{name}}}.")
        bare = placeholders.PLACEHOLDER.sub("", text)
        # "x2" (first charge) and "1 in N" odds wording are fixed; other numbers come from game.json.
        if re.search(r"(?<![x\w])\d", re.sub(r"\b1 in\b", "", bare)):
            warn(f"text/en.json/{key}", "Typed number: use a {placeholder} so it follows game.json.")
        if key.startswith("mode.") and key.endswith(".title"):
            hit = [w for w in words if re.search(rf"\b{re.escape(w)}\b", text, re.I)]
            if hit:
                warn(f"text/en.json/{key}", f"Social casino play rewrites {hit} in this title.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    game_path = Path(args[0]).resolve()
    gdef, errors, warnings = validate(game_path)
    if "--json" in sys.argv:
        print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, indent=2))
    else:
        for e in errors:
            print(f"ERROR  {e['path']}: {e['message']}")
        for w in warnings:
            print(f"warn   {w['path']}: {w['message']}")
        print(f"{'OK' if not errors else 'FAIL'}: {len(errors)} error(s), {len(warnings)} warning(s) - {game_path.name}")
    sys.exit(2 if gdef is None else (1 if errors else 0))


if __name__ == "__main__":
    main()
