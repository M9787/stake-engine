r"""Pick one reviewer event ID per mode and outcome: loss, win, big win, bonus trigger, max win.

Usage (from stake\):
    math-sdk\env\Scripts\python.exe tools\release\pick_event_ids.py --game <id> [--version N] [--json]

Reads math-sdk\games\<id>\library\publish_files (index.json, books_<mode>.jsonl.zst, lookUpTable_<mode>_0.csv).
Writes build\<id>\reports\event_ids.json and prints a table (--json prints the JSON instead).

- An event ID is the book id (simulation id) in the published books (docs/10 C3: "event IDs come from the
  frozen books"); Engine replays it with GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event} (docs/03).
- Outcome classes come from scripts\books_to_stories.py categorize() (imported, not copied):
    loss = "loss"; win = "win" (else "win_below_cost"); big win = "big_win" (else "big_bonus");
    bonus trigger = "bonus_<variant>" or any book with a freeSpinTrigger event; max win = "max_win".
- Books with weight > 0 in the published lookup are preferred (weight 0 = never drawn on Stake).
- Buy modes have no "bonus trigger" pick: every buy round is a bonus.
- --version is the Studio math version number (Studio > Files after Publish Game > Math). Without it the
  replay links carry the placeholder "<version>".
Exit: 0 = written (missing picks are listed with a reason), 1 = no math.
"""

import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
if "--game" not in sys.argv:
    sys.exit(__doc__)
import books_to_stories as bts  # noqa: E402  (reads --game from sys.argv on import)
import zstandard as zstd  # noqa: E402

CATS = ["loss", "win", "big", "bonus", "max"]
LABEL = {"loss": "Loss", "win": "Normal win", "big": "Big win", "bonus": "Bonus trigger", "max": "Max win"}
HEAD = re.compile(r'^\{"id":\s*(\d+),\s*"payoutMultiplier":\s*(\d+)')


def replay_query(game: str, version: str | None, mode: str, event: int) -> str:
    """Engine replay query (same parameters as tools\\e2e\\tests\\replay.spec.ts; mode key upper case)."""
    return (f"?replay=true&game={game}&version={version or '<version>'}&mode={mode.upper()}"
            f"&event={event}&rgs_url=<rgs_url>")


def read_lookup(path: Path) -> dict:
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                i, w, p = line.strip().split(",")
                out[int(i)] = (int(w), int(p))
    return out


def classes(book: dict, cost: float, buy: bool) -> list:
    """Reviewer classes of one book, best match first: (class, rank). Lower rank = preferred."""
    cat = bts.categorize(book, cost)
    types = {ev["type"] for ev in book["events"]}
    out = []
    if cat == "loss":
        out.append(("loss", 0))
    elif cat == "win":
        out.append(("win", 0))
    elif cat == "win_below_cost":
        out.append(("win", 1))
    elif cat == "big_win":
        out.append(("big", 0))
    elif cat == "big_bonus":
        out.append(("big", 0 if buy else 1))
    elif cat == "max_win":
        out.append(("max", 0))
    if not buy and (cat.startswith("bonus_") or "freeSpinTrigger" in types):
        out.append(("bonus", 0))
    return [(c, r, cat) for c, r in out]


def pick_mode(mode: dict, buy: bool) -> dict:
    name, cost = mode["name"], float(mode["cost"])
    lut = read_lookup(Path(bts.PUB) / mode["weights"])
    live = [(w, p) for w, p in lut.values() if w > 0]
    na = {}
    if buy:
        na["bonus"] = "buy mode: every round is a bonus, so any event ID of this mode shows the bonus"
    if not any(p == 0 for _, p in live):
        na["loss"] = "no losing round in this mode (no 0x payout with weight > 0 in the lookup table)"
    if not any(p >= bts.MAX_PAYOUT for w, p in lut.values()):
        na["max"] = f"no book reaches the win cap ({bts.MAX_PAYOUT / 100:,.0f}x) in this mode"
    want = [c for c in CATS if c not in na]
    best = {}  # class -> (rank, weight0, record)
    scanned = 0
    with open(Path(bts.PUB) / mode["events"], "rb") as fh:
        reader = io.TextIOWrapper(zstd.ZstdDecompressor().stream_reader(fh), encoding="utf-8")
        for line in reader:
            if not line.strip():
                continue
            scanned += 1
            m = HEAD.match(line)
            if m:
                bid, pay = int(m.group(1)), int(m.group(2))
                # Cheap filter: parse only books that can still improve a missing or fallback pick.
                open_ = [c for c in want if c not in best or best[c][:2] != (0, 0)]
                if not open_:
                    break
                maybe = (
                    ("loss" in open_ and pay == 0)
                    or ("max" in open_ and pay >= bts.MAX_PAYOUT)
                    or ("bonus" in open_ and ("freeSpinTrigger" in line or "bonusVariant" in line))
                    or (("win" in open_ or "big" in open_) and 0 < pay < bts.MAX_PAYOUT)
                )
                if not maybe:
                    continue
            book = json.loads(line)
            bid = book["id"]
            weight = lut.get(bid, (0, 0))[0]
            for cls, rank, cat in classes(book, cost, buy):
                if cls not in want:
                    continue
                key = (rank, 0 if weight > 0 else 1)
                if cls not in best or key < best[cls][:2]:
                    best[cls] = (*key, {
                        "event": bid,
                        "payoutX": book["payoutMultiplier"] / 100,
                        "category": cat,
                        "weight": weight,
                    })
            if all(c in best and best[c][:2] == (0, 0) for c in want):
                break
    picks = {}
    for c in CATS:
        if c in na:
            picks[c] = {"na": na[c]}
        elif c in best:
            rec = dict(best[c][2])
            notes = []
            if best[c][0] > 0:
                notes.append(f"closest match ({rec['category']})")
            if best[c][1] > 0:
                notes.append("weight 0 in the published lookup: never drawn on Stake, but replayable")
            if notes:
                rec["note"] = "; ".join(notes)
            picks[c] = rec
        else:
            picks[c] = {"na": f"no {LABEL[c].lower()} book found in {mode['events']}"}
    return {"mode": name, "key": name.upper(), "cost": cost, "kind": "buy" if buy else "spin", "booksScanned": scanned, "picks": picks}


def main():
    game = bts.G.id
    version = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else None
    if version is not None and not re.fullmatch(r"\d{1,6}", version):
        sys.exit("--version must be the Studio math version number, e.g. --version 3")
    index_path = Path(bts.PUB) / "index.json"
    if not index_path.exists():
        print(f"FAIL: no math for {game}: {index_path.relative_to(ROOT)} missing (build the math first)")
        sys.exit(1)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    kinds = {m["name"]: m["kind"] for m in bts.G.gdef["modes"]}
    modes = []
    for m in index["modes"]:
        r = pick_mode(m, kinds.get(m["name"]) == "buy")
        for c, p in r["picks"].items():
            if "event" in p:
                p["replay"] = replay_query(game, version, m["name"], p["event"])
        modes.append(r)
        if "--json" not in sys.argv:
            print(f"  scanned {r['mode']}: {r['booksScanned']:,} books", file=sys.stderr)
    out = {
        "_generated": "tools/release/pick_event_ids.py from math-sdk/games/<id>/library/publish_files. Do not edit.",
        "game": game,
        "version": version,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "categories": {c: LABEL[c] for c in CATS},
        "replayNote": "Append the query to the game's front-end URL; <rgs_url> is the RGS host Stake gives the reviewer. "
                      + ("" if version else "Rerun with --version <Studio math version> to fill <version>."),
        "modes": modes,
    }
    rep = ROOT / "build" / game / "reports"
    rep.mkdir(parents=True, exist_ok=True)
    (rep / "event_ids.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    if "--json" in sys.argv:
        print(json.dumps(out, indent=2))
        return
    w = 14
    print(f"Reviewer event IDs for {game} (math version {version or '<version>'})")
    print(f"{'mode':<10}" + "".join(f"{LABEL[c]:<{w}}" for c in CATS))
    for r in modes:
        cells = []
        for c in CATS:
            p = r["picks"][c]
            cells.append("n/a" if "na" in p else f"{p['event']} ({p['payoutX']:g}x)" + ("*" if "note" in p else ""))
        print(f"{r['mode']:<10}" + "".join(f"{x:<{w}}" for x in cells))
    for r in modes:
        for c in CATS:
            p = r["picks"][c]
            if "na" in p:
                print(f"  {r['mode']} {LABEL[c].lower()}: n/a - {p['na']}")
            elif "note" in p:
                print(f"  {r['mode']} {LABEL[c].lower()}: * {p['note']}")
    print(f"wrote build/{game}/reports/event_ids.json")


if __name__ == "__main__":
    main()
