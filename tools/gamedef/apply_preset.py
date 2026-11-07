r"""Set up a cluster_tumble game's mechanics and math from simple presets (factory editor "Setup > Presets").

Usage:  math-sdk\env\Scripts\python.exe tools\gamedef\apply_preset.py --game <gameId> --board <reels>x<rows>
            --volatility low|medium|high --wincap <N> --bonus-one-in <N> --modes base[,ante][,buy] [--json]

Rewrites the math-related sections of skins/<skin>/game.json (board, symbols, paytable, reels, freespinTriggers,
features, reelWeights, modes, math) from core/presets/boards.json and core/presets/volatility/<v>.json, writes the
reel strips BR0/FR0/WCAP to skins/<skin>/math/reels (columns of Oracle's strips, taken in order and repeated
from the first column when the board has more reels), adds missing text keys for symbols and modes to
text/en.json (existing wording is kept; texts of removed modes move to _removed.* keys and come back with the mode), then runs validate.py and prints its result.

Kept: identity, theme, presentation (initialBoard dropped when its shape no longer fits), review, listing, the ids
of the first bonus variant, the first extra-cost spin mode and the first buy mode. Symbols become H1-H4, L1-L4, S.
Mode names: base, the ante mode keeps its name (else 'boost'), the buy mode keeps its name (else the variant id).
Does not snapshot (the editor snapshots before it starts this job). Deterministic. Refuses frozen games (Oracle).
Exit: 0 = written and valid, 1 = written but validate.py found errors, 2 = refused (nothing written).
"""

import csv
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESETS = ROOT / "core" / "presets"
SOURCE_STRIPS = ROOT / "skins" / "oracle-of-sevens" / "math" / "reels"  # proven 7-reel strips (skin #1)
STRIPS = ("BR0", "FR0", "WCAP")
FROZEN_GAMES = {"seventh_veil"}  # PROJECT.md section 4 (same list as factory/src/lib/server/repo.ts)
RTP = 0.965
SIMS = 100000
DEFAULT_RUN = {"threads": 10, "rustThreads": 20, "batching": 50000}
SYMBOLS = [("H1", "high"), ("H2", "high"), ("H3", "high"), ("H4", "high"),
           ("L1", "low"), ("L2", "low"), ("L3", "low"), ("L4", "low")]
SYMBOL_NAMES = {"H1": "Ruby", "H2": "Sapphire", "H3": "Emerald", "H4": "Topaz",
                "L1": "Ace", "L2": "King", "L3": "Queen", "L4": "Jack", "S": "Bonus Gem"}
MODE_KINDS = ("base", "ante", "buy")


class Refused(Exception):
    pass


def num(x):
    """Round to 6 places; whole numbers stay floats only where the input was a float (cost 1.0)."""
    return round(float(x), 6)


def arg(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
        raise Refused(f"{name} needs a value")
    if default is None:
        raise Refused(f"missing {name}")
    return default


def parse(argv):
    game = arg(argv, "--game")
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,40}", game):
        raise Refused(f"invalid game id '{game}'")
    board = arg(argv, "--board")
    if not re.fullmatch(r"[5-8]x[5-8]", board):
        raise Refused("board: <reels>x<rows>, each 5 to 8 (for example 6x6)")
    vol = arg(argv, "--volatility")
    if vol not in ("low", "medium", "high"):
        raise Refused("volatility: low, medium or high")
    try:
        wincap = float(arg(argv, "--wincap"))
        bonus = float(arg(argv, "--bonus-one-in"))
    except ValueError:
        raise Refused("max win and bonus frequency must be numbers") from None
    if not 100 <= wincap <= 1_000_000:
        raise Refused("max win: 100 to 1,000,000 x bet")
    if not 20 <= bonus <= 2000:
        raise Refused("bonus frequency: about 1 in 20 to 1 in 2000 spins")
    modes = [m.strip() for m in arg(argv, "--modes").split(",") if m.strip()]
    if not modes or any(m not in MODE_KINDS for m in modes) or len(set(modes)) != len(modes):
        raise Refused("modes: base, ante, buy (comma separated, no repeats)")
    if "base" not in modes:
        raise Refused("the base mode is always needed (the cheapest mode must cost 1x)")
    return game, board, vol, wincap, bonus, [m for m in MODE_KINDS if m in modes]


def find_skin(game_id):
    for path in sorted((ROOT / "skins").glob("*/game.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("identity", {}).get("gameId") == game_id:
            return path.parent, data
    raise Refused(f"unknown game '{game_id}'")


def read_strip(name):
    with (SOURCE_STRIPS / f"{name}.csv").open(encoding="utf-8") as f:
        return [r for r in csv.reader(f) if r]


def build_strip(name, reels):
    """Columns 0..reels-1 of the source strip; column i takes source column i mod (source width)."""
    rows = read_strip(name)
    width = len(rows[0])
    buf = io.StringIO()
    for r in rows:
        buf.write(",".join(r[i % width] for i in range(reels)) + "\n")
    return buf.getvalue()


def cut_counts(table, most):
    return {k: v for k, v in table.items() if int(k) <= most}


def grid_cap(preset, wincap):
    cap = next(c for limit, c in preset["grid"]["capByWincap"] if wincap <= limit)
    return int(min(4096, cap * preset["grid"]["capFactor"]))


def buy_scaling(buy, wincap):
    top_from = round(wincap * buy["topScaling"][0])
    rules = []
    for (lo, hi), factor in buy["scaling"]:
        if lo >= top_from:
            continue
        rules.append([[lo, min(hi, top_from)], factor])
    rules.append([[top_from, int(wincap) - 1], buy["topScaling"][1]])
    return rules


def spin_target(section, bonus_one_in):
    base_rtp = RTP - section["wincapRtp"] - section["freegameRtp"]
    return {
        "kind": "spin",
        "wincapRtp": section["wincapRtp"],
        "freegameRtp": section["freegameRtp"],
        "bonusOneIn": bonus_one_in,
        "basegameRtp": num(base_rtp),
        "hitOneIn": section["hitOneIn"],
        "midWinLift": section["midWinLift"],
        "baseScaling": section["baseScaling"],
    }


def whole(x):
    return int(x) if float(x).is_integer() else x


def apply(gdef, board_key, vol, wincap, bonus, kinds):
    boards = json.loads((PRESETS / "boards.json").read_text(encoding="utf-8"))
    preset = json.loads((PRESETS / "volatility" / f"{vol}.json").read_text(encoding="utf-8"))
    b = boards["boards"][board_key]
    reels, rows, cells, most = b["reels"], b["rows"], b["cells"], b["maxWindowScatters"]

    # Ids that stay: first bonus variant, first extra-cost spin mode, first buy mode.
    old_modes = gdef.get("modes", [])
    old_variants = gdef.get("features", {}).get("bonusVariants", [])
    variant_id = old_variants[0]["id"] if old_variants else "bonus"
    ante_name = next((m["name"] for m in old_modes if m["kind"] == "spin" and m["cost"] > 1), "boost")
    buy_name = next((m["name"] for m in old_modes if m["kind"] == "buy"), variant_id)
    names = {"base": "base", "ante": ante_name, "buy": buy_name}
    if ante_name.lower() == "base":
        names["ante"] = "boost"

    old_symbols = {s["id"]: s for s in gdef.get("symbols", [])}
    symbols = [{"id": sid, "role": "pay", "tier": tier, "nameKey": old_symbols.get(sid, {}).get("nameKey", f"symbol.{sid}")}
               for sid, tier in SYMBOLS]
    symbols.append({"id": "S", "role": "scatter", "nameKey": old_symbols.get("S", {}).get("nameKey", "symbol.S")})

    pays = {sid: [float(p) for p in preset["pays"][sid]] for sid, _ in SYMBOLS}
    retrigger = preset["retriggerSpins"]
    triggers = {"basegame": dict(b["freespinTriggers"]["basegame"]),
                "freegame": {k: retrigger for k in b["freespinTriggers"]["freegame"]}}
    trigger_min = min(int(k) for k in triggers["basegame"])
    cap = grid_cap(preset, wincap)
    old_grid = gdef.get("features", {}).get("gridMultiplier", {})

    modes, targets, sims = [], {}, {}
    for kind in kinds:
        sec = preset[kind]
        name = names[kind]
        if kind == "buy":
            modes.append({"name": name, "kind": "buy", "variant": variant_id, "cost": float(sec["cost"]),
                          "quotas": dict(sec["quotas"]),
                          "scatterTriggers": {"all": cut_counts(sec["scatterTriggers"]["all"], most)}})
            targets[name] = {"kind": "buy", "wincapRtp": sec["wincapRtp"], "freegameRtp": sec["freegameRtp"],
                             "minM2m": sec["minM2m"], "maxM2m": sec["maxM2m"], "scaling": buy_scaling(sec, wincap)}
        else:
            cost = 1.0 if kind == "base" else float(sec["cost"])
            one_in = bonus if kind == "base" else max(20, round(bonus * sec["bonusRatio"]))
            modes.append({"name": name, "kind": "spin", "cost": cost, "quotas": dict(sec["quotas"]),
                          "scatterTriggers": {"wincap": cut_counts(sec["scatterTriggers"]["wincap"], most),
                                              "freegame": cut_counts(sec["scatterTriggers"]["freegame"], most)}})
            targets[name] = spin_target(sec, whole(one_in))
        sims[name] = SIMS

    new = {
        "board": {"reels": reels, "rows": rows, "includePadding": gdef.get("board", {}).get("includePadding", True)},
        "symbols": symbols,
        "paytable": {"bands": b["bands"], "pays": pays, "minPay": min(p for v in pays.values() for p in v)},
        "reels": {"files": {s: f"{s}.csv" for s in STRIPS}},
        "freespinTriggers": triggers,
        "features": {
            "gridMultiplier": {"enabled": True, "cap": cap, "scope": old_grid.get("scope", "spin")},
            "bonusVariants": [{"id": variant_id, "scatterMin": trigger_min, "scatterMax": cells,
                               "precharge": dict(preset["precharge"]), "buyFloor": float(preset["buyFloor"])}],
        },
        "reelWeights": {"fg": {"basegame": {"BR0": 1}, "freegame": {"FR0": 1}},
                        "cap": {"basegame": {"BR0": 1}, "freegame": {"FR0": 1, "WCAP": 5}}},
        "modes": modes,
        "math": {"rtp": RTP, "wincap": float(wincap), "sims": sims,
                 "run": gdef.get("math", {}).get("run", DEFAULT_RUN), "targets": targets},
    }
    # Keep the file's key order: replace sections in place, add missing ones before theme/review.
    out = {}
    for k, v in gdef.items():
        out[k] = new.pop(k) if k in new else v
    for k, v in new.items():
        out[k] = v
    pres = out.get("presentation")
    if isinstance(pres, dict) and "initialBoard" in pres:
        ib = pres["initialBoard"]
        pad = 2 if out["board"]["includePadding"] else 0
        if len(ib) != reels or any(len(col) != rows + pad for col in ib) or any(c not in {s["id"] for s in symbols} for col in ib for c in col):
            pres.pop("initialBoard")
    return out, names, preset


PARKED = "_removed."  # texts of removed modes: kept (validate.py skips "_" keys), restored when the mode returns


def park_texts(texts, kept_names):
    """Move mode.<name>.* texts of modes that do not exist (any more) to _removed.mode.<name>.* (their
    placeholders would no longer resolve). Returns the parked keys."""
    parked = []
    for key in list(texts):
        parts = key.split(".")
        if len(parts) >= 3 and parts[0] == "mode" and parts[1] not in kept_names:
            texts[PARKED + key] = texts.pop(key)
            parked.append(key)
    return parked


def add_texts(texts, gdef, names, kinds):
    added = []

    def put(key, value):
        if key not in texts:
            texts[key] = texts.pop(PARKED + key, value)
            added.append(key)

    for s in gdef["symbols"]:
        put(s["nameKey"], SYMBOL_NAMES.get(s["id"], s["id"]))
    for kind in kinds:
        n = names[kind]
        pretty = n.replace("_", " ").replace("-", " ").title()
        if kind == "base":
            put(f"mode.{n}.title", "STANDARD")
            put(f"mode.{n}.label", "Standard")
            put(f"mode.{n}.dialog", f"Standard play. {{mode.{n}.rtpText}}")
        elif kind == "ante":
            put(f"mode.{n}.title", pretty.upper())
            put(f"mode.{n}.label", pretty)
            put(f"mode.{n}.dialog", f"Price {{mode.{n}.cost}}x per spin for more frequent bonuses. {{mode.{n}.rtpText}}")
        else:
            put(f"mode.{n}.title", f"{pretty.upper()} BONUS")
            put(f"mode.{n}.label", f"{pretty} Bonus")
            put(f"mode.{n}.dialog", f"Starts the bonus at once. {{mode.{n}.rtpText}}")
    return added


def validate(game_json):
    v = subprocess.run([sys.executable, str(ROOT / "tools" / "gamedef" / "validate.py"), str(game_json), "--json"],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(v.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "errors": [{"path": "", "message": (v.stderr or v.stdout).strip()[:500]}], "warnings": []}


def main():
    argv = sys.argv[1:]
    as_json = "--json" in argv
    try:
        game, board, vol, wincap, bonus, kinds = parse(argv)
        if game in FROZEN_GAMES:
            raise Refused(f"'{game}' is an approved game: its modes and math are frozen (PROJECT.md section 4)")
        skin, gdef = find_skin(game)
        out, names, preset = apply(gdef, board, vol, wincap, bonus, kinds)
    except Refused as exc:
        if as_json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"REFUSED: {exc}")
        sys.exit(2)

    reel_dir = skin / "math" / "reels"
    reel_dir.mkdir(parents=True, exist_ok=True)
    for s in STRIPS:
        (reel_dir / f"{s}.csv").write_text(build_strip(s, out["board"]["reels"]), encoding="utf-8", newline="\n")
    (skin / "game.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    text_path = skin / "text" / "en.json"
    texts = json.loads(text_path.read_text(encoding="utf-8")) if text_path.exists() else {}
    parked = park_texts(texts, {m["name"] for m in out["modes"]})
    added = add_texts(texts, out, names, kinds)
    if added or parked or not text_path.exists():
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(json.dumps(texts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    result = validate(skin / "game.json")
    notes = []
    if (skin / "math" / "lookups").exists():
        notes.append("This game had frozen math weights (math\\lookups); they no longer match. Run the math again before freezing.")
    summary = {
        "ok": bool(result.get("ok")),
        "game": game,
        "skin": skin.name,
        "applied": {"board": board, "volatility": vol, "wincap": wincap, "bonusOneIn": bonus,
                    "modes": [{"kind": k, "name": names[k]} for k in kinds], "gridCap": out["features"]["gridMultiplier"]["cap"]},
        "textsAdded": added,
        "textsParked": parked,
        "notes": notes,
        "validation": result,
    }
    if as_json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Applied {vol} preset on a {board} board to skins\\{skin.name} (game {game}).")
        print("Modes: " + ", ".join(f"{names[k]} ({k})" for k in kinds) + f"; max win {wincap:g}x; bonus about 1 in {bonus:g}.")
        if added:
            print("Texts added or restored (please check the wording): " + ", ".join(added))
        if parked:
            print("Texts of removed modes kept as _removed.*: " + ", ".join(parked))
        for n in notes:
            print("Note: " + n)
        for e in result.get("errors", []):
            print(f"ERROR  {e['path']}: {e['message']}")
        for w in result.get("warnings", []):
            print(f"warn   {w['path']}: {w['message']}")
        print(f"{'OK' if result.get('ok') else 'FAIL'}: {len(result.get('errors', []))} error(s), {len(result.get('warnings', []))} warning(s)")
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
