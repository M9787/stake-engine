r"""Fail when a skin holds anything but data (docs/10 section 2 "Enforcement", plan v3.3 M11).

Usage:  math-sdk\env\Scripts\python.exe tools\lint_skin.py [--game <gameId>]   (default: every skin)
Checks: file types on an allowlist (no code: .py .ts .js .svelte .css .html ...), game.json validates
(tools\gamedef\validate.py), asset prompts lint clean (tools\assets\catalog.py), and assets.lock.json
points only at files inside the skin.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "assets"))
from catalog import Catalog, lint  # noqa: E402

ALLOWED = {".json", ".csv", ".png", ".webp", ".jpg", ".jpeg", ".ogg", ".wav", ".mp3", ".m4a", ".flac", ".aiff",
           ".ttf", ".otf", ".txt", ".md"}
IGNORED_DIRS = {"art_in", ".history"}  # owner drop folder (git-ignored) and editor snapshots


def skins(game_filter):
    for gpath in sorted((ROOT / "skins").glob("*/game.json")):
        gid = json.loads(gpath.read_text(encoding="utf-8"))["identity"]["gameId"]
        if not game_filter or gid == game_filter:
            yield gid, gpath.parent


def main():
    game = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else None
    problems = []
    for gid, folder in skins(game):
        for f in sorted(folder.rglob("*")):
            rel = f.relative_to(ROOT)
            if f.is_file() and not (set(f.relative_to(folder).parts) & IGNORED_DIRS):
                if f.suffix.lower() not in ALLOWED:
                    problems.append(f"{rel}: file type {f.suffix or '(none)'} is not data; skins hold no code")
        v = subprocess.run([sys.executable, str(ROOT / "tools" / "gamedef" / "validate.py"), str(folder / "game.json")],
                           capture_output=True, text=True)
        if v.returncode != 0:
            problems.append(f"{folder.relative_to(ROOT)}\\game.json: validate.py failed: {v.stdout.strip().splitlines()[-1] if v.stdout.strip() else v.stderr.strip()}")
        cat = Catalog(gid)
        for sid, msg in lint(cat):
            problems.append(f"{folder.relative_to(ROOT)}\\assets.json {sid}: {msg}")
        lock = folder / "assets.lock.json"
        if lock.exists():
            for sid, rec in json.loads(lock.read_text(encoding="utf-8")).get("slots", {}).items():
                target = (folder / rec["file"]).resolve()
                if folder.resolve() not in target.parents or not target.exists():
                    problems.append(f"{lock.relative_to(ROOT)} {sid}: file {rec['file']} missing or outside the skin")
        print(f"checked {gid} ({folder.relative_to(ROOT)})")
    for p in problems:
        print(f"  {p}")
    print(("FAIL" if problems else "OK") + f": {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
