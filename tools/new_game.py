r"""Create a new game from a template skin (docs/10 plan v3.3, M12 "New game from template").

Usage:  math-sdk\env\Scripts\python.exe tools\new_game.py --from <template skin folder> --id <gameId> --name "<Display Name>" [--json]
Copies game.json, text\, math\reels\ and the assets.json style bible (slot fills are not copied: the new
game starts on fallbacks), sets a new identity (version 0.1.0, testOnly off, art sign-off cleared),
drops any frozen weights and initial board, then runs validate.py. Never overwrites an existing skin.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME_ID = re.compile(r"^[a-z][a-z0-9_]{2,31}$")


def fail(msg, as_json):
    if as_json:
        print(json.dumps({"ok": False, "error": msg}))
    else:
        print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    a = sys.argv
    as_json = "--json" in a
    try:
        template = a[a.index("--from") + 1]
        gid = a[a.index("--id") + 1]
        name = a[a.index("--name") + 1]
    except (ValueError, IndexError):
        sys.exit(__doc__)
    src = ROOT / "skins" / template
    if not (src / "game.json").exists():
        fail(f"template '{template}' is not a skin folder", as_json)
    if not GAME_ID.match(gid):
        fail("game id: 3-32 characters, lower case letters, digits and _, starting with a letter", as_json)
    if not (2 <= len(name.strip()) <= 40):
        fail("display name: 2-40 characters", as_json)
    folder = gid.replace("_", "-")
    dst = ROOT / "skins" / folder
    taken = {json.loads(p.read_text(encoding="utf-8"))["identity"]["gameId"] for p in (ROOT / "skins").glob("*/game.json")}
    if dst.exists() or gid in taken:
        fail(f"a game '{gid}' (or folder skins\\{folder}) already exists", as_json)

    g = json.loads((src / "game.json").read_text(encoding="utf-8"))
    g["identity"].update({"gameId": gid, "displayName": name.strip(), "workingName": name.strip(), "version": "0.1.0"})
    g["identity"].pop("testOnly", None)
    g.get("presentation", {}).pop("initialBoard", None)
    g["review"] = {"signatureMoment": "Describe the one moment players will remember (min 10 characters).",
                   "originality": ["mechanic difference 1", "mechanic difference 2"], "artSignoff": None}
    (dst / "math" / "reels").mkdir(parents=True)
    shutil.copytree(src / "math" / "reels", dst / "math" / "reels", dirs_exist_ok=True)
    shutil.copytree(src / "text", dst / "text")
    texts = json.loads((dst / "text" / "en.json").read_text(encoding="utf-8"))
    texts["game.name"] = name.strip().upper()
    (dst / "text" / "en.json").write_text(json.dumps(texts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (dst / "game.json").write_text(json.dumps(g, indent=2) + "\n", encoding="utf-8", newline="\n")
    if (src / "assets.json").exists():
        assets = json.loads((src / "assets.json").read_text(encoding="utf-8"))
        assets["slots"] = {}  # prompts are per game; the style bible is the starting point
        (dst / "assets.json").write_text(json.dumps(assets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    v = subprocess.run([sys.executable, str(ROOT / "tools" / "gamedef" / "validate.py"), str(dst / "game.json"), "--json"],
                       capture_output=True, text=True)
    result = json.loads(v.stdout) if v.stdout.strip().startswith("{") else {"ok": False, "errors": [{"path": "", "message": v.stderr}]}
    if as_json:
        print(json.dumps({"ok": True, "id": gid, "skin": folder, "validation": result}))
    else:
        print(f"OK: created skins\\{folder} (game {gid}); validation: {len(result.get('errors', []))} error(s)")


if __name__ == "__main__":
    main()
