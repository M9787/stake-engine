"""Hash every math artifact of a game so two runs (or two code versions) can be compared.

Usage (from stake\\):
  math-sdk\\env\\Scripts\\python.exe tools\\golden\\snapshot.py seventh_veil --write build\\seventh_veil\\det1.json
  math-sdk\\env\\Scripts\\python.exe tools\\golden\\snapshot.py seventh_veil --verify build\\seventh_veil\\det1.json

Books are hashed after zstd decompression, so the compression level does not matter.
Force records are hashed raw and also "normalized" (lists sorted), because force-key
lists come from Python sets (math-sdk write_data.py:69-75) whose order depends on
PYTHONHASHSEED. Run pins (threads, batching, Python, zstandard, PYTHONHASHSEED) come
from library\\run_meta.json, written by run.py, and must match on --verify.

Exit codes: 0 = written or identical, 1 = differences, 2 = usage or missing files.
"""

import argparse
import hashlib
import json
import os
import sys

import zstandard

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHUNK = 1 << 20

# Not compared: configs\event_config_<mode>.json is a sample-event dump written by every
# sim thread (math-sdk state.py:289 -> write_data.py:107), so the last thread to finish wins.
# It is not a published file (not in publish_files or index.json).
RACE_FILES_PREFIX = "configs/event_config_"

# Pins that change book bytes or order. A mismatch makes --verify fail even if hashes agree.
PIN_KEYS = ("python", "zstandard", "num_threads", "batching_size", "num_sim_args", "PYTHONHASHSEED")


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def sha_zst(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        reader = zstandard.ZstdDecompressor().stream_reader(f)
        for block in iter(lambda: reader.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def normalize(obj):
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        items = [normalize(v) for v in obj]
        return sorted(items, key=lambda v: json.dumps(v, sort_keys=True))
    return obj


def sha_json_normalized(path: str) -> str:
    with open(path, encoding="UTF-8") as f:
        data = json.load(f)
    return hashlib.sha256(json.dumps(normalize(data), sort_keys=True).encode()).hexdigest()


def snapshot(game: str) -> dict:
    lib = os.path.join(ROOT, "math-sdk", "games", game, "library")
    if not os.path.isdir(lib):
        print(f"missing library folder: {lib}")
        sys.exit(2)

    files = {}
    for sub, names in sorted((d, sorted(os.listdir(os.path.join(lib, d)))) for d in ("publish_files", "lookup_tables", "forces", "configs") if os.path.isdir(os.path.join(lib, d))):
        for name in names:
            path = os.path.join(lib, sub, name)
            if not os.path.isfile(path):
                continue
            key = f"{sub}/{name}"
            if name.endswith(".zst"):
                files[key] = {"decompressed": sha_zst(path)}
            elif sub == "forces" and name.endswith(".json"):
                files[key] = {"raw": sha_file(path), "normalized": sha_json_normalized(path)}
            else:
                files[key] = {"raw": sha_file(path)}

    meta_path = os.path.join(lib, "run_meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="UTF-8") as f:
            meta = json.load(f)
    else:
        print("warning: library\\run_meta.json missing (run.py older than M6a); pins not recorded")

    return {"game": game, "pins": {k: meta.get(k) for k in PIN_KEYS}, "hash_randomization": meta.get("hash_randomization"), "files": files}


def compare(old: dict, new: dict) -> list[str]:
    diffs = []
    for k in PIN_KEYS:
        if old["pins"].get(k) != new["pins"].get(k):
            diffs.append(f"pin {k}: {old['pins'].get(k)!r} -> {new['pins'].get(k)!r}")
    for key in sorted(set(old["files"]) | set(new["files"])):
        if key.startswith(RACE_FILES_PREFIX):
            continue
        a, b = old["files"].get(key), new["files"].get(key)
        if a is None or b is None:
            diffs.append(f"{key}: {'added' if a is None else 'removed'}")
        elif a != b:
            if "normalized" in a and a.get("normalized") == b.get("normalized"):
                diffs.append(f"{key}: raw differs, normalized equal (set order; check PYTHONHASHSEED)")
            else:
                diffs.append(f"{key}: content differs")
    return diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("game")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", metavar="FILE")
    g.add_argument("--verify", metavar="FILE")
    args = ap.parse_args()

    snap = snapshot(args.game)
    if snap["hash_randomization"] not in (0, None):
        print(f"FAIL: run.py ran with hash randomization on (PYTHONHASHSEED={snap['pins']['PYTHONHASHSEED']!r}); set PYTHONHASHSEED=0")
        sys.exit(1)

    if args.write:
        os.makedirs(os.path.dirname(os.path.abspath(args.write)), exist_ok=True)
        with open(args.write, "w", encoding="UTF-8") as f:
            json.dump(snap, f, indent=1)
        print(f"wrote {len(snap['files'])} hashes to {args.write}")
        return

    with open(args.verify, encoding="UTF-8") as f:
        old = json.load(f)
    diffs = compare(old, snap)
    if diffs:
        print(f"DIFFERENT: {len(diffs)} item(s)")
        for d in diffs:
            print("  " + d)
        sys.exit(1)
    print(f"IDENTICAL: {len(snap['files'])} files, pins {snap['pins']}")


if __name__ == "__main__":
    main()
