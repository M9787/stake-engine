r"""Build one game's static web folder: build\<id>\web\static (docs/10 plan v3.3, slice 10.3).

Usage:  math-sdk\env\Scripts\python.exe tools\gen\gen_web_static.py --game <gameId> [--check]

The core app serves static files from the skin (svelte.config.js kit.files.assets), so this folder
must hold everything the app loads by URL. Layers, later wins:
  1. core\web\cluster-tumble\static-core\     core files every game needs (favicon; spike rule 1)
  3. skins\<skin>\assets\                       the skin's edited, ingested finals (slice 10.6a onward)
  4. build\<id>\web\static-gen\                  generated from the skin: Howler audio sprite (tools\assets\audio.py)
Unchanged files are not rewritten; files no layer provides are removed. --check exits 1 if stale.
"""

import filecmp
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gamedef"))
from gamectx import CORE_WEB, Game, game_arg  # noqa: E402


def layers(g: Game):
    return [CORE_WEB / "static-core", g.skin / "assets", g.gen_web / "static-gen"]


def plan(g: Game) -> dict:
    """Relative path -> source file, later layers override earlier ones."""
    files = {}
    for layer in layers(g):
        if layer.exists():
            for f in sorted(layer.rglob("*")):
                if f.is_file():
                    files[f.relative_to(layer).as_posix()] = f
    return files


def main():
    g = Game(game_arg())
    out = g.gen_web / "static"
    want = plan(g)
    stale, written, removed = [], 0, 0
    for rel, src in want.items():
        dst = out / rel
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        stale.append(rel)
        if "--check" not in sys.argv:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            written += 1
    if out.exists():
        for f in sorted(out.rglob("*"), reverse=True):
            rel = f.relative_to(out).as_posix()
            if f.is_file() and rel not in want:
                stale.append(rel)
                if "--check" not in sys.argv:
                    f.unlink()
                    removed += 1
            elif f.is_dir() and "--check" not in sys.argv and not any(f.iterdir()):
                f.rmdir()
    if "--check" in sys.argv:
        print(f"{'STALE' if stale else 'OK'}: build/{g.id}/web/static ({len(want)} files, {len(stale)} stale)")
        sys.exit(1 if stale else 0)
    print(f"ok    build/{g.id}/web/static: {len(want)} files ({written} written, {removed} removed)")


if __name__ == "__main__":
    main()
