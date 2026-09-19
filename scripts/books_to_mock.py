"""Build demo-play data for the local mock RGS (web dev server only, never shipped).

For each mode in publish_files/index.json, draw book IDs from the lookup table by weight
(with replacement). Picking uniformly from that list then follows the real math.
Also stores one max-win book and one bonus book per mode for forced demo rounds.

Output: web-sdk/apps/seventh-veil/.mock-rgs/<mode>.json (git-ignored, skipped by sync.ps1).
Usage (from stake\\): math-sdk\\env\\Scripts\\python.exe scripts\\books_to_mock.py [--spin N] [--buy N]
"""

import json
import os
import random
import sys

import zstandard as zstd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = "seventh_veil"
PUB = os.path.join(ROOT, "math-sdk", "games", GAME, "library", "publish_files")
OUT = os.path.join(ROOT, "web-sdk", "apps", "seventh-veil", ".mock-rgs")


def arg(name, default):
    if name in sys.argv:
        return int(sys.argv[sys.argv.index(name) + 1])
    return default


def main():
    spin_n, buy_n = arg("--spin", 3000), arg("--buy", 300)
    rng = random.Random(7)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(PUB, "index.json"), encoding="utf-8") as f:
        index = json.load(f)
    for mode in index["modes"]:
        name, cost = mode["name"], mode["cost"]
        rows = []
        with open(os.path.join(PUB, mode["weights"]), encoding="utf-8") as f:
            for line in f:
                i, w, p = line.strip().split(",")
                if int(w) > 0:
                    rows.append((int(i), int(w), int(p)))
        n = spin_n if cost < 10 else buy_n
        ids = rng.choices([r[0] for r in rows], weights=[r[1] for r in rows], k=n)
        max_id = max(rows, key=lambda r: r[2])[0]
        want = set(ids) | {max_id}
        books, bonus_id = {}, None
        with open(os.path.join(PUB, mode["events"]), "rb") as fh:
            reader = zstd.ZstdDecompressor().stream_reader(fh)
            buf = b""
            while True:
                chunk = reader.read(1 << 20)
                if not chunk:
                    break
                buf += chunk
                *lines, buf = buf.split(b"\n")
                for line in lines:
                    if not line.strip():
                        continue
                    book = json.loads(line)
                    is_bonus = any(e["type"] == "freeSpinTrigger" for e in book["events"])
                    if book["id"] in want or (bonus_id is None and is_bonus and book["payoutMultiplier"] > 0):
                        books[book["id"]] = {"payoutMultiplier": book["payoutMultiplier"], "events": book["events"]}
                        if bonus_id is None and is_bonus and book["payoutMultiplier"] > 0:
                            bonus_id = book["id"]
        data = {
            "mode": name,
            "cost": cost,
            "ids": ids,
            "forced": {"maxwin": max_id, "bonus": bonus_id},
            "books": books,
        }
        path = os.path.join(OUT, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
        print(f"{name}: {len(ids)} draws, {len(books)} books, {os.path.getsize(path) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
