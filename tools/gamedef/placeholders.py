"""Placeholder values for skin texts (text/<lang>.json), computed from game.json.

Texts never type numbers that the math defines: "{mode.omen.cost}x" instead of "1.25x", so a
changed game.json can never leave a stale number in the rules (docs/10 section 2). Values that
need the published math (rtpText: RTP and max win per mode) are filled by tools/gen (M9);
here they resolve from game.json targets.

Grammar: {mode.<name>.<field>} {variant.<id>.<field>} {paytable.minPay} {paytable.minCluster}
         {grid.cap} {grid.steps} {board.size} {retrigger.<field>}
"""

import re

PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_.]+)\}")


def _fmt(value):
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}" if isinstance(value, int) and value >= 10000 else str(value)


def values(gdef: dict) -> dict:
    out = {}
    math = gdef["math"]
    base_triggers = {int(k): v for k, v in gdef["freespinTriggers"]["basegame"].items()}
    fg_triggers = {int(k): v for k, v in gdef["freespinTriggers"]["freegame"].items()}

    for m in gdef["modes"]:
        p = f"mode.{m['name']}"
        out[f"{p}.cost"] = _fmt(m["cost"])
        target = math["targets"].get(m["name"], {})
        if "bonusOneIn" in target:
            out[f"{p}.bonusOneIn"] = _fmt(target["bonusOneIn"])
        out[f"{p}.rtpText"] = f"RTP {math['rtp'] * 100:.2f}%. Max win {_fmt(math['wincap'])}x."

    for v in gdef["features"]["bonusVariants"]:
        p = f"variant.{v['id']}"
        spins = [s for c, s in base_triggers.items() if v["scatterMin"] <= c <= v["scatterMax"]]
        if spins:
            out[f"{p}.spinsMin"] = _fmt(min(spins))
            out[f"{p}.spinsMax"] = _fmt(max(spins))
        out[f"{p}.prechargeSpots"] = _fmt(v["precharge"]["spots"])
        out[f"{p}.prechargeValue"] = _fmt(v["precharge"]["value"])
        out[f"{p}.scatterMin"] = _fmt(v["scatterMin"])
        out[f"{p}.scatterMax"] = _fmt(v["scatterMax"])

    out["paytable.minPay"] = _fmt(gdef["paytable"]["minPay"])
    cap = gdef["features"]["gridMultiplier"]["cap"]
    out["grid.cap"] = _fmt(cap)
    # Doubling steps after the first charge (x2), below the cap: "x4, x8, ..., x512".
    steps, v = [], 4
    while v < cap:
        steps.append(f"x{v}")
        v *= 2
    out["grid.steps"] = ", ".join(steps)
    out["board.size"] = f"{gdef['board']['reels']}x{gdef['board']['rows']}"
    out["paytable.minCluster"] = _fmt(gdef["paytable"]["bands"][0][0])
    if fg_triggers:
        first = min(fg_triggers)
        out["retrigger.min"] = _fmt(first)
        out["retrigger.spins"] = _fmt(fg_triggers[first])
    return out


def fill(text: str, vals: dict) -> str:
    return PLACEHOLDER.sub(lambda m: vals.get(m.group(1), m.group(0)), text)


def unresolved(text: str, vals: dict) -> list:
    return [name for name in PLACEHOLDER.findall(text) if name not in vals]
