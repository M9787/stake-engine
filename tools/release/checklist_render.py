r"""Submission-pack section "Stake approval checklist (preview)" from build\<id>\reports\stake_checklist.json.

Used by tools\release\pack.py (one call): `title, blocks, summary = checklist_render.section(g)`.
Runs tools\release\checklist.py first when the report is missing or older than its inputs.
Blocks use pack.py's block format: ('p', text) | ('table', head, rows).
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TITLE = "Stake approval checklist (preview)"
ICON = {"pass": "✔ pass", "fail": "✘ FAIL", "manual": "☐ look", "unknown": "? unknown"}
GROUPS = ["math", "frontend", "replay", "social", "rules", "ui", "quality", "ip", "tiles", "general"]


def report_path(game_id: str) -> Path:
    return ROOT / "build" / game_id / "reports" / "stake_checklist.json"


def inputs(g) -> list:
    rep = ROOT / "build" / g.id / "reports"
    return [ROOT / "core" / "stake_checklist.v1.json", g.skin / "game.json", g.gen_web / "rules.generated.en.json",
            ROOT / "build" / g.id / "dist" / "index.html", g.publish / "index.json",
            rep / "math_stats.json", rep / "gate.json", rep / "e2e.json"]


def load(g) -> dict | None:
    """The current checklist; reruns checklist.py when missing or stale."""
    out = report_path(g.id)
    newest = max((p.stat().st_mtime for p in inputs(g) if p.exists()), default=0)
    if not out.exists() or out.stat().st_mtime < newest:
        print("running tools\\release\\checklist.py (stake_checklist.json missing or stale)")
        subprocess.run([sys.executable, str(ROOT / "tools" / "release" / "checklist.py"), "--game", g.id],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return json.loads(out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def section(g):
    """(title, blocks, summary) for pack.py; summary goes into pack.json `checklist`."""
    doc = load(g)
    if not doc:
        return TITLE, [("p", "No checklist: tools\\release\\checklist.py did not write build\\<id>\\reports\\stake_checklist.json.")], None
    s = doc["summary"]
    blocks = [("p", f"Generated {doc['generated']} ({doc['mode']} mode) by tools\\release\\checklist.py from core\\stake_checklist.v1.json. "
                    f"{s['pass']} pass, {s['fail']} fail, {s['manual']} to look at by hand, {s['unknown']} without evidence yet. "
                    "A preview of Stake's review: numbered rows are guideline ids of the Stake AI-review prompt; three reviewers "
                    "then rate 0-3 stars each and the game needs 6 of 9 points.")]
    groups = GROUPS + sorted({i["group"] for i in doc["items"]} - set(GROUPS))
    for grp in groups:
        rows = [i for i in doc["items"] if i["group"] == grp]
        if not rows:
            continue
        counts = ", ".join(f"{sum(1 for r in rows if r['status'] == k)} {k}" for k in ("pass", "fail", "manual", "unknown") if any(r["status"] == k for r in rows))
        blocks.append(("p", f"{grp.capitalize()} ({counts})"))
        blocks.append(("table", ["Status", "ID", "Check", "Evidence / what to look at"],
                       [[ICON.get(r["status"], r["status"]), r["id"], r["text"], r["evidence"]] for r in rows]))
    summary = {"generated": doc["generated"], "mode": doc["mode"], **s,
               "failed": [f"{i['id']}: {i['evidence'][:160]}" for i in doc["items"] if i["status"] == "fail"]}
    return TITLE, blocks, summary
