r"""Freeze (or unfreeze) the math weights of a game.

Usage:  math-sdk\env\Scripts\python.exe tools\math\freeze.py --game <gameId> [--unfreeze]

Freeze: copies math-sdk\games\<id>\library\publish_files\lookUpTable_<mode>_0.csv for every mode in
game.json into skins\<skin>\math\lookups\ and writes skins\<skin>\math\frozen.json
{date, runMeta, files: {name: sha256}}. Later math runs from the editor reuse these weights
(CT_REUSE_WEIGHTS) and only re-simulate the books. Refuses a preview-tier run or fewer than
100,000 rows per table: those weights are an estimate, not a result.
Unfreeze: moves skins\<skin>\math\lookups to skins\<skin>\.history\<timestamp>\lookups (with frozen.json).
seventh_veil (Oracle) is frozen by hand and refused either way.
"""

import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_ROWS = 100_000
HAND_FROZEN = {"seventh_veil"}


def fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def skin_of(game_id: str):
    for gj in sorted((ROOT / "skins").glob("*/game.json")):
        gdef = json.loads(gj.read_text(encoding="utf-8"))
        if gdef.get("identity", {}).get("gameId") == game_id:
            return gj.parent, gdef
    fail(f"no skin folder has game id '{game_id}' (skins\\*\\game.json)")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_rows(p: Path) -> int:
    with p.open("rb") as f:
        return sum(1 for line in f if line.strip())


def freeze(game_id: str, skin: Path, gdef: dict):
    lookups = skin / "math" / "lookups"
    if lookups.exists():
        fail(f"{game_id} is already frozen ({lookups.relative_to(ROOT)} exists). Unfreeze first to replace the weights.")
    lib = ROOT / "math-sdk" / "games" / game_id / "library"
    meta_file = lib / "run_meta.json"
    if not meta_file.exists():
        fail(f"no math result yet for {game_id}: run the final math (100,000 sims) first.")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    if meta.get("tier") == "preview":
        fail("the last math run was a quick estimate (preview, 10,000 sims). Run the final math (100,000 sims) first, then freeze.")
    modes = [m["name"] for m in gdef["modes"]]
    srcs = {}
    for mode in modes:
        src = lib / "publish_files" / f"lookUpTable_{mode}_0.csv"
        if not src.exists():
            fail(f"weights for mode '{mode}' are missing ({src.relative_to(ROOT)}). Run the final math first.")
        rows = count_rows(src)
        if rows < MIN_ROWS:
            fail(f"mode '{mode}' has only {rows:,} results; freezing needs at least {MIN_ROWS:,}. Run the final math (100,000 sims) first.")
        srcs[mode] = src
    tmp = skin / "math" / "lookups.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    files = {}
    for mode, src in srcs.items():
        dst = tmp / src.name
        shutil.copyfile(src, dst)
        files[src.name] = sha256(dst)
    tmp.rename(lookups)
    frozen = {
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "game": game_id,
        "runMeta": meta,
        "files": files,
    }
    (skin / "math" / "frozen.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    print(f"ok    froze {len(files)} weight tables -> {lookups.relative_to(ROOT)} (frozen.json written)")


def unfreeze(game_id: str, skin: Path):
    lookups = skin / "math" / "lookups"
    if not lookups.exists():
        fail(f"{game_id} is not frozen (no {lookups.relative_to(ROOT)}). Nothing to do.")
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = skin / ".history" / ts
    dest.mkdir(parents=True, exist_ok=False)
    shutil.move(str(lookups), str(dest / "lookups"))
    fj = skin / "math" / "frozen.json"
    if fj.exists():
        shutil.move(str(fj), str(dest / "frozen.json"))
    print(f"ok    unfroze {game_id}: weights moved to {dest.relative_to(ROOT)}. The next final math run makes new weights.")


def main():
    a = sys.argv
    try:
        game_id = a[a.index("--game") + 1]
    except (ValueError, IndexError):
        sys.exit(__doc__)
    if game_id in HAND_FROZEN:
        fail(f"{game_id} was frozen by hand and its math is approved; it cannot be frozen or unfrozen here.")
    skin, gdef = skin_of(game_id)
    if "--unfreeze" in a:
        unfreeze(game_id, skin)
    else:
        freeze(game_id, skin, gdef)


if __name__ == "__main__":
    main()
