r"""Bundle budget gate for one game's web build (docs/10 plan v3.3 M11; PROJECT.md Q20).

Usage:  math-sdk\env\Scripts\python.exe tools\gates\bundle_budget.py --game <gameId> [--json] [--strict]
Reads build\<id>\dist (tools\web_build.ps1). Budgets (MB): total 10, textures 5, audio 2.5, JS 1.5,
plus each filled image slot's budgetKB from core\assets\slots.v1.json. Over budget is our own rule
(core\policy.v1.json bundle.size, level ours): printed as WARN lines, exit 0. --strict: exit 1 when over.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "assets"))
from catalog import Catalog  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gamedef"))
from gamectx import game_arg  # noqa: E402

BUDGET_MB = {"total": 10.0, "textures": 5.0, "audio": 2.5, "js": 1.5}
KIND = {".png": "textures", ".webp": "textures", ".jpg": "textures", ".jpeg": "textures", ".atlas": "textures",
        ".ogg": "audio", ".m4a": "audio", ".mp3": "audio", ".js": "js"}


def main():
    cat = Catalog(game_arg())
    dist = cat.game.gen_web.parent / "dist"
    if not (dist / "index.html").exists():
        sys.exit(f"FAIL: no build at {dist}; run tools\\web_build.ps1 -Game {cat.game.id}")
    sizes = {"total": 0, "textures": 0, "audio": 0, "js": 0}
    for f in dist.rglob("*"):
        if f.is_file():
            n = f.stat().st_size
            sizes["total"] += n
            if KIND.get(f.suffix.lower()):
                sizes[KIND[f.suffix.lower()]] += n
    problems = []
    for k, mb in BUDGET_MB.items():
        if sizes[k] / 2**20 > mb:
            problems.append(f"{k} {sizes[k] / 2**20:.2f} MB > {mb} MB")
    for s in cat.slots:
        f = dist / "slots" / f"{s['id']}.webp"
        if s.get("budgetKB") and f.exists() and f.stat().st_size / 1024 > s["budgetKB"]:
            problems.append(f"slot {s['id']} {f.stat().st_size / 1024:.0f} KB > {s['budgetKB']} KB")
    strict = "--strict" in sys.argv
    report = {k: round(v / 2**20, 2) for k, v in sizes.items()} | {"problems": problems, "rule": "bundle.size", "level": "ours", "strict": strict}
    if "--json" in sys.argv:
        print(json.dumps(report))
    else:
        print("  " + ", ".join(f"{k} {v} MB" for k, v in report.items() if k in sizes))
        for p in problems:
            print(f"{'FAIL' if strict else 'WARN'}  [bundle.size] over: {p} - why: Stake's top-rating criteria: optimised bundle size")
        status = "OK" if not problems else ("FAIL" if strict else "OK (warnings)")
        print(f"{status}: bundle budget for {cat.game.id}" + (f" ({len(problems)} over budget)" if problems else ""))
    sys.exit(1 if problems and strict else 0)


if __name__ == "__main__":
    main()
