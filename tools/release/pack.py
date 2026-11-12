r"""Submission pack: every document the owner needs for the Stake Studio submission form, in one folder.

Usage (from stake\):
    math-sdk\env\Scripts\python.exe tools\release\pack.py --game <id> [--dry-run]

Writes build\<id>\pack\ :
    submission.html   self-contained, printable, for a non-developer (screenshots embedded)
    submission.md     the same content as Markdown (screenshots as relative links shots\*.png)
    pack.json         PackSummary (factory\src\lib\types.ts) + upload file lists
    math_stats.json, event_ids.json, shots\*.png   copies of the evidence
Also refreshes build\<id>\reports\math_stats.json (scripts\math_stats.py <id>; reused while newer than the
math) and build\<id>\reports\event_ids.json (tools\release\pick_event_ids.py, only when missing).

Sections: 1 Studio form fields, 2 modes table + critical tests, 3 rules and paytable, 4 reviewer event IDs,
5 compliance checklist (core\policy.v1.json: level "stake" blocks, "ours" warns), 6 licences and art
sign-off, 7 screenshots, 8 files to upload (sizes, sha256).
Factory mode (game.json release.mode, tools\gamedef\mode.py): in test mode the rules core\policy.v1.json marks
"modes": ["release"] (assets.test/provenance/humanEdit/signoff/complete) are not evaluated, section 6 (licences)
is left out and the sections are renumbered; the header says "Mode: TEST" (owner documents only, never the game).

pack.py never writes release\. tools\package.ps1 runs it without --dry-run and copies build\<id>\pack\*
into release\<id>\<ver>\.
Exit: --dry-run 0 when the pack was written; without --dry-run 1 when a Stake-level blocker exists.
"""

import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import Game, game_arg  # noqa: E402
from mode import release_mode, rule_active  # noqa: E402

PY = sys.executable
# Restricted title terms (stake-engine.com/docs-content/prompt.md [213], checked 2026-11-07; core/policy.v1.json title.terms).
TITLE_TERMS = ["Megaways", "XWays", "Enhanced", "Boosted", "RTP", "Gates of", "Bonanza", "Olympus", "Rush", "Kraken", "Waylanders"]
OUR_RTP = (0.9615, 0.9655)  # policy rtp.ourBand
SIMS = (100_000, 1_000_000)  # policy sims.min
TILE_SLOTS = {"tile.bg": "3:4 tile background", "tile.fg": "3:4 tile foreground (transparent)", "cover": "16:9 cover"}
CATS = ["loss", "win", "big", "bonus", "max"]
CAT_LABEL = {"loss": "Loss", "win": "Normal win", "big": "Big win", "bonus": "Bonus trigger", "max": "Max win"}


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_json(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else default


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


class Policy:
    def __init__(self, mode: str = "release"):
        doc = read_json(ROOT / "core" / "policy.v1.json", {"rules": []})
        self.rules = {r["id"]: r for r in doc["rules"]}
        self.mode = mode

    def active(self, rule: str) -> bool:
        """False for a rule that is off in this factory mode (policy "modes"); unknown rule ids always apply."""
        return rule_active(self.rules.get(rule), self.mode)

    def issue(self, rule: str, message: str, level: str | None = None, why: str | None = None) -> dict:
        r = self.rules.get(rule, {})
        out = {"rule": rule, "level": level or r.get("level", "stake"), "message": message}
        if why or r.get("why"):
            out["why"] = why or r.get("why")
        if r.get("source"):
            out["source"] = r["source"]
        return out


# ---- data collection -----------------------------------------------------------------------------
def math_stats(g: Game) -> dict | None:
    rep = ROOT / "build" / g.id / "reports" / "math_stats.json"
    index = g.publish / "index.json"
    if not index.exists():
        return None
    newest = max(p.stat().st_mtime for p in g.publish.iterdir())
    if rep.exists() and rep.stat().st_mtime > newest:
        return read_json(rep)
    print(f"running scripts\\math_stats.py {g.id} (reads every book; can take minutes)")
    r = subprocess.run([PY, str(ROOT / "scripts" / "math_stats.py"), g.id], capture_output=True, text=True, encoding="utf-8")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(r.stdout[-2000:], r.stderr[-2000:])
        return {"error": "math_stats.py did not return JSON", "modes": [], "critical_fails": ["math_stats.py failed"], "engine_failed_classes": [], "soft_warnings": []}
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return data


def event_ids(g: Game) -> dict | None:
    rep = ROOT / "build" / g.id / "reports" / "event_ids.json"
    if not rep.exists() and (g.publish / "index.json").exists():
        print("running tools\\release\\pick_event_ids.py (no event_ids.json yet)")
        subprocess.run([PY, str(ROOT / "tools" / "release" / "pick_event_ids.py"), "--game", g.id], check=False)
    return read_json(rep)


def precheck(g: Game) -> dict:
    """tools\\assets\\precheck.py --json -> {blockers, warnings}; falls back to parsing its text output."""
    r = subprocess.run([PY, str(ROOT / "tools" / "assets" / "precheck.py"), "--game", g.id, "--json"],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        data = json.loads(r.stdout)
        if isinstance(data, dict) and "blockers" in data:
            return {"blockers": data.get("blockers", []), "warnings": data.get("warnings", []), "text": False}
    except json.JSONDecodeError:
        pass
    lines = [ln.strip() for ln in r.stdout.splitlines()]
    fails = [ln[4:].strip() for ln in lines if ln.startswith(("FAIL ", "TODO ")) and not ln.startswith("FAIL:")]
    return {"blockers": [], "warnings": [], "lines": fails, "text": True}


def lookup_rows(p: Path) -> int:
    with open(p, "rb") as f:
        return sum(1 for line in f if line.strip())


def restricted_words() -> list:
    src = ROOT / "core" / "web" / "cluster-tumble" / "src" / "game" / "wording.ts"
    if not src.exists():
        return []
    body = src.read_text(encoding="utf-8").split("const SWEEPS", 1)[-1].split("];", 1)[0]
    return [a or b for a, b in re.findall(r"\[(?:'([^']+)'|\"([^\"]+)\"),", body)]


def file_list(folder: Path) -> list:
    if not folder.exists():
        return []
    return [{"file": p.relative_to(folder).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in sorted(folder.rglob("*")) if p.is_file()]


# ---- evaluation ----------------------------------------------------------------------------------
def evaluate(g, pol, stats, ev, pre, gate, lock, signoff, tiles_dir):
    blockers, warnings, auto = [], [], []  # auto: (rule, ok, evidence) for the checklist
    # Rules precheck --json already reports (A1, core/policy.v1.json ids): our own copies are skipped.
    pre_rules = {r.get("rule") for r in pre["blockers"] + pre["warnings"] if isinstance(r, dict)}
    OVERLAP = {"sims.min", "assets.required", "assets.signoff", "assets.test", "skin.testOnly"}

    def add(issue, own=True):
        if not pol.active(issue["rule"]):
            return  # off in this factory mode
        if own and issue["rule"] in OVERLAP and issue["rule"] in pre_rules:
            return
        (blockers if issue["level"] == "stake" else warnings).append(issue)

    gdef, ident = g.gdef, g.gdef["identity"]
    title = ident["displayName"]
    hits = [t for t in TITLE_TERMS if re.search(rf"\b{re.escape(t)}\b", title, re.I)]
    for t in hits:
        add(pol.issue("title.terms", f"Title '{title}' contains the restricted term '{t}'."))
    auto.append(("title.terms", not hits, f"title '{title}' checked against {len(TITLE_TERMS)} terms"))
    if ident.get("testOnly"):
        add(pol.issue("skin.testOnly", "This is a test skin (identity.testOnly): it can never be submitted.", level="stake"))

    # math
    if not stats or not stats.get("modes"):
        add(pol.issue("rtp.band", "No math results: build the math (Build page, math steps) before packing."))
    else:
        crit_rule = [("rtp", "rtp.band"), ("max win", "wincap.hard"), ("cheapest", "cost.cheapest"), ("std", "cost.cheapest"), ("cost", "cost.max")]
        for c in stats.get("critical_fails", []):
            rule = next((r for k, r in crit_rule if k in c), "rtp.band")
            add(pol.issue(rule, f"Stake critical math test fails: {c}"))
        for s in stats.get("soft_warnings", []):
            if "max win" in s:
                add(pol.issue("wincap.reachable", f"Max win is too rare: {s}"))
            else:
                add(pol.issue("math.hitRate", f"Engine guidance: {s}", level="ours", why="Engine guidance: a win at least 1 in 50 spins; reviewers rate dead games low."))
        for m in stats["modes"]:
            if not OUR_RTP[0] <= m["rtp"] <= OUR_RTP[1]:
                add(pol.issue("rtp.ourBand", f"{m['mode']}: RTP {m['rtp'] * 100:.2f}% is outside our margin 96.15-96.55%."))
            if m["max_win_x"] > 100_000:
                add(pol.issue("wincap.soft", f"{m['mode']}: max win {m['max_win_x']:,.0f}x is above 100,000x."))
        if stats.get("engine_failed_classes"):
            add(pol.issue("math.nonCritical", f"Engine non-critical classes failed: {', '.join(stats['engine_failed_classes'])}", level="ours",
                          why="Not blocking; Stake lowers exposure and bet limits for each failed class."))
        if len(stats["modes"]) > 20:
            add(pol.issue("modes.count", f"{len(stats['modes'])} modes; Stake allows at most 20."))
        auto.append(("rtp.band / wincap.hard / cost.*", not stats.get("critical_fails"), "scripts\\math_stats.py critical tests: " + ("PASS" if not stats.get("critical_fails") else "; ".join(stats["critical_fails"]))))
        auto.append(("wincap.reachable", not any("max win" in s for s in stats.get("soft_warnings", [])), "max win odds per mode in section 2"))
    sims_ok = True
    index = read_json(g.publish / "index.json", {"modes": []})
    for m in index["modes"]:
        n = lookup_rows(g.publish / m["weights"])
        if not SIMS[0] <= n <= SIMS[1]:
            sims_ok = False
            add(pol.issue("sims.min", f"{m['name']}: {n:,} simulations; Stake needs 100,000 to 1,000,000."))
    auto.append(("sims.min", sims_ok and bool(index["modes"]), f"{len(index['modes'])} lookup tables counted"))

    # social words in mode names (texts are rewritten at display time by core wording.ts t())
    words = restricted_words()
    bad = [(m["name"], w) for m in gdef["modes"] for w in words if re.search(rf"\b{re.escape(w)}\b", m["name"], re.I)]
    for name, w in bad:
        add(pol.issue("social.words", f"Mode name '{name}' contains the social-casino restricted word '{w}'."))
    auto.append(("social.words", not bad, f"mode names checked against {len(words)} phrases; player texts pass through wording.ts t() (docs/08 [77])"))

    # tiles
    missing = [s for s in TILE_SLOTS if not (tiles_dir / f"{s}.png").exists()]
    for s in missing:
        add(pol.issue("assets.required", f"{TILE_SLOTS[s]} source image missing: {rel(tiles_dir)}\\{s}.png (Asset desk slot '{s}')."))
    auto.append(("assets.required", not missing, f"tile sources in {rel(tiles_dir)}: {', '.join(s for s in TILE_SLOTS if s not in missing) or 'none'}"))

    # test assets in the lock
    tests = [sid for sid, rec in lock.items() if is_test(rec)]
    if tests:
        add(pol.issue("assets.test", f"{len(tests)} slot(s) still hold factory test assets: {', '.join(tests[:8])}{' ...' if len(tests) > 8 else ''}"))
    auto.append(("assets.test", not tests, f"{len(lock)} lock records checked"))

    # precheck (art, math tier); A1's --json gives PolicyIssue-like rows, else map its text lines
    for kind, rows in (("blockers", pre["blockers"]), ("warnings", pre["warnings"])):
        for row in rows:
            if isinstance(row, dict):
                add({"rule": row.get("rule", "precheck"), "level": row.get("level", "stake" if kind == "blockers" else "ours"),
                     "message": row.get("message", str(row)), **({"why": row["why"]} if row.get("why") else {}),
                     **({"source": row["source"]} if row.get("source") else {})}, own=False)
            else:
                add(pol.issue("precheck", str(row), level="stake" if kind == "blockers" else "ours"), own=False)
    for line in pre.get("lines", []):
        if "simulations" in line or "testOnly" in line:
            continue  # counted above
        low = line.lower()
        rule = ("assets.signoff" if "sign-off" in low else "assets.humanEdit" if "edit" in low
                else "assets.provenance" if ("licence" in low or "source url" in low) else "assets.complete" if "not filled" in low
                else "sims.min" if low.startswith("math") else "precheck")
        add(pol.issue(rule, line, level="stake" if rule in ("sims.min", "precheck") else None))

    # gate
    if not gate:
        add(pol.issue("gate.full", "No gate report: run Build step 'Check' (tools\\gates\\gate.ps1).", level="ours",
                      why="package.ps1 refuses without a full gate run with 0 failures."))
    else:
        for s in gate.get("steps", []):
            if s["status"] == "FAIL":
                add(pol.issue("assets.unique" if s["step"] == "no sample assets" else "gate.step", f"Gate step '{s['step']}' failed: {s['detail']}", level="stake"))
            elif s["status"] == "todo":
                rule = {"no sample assets": "assets.unique", "bundle budget": "bundle.size"}.get(s["step"], "gate.step")
                add(pol.issue(rule, f"Gate step '{s['step']}' not passing yet (reported only, -PreArt): {s['detail']}",
                              level="stake" if rule == "assets.unique" else "ours"))
        if gate.get("fast") or gate.get("preArt"):
            add(pol.issue("gate.full", f"Last gate run ({gate.get('date')}) was {'fast' if gate.get('fast') else ''}{' and ' if gate.get('fast') and gate.get('preArt') else ''}{'pre-art' if gate.get('preArt') else ''}.",
                          level="ours", why="package.ps1 refuses unless the last gate was a full run (no -Fast, no -PreArt) with 0 failures."))
        auto.append(("gate", gate.get("failed", 1) == 0, f"gate.json {gate.get('date')} head {gate.get('gitHead')}: {gate.get('failed')} failed, fast={gate.get('fast')}, preArt={gate.get('preArt')}"))

    # listing, review
    listing = gdef.get("listing", {})
    if not (listing.get("blurb") or "").strip():
        add(pol.issue("listing.blurb", "Description (blurb) is empty: fill listing.blurb in game.json.", level="ours",
                      why="The Studio form needs a short description; reviewers read it first."))
    if not listing.get("distribution"):
        add(pol.issue("listing.distribution", "Distribution not chosen (listing.distribution: onlyStake or network).", level="ours",
                      why="Fixed at launch and asked by the Studio form; 'network' forbids reskins later."))
    rv = gdef.get("review", {})
    if len(rv.get("originality", [])) < 2 or len(rv.get("signatureMoment", "")) < 10:
        add(pol.issue("originality.formula", "review.originality needs 2+ mechanic differences and a signature moment."))
    if not signoff:
        add(pol.issue("assets.signoff", "Art not signed off (Asset desk > Sign off)."))

    # event ids
    if not ev:
        add(pol.issue("events.ids", "No reviewer event IDs: press 'Pick event IDs'.", level="ours", why="Reviewers may ask for one event ID per outcome and mode."))
    else:
        for m in ev["modes"]:
            if "event" not in m["picks"].get("max", {}):
                add(pol.issue("events.maxWin", f"{m['mode']}: no max-win event ID ({m['picks']['max'].get('na')}).", level="ours",
                              why="Reviewers ask for a max-win replay; docs/08 requires one max-win book per mode."))
        if not ev.get("version"):
            add(pol.issue("events.version", "Replay links have no Studio math version: re-pick with the version number after Publish Game > Math.",
                          level="ours", why="A replay link needs the published math version."))
    return group(blockers), group(warnings), [a for a in auto if pol.active(a[0])]


def group(rows):
    """Drop identical messages; fold 4+ '<slot>: <same problem>' rows of one rule into one row."""
    seen, uniq = set(), []
    for r in rows:
        if r["message"] not in seen:
            seen.add(r["message"])
            uniq.append(r)
    slot_msg = re.compile(r"^([a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+){0,3}): (.+)$")
    buckets = {}
    for r in uniq:
        m = slot_msg.match(r["message"])
        if m and not r["message"].startswith("math:"):
            buckets.setdefault((r["rule"], m.group(2)), []).append(m.group(1))
    out, done = [], set()
    for r in uniq:
        m = slot_msg.match(r["message"])
        key = (r["rule"], m.group(2)) if m and not r["message"].startswith("math:") else None
        if key and len(buckets[key]) >= 4:
            if key in done:
                continue
            done.add(key)
            slots = buckets[key]
            out.append({**r, "message": f"{len(slots)} slots - {key[1]}: {', '.join(slots)}"})
        else:
            out.append(r)
    return out


def is_test(rec: dict) -> bool:
    p = rec.get("provenance") or {}
    return bool(rec.get("test")) or "test" in str(p.get("licence") or "").lower() or any("test" in str(f).lower() for f in rec.get("flags") or [])


# ---- rendering -----------------------------------------------------------------------------------
def build_doc(g, pol, stats, ev, rules, gate, lock, signoff, shots, uploads, blockers, warnings, auto):
    """Returns a list of sections: (title, blocks). A block is ('p', text) | ('table', head, rows) | ('list', items)
    | ('checks', [(done, text)]) | ('img', name, path)."""
    gdef, ident = g.gdef, g.gdef["identity"]
    listing = gdef.get("listing", {})
    dist = {"onlyStake": "Only on Stake", "network": "Stake + Engine network"}.get(listing.get("distribution"), "NOT CHOSEN")
    disclaimer = (ROOT / "core" / "web" / "cluster-tumble" / "src" / "components" / "GameInfo.svelte")
    disc_ok = disclaimer.exists() and "Malfunction voids all wins" in disclaimer.read_text(encoding="utf-8")
    social_rows = [a for a in auto if a[0] == "social.words"]
    fields = [
        ("Game title", ident["displayName"]),
        ("Description (blurb)", (listing.get("blurb") or "").strip() or "(empty: fill listing.blurb in game.json)"),
        ("Features", "\n".join(f"- {f}" for f in listing.get("features", [])) or "(none listed)"),
        ("Distribution", dist),
        ("Confirmation: general disclaimer in the rules", ("Yes. Evidence: Engine disclaimer template in GameInfo.svelte rules screen (docs/08 [185])." if disc_ok else "CHECK: disclaimer text not found in GameInfo.svelte")),
        ("Confirmation: social mode has no restricted phrases", ("Yes. Evidence: " + social_rows[0][2] + "." if social_rows and social_rows[0][1] else "CHECK: " + (social_rows[0][2] if social_rows else "not evaluated"))),
        ("Reviewer notes", ((listing.get("reviewerNotes") or "").strip() + ("\n" if listing.get("reviewerNotes") else "") + f"Signature moment: {gdef.get('review', {}).get('signatureMoment', '')}").strip()),
    ]
    S = []
    title_hits = [b for b in blockers if b["rule"] == "title.terms"]
    S.append(("1. Studio form fields (copy these)", [
        ("p", f"Game id {g.id}, version {ident['version']}. Title check: " + ("FAIL: " + "; ".join(b["message"] for b in title_hits) if title_hits else f"OK, none of the {len(TITLE_TERMS)} restricted terms ({', '.join(TITLE_TERMS)}).")),
        ("table", ["Field", "Value"], [[k, v] for k, v in fields]),
    ]))
    # 2 modes
    if stats and stats.get("modes"):
        rows = [[m["mode"], f"{m['cost']:g}x", f"{m['rtp'] * 100:.2f}%", f"{m['max_win_x']:,.0f}x", f"1 in {1 / m['hit_rate']:.1f}" if m["hit_rate"] else "-",
                 f"1 in {m['max_win_1_in']:,}" if m.get("max_win_1_in") else "-", f"{m['std_raw']:g}", f"1 in {m['bonus_1_in']:,}" if m.get("bonus_1_in") else "-"] for m in stats["modes"]]
        crit = stats.get("critical_fails", [])
        S.append(("2. Modes and math", [
            ("table", ["Mode", "Cost", "RTP", "Max win", "Hit rate", "Max-win odds", "Std dev", "Bonus"], rows),
            ("p", "Stake critical tests (block the form): " + ("PASS" if not crit else "FAIL - " + "; ".join(crit))),
            ("p", "Engine non-critical failed classes: " + (", ".join(stats.get("engine_failed_classes", [])) or "none")),
            ("p", "Engine guidance: " + ("; ".join(stats.get("soft_warnings", [])) or "ok")),
        ]))
    else:
        S.append(("2. Modes and math", [("p", "No math results yet.")]))
    # 3 rules
    if rules:
        t = rules["texts"]
        blocks = [("table", ["Symbol"] + rules["paytable"]["bands"], [[r["name"]] + [f"{p:g}x" if p is not None else "-" for p in r["pays"]] for r in rules["paytable"]["rows"]])]
        blocks.append(("table", ["Mode", "Cost", "RTP", "Max win", "What the player reads"],
                       [[m["title"], f"{m['cost']:g}x", f"{m['rtp'] * 100:.2f}%" if m["rtp"] else "-", f"{m['maxWin']:,.0f}x" if m["maxWin"] else "-", m["dialog"]] for m in rules["modes"]]))
        blocks.append(("list", [f"{t.get(k + '.title', '')}{': ' if t.get(k + '.title') else ''}{v}" for k, v in t.items() if k.startswith("rules.") and not k.endswith(".title")]))
        S.append(("3. Rules and paytable (as shown in the game)", blocks))
    else:
        S.append(("3. Rules and paytable", [("p", f"build\\{g.id}\\web\\rules.generated.en.json missing: run Build step 1 (Sync).")]))
    # 4 event ids
    if ev:
        rows = []
        for m in ev["modes"]:
            cells = [m["mode"]]
            for c in CATS:
                p = m["picks"][c]
                cells.append("n/a: " + p["na"] if "na" in p else f"{p['event']} ({p['payoutX']:g}x)" + (f" [{p['note']}]" if p.get("note") else ""))
            rows.append(cells)
        links = [f"{m['mode']} {CAT_LABEL[c]}: {m['picks'][c]['replay']}" for m in ev["modes"] for c in CATS if "replay" in m["picks"][c]]
        S.append(("4. Reviewer event IDs (give these when a reviewer asks)", [
            ("p", f"Studio math version: {ev.get('version') or '<version> (not set: re-pick on the Submit page with the version number)'}. Picked {ev.get('generated')}."),
            ("table", ["Mode"] + [CAT_LABEL[c] for c in CATS], rows),
            ("p", "Replay link = the game's front-end URL + the query below; " + ev.get("replayNote", "")),
            ("list", links),
        ]))
    else:
        S.append(("4. Reviewer event IDs", [("p", "Not picked yet (no math).")]))
    # 5 checklist
    S.append(("5. Compliance checklist", [
        ("p", f"Ready to submit: {'YES' if not blockers else 'NO'} - {len(blockers)} Stake blocker(s), {len(warnings)} warning(s). Rules and levels: core\\policy.v1.json; full checklist: docs\\08-compliance.md."),
        ("table", ["Level", "Rule", "Problem", "Why / source"], [["BLOCKS", b["rule"], b["message"], b.get("source", b.get("why", ""))] for b in blockers]
         + [["warns", w["rule"], w["message"], w.get("why", w.get("source", ""))] for w in warnings]),
        ("p", "Automatic checks:"),
        ("checks", [(ok, f"{rule}: {evid}") for rule, ok, evid in auto]),
        ("p", "By hand (tick when done):"),
        ("checks", [(False, "Studio: upload math (publish_files) and front end (dist), Publish Game > Math and > Front End."),
                    (False, "Studio Play Game: one round in every mode (" + ", ".join(m["name"] for m in gdef["modes"]) + "), one replay, and once with social=true."),
                    (False, "Stake AI review prompt run on the final build (https://stake-engine.com/docs-content/prompt.md): 0 FAIL."),
                    (False, "Tile (3:4) and cover (16:9) made in the Studio Media Editor from the tiles\\ sources."),
                    (False, "Studio logo set in team settings (once per team)."),
                    (False, "Both confirmations ticked; distribution chosen (fixed at launch)."),
                    (False, "Game is not substantially similar to an earlier game, including ours (Game Licence Terms 7.1(a)(viii)).")]),
    ]))
    # 6 provenance (release mode only: test mode has no licence output)
    prov_rows = []
    for sid, rec in sorted(lock.items()):
        p = rec.get("provenance") or {}
        edited = bool(rec.get("editedSha")) and rec.get("editedSha") != rec.get("rawSha")
        prov_rows.append([sid, ("TEST " if is_test(rec) else "") + str(p.get("licence") or "-"), p.get("sourceUrl") or "-", "yes" if edited else "no", p.get("editNote") or "-"])
    so = (f"Art signed off by {signoff.get('signedBy')} on {signoff.get('date')} (asset set {str(signoff.get('assetSetSha256', ''))[:12]})." if signoff else "Art NOT signed off.")
    if pol.mode != "test":
        S.append(("6. Licences and provenance", [("p", so), ("table", ["Slot", "Licence", "Source", "Human edit", "Edit note"], prov_rows) if prov_rows else ("p", "No assets ingested yet (assets.lock.json missing).")]))
    # 7 shots
    S.append(("7. Screenshots (reviewer sizes)", [("img", s.name, s) for s in shots] or [("p", "None yet: press 'Screenshots' on the Submit page.")]))
    # 8 uploads
    S.append(("8. Files to upload", [
        ("p", f"Math: Studio > Files > Import Files > folder {uploads['math']['folder']} ({len(uploads['math']['files'])} files, {human(sum(f['bytes'] for f in uploads['math']['files']))})."),
        ("table", ["File", "Size", "sha256"], [[f["file"], human(f["bytes"]), f["sha256"]] for f in uploads["math"]["files"]]),
        ("p", f"Front end: Import Files > folder {uploads['front']['folder']} ({len(uploads['front']['files'])} files, {human(sum(f['bytes'] for f in uploads['front']['files']))})."
              + ("" if uploads["front"]["files"] else " Not built yet: Build step 'Build web'.")),
        ("table", ["File", "Size", "sha256"], [[f["file"], human(f["bytes"]), f["sha256"][:16] + "..."] for f in uploads["front"]["files"]]),
        ("p", f"Tile sources for the Media Editor: {rel(g.skin / 'tiles')} ({', '.join(TILE_SLOTS)})."),
    ]))
    # sections are numbered by position (test mode leaves section 6 out)
    S = [(re.sub(r"^\d+\. ", f"{n}. ", title), blocks) for n, (title, blocks) in enumerate(S, 1)]
    return fields, S


def mode_line(g) -> str:
    m = release_mode(g.gdef)
    return ("Mode: TEST (factory test mode: any assets allowed, no licence checks; every Stake rule still applies. "
            "Shown in these owner documents only, never in the game.)" if m == "test" else "")


def render_md(g, S, generated):
    out = [f"# Submission pack: {g.gdef['identity']['displayName']} {g.gdef['identity']['version']}", "",
           f"Game id `{g.id}`. Generated by tools/release/pack.py on {generated}. Do not edit; rerun pack.py.", ""]
    if mode_line(g):
        out += [f"**{mode_line(g)}**", ""]
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", "<br>")
    for title, blocks in S:
        out += [f"## {title}", ""]
        for b in blocks:
            if b[0] == "p":
                out += [b[1], ""]
            elif b[0] == "table":
                out += ["| " + " | ".join(b[1]) + " |", "|" + "---|" * len(b[1])] + ["| " + " | ".join(cell(c) for c in r) + " |" for r in b[2]] + [""]
            elif b[0] == "list":
                out += [f"- {cell(x)}" for x in b[1]] + [""]
            elif b[0] == "checks":
                out += [f"- [{'x' if ok else ' '}] {cell(t)}" for ok, t in b[1]] + [""]
            elif b[0] == "img":
                out += [f"![{b[1]}](shots/{b[1]})", ""]
    return "\n".join(out)


CSS = """body{font:15px/1.5 system-ui,'Segoe UI',sans-serif;color:#1d1a2b;max-width:1100px;margin:24px auto;padding:0 18px}
h1{font-size:24px}h2{font-size:18px;border-bottom:2px solid #e0b84f;padding-bottom:3px;margin-top:28px}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:13px}th,td{border:1px solid #c9c3dc;padding:4px 7px;text-align:left;vertical-align:top;white-space:pre-wrap;word-break:break-word}
th{background:#f1eef8}.ready{font-size:18px;font-weight:700;padding:8px 12px;border-radius:6px}.yes{background:#dff5e1}.no{background:#fbe0dc}
tr.BLOCKS td:first-child{color:#b3261e;font-weight:700}tr.warns td:first-child{color:#8a6100;font-weight:700}
ul.checks{list-style:none;padding-left:4px}ul.checks li:before{content:'\\2610  '}ul.checks li.done:before{content:'\\2611  ';color:#287a33}
figure{display:inline-block;margin:6px;vertical-align:top}img{max-width:520px;border:1px solid #c9c3dc}figcaption{font-size:12px;color:#555}
@media print{h2{break-after:avoid}table,figure{break-inside:avoid}}"""


def render_html(g, S, generated, ready):
    e = html.escape
    ident = g.gdef["identity"]
    out = [f"<!DOCTYPE html><html lang=en><meta charset=utf-8><title>Submission pack: {e(ident['displayName'])} {e(ident['version'])}</title><style>{CSS}</style><body>",
           f"<h1>Submission pack: {e(ident['displayName'])} {e(ident['version'])}</h1>",
           f"<p>Game id <code>{e(g.id)}</code>. Generated {e(generated)} by tools/release/pack.py. Print this page or keep it open beside the Stake Studio form.</p>",
           *([f"<p><strong>{e(mode_line(g))}</strong></p>"] if mode_line(g) else []),
           f"<p class='ready {'yes' if ready else 'no'}'>{'Ready: no Stake-level blockers.' if ready else 'Not ready: fix the BLOCKS rows in section 5 first.'}</p>"]
    for title, blocks in S:
        out.append(f"<h2>{e(title)}</h2>")
        for b in blocks:
            if b[0] == "p":
                out.append(f"<p>{e(b[1])}</p>")
            elif b[0] == "table":
                out.append("<table><tr>" + "".join(f"<th>{e(h)}</th>" for h in b[1]) + "</tr>")
                for r in b[2]:
                    out.append(f"<tr class='{e(str(r[0]))}'>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>")
                out.append("</table>")
            elif b[0] == "list":
                out.append("<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in b[1]) + "</ul>")
            elif b[0] == "checks":
                out.append("<ul class=checks>" + "".join(f"<li class='{'done' if ok else ''}'>{e(t)}</li>" for ok, t in b[1]) + "</ul>")
            elif b[0] == "img":
                data = base64.b64encode(b[2].read_bytes()).decode()
                out.append(f"<figure><img src='data:image/png;base64,{data}' alt='{e(b[1])}'><figcaption>{e(b[1])}</figcaption></figure>")
    out.append("</body></html>")
    return "\n".join(out)


def main():
    g = Game(game_arg())
    dry = "--dry-run" in sys.argv
    mode = release_mode(g.gdef)
    pol = Policy(mode)
    out = ROOT / "build" / g.id / "pack"
    reports = ROOT / "build" / g.id / "reports"
    stats = math_stats(g)
    ev = event_ids(g)
    pre = precheck(g)
    gate = read_json(reports / "gate.json")
    lock = (read_json(g.skin / "assets.lock.json", {}) or {}).get("slots", {})
    signoff = read_json(g.skin / "art_signoff.json")
    rules = read_json(g.gen_web / "rules.generated.en.json")
    shots_dir = ROOT / "build" / g.id / "shots"
    shots = sorted(shots_dir.glob("*.png")) if shots_dir.exists() else []
    blockers, warnings, auto = evaluate(g, pol, stats, ev, pre, gate, lock, signoff, g.skin / "tiles")
    uploads = {
        "math": {"folder": rel(g.publish), "files": file_list(g.publish)},
        "front": {"folder": rel(ROOT / "build" / g.id / "dist"), "files": file_list(ROOT / "build" / g.id / "dist")},
    }
    generated = datetime.now().isoformat(timespec="seconds")
    fields, S = build_doc(g, pol, stats, ev, rules, gate, lock, signoff, shots, uploads, blockers, warnings, auto)
    import checklist_render  # Stake approval checklist (preview): tools\release\checklist_render.py
    ck_title, ck_blocks, checklist = checklist_render.section(g)
    S.append((ck_title, ck_blocks))
    ready = not blockers

    if out.exists():
        shutil.rmtree(out)  # generated folder: fully rebuilt every run
    (out / "shots").mkdir(parents=True)
    for s in shots:
        shutil.copyfile(s, out / "shots" / s.name)
    files = [{"label": "Submission pack (printable)", "path": "submission.html"}, {"label": "Submission pack (Markdown)", "path": "submission.md"}]
    for name, src in (("math_stats.json", reports / "math_stats.json"), ("event_ids.json", reports / "event_ids.json")):
        if src.exists():
            shutil.copyfile(src, out / name)
            files.append({"label": f"Report: {name}", "path": name})
    files += [{"label": f"Screenshot {s.stem}", "path": f"shots/{s.name}"} for s in shots]
    (out / "submission.md").write_text(render_md(g, S, generated) + "\n", encoding="utf-8", newline="\n")
    (out / "submission.html").write_text(render_html(g, S, generated, ready), encoding="utf-8", newline="\n")
    summary = {
        "game": g.id,
        "version": g.gdef["identity"]["version"],
        "mode": mode,
        "generated": generated,
        "ready": ready,
        "blockers": blockers,
        "warnings": warnings,
        "studioFields": [{"label": k, "value": v} for k, v in fields],
        "files": files,
        "dryRun": dry,
        "uploads": uploads,
        "checklist": checklist,
    }
    (out / "pack.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    for b in blockers:
        print(f"  BLOCK {b['rule']}: {b['message']}")
    for w in warnings:
        print(f"  warn  {w['rule']}: {w['message']}")
    print(f"{'OK' if ready else 'NOT READY'}: pack {g.id} [{mode} mode] -> {rel(out)} ({len(blockers)} blocker(s), {len(warnings)} warning(s){', dry run' if dry else ''})")
    sys.exit(0 if dry or ready else 1)


if __name__ == "__main__":
    main()
