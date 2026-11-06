r"""Asset-slot catalogue for one game: core slots (core/assets/slots.v1.json) expanded with the skin's
game.json and filled with the skin's style bible and prompts (skins/<skin>/assets.json).

    from catalog import Catalog
    cat = Catalog("seventh_veil")
    for slot in cat.slots: print(slot["id"], slot["promptFull"])

Docs: docs/10 plan v3.3 section 3. Standard library only.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import Game  # noqa: E402

CATALOGUE = ROOT / "core" / "assets" / "slots.v1.json"
TOOLS = ROOT / "core" / "assets" / "tools.v1.json"
TOKEN = re.compile(r"\{([A-Za-z0-9_.]+)\}")
AR_FLAG = re.compile(r"\s*--ar\s+\d+:\d+")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
AUDIO_EXT = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aiff")
FONT_EXT = (".ttf", ".otf")
EXT = {"image": IMAGE_EXT, "music": AUDIO_EXT, "sfx": AUDIO_EXT, "font": FONT_EXT}


def _lookup(ctx: dict, path: str):
    cur = ctx
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur if isinstance(cur, (str, int, float)) else None


def render(template: str, ctx: dict) -> str:
    """Fill {a.b.c} tokens, innermost first, so {style.motifs.{symbol.tier}} works. Unknown tokens stay."""
    for _ in range(5):
        changed = False

        def sub(m):
            nonlocal changed
            val = _lookup(ctx, m.group(1))
            if val is None:
                return m.group(0)
            changed = True
            return str(val)

        template = TOKEN.sub(sub, template)
        if not changed:
            break
    return template


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Catalog:
    def __init__(self, game_id: str):
        self.game = Game(game_id)
        self.core = json.loads(CATALOGUE.read_text(encoding="utf-8"))
        self.tools = json.loads(TOOLS.read_text(encoding="utf-8"))["tools"]
        apath = self.game.skin / "assets.json"
        self.skin_assets = json.loads(apath.read_text(encoding="utf-8")) if apath.exists() else {"style": {}, "slots": {}}
        self.style = self.skin_assets.get("style", {})
        self.text = self.game.text("en")
        self.art_in = self.game.skin / "art_in"
        self.slots = self._expand()

    # ---- expansion -------------------------------------------------------------------------
    def _items(self, expand: str):
        g = self.game.gdef
        if expand == "symbols:pay":
            return [{"symbol": self._sym(s)} for s in g["symbols"] if s.get("role") == "pay"]
        if expand == "symbols:scatter":
            return [{"symbol": self._sym(s)} for s in g["symbols"] if s.get("role") == "scatter"]
        if expand == "variants":
            variants = g.get("features", {}).get("bonusVariants") or g.get("bonusVariants") or []
            return [{"variant": {"id": v["id"]}} for v in variants]
        raise ValueError(f"unknown expand '{expand}' in {CATALOGUE.name}")

    def _sym(self, s: dict) -> dict:
        return {"id": s["id"], "tier": s.get("tier", s.get("role")), "name": self.text.get(s.get("nameKey", ""), s["id"])}

    def _expand(self):
        out = []
        for raw in self.core["slots"]:
            items = self._items(raw["expand"]) if raw.get("expand") else [{}]
            for item in items:
                ctx = {"style": self.style, "text": self.text, **item}
                slot = {k: v for k, v in raw.items() if k != "expand"}
                slot["id"] = render(raw["id"], ctx)
                skin = self.skin_assets.get("slots", {}).get(slot["id"], {})
                slot["skin"] = skin
                slot["tool"] = skin.get("tool", raw.get("tool"))
                slot["promptBase"] = skin.get("prompt") or render(raw["prompt"], ctx)
                slot["promptFull"] = self._full_prompt(slot)
                slot["promptSha"] = hashlib.sha256(slot["promptFull"].encode("utf-8")).hexdigest()[:12]
                slot["fileStem"] = slot["id"]
                out.append(slot)
        return out

    def _full_prompt(self, slot: dict) -> str:
        base = AR_FLAG.sub("", slot["promptBase"]).strip()
        if slot["kind"] != "image":
            return base
        parts = [base]
        if slot.get("cutout") and self.style.get("cutout"):
            parts.append(", " + self.style["cutout"])
        parts.append(self.style.get("suffix", ""))
        full = "".join(parts)
        if slot.get("aspect"):
            full += f" --ar {slot['aspect']}"
        if slot.get("sref", True) and self.style.get("sref"):
            full += f" --sref {self.style['sref']}"
        return full

    # ---- files in art_in -------------------------------------------------------------------
    def find(self, lane: str, slot: dict):
        """art_in/<lane>/<slot id>.<ext> for lane raw|edited, or None."""
        folder = self.art_in / lane
        for ext in EXT[slot["kind"]]:
            p = folder / f"{slot['fileStem']}{ext}"
            if p.exists():
                return p
        return None

    def provenance(self) -> dict:
        p = self.art_in / "provenance.json"
        return json.loads(p.read_text(encoding="utf-8")).get("slots", {}) if p.exists() else {}

    def tool(self, slot: dict) -> dict:
        return self.tools.get(slot.get("tool") or "", {})


def best_file(cat: "Catalog", s: dict):
    return cat.find("edited", s) or cat.find("raw", s)


def asset_set_hash(cat: "Catalog") -> str:
    h = hashlib.sha256()
    for s in sorted(cat.slots, key=lambda x: x["id"]):
        f = best_file(cat, s)
        h.update(f"{s['id']}={sha256_file(f) if f else '-'}\n".encode())
    return h.hexdigest()


def lint(cat: Catalog):
    """Prompt problems in plain language: list of (slot id, message)."""
    problems = []
    ids = [s["id"] for s in cat.slots]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append((dup, "slot id appears twice"))
    for s in cat.slots:
        left = TOKEN.findall(s["promptFull"])
        if left:
            problems.append((s["id"], f"prompt has unfilled fields {left}: add them to the style bible in assets.json"))
        if s["kind"] == "image":
            if re.search(r"[\"“”]", s["promptBase"]):
                problems.append((s["id"], "image prompt contains quoted words; Midjourney would draw them as text"))
            if "no text" not in s["promptFull"]:
                problems.append((s["id"], "image prompt does not end with 'no text' (style suffix missing)"))
        if re.search(r"\bstake\b", s["promptFull"], re.I):
            problems.append((s["id"], "prompt names a real brand (Stake)"))
        if s.get("tool") and s["tool"] not in cat.tools:
            problems.append((s["id"], f"unknown tool '{s['tool']}'"))
        if cat.tools.get(s.get("tool") or "", {}).get("blocked"):
            problems.append((s["id"], f"tool '{s['tool']}' is blocked until {cat.tools[s['tool']]['blocked']} closes"))
    known = set(ids)
    for extra in sorted(set(cat.skin_assets.get("slots", {})) - known):
        problems.append((extra, "assets.json has a slot the core catalogue does not know (typo?)"))
    return problems
