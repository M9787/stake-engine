r"""Write build/<id>/web/rules.generated.json: every player text with its numbers filled in.

Usage:  math-sdk\env\Scripts\python.exe tools\gen\gen_rules.py [--game <gameId>] [--lang en] [--out <file>]
Exit:   0 = written, 1 = a text has a placeholder that nothing fills.

Numbers come only from data, never from hand-typed text (docs/10 section 2):
- the published math (library/configs/config_fe_<id>.json): RTP, max win, cost and pays per mode;
- game.json for design values that the math does not publish (spins, precharge, bonus 1-in-N target).
The pay table and the mode table are built here too, so GameInfo renders data only (M10).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gamedef"))
from gamectx import Game, game_arg  # noqa: E402
from placeholders import _fmt, fill, unresolved, values  # noqa: E402


def sdk_type(mode: dict) -> str:
    """Bet mode type in the web SDK: the 1x spin mode is 'default', priced spin modes 'activate'."""
    if mode["kind"] == "buy":
        return "buy"
    return "default" if mode["cost"] == 1.0 else "activate"


def band_label(lo: int, hi: int, last: bool) -> str:
    if last:
        return f"{lo}+"
    return str(lo) if lo == hi else f"{lo}-{hi}"


def build(g: Game, lang: str = "en") -> dict:
    gdef, fe, text = g.gdef, g.fe(), g.text(lang)
    vals = values(gdef)
    # Published math wins over game.json targets for anything the math publishes.
    for name, m in fe["betModes"].items():
        vals[f"mode.{name}.cost"] = _fmt(m["cost"])
        vals[f"mode.{name}.rtp"] = f"{m['rtp'] * 100:.2f}"
        vals[f"mode.{name}.maxWin"] = _fmt(m["max_win"])
        vals[f"mode.{name}.rtpText"] = f"RTP {m['rtp'] * 100:.2f}%. Max win {m['max_win']:,.0f}x."

    texts, missing = {}, {}
    for key, raw in text.items():
        if key.startswith("_") or not isinstance(raw, str):
            continue
        gaps = unresolved(raw, vals)
        if gaps:
            missing[key] = gaps
        texts[key] = fill(raw, vals)

    pays = {}
    for entry in fe["symbols"]:
        pays.update(entry)
    bands = gdef["paytable"]["bands"]
    paytable = {
        "bands": [band_label(lo, hi, i == len(bands) - 1) for i, (lo, hi) in enumerate(bands)],
        "rows": [],
    }
    for sym in gdef["symbols"]:
        if sym["role"] != "pay":
            continue
        table = {k: v for e in (pays.get(sym["id"], {}).get("paytable") or []) for k, v in e.items()}
        paytable["rows"].append({
            "symbol": sym["id"],
            "name": texts.get(sym["nameKey"], sym["id"]),
            "pays": [table.get(str(lo)) for lo, _ in bands],
        })

    modes = []
    for m in gdef["modes"]:
        pub = fe["betModes"].get(m["name"], {})
        modes.append({
            "key": m["name"].upper(),
            "name": m["name"],
            "type": sdk_type(m),
            "cost": pub.get("cost", m["cost"]),
            "rtp": pub.get("rtp"),
            "maxWin": pub.get("max_win"),
            "title": texts.get(f"mode.{m['name']}.title", m["name"].upper()),
            "label": texts.get(f"mode.{m['name']}.label", m["name"]),
            "dialog": texts.get(f"mode.{m['name']}.dialog", ""),
        })

    return {
        "_generated": f"tools/gen/gen_rules.py from skins/{g.skin.name}/game.json, text/{lang}.json and config_fe_{g.id}.json. Do not edit.",
        "gameId": g.id,
        "lang": lang,
        "texts": texts,
        "paytable": paytable,
        "modes": modes,
        "missing": missing,
    }


def render(g: Game, lang: str = "en") -> str:
    return json.dumps(build(g, lang), indent="\t", ensure_ascii=False) + "\n"


def main():
    g = Game(game_arg())
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "en"
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else g.gen_web / f"rules.generated.{lang}.json"
    data = build(g, lang)
    for key, gaps in data["missing"].items():
        print(f"ERROR text '{key}': nothing fills {', '.join('{' + x + '}' for x in gaps)}")
    os.makedirs(out.parent, exist_ok=True)
    out.write_text(render(g, lang), encoding="utf-8", newline="\n")
    print(f"wrote {out}: {len(data['texts'])} texts, {len(data['paytable']['rows'])} pay rows, {len(data['modes'])} modes")
    sys.exit(1 if data["missing"] else 0)


if __name__ == "__main__":
    main()
