"""Build demo-play data for the local mock RGS (web dev server only, never shipped).

For each mode in publish_files/index.json, draw book IDs from the lookup table by weight
(with replacement). Picking uniformly from that list then follows the real math.
Also stores forced books per mode for demo rounds and the e2e replay suite: maxwin, bonus,
and, from the drawn books, loss / win / big (categories of books_to_stories.categorize).

Output: web-sdk/apps/<app>/.mock-rgs/<mode>.json (git-ignored, skipped by sync.ps1).
Usage (from stake\\): math-sdk\\env\\Scripts\\python.exe scripts\\books_to_mock.py [--game <gameId>] [--spin N] [--buy N]
"""

import json
import os
import random
import sys

import zstandard as zstd

from books_to_stories import G, categorize  # G: the game from --game (default seventh_veil)

PUB = str(G.publish)
OUT = str(G.sdk_app / ".mock-rgs" / G.id)  # one folder per game: the core app is shared


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
        # Buy modes rarely draw a big win (>= 15x cost); then take the smallest one in the table.
        pay = {r[0]: r[2] for r in rows}
        big_pay = 15 * cost * 100
        extra = []
        if not any(big_pay <= pay[i] < pay[max_id] for i in ids):
            big = [r for r in rows if big_pay <= r[2] < pay[max_id]]
            if big:
                extra.append(min(big, key=lambda r: r[2])[0])
        want = set(ids) | {max_id} | set(extra)
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
        forced = {"maxwin": max_id, "bonus": bonus_id}
        # First drawn book per category (deterministic: rng seed 7). A mode without such a book
        # (buy modes never lose) gets no key; the mock then draws at random.
        want_cat = {"loss": ["loss"], "win": ["win", "win_below_cost"], "big": ["big_win", "big_bonus"]}
        for key, cats in want_cat.items():
            for cat in cats:
                hit = next((i for i in ids + extra if categorize(books[i], cost) == cat), None)
                if hit is not None:
                    forced[key] = hit
                    break
        data = {
            "mode": name,
            "cost": cost,
            "ids": ids,
            "forced": forced,
            "books": books,
        }
        path = os.path.join(OUT, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
        print(f"{name}: {len(ids)} draws, {len(books)} books, forced {forced}, {os.path.getsize(path) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
