r"""Fail when a generated file differs from what its generator writes now (docs/10 section 2).

Usage:  math-sdk\env\Scripts\python.exe tools\gen\check_generated.py [--game <gameId>]
Exit:   0 = all generated files current, 1 = a file is stale, missing or hand-edited.

Checks: config.ts (gen_fe_config), rules.generated.en.json (gen_rules), skin.generated.ts (gen_skin_ts),
the math shim game_config.py and run.py (gen_shim). Fix a failure by rerunning the generator, never by hand.
"""

import difflib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "gamedef"))
sys.path.insert(0, str(ROOT / "tools" / "gen"))
from gamectx import Game, game_arg  # noqa: E402
import gen_rules  # noqa: E402
import gen_skin_ts  # noqa: E402


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    g = Game(game_arg())
    fe = load(ROOT / "scripts" / "gen_fe_config.py", "gen_fe_config")
    shim = load(ROOT / "tools" / "gen" / "gen_shim.py", "gen_shim")
    expected = {
        g.config_ts: (fe.render(g), "scripts/gen_fe_config.py"),
        g.gen_web / "rules.generated.en.json": (gen_rules.render(g, "en"), "tools/gen/gen_rules.py"),
        g.gen_web / "skin.generated.ts": (gen_skin_ts.render(g), "tools/gen/gen_skin_ts.py"),
    }
    game_dir = ROOT / "math-sdk" / "games" / g.id
    expected[game_dir / "game_config.py"] = (shim.GAME_CONFIG.format(skin=f"skins/{g.skin.name}", game_id=g.id), "tools/gen/gen_shim.py")
    expected[game_dir / "run.py"] = (shim.RUN.format(game_id=g.id), "tools/gen/gen_shim.py")

    bad = 0
    for path, (want, gen) in expected.items():
        rel = path.relative_to(ROOT)
        if not path.exists():
            print(f"MISSING {rel}  (run {gen} --game {g.id})")
            bad += 1
            continue
        have = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
        if have != want:
            bad += 1
            print(f"STALE   {rel}  (run {gen} --game {g.id})")
            diff = list(difflib.unified_diff(have.splitlines(), want.splitlines(), "on disk", "generator", lineterm="", n=0))
            print("\n".join(diff[:12]))
        else:
            print(f"OK      {rel}")
    print(f"{'FAIL' if bad else 'OK'}: {len(expected) - bad}/{len(expected)} generated files current for {g.id}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
