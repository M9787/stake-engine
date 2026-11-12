r"""Stake approval checklist (preview) for one game: core\stake_checklist.v1.json evaluated per item.

Usage (from stake\):
    math-sdk\env\Scripts\python.exe tools\release\checklist.py --game <id> [--json] [--strict]

Writes build\<id>\reports\stake_checklist.json (StakeChecklist, factory\src\lib\types.ts).
--json prints that document instead of the text table.
Status per item: pass | fail | manual (a person looks; evidence says what to look at) | unknown (evidence missing).
Evidence read (nothing is built here):
    build\<id>\dist                         static scan: viewport [223], loader/branding [275], disclaimer [185]
    build\<id>\web\rules.generated.en.json  rules vs math [25][27], paytable [24], features [26][29], texts [239], social [77][225][188]
    math-sdk\games\<id>\library\publish_files + build\<id>\reports\math_stats.json (run scripts\math_stats.py when stale)
    build\<id>\reports\e2e.json             Playwright JSON (gate.ps1 e2e step); else the gate.json e2e step
    scripts\check_amount.ts [219][273][78], scripts\check_external_urls.ps1, tools\check_sample_assets.ps1
Exit: 0 = written (failed items are in the report); 1 = unknown game, or --strict and an auto/e2e item failed.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import Game, game_arg  # noqa: E402

try:
    from mode import release_mode  # noqa: E402  (D1, tools\gamedef\mode.py)
except ImportError:  # pragma: no cover
    def release_mode(gdef):
        m = ((gdef or {}).get("release") or {}).get("mode")
        return m if m in ("test", "release") else "release"

PY = sys.executable
SPEC = ROOT / "core" / "stake_checklist.v1.json"
CORE_WEB = ROOT / "core" / "web" / "cluster-tumble" / "src"
# Restricted title terms: prompt.md [213] (core/policy.v1.json title.terms; same list as tools\release\pack.py).
TITLE_TERMS = ["Megaways", "XWays", "Enhanced", "Boosted", "RTP", "Gates of", "Bonanza", "Olympus", "Rush", "Kraken", "Waylanders"]
# Engine critical tests (scripts\math_stats.py constants).
RTP_BAND = (0.960, 0.967)
SIMS = (100_000, 1_000_000)
DISCLAIMER = "Malfunction voids all wins"
TILES = {"tile.bg": "3:4", "tile.fg": "3:4", "cover": "16:9"}


def read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def run(cmd: list, cwd: Path = ROOT, timeout: int = 600) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        # stdout first; stderr only when stdout is empty (node prints its ExperimentalWarning there)
        return r.returncode, (r.stdout or "") if (r.stdout or "").strip() else (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 99, str(e)


def last_line(out: str) -> str:
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


# ---- evidence collectors -------------------------------------------------------------------------
class Ctx:
    def __init__(self, g: Game):
        self.g = g
        self.reports = ROOT / "build" / g.id / "reports"
        self.dist = ROOT / "build" / g.id / "dist"
        self.rules = read_json(g.gen_web / "rules.generated.en.json")
        self.index = read_json(g.publish / "index.json")
        self._cache = {}

    def once(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    # dist text (html, js, css) as one string per file
    def dist_files(self):
        def load():
            if not (self.dist / "index.html").exists():
                return None
            out = {}
            for p in self.dist.rglob("*"):
                if p.is_file() and p.suffix.lower() in (".html", ".js", ".css", ".json"):
                    out[rel(p)] = p.read_text(encoding="utf-8", errors="replace")
            return out
        return self.once("dist", load)

    def stats(self):
        def load():
            if not self.index:
                return None
            rep = self.reports / "math_stats.json"
            newest = max(p.stat().st_mtime for p in self.g.publish.iterdir())
            if rep.exists() and rep.stat().st_mtime > newest:
                data = read_json(rep)
                if data and data.get("modes"):
                    return data
            print(f"running scripts\\math_stats.py {self.g.id} (reads every book; can take minutes)")
            code, out = run([PY, str(ROOT / "scripts" / "math_stats.py"), self.g.id], timeout=3600)
            start = out.find("{")
            try:
                data = json.loads(out[start:out.rfind("}") + 1]) if start >= 0 else None
            except json.JSONDecodeError:
                data = None
            if not data:
                return {"error": last_line(out)}
            rep.parent.mkdir(parents=True, exist_ok=True)
            rep.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
            return data
        return self.once("stats", load)

    def e2e(self):
        """{'source': str, 'tests': [(file, title, status)]} from e2e.json, or {'source', 'gate': step} fallback."""
        def load():
            rep = read_json(self.reports / "e2e.json")
            if rep and "suites" in rep:
                tests = []

                def walk(suite, file):
                    file = suite.get("file") or file
                    for spec in suite.get("specs", []):
                        for t in spec.get("tests", []):
                            st = t.get("status") or ("expected" if spec.get("ok") else "unexpected")
                            tests.append((spec.get("file") or file or "", spec.get("title", ""), st))
                    for s in suite.get("suites", []):
                        walk(s, file)
                for s in rep["suites"]:
                    walk(s, "")
                started = (rep.get("stats") or {}).get("startTime", "")
                return {"source": f"reports\\e2e.json {started[:19]}", "tests": tests}
            gate = read_json(self.reports / "gate.json")
            step = next((s for s in (gate or {}).get("steps", []) if str(s.get("step", "")).startswith("e2e (")), None)
            if step:
                return {"source": f"gate.json {gate.get('date')} step '{step['step']}' (no per-test e2e.json yet)", "gate": step}
            return None
        return self.once("e2e", load)

    def amount(self):
        return self.once("amount", lambda: run(["node", "--experimental-strip-types", str(Path("scripts") / "check_amount.ts")]))

    def player_texts(self):
        """(where, text, raw) for every player text: rules texts, mode names/titles/labels and core GameInfo strings.
        raw=True: the text is rendered without wording.ts t() (GameInfo section titles)."""
        out = []
        texts = (self.rules or {}).get("texts", {})
        for k, v in texts.items():
            out.append((k, v, k.startswith("rules.") and k.endswith(".title")))
        info = CORE_WEB / "components" / "GameInfo.svelte"
        if info.exists():
            src = info.read_text(encoding="utf-8")
            for m in re.finditer(r"\bt\(\s*(`[^`]*`|'[^']*')\s*\)", src):
                s = re.sub(r"\$\{[^}]*\}", "1", m.group(1)[1:-1])
                out.append(("GameInfo.svelte", re.sub(r"\s+", " ", s), False))
            for m in re.finditer(r"\[\s*'([^']+)',\s*'([^']+)'\s*\]", src):
                out += [("GameInfo.svelte BUTTONS", m.group(1), False), ("GameInfo.svelte BUTTONS", m.group(2), False)]
        return out


def sweeps():
    """(from, to) pairs of core wording.ts SWEEPS (the runtime social-casino rewrite)."""
    src = (CORE_WEB / "game" / "wording.ts").read_text(encoding="utf-8")
    body = src.split("const SWEEPS", 1)[-1].split("];\n", 1)[0]
    q = r"""(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")"""
    return [(a or b, c or d) for a, b, c, d in re.findall(rf"\[\s*{q}\s*,\s*{q}\s*\]", body)]


def to_sweeps(text: str, pairs) -> str:
    lookup = {a.lower(): b for a, b in pairs}
    pat = re.compile(r"\b(" + "|".join(re.escape(a).replace("'", "['’]") for a, _ in pairs) + r")\b", re.I)

    def repl(m):
        hit = m.group(0)
        to = lookup.get(hit.lower().replace("’", "'"), hit)
        if hit == hit.upper():
            return to.upper()
        if hit[0] == hit[0].upper():
            return to[0].upper() + to[1:]
        return to
    return pat.sub(repl, text)


def social_hits(text: str, pairs) -> list:
    """Restricted words still present: every SWEEPS phrase, single words also with s/es/ed/ing/er suffixes."""
    hits = []
    for a, _ in pairs:
        if " " in a or "'" in a:
            if re.search(rf"\b{re.escape(a)}\b", text, re.I):
                hits.append(a)
        elif re.search(rf"\b{re.escape(a)}(s|es|ed|ing|er|ers)?\b", text, re.I):
            hits.append(re.search(rf"\b{re.escape(a)}\w*", text, re.I).group(0))
    return hits


# ---- checks: each returns (status, evidence) -----------------------------------------------------
def c_dist_viewport(c: Ctx):
    files = c.dist_files()
    if files is None:
        return "unknown", f"no build at {rel(c.dist)} (Build web first)"
    html_ = files.get(rel(c.dist / "index.html"), "")
    m = re.search(r"<meta[^>]*name=\"viewport\"[^>]*content=\"([^\"]*)\"", html_, re.S) or re.search(r"<meta[^>]*content=\"([^\"]*)\"[^>]*name=\"viewport\"", html_, re.S)
    content = (m.group(1) if m else "").replace(" ", "")
    meta_ok = "maximum-scale=1" in content and "user-scalable=no" in content
    touch = any(re.search(r"touch-action:\s*(manipulation|none)", t) for t in files.values())
    if meta_ok or touch:
        return "pass", f"index.html viewport '{content or '-'}'" + ("; touch-action set in CSS" if touch else "")
    return "fail", f"index.html viewport '{content or 'missing'}' lacks maximum-scale=1, user-scalable=no and no touch-action CSS"


def c_dist_loader(c: Ctx):
    files = c.dist_files()
    if files is None:
        return "unknown", f"no build at {rel(c.dist)}"
    bad = []
    for name, t in files.items():
        for pat in (r"powered\s+by\s+stake", r"stake[\s-]?engine", r"stake[_-]?logo", r"engine[_-]?loader"):
            m = re.search(pat, t, re.I)
            if m:
                bad.append(f"'{m.group(0)}' in {name}")
    imgs = [rel(p) for p in c.dist.rglob("*") if p.is_file() and (p.suffix.lower() == ".gif" or "stake" in p.name.lower())]
    bad += [f"file {p}" for p in imgs]
    if bad:
        return "fail", "; ".join(bad[:5])
    return "pass", f"{len(files)} html/js/css files: no 'Powered by Stake Engine', Stake logo or loader gif"


def c_dist_external(c: Ctx):
    code, out = run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "check_external_urls.ps1"), "-Game", c.g.id])
    return ("pass" if code == 0 else "fail"), f"scripts\\check_external_urls.ps1: {last_line(out)}"


def c_title(c: Ctx):
    names = [c.g.gdef["identity"]["displayName"], ((c.rules or {}).get("texts") or {}).get("game.name", "")]
    hits = sorted({t for n in names for t in TITLE_TERMS if n and re.search(rf"\b{re.escape(t)}\b", n, re.I)})
    if hits:
        return "fail", f"title '{names[0]}' contains restricted term(s): {', '.join(hits)}"
    return "pass", f"title '{names[0]}' checked against {len(TITLE_TERMS)} restricted terms; uniqueness: search the lobby"


def c_currency(c: Ctx):
    code, out = c.amount()
    return ("pass" if code == 0 else "fail"), f"scripts\\check_amount.ts: {last_line(out)}"


def need_rules(c: Ctx):
    return None if c.rules else ("unknown", f"no {rel(c.g.gen_web / 'rules.generated.en.json')} (run scripts\\sync.ps1)")


def c_rules_rtp(c: Ctx):
    if (r := need_rules(c)):
        return r
    st = c.stats()
    if not st or not st.get("modes"):
        return "unknown", "no math results (math_stats): " + str((st or {}).get("error", "no index.json"))
    sm = {m["mode"]: m for m in st["modes"]}
    bad, n = [], 0
    for m in c.rules["modes"]:
        s = sm.get(m["name"])
        if not s:
            bad.append(f"{m['name']}: not in math")
            continue
        n += 1
        if m.get("rtp") is None or abs(m["rtp"] - s["rtp"]) > 0.00011:
            bad.append(f"{m['name']}: rules RTP {m.get('rtp')} vs math {s['rtp']}")
        if m.get("maxWin") is None or abs(m["maxWin"] - s["max_win_x"]) > 0.01:
            bad.append(f"{m['name']}: rules max win {m.get('maxWin')} vs math {s['max_win_x']}")
    missing = [k for k in sm if k not in {m["name"] for m in c.rules["modes"]}]
    bad += [f"{k}: mode in math but not in rules" for k in missing]
    if bad:
        return "fail", "; ".join(bad)
    return "pass", f"{n} modes: rules RTP and max win equal the math (math_stats.json); shown in GameInfo mode table"


def c_rules_modes(c: Ctx):
    if (r := need_rules(c)):
        return r
    if not c.index:
        return "unknown", "no publish_files\\index.json"
    rm = {m["name"]: m for m in c.rules["modes"]}
    bad = []
    for m in c.index["modes"]:
        r = rm.get(m["name"])
        if not r:
            bad.append(f"{m['name']}: no rules entry")
            continue
        if abs(float(r["cost"]) - float(m["cost"])) > 1e-9:
            bad.append(f"{m['name']}: rules cost {r['cost']} vs index.json {m['cost']}")
        if not (r.get("dialog") or "").strip():
            bad.append(f"{m['name']}: no description (mode.{m['name']}.dialog)")
        if not (r.get("title") or "").strip() or r.get("title") == m["name"].upper() and f"mode.{m['name']}.title" not in c.rules["texts"]:
            bad.append(f"{m['name']}: no title text")
    if bad:
        return "fail", "; ".join(bad)
    return "pass", f"{len(c.index['modes'])} modes: cost equals index.json, each has a title and a description"


def c_rules_paytable(c: Ctx):
    if (r := need_rules(c)):
        return r
    rows = {r["symbol"]: r for r in c.rules["paytable"]["rows"]}
    game_pays = c.g.gdef.get("paytable", {}).get("pays", {})
    bad = []
    pay_syms = [s["id"] for s in c.g.gdef["symbols"] if s["role"] == "pay"]
    for sid in pay_syms:
        row = rows.get(sid)
        if not row or not any(p for p in row["pays"] if p):
            bad.append(f"{sid}: no pays in the pay table")
        elif sid in game_pays and [float(p) if p is not None else None for p in row["pays"]] != [float(p) for p in game_pays[sid]]:
            bad.append(f"{sid}: shown pays {row['pays']} differ from game.json {game_pays[sid]}")
    if bad:
        return "fail", "; ".join(bad)
    return "pass", f"{len(pay_syms)} pay symbols, each with pays for {len(c.rules['paytable']['bands'])} cluster bands (equal to game.json)"


def reel_symbols(c: Ctx) -> set:
    found = set()
    reels = c.g.skin / "math" / "reels"
    for p in reels.glob("*.csv") if reels.exists() else []:
        found |= {x.strip() for x in p.read_text(encoding="utf-8").replace("\n", ",").split(",") if x.strip()}
    return found


def all_text(c: Ctx) -> str:
    return " \n".join(v for k, v in c.rules["texts"].items() if not k.startswith(("symbol.", "winlevel.")))


def c_rules_features(c: Ctx):
    if (r := need_rules(c)):
        return r
    gdef, body, on_reels = c.g.gdef, all_text(c), reel_symbols(c)
    info = (CORE_WEB / "components" / "GameInfo.svelte").read_text(encoding="utf-8")
    checks = [("clusters", "touching identical symbols form a cluster" in info, "core GameInfo 'Clusters and tumbles'")]
    for s in gdef["symbols"]:
        if s["role"] in ("scatter", "wild") and (not on_reels or s["id"] in on_reels):
            name = c.rules["texts"].get(s.get("nameKey", ""), s["id"])
            ok = bool(re.search(rf"\b({re.escape(name)}|{s['role']})\b", body, re.I))
            checks.append((f"{s['role']} {s['id']}", ok, f"a rules text naming '{name}' or '{s['role']}'"))
    gm = (gdef.get("features") or {}).get("gridMultiplier") or {}
    if gm.get("enabled"):
        checks.append(("multiplier grid", bool(re.search(r"multipl|charged|\bx2\b", body, re.I)), "a rules text on the multiplier spots"))
    missing = [f"{n} (needs {how})" for n, ok, how in checks if not ok]
    if missing:
        return "fail", "not explained: " + "; ".join(missing)
    return "pass", "explained: " + ", ".join(n for n, _, _ in checks)


def c_rules_freespins(c: Ctx):
    if (r := need_rules(c)):
        return r
    gdef, body = c.g.gdef, all_text(c)
    trig = gdef.get("freespinTriggers") or {}
    has_fs = bool(trig.get("basegame")) or bool((gdef.get("features") or {}).get("bonusVariants"))
    if not has_fs:
        return "pass", "no free spins in game.json (n/a)"
    checks = [("free spins", bool(re.search(r"free\s*spins?|free\s*games?", body, re.I)))]
    if trig.get("freegame"):
        checks.append(("re-trigger", bool(re.search(r"re-?trigger|\badds?\s+\d+\s+(free\s+)?spins|extra\s+spins|more\s+spins", body, re.I))))
    missing = [n for n, ok in checks if not ok]
    if missing:
        return "fail", "game.json has free spins but no rules text explains: " + ", ".join(missing) + " (add rules.bonuses / rules.freeSpins to text\\en.json)"
    return "pass", "rules texts explain " + " and ".join(n for n, _ in checks)


def c_rules_buttons(c: Ctx):
    info = (CORE_WEB / "components" / "GameInfo.svelte").read_text(encoding="utf-8")
    names = re.findall(r"\[\s*'([^']+)',", info.split("const BUTTONS", 1)[-1].split("];", 1)[0])
    need = {"Spin", "Stop", "Turbo", "Auto spin", "Menu", "Sound", "Settings"}
    lack = sorted(need - set(names))
    files = c.dist_files()
    in_dist = files is not None and any("Turns all sound on or off" in t for t in files.values())
    if lack:
        return "fail", f"GameInfo Buttons table lacks: {', '.join(lack)}"
    if files is None:
        return "unknown", "Buttons table in core GameInfo; no build to confirm"
    return ("pass" if in_dist else "fail"), f"{len(names)} buttons explained in core GameInfo ({', '.join(names)})" + ("" if in_dist else "; table text not found in the build")


def c_rules_disclaimer(c: Ctx):
    files = c.dist_files()
    if files is not None:
        hit = next((n for n, t in files.items() if DISCLAIMER in t), None)
        return ("pass", f"Engine disclaimer found in {hit}") if hit else ("fail", f"'{DISCLAIMER}...' not in the build")
    info = (CORE_WEB / "components" / "GameInfo.svelte").read_text(encoding="utf-8")
    return ("pass" if DISCLAIMER in info else "fail"), "GameInfo.svelte (no build yet)"


def c_rules_mystery(c: Ctx):
    words = " ".join([m["name"] for m in c.g.gdef["modes"]] + list(((c.rules or {}).get("texts") or {}).values()))
    if re.search(r"mystery", words, re.I):
        return "manual", "a Mystery mode exists: compare its stated chances with the math"
    return "pass", "no Mystery mode (n/a)"


def c_texts_en(c: Ctx):
    if (r := need_rules(c)):
        return r
    bad = [f"missing placeholders: {c.rules['missing']}"] if c.rules.get("missing") else []
    vals = list(c.rules["texts"].items()) + [(f"mode {m['name']}.{f}", m.get(f) or "") for m in c.rules["modes"] for f in ("title", "label", "dialog")]
    for k, v in vals:
        if not str(v).strip():
            bad.append(f"{k}: empty")
        elif re.search(r"\b(undefined|NaN|null)\b|\{[A-Za-z0-9_.]+\}", v):
            bad.append(f"{k}: '{v[:50]}'")
        elif re.fullmatch(r"[a-z][A-Za-z0-9]*(\.[A-Za-z0-9]+)+", v.strip()):
            bad.append(f"{k}: raw key '{v}'")
    if bad:
        return "fail", "; ".join(bad[:6])
    return "pass", f"{len(vals)} English texts: none empty, no undefined/NaN/raw keys/unfilled placeholders"


def c_social_texts(c: Ctx):
    if (r := need_rules(c)):
        return r
    pairs = sweeps()
    bad = []
    items = c.player_texts()
    for where, text, raw in items:
        shown = text if raw else to_sweeps(text, pairs)
        hits = social_hits(shown, pairs)
        if hits:
            bad.append(f"{where}: '{', '.join(sorted(set(hits)))}' in social text '{shown[:60]}'" + (" (rendered without t())" if raw else ""))
    if bad:
        return "fail", "; ".join(bad[:5]) + (f" (+{len(bad) - 5} more)" if len(bad) > 5 else "")
    return "pass", f"{len(items)} player texts after wording.ts t() ({len(pairs)} phrases): no restricted word left"


def c_social_modes(c: Ctx):
    if (r := need_rules(c)):
        return r
    pairs = sweeps()
    bad = []
    for m in c.g.gdef["modes"]:
        if social_hits(m["name"], pairs):
            bad.append(f"mode id '{m['name']}'")
    for m in c.rules["modes"]:
        for f in ("title", "label"):
            shown = to_sweeps(m.get(f) or "", pairs)
            if social_hits(shown, pairs):
                bad.append(f"{m['name']}.{f} '{shown}'")
    if bad:
        return "fail", "restricted word in: " + "; ".join(bad)
    return "pass", f"{len(c.rules['modes'])} mode ids, titles and labels: no restricted word in social mode"


def math_get(c: Ctx):
    st = c.stats()
    if not st or not st.get("modes"):
        return None, ("unknown", "no math results: " + str((st or {}).get("error", "no publish_files\\index.json (build the math)")))
    return st, None


def c_math(key):
    def check(c: Ctx):
        st, err = math_get(c)
        if err:
            return err
        modes = st["modes"]
        if key == "cheapest":
            low = min(m["cost"] for m in modes)
            return ("pass" if low == 1.0 else "fail"), f"cheapest mode cost {low}x"
        if key == "std":
            ones = [m for m in modes if m["cost"] == 1.0]
            bad = [f"{m['mode']} {m['std_raw']}" for m in ones if m["std_raw"] < 0.6]
            return ("fail" if bad or not ones else "pass"), ("std < 0.6: " + ", ".join(bad) if bad else "no 1.0x mode" if not ones else "std " + ", ".join(f"{m['mode']} {m['std_raw']}" for m in ones))
        if key == "rtp":
            bad = [f"{m['mode']} {m['rtp'] * 100:.2f}%" for m in modes if not RTP_BAND[0] <= m["rtp"] <= RTP_BAND[1] + 1e-9]
            return ("fail" if bad else "pass"), ("outside 96.0-96.7%: " + ", ".join(bad) if bad else "RTP " + ", ".join(f"{m['mode']} {m['rtp'] * 100:.2f}%" for m in modes))
        if key == "maxWin":
            top = max(m["max_win_x"] for m in modes)
            return ("pass" if top <= 1_000_000 else "fail"), f"highest max win {top:,.0f}x"
        if key == "cost":
            top = max(m["cost"] for m in modes)
            return ("pass" if top <= 50_000 else "fail"), f"highest mode cost {top:,.2f}x"
        if key == "books":
            bad = [m["mode"] for m in modes if not m.get("books_match_lookup")]
            return ("fail" if bad else "pass"), ("books differ from lookup: " + ", ".join(bad) if bad else f"{len(modes)} modes: books payouts = lookup")
        if key == "hitRate":
            bad = [s for s in st.get("soft_warnings", []) if "hit rate" in s]
            return ("fail" if bad else "pass"), ("; ".join(bad) if bad else "hit rate " + ", ".join(f"{m['mode']} 1 in {1 / m['hit_rate']:.1f}" for m in modes if m["hit_rate"]))
        if key == "maxWinReachable":
            bad = [s for s in st.get("soft_warnings", []) if "max win" in s]
            return ("fail" if bad else "pass"), ("; ".join(bad) if bad else "max win " + ", ".join(f"{m['mode']} 1 in {m['max_win_1_in']:,}" for m in modes if m.get("max_win_1_in")))
        if key == "sims":
            counts = []
            for m in c.index["modes"]:
                with open(c.g.publish / m["weights"], "rb") as f:
                    counts.append((m["name"], sum(1 for ln in f if ln.strip())))
            bad = [f"{n} {k:,}" for n, k in counts if not SIMS[0] <= k <= SIMS[1]]
            return ("fail" if bad else "pass"), ("outside 100k-1M: " + ", ".join(bad) if bad else ", ".join(f"{n} {k:,}" for n, k in counts))
        if key == "classes":
            cls = st.get("engine_failed_classes", [])
            return ("fail" if cls else "pass"), ("failed classes: " + ", ".join(cls) if cls else "0 failed risk classes")
        raise KeyError(key)
    return check


def c_sample_assets(c: Ctx):
    code, out = run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tools" / "check_sample_assets.ps1"), "-Game", c.g.id])
    return ("pass" if code == 0 else "fail"), f"tools\\check_sample_assets.ps1: {last_line(out)}"


def c_tiles(c: Ctx):
    tiles = c.g.skin / "tiles"
    have, missing, ratio_bad = [], [], []
    for slot, want in TILES.items():
        p = tiles / f"{slot}.png"
        if not p.exists():
            missing.append(slot)
            continue
        have.append(slot)
        try:
            from PIL import Image
            w, h = Image.open(p).size
            a, b = (int(x) for x in want.split(":"))
            if abs(w / h - a / b) > 0.02:
                ratio_bad.append(f"{slot} {w}x{h} is not {want}")
        except ImportError:
            pass
    if missing or ratio_bad:
        return "fail", "; ".join(([f"missing {rel(tiles)}\\{s}.png" for s in missing]) + ratio_bad)
    return "pass", f"{', '.join(have)} in {rel(tiles)} ({c.g.gdef and release_mode(c.g.gdef)} mode)"


def c_e2e(spec: str, pattern: str):
    def check(c: Ctx):
        ev = c.e2e()
        if not ev:
            return "unknown", "no e2e evidence: run the gate (tools\\gates\\gate.ps1) to write reports\\e2e.json"
        parts = [p for p in pattern.split(",") if p]
        if "tests" in ev:
            mine = [(f, t, s) for f, t, s in ev["tests"] if spec in Path(f).stem]
            if not mine:
                return "unknown", f"{ev['source']}: spec '{spec}' was not run"
            passed, failed, untested = [], [], []
            for p in parts:
                hits = [(t, s) for _, t, s in mine if re.search(p, t)]
                ran = [(t, s) for t, s in hits if s != "skipped"]
                failed += [t for t, s in ran if s not in ("expected", "flaky")]
                passed += [t for t, s in ran if s in ("expected", "flaky")]
                if not ran:
                    untested.append(p)
            if failed:
                return "fail", f"{ev['source']}: failed: {', '.join(failed[:4])}"
            if untested:
                return "manual", f"{ev['source']}: no e2e test for {', '.join(untested)}" + (f" (passed: {', '.join(passed[:4])})" if passed else "")
            return "pass", f"{ev['source']}: {len(passed)} test(s) passed: {', '.join(sorted(set(passed))[:4])}{' ...' if len(set(passed)) > 4 else ''}"
        step = ev["gate"]
        specs = step["step"][5:-1].split()
        if spec not in specs:
            return "unknown", f"{ev['source']}: spec '{spec}' not in that run (fast gate skips replay)"
        src = ROOT / "tools" / "e2e" / "tests" / f"{spec}.spec.ts"
        body = src.read_text(encoding="utf-8") if src.exists() else ""
        untested = []
        for p in parts:
            m = re.fullmatch(r"(\d+)x(\d+)", p)
            if m and f"[{m.group(1)}, {m.group(2)}]" not in body:
                untested.append(p)
        if step["status"] not in ("pass", "warn"):
            return "unknown", f"{ev['source']}: e2e step {step['status']} ({step.get('detail', '')}); per-test result unknown"
        if untested:
            return "manual", f"{ev['source']}: no e2e test for {', '.join(untested)}"
        return "pass", f"{ev['source']}: spec {spec} passed"
    return check


CHECKS = {
    "dist.viewport": c_dist_viewport,
    "dist.loader": c_dist_loader,
    "dist.external": c_dist_external,
    "title.terms": c_title,
    "currency": c_currency,
    "rules.rtpMaxWin": c_rules_rtp,
    "rules.modes": c_rules_modes,
    "rules.paytable": c_rules_paytable,
    "rules.features": c_rules_features,
    "rules.freeSpins": c_rules_freespins,
    "rules.buttons": c_rules_buttons,
    "rules.disclaimer": c_rules_disclaimer,
    "rules.mystery": c_rules_mystery,
    "texts.en": c_texts_en,
    "social.texts": c_social_texts,
    "social.modes": c_social_modes,
    "gate:no sample assets": c_sample_assets,
    "tiles.sources": c_tiles,
    **{f"math.{k}": c_math(k) for k in ("cheapest", "std", "rtp", "maxWin", "cost", "books", "hitRate", "maxWinReachable", "sims", "classes")},
}


def evaluate(g: Game) -> dict:
    spec = read_json(SPEC)
    srcs = spec.get("sources", {})
    c = Ctx(g)
    items = []
    for it in spec["items"]:
        key = it.get("evidence", "manual")
        if it["verify"] == "manual" or key == "manual":
            status, evidence = "manual", it.get("look", "")
        elif key.startswith("e2e:"):
            _, s, pat = key.split(":", 2)
            status, evidence = c_e2e(s, pat)(c)
        elif key in CHECKS:
            try:
                status, evidence = CHECKS[key](c)
            except Exception as e:  # a broken check must not hide the others
                status, evidence = "unknown", f"check '{key}' crashed: {type(e).__name__}: {e}"
        else:
            status, evidence = "unknown", f"no check for evidence key '{key}'"
        if status == "manual" and it["verify"] != "manual" and it.get("look"):
            evidence = f"{evidence}. Look: {it['look']}"
        items.append({"id": it["id"], "group": it["group"], "text": it["text"], "verify": it["verify"], "status": status,
                      "evidence": evidence, "source": srcs.get(it.get("source"), it.get("source", ""))})
    summary = {s: sum(1 for i in items if i["status"] == s) for s in ("pass", "fail", "manual", "unknown")}
    summary["autoFail"] = sum(1 for i in items if i["status"] == "fail" and i["verify"] != "manual")
    summary["total"] = len(items)
    return {"game": g.id, "generated": datetime.now().isoformat(timespec="seconds"), "mode": release_mode(g.gdef),
            "items": items, "summary": summary}


ICON = {"pass": "PASS", "fail": "FAIL", "manual": "LOOK", "unknown": "  ? "}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        g = Game(game_arg())
    except Exception as e:  # unknown game id
        print(f"FAIL: {e}")
        sys.exit(1)
    doc = evaluate(g)
    out = ROOT / "build" / g.id / "reports" / "stake_checklist.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    if "--json" in sys.argv:
        print(json.dumps(doc, indent=1, ensure_ascii=False))
    else:
        for i in doc["items"]:
            print(f"{ICON[i['status']]}  {i['group']:<8} {i['id']:<22} {i['evidence'][:150]}")
        s = doc["summary"]
        print(f"{'OK' if not s['autoFail'] else 'FAIL'}: checklist {g.id} ({doc['mode']} mode) -> {rel(out)}: "
              f"{s['pass']} pass, {s['fail']} fail ({s['autoFail']} auto/e2e), {s['manual']} to look at, {s['unknown']} unknown")
    sys.exit(1 if "--strict" in sys.argv and doc["summary"]["autoFail"] else 0)


if __name__ == "__main__":
    main()
