r"""Render every asset slot's generation prompt for one game (docs/10 plan v3.3, slice 0).

Usage (from stake\, any Python 3.12):
  python tools\assets\prompts.py --game seventh_veil          writes build\<id>\prompts.json + prompts.html
  python tools\assets\prompts.py --game seventh_veil --check  lint only; exit 1 on any problem

prompts.html is self-contained for the owner: one card per slot grouped by sitting, a Copy button per
prompt, tool steps, file names, the human-edit recipe, and a provenance line per slot (licence, source
URL, edit note) plus minutes per sitting. "Save provenance.json" downloads the lines; put the file in
skins\<skin>\art_in\provenance.json. tools\assets\check_art_in.py reads it.
"""

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, Catalog, lint  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402


def slot_json(cat: Catalog, s: dict) -> dict:
    tool = cat.tool(s)
    raw, edited = cat.find("raw", s), cat.find("edited", s)
    return {
        "id": s["id"],
        "kind": s["kind"],
        "sitting": s["sitting"],
        "required": s["required"],
        "px": s.get("px"),
        "aspect": s.get("aspect"),
        "alpha": s.get("alpha"),
        "variants": s.get("variants"),
        "tool": s.get("tool"),
        "toolLabel": tool.get("label", ""),
        "toolUrl": tool.get("url", ""),
        "steps": tool.get("steps", []),
        "licenceDefault": tool.get("licence", ""),
        "humanEdit": tool.get("humanEdit", "optional"),
        "editRecipe": cat.core["editRecipes"].get(s.get("editRecipe") or "", []),
        "source": s["skin"].get("source", ""),
        "prompt": s["promptFull"],
        "promptSha": s["promptSha"],
        "feeds": s.get("feeds", []),
        "files": {"raw": f"art_in/raw/{s['fileStem']}.<ext>", "edited": f"art_in/edited/{s['fileStem']}.<ext>"},
        "have": {"raw": raw.name if raw else None, "edited": edited.name if edited else None},
    }


CSS = """
body{font:14px/1.45 system-ui,sans-serif;margin:0;background:#14111f;color:#ece8f6}
header{position:sticky;top:0;background:#1d1830;padding:10px 18px;border-bottom:1px solid #3a3157;z-index:2}
h1{font-size:18px;margin:0 0 4px} h2{margin:28px 18px 6px;font-size:17px}
.note{color:#b9b0d4;margin:0 18px 10px} .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:12px;padding:0 18px}
.card{background:#1f1a33;border:1px solid #3a3157;border-radius:8px;padding:12px}
.card.done{border-color:#4f9a5d} .id{font-weight:700;font-size:15px} .meta{color:#b9b0d4;font-size:12px;margin:2px 0 8px}
textarea{width:100%;box-sizing:border-box;background:#120f1d;color:#ece8f6;border:1px solid #3a3157;border-radius:6px;font:12px/1.4 ui-monospace,monospace;padding:6px}
button{background:#d4a845;color:#1b1446;border:0;border-radius:6px;padding:5px 10px;font-weight:700;cursor:pointer}
input,select{background:#120f1d;color:#ece8f6;border:1px solid #3a3157;border-radius:4px;padding:3px 5px;width:100%;box-sizing:border-box}
label{display:block;font-size:12px;color:#b9b0d4;margin-top:6px} ol{margin:4px 0 4px 18px;padding:0;color:#d6d0ea}
.req{color:#e9b949} .opt{color:#8fa0b8} .ok{color:#6fcf7f} .miss{color:#e07a6f} code{color:#e9d9a6}
"""

JS = """
const KEY='prov:'+GAME;
const state=JSON.parse(localStorage.getItem(KEY)||'{"slots":{},"minutes":{}}');
function save(){localStorage.setItem(KEY,JSON.stringify(state));}
document.querySelectorAll('[data-copy]').forEach(b=>b.onclick=()=>{navigator.clipboard.writeText(document.getElementById(b.dataset.copy).value);b.textContent='Copied';setTimeout(()=>b.textContent='Copy prompt',1200);});
document.querySelectorAll('[data-slot]').forEach(el=>{const s=el.dataset.slot,f=el.dataset.field;state.slots[s]=state.slots[s]||{};
 if(state.slots[s][f]!==undefined)el.value=state.slots[s][f]; else if(el.dataset.default){el.value=el.dataset.default;}
 el.oninput=()=>{state.slots[s][f]=el.value;save();};});
document.querySelectorAll('[data-minutes]').forEach(el=>{const k=el.dataset.minutes;if(state.minutes[k]!==undefined)el.value=state.minutes[k];el.oninput=()=>{state.minutes[k]=el.value;save();};});
document.getElementById('export').onclick=()=>{
 const out={game:GAME,savedAt:new Date().toISOString(),minutes:state.minutes,slots:{}};
 for(const [k,v] of Object.entries(state.slots)){ if(Object.values(v).some(x=>x)) out.slots[k]={...v,promptSha:SHAS[k]}; }
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:'application/json'}));
 a.download='provenance.json';a.click();};
"""


def write_html(cat: Catalog, data: dict, path: Path):
    e = html.escape
    sittings = {s["id"]: s for s in cat.core["sittings"]}
    suno = sum(1 for s in data["slots"] if s["tool"] == "suno")
    out = [f"<!doctype html><meta charset=utf-8><title>Asset prompts: {e(data['displayName'])}</title><style>{CSS}</style>",
           f"<header><h1>Asset prompts: {e(data['displayName'])} ({e(data['game'])})</h1>"
           f"<div>Save each download as <code>art_in/raw/&lt;slot&gt;.&lt;ext&gt;</code>, your edited image as "
           f"<code>art_in/edited/&lt;slot&gt;.png</code>. Fill the provenance line on each card, then "
           f"<button id=export>Save provenance.json</button> into <code>{e(str(cat.art_in.relative_to(ROOT)))}\\</code>. "
           f"Suno downloads needed: {suno} (plan limit {cat.tools['suno'].get('monthlyDownloads', '?')}/month).</div></header>"]
    for sid in sorted({s["sitting"] for s in data["slots"]}):
        sit = sittings.get(sid, {"title": f"Sitting {sid}", "note": "", "minutes": ""})
        out.append(f"<h2>Sitting {sid}: {e(sit['title'])} (about {sit['minutes']} min) "
                   f"<span style='font-size:12px;font-weight:400'>minutes spent <input style='width:60px' data-minutes='{sid}'></span></h2>"
                   f"<p class=note>{e(sit['note'])}</p><div class=grid>")
        for s in [x for x in data["slots"] if x["sitting"] == sid]:
            done = s["have"]["raw"] and (s["have"]["edited"] or s["humanEdit"] != "required")
            req = "<span class=req>required</span>" if s["required"] == "ship" else f"<span class=opt>{e(s['required'])}</span>"
            size = f"{s['px'][0]}x{s['px'][1]} px" if s.get("px") else ""
            alpha = "transparent" if s.get("alpha") else ""
            feeds = f"<div class=meta>feeds: {e(', '.join(s['feeds']))}</div>" if s["feeds"] else ""
            have = (f"<span class=ok>raw: {e(s['have']['raw'])}</span>" if s["have"]["raw"] else "<span class=miss>raw: missing</span>")
            if s["humanEdit"] == "required":
                have += " · " + (f"<span class=ok>edited: {e(s['have']['edited'])}</span>" if s["have"]["edited"] else "<span class=miss>edited: missing</span>")
            steps = "".join(f"<li>{e(x.replace('<slot>', s['id']))}</li>" for x in s["steps"])
            recipe = ("<label>Human edit in Photopea (required for images)</label><ol>" + "".join(f"<li>{e(x)}</li>" for x in s["editRecipe"]) + "</ol>") if s["editRecipe"] else ""
            source = f"<div class=meta>source: {e(s['source'])}</div>" if s["source"] else ""
            tid = "p_" + s["id"].replace(".", "_")
            out.append(
                f"<div class='card{' done' if done else ''}'><div class=id>{e(s['id'])} {req}</div>"
                f"<div class=meta>{e(s['kind'])} {size} {alpha} · {e(s['toolLabel'])}"
                f"{' · make ' + str(s['variants']) + ', pick 1' if s.get('variants') else ''} · {have}</div>{feeds}{source}"
                f"<textarea id={tid} rows=4 readonly>{e(s['prompt'])}</textarea> <button data-copy={tid}>Copy prompt</button>"
                f"{' <a href=' + e(s['toolUrl']) + ' target=_blank>open tool</a>' if s['toolUrl'] else ''}"
                f"<ol>{steps}</ol>{recipe}"
                f"<label>Licence</label><select data-slot='{e(s['id'])}' data-field=licence data-default='{e(s['licenceDefault'])}'>"
                + "".join(f"<option>{e(x)}</option>" for x in data["licences"]) +
                f"</select><label>Source URL (Midjourney job link, Suno song link or sound page)</label>"
                f"<input data-slot='{e(s['id'])}' data-field=sourceUrl>"
                f"<label>What you changed (human edit note)</label><input data-slot='{e(s['id'])}' data-field=editNote>"
                f"<label>Redo? (leave empty if fine)</label><input data-slot='{e(s['id'])}' data-field=redo></div>")
        out.append("</div>")
    shas = {s["id"]: s["promptSha"] for s in data["slots"]}
    out.append(f"<script>const GAME={json.dumps(data['game'])};const SHAS={json.dumps(shas)};{JS}</script>")
    path.write_text("".join(out), encoding="utf-8")


def main():
    gid = game_arg()
    cat = Catalog(gid)
    problems = lint(cat)
    for sid, msg in problems:
        print(f"PROBLEM {sid}: {msg}")
    if "--check" in sys.argv:
        print(f"{'OK' if not problems else 'FAIL'}: {len(cat.slots)} slots, {len(problems)} problem(s)")
        sys.exit(1 if problems else 0)
    licences = sorted(set(cat.core["imageLicences"] + cat.core["audioLicences"] + cat.core["fontLicences"]))
    data = {
        "game": gid,
        "displayName": cat.game.gdef["identity"]["displayName"],
        "licences": licences,
        "slots": [slot_json(cat, s) for s in cat.slots],
    }
    out = ROOT / "build" / gid
    out.mkdir(parents=True, exist_ok=True)
    (out / "prompts.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    write_html(cat, data, out / "prompts.html")
    req = [s for s in data["slots"] if s["required"] == "ship"]
    have = [s for s in req if s["have"]["raw"]]
    print(f"wrote build/{gid}/prompts.json + prompts.html: {len(data['slots'])} slots, {len(req)} required, {len(have)} with a raw file")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
