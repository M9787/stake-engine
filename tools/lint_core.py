r"""Fail when the core holds skin literals (docs/10 section 2 "Enforcement").

Usage:  math-sdk\env\Scripts\python.exe tools\lint_core.py [--scope math|web|all]
        math = core\math, core\schema, core\assets (gate until M10 slice 10.5); web = core\web; all = everything (default)
Exit:   0 = clean, 1 = skin literals found.

Skin words come from every skins/*/game.json (game id, display name, mode names, bonus variant ids,
symbol names in text/en.json) plus the Oracle theme words. Matching is whole-word and
case-insensitive, in code and comments alike: a core comment naming a skin is a leak too.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
SCAN_SUFFIXES = {".py", ".ts", ".js", ".svelte", ".json", ".md"}
ALWAYS = {"seventh", "oracle", "veil"}
# Generic words that a mode or text may also use; never flagged.
ALLOW = {"base", "bonus", "spin", "free", "wild", "scatter", "high", "the"}


def skin_words():
    words = set(ALWAYS)
    for gpath in (ROOT / "skins").glob("*/game.json"):
        g = json.loads(gpath.read_text(encoding="utf-8"))
        words.add(g["identity"]["gameId"])
        words.update(w for w in re.findall(r"[A-Za-z]{4,}", g["identity"]["displayName"]))
        words.update(m["name"] for m in g["modes"])
        words.update(v["id"] for v in g["features"]["bonusVariants"])
        text = gpath.parent / "text" / "en.json"
        if text.exists():
            t = json.loads(text.read_text(encoding="utf-8"))
            for key, val in t.items():
                if key.startswith("symbol.") and isinstance(val, str):
                    words.update(w for w in re.findall(r"[A-Za-z]{4,}", val))
    return sorted(w.lower() for w in words if w.lower() not in ALLOW)


# Generated or sample files that still sit inside the core app, with the slice that removes them.
TEMP_EXCLUDE = {
    "web/cluster-tumble/src/stories": "M10 slice 10.7 moves generated stories to src/stories/generated (ignored)",
}
ALLOW_MARK = "lint-core: allow"

SCOPES = {
    "math": ["math", "schema", "assets"],
    "web": ["web"],
}


def scan_roots(argv):
    scope = argv[argv.index("--scope") + 1] if "--scope" in argv else "all"
    if scope == "all":
        return scope, [CORE]
    if scope not in SCOPES:
        sys.exit(f"unknown --scope {scope}; use math, web or all")
    return scope, [CORE / d for d in SCOPES[scope] if (CORE / d).exists()]


def main():
    scope, roots = scan_roots(sys.argv)
    words = skin_words()
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.I)
    hits = []
    for path in sorted(p for r in roots for p in r.rglob("*")):
        if path.suffix not in SCAN_SUFFIXES or "__pycache__" in path.parts or "node_modules" in path.parts:
            continue
        rel = path.relative_to(CORE).as_posix()
        if any(rel.startswith(prefix + "/") for prefix in TEMP_EXCLUDE):
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ALLOW_MARK in line:
                continue
            for m in pattern.finditer(line):
                hits.append(f"{path.relative_to(ROOT)}:{n}: '{m.group(0)}'  {line.strip()[:90]}")
    for h in hits:
        print(h)
    print(f"{'FAIL' if hits else 'OK'}: {len(hits)} skin literal(s) in core/ (scope {scope}, {len(words)} skin words checked)")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
