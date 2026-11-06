r"""Licence audit of the web app's production dependencies (docs/10 section 8, plan v3.3 M11).

Usage:  math-sdk\env\Scripts\python.exe tools\gates\licence_audit.py [--json]
Runs `pnpm licenses list --prod --json --filter cluster-tumble` in web-sdk and fails on copyleft
licences (GPL, AGPL, LGPL) or packages with no licence. Fonts and art are covered by the skin precheck.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLOCKED = re.compile(r"\b(A?GPL|LGPL)", re.I)


def main():
    proc = subprocess.run("pnpm licenses list --prod --json --filter cluster-tumble", cwd=ROOT / "web-sdk",
                          capture_output=True, text=True, shell=True, encoding="utf-8")
    if proc.returncode != 0:
        sys.exit(f"FAIL: pnpm licenses failed: {proc.stderr.strip()[-300:]}")
    data = json.loads(proc.stdout)
    problems, count = [], 0
    for licence, pkgs in data.items():
        for p in pkgs:
            count += 1
            name = f"{p.get('name')}@{','.join(p.get('versions', []) or [p.get('version', '?')])}"
            if BLOCKED.search(licence):
                problems.append(f"{name}: {licence} (copyleft)")
            elif licence.lower() in ("unknown", "unlicensed", ""):
                problems.append(f"{name}: no licence")
    if "--json" in sys.argv:
        print(json.dumps({"packages": count, "licences": sorted(data), "problems": problems}))
    else:
        for p in problems:
            print(f"  {p}")
        print(("FAIL" if problems else "OK") + f": {count} production packages, licences {', '.join(sorted(data))}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
