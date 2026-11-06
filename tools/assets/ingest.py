r"""Ingest the owner's asset files into a skin (docs/10 plan v3.3, slice 10.6a). One code path for the CLI
and the factory editor.

Usage (from stake\, asset venv):
  .venv-assets\Scripts\python.exe tools\assets\ingest.py --game <id> --all            every slot with a file
  .venv-assets\Scripts\python.exe tools\assets\ingest.py --game <id> --slot symbol.H1 [<file>]
Options: --no-rembg (black colour key instead of rembg), --force (re-ingest unchanged files)

Source: art_in\edited\<slot>.* (images that need a human edit), else art_in\raw\<slot>.*, or <file>.
Output (tracked, data only):
  images  skins\<skin>\assets\slots\<slot>.webp      game images, served as /slots/<slot>.webp
          skins\<skin>\tiles\<slot>.png               Engine tile and cover art (not in the game bundle)
  fonts   skins\<skin>\assets\fonts\<slot>.ttf
  audio   skins\<skin>\audio\<slot>.ogg              loudness-normalised; the Howler sprite is built on Build
  record  skins\<skin>\assets.lock.json               shas, provenance, flags (machine-written; assets.json stays hand-made)
Deterministic: inputs sorted, no metadata written, fixed encoder settings.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import ROOT, Catalog, sha256_file  # noqa: E402

sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
from gamectx import game_arg  # noqa: E402

LUFS = {"music": -16, "sfx": -12}


def load_pipeline(game_id: str):
    spec = importlib.util.spec_from_file_location("assets_build", ROOT / "scripts" / "assets_build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.apply_theme(game_id)  # palette, glow and pull strength from game.json theme
    return mod


def ingest_image(ab, slot: dict, src: Path, dst: Path, session):
    from PIL import Image

    flags = []
    with Image.open(src) as im:
        img = im.copy()
    if slot.get("cutout"):
        img = ab.trim_square(ab.cut_out(img, session))
        if ab.cutout_quality(img) > ab.BAD_CUTOUT_LIMIT:
            flags.append("bad cut-out")
    else:
        img = img.convert("RGBA")
    img, dist = ab.palette_pull(img)
    if dist > ab.OFF_STYLE_LIMIT:
        flags.append("off-style")
    w, h = slot["px"]
    if slot.get("cutout") and w == h:
        img = img.resize((w, h), Image.LANCZOS)
        img = ab.add_glow(img, w / 256)
    else:
        img = ab.cover(img, (w, h))
    if not slot.get("alpha"):
        img = img.convert("RGB")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix == ".png":
        img.save(dst, "PNG", optimize=True)
    else:
        img.save(dst, "WEBP", quality=85, method=6)
    kb = dst.stat().st_size / 1024
    if slot.get("budgetKB") and kb > slot["budgetKB"]:
        flags.append(f"over budget ({kb:.0f} KB > {slot['budgetKB']} KB)")
    return flags


def ingest_audio(slot: dict, src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    lufs = LUFS["music" if slot["kind"] == "music" else "sfx"]
    filters = f"loudnorm=I={lufs}:TP=-1.5:LRA=11"
    if slot["kind"] == "sfx":
        filters = "silenceremove=start_periods=1:start_threshold=-50dB," + filters
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-af", filters,
           "-ar", "44100", "-ac", "2", "-map_metadata", "-1", "-fflags", "+bitexact", "-c:a", "libvorbis", "-q:a", "5", str(dst)]
    subprocess.run(cmd, check=True)
    return []


def output_path(cat: Catalog, slot: dict) -> Path:
    skin = cat.game.skin
    if slot["kind"] == "image":
        if slot.get("ship") == "tile":
            return skin / "tiles" / f"{slot['id']}.png"
        return skin / "assets" / "slots" / f"{slot['id']}.webp"
    if slot["kind"] == "font":
        return skin / "assets" / "fonts" / f"{slot['id']}.ttf"
    return skin / "audio" / f"{slot['id']}.ogg"


def main():
    gid = game_arg()
    cat = Catalog(gid)
    lock_path = cat.game.skin / "assets.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {"slots": {}}
    prov = cat.provenance()
    by_id = {s["id"]: s for s in cat.slots}
    if "--slot" in sys.argv:
        sid = sys.argv[sys.argv.index("--slot") + 1]
        if sid not in by_id:
            sys.exit(f"Unknown slot '{sid}'. Slot ids are listed in build/{gid}/prompts.html.")
        explicit = None
        i = sys.argv.index("--slot") + 2
        if i < len(sys.argv) and not sys.argv[i].startswith("--"):
            explicit = Path(sys.argv[i])
        todo = [(by_id[sid], explicit)]
    elif "--all" in sys.argv:
        todo = [(s, None) for s in sorted(cat.slots, key=lambda x: x["id"])]
    else:
        sys.exit(__doc__)
    ab = session = None
    done = skipped = 0
    for slot, explicit in todo:
        if slot["required"] == "source":
            continue
        raw, edited = cat.find("raw", slot), cat.find("edited", slot)
        src = explicit or edited or raw
        if not src:
            continue
        rec = lock["slots"].get(slot["id"], {})
        src_sha = sha256_file(src)
        dst = output_path(cat, slot)
        if not ("--force" in sys.argv) and rec.get("sourceSha") == src_sha and dst.exists() and rec.get("finalSha") == sha256_file(dst):
            skipped += 1
            continue
        if slot["kind"] == "image":
            if ab is None:
                ab = load_pipeline(gid)
                if "--no-rembg" not in sys.argv:
                    try:
                        from rembg import new_session

                        session = new_session("u2net")  # same cached model as scripts\assets_build.py
                    except Exception as exc:  # noqa: BLE001 - plain message, colour key still works
                        print(f"rembg unavailable ({exc}); using the black colour key")
            flags = ingest_image(ab, slot, src, dst, session)
        elif slot["kind"] == "font":
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            flags = []
        else:
            flags = ingest_audio(slot, src, dst)
        p = prov.get(slot["id"], {})
        lock["slots"][slot["id"]] = {
            "file": dst.relative_to(cat.game.skin).as_posix(),
            "sourceSha": src_sha,
            "rawSha": sha256_file(raw) if raw else None,
            "editedSha": sha256_file(edited) if edited else None,
            "finalSha": sha256_file(dst),
            "promptSha": s_sha if (s_sha := p.get("promptSha")) else slot["promptSha"],
            "provenance": {k: p.get(k) for k in ("licence", "sourceUrl", "editNote")},
            "flags": flags,
        }
        done += 1
        print(f"ok    {slot['id']} -> {dst.relative_to(ROOT)}" + (f"  [{', '.join(flags)}]" if flags else ""))
    lock["slots"] = dict(sorted(lock["slots"].items()))
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"ingested {done}, unchanged {skipped}; record: {lock_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
