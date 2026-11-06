r"""Prove the core config builder reproduces a hand-written game config (docs/10 M7 exit).

Usage:  math-sdk\\env\\Scripts\\python.exe tools\\golden\\compare_config.py seventh_veil
Exit:   0 = identical, 1 = differences (printed), 2 = setup error.

Builds both configs inside math-sdk (same PATH_TO_GAMES, so reels are read from the same files):
- fork:    game/math/<id>/game_config.py (hand-written original; reels read from math-sdk/games/<id>/reels)
- builder: core/math/cluster_tumble/config_builder.py build(<id>) from skins/*/game.json
Every attribute is compared, in insertion order (dict order reaches the books and the FE config).
Per-variant attributes of the fork (star_* / tower_*) are checked against builder.bonus_variants.
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATH_SDK = ROOT / "math-sdk"

# Fork attribute -> (variant id, builder variant key). The fork picks "tower" from tower_scatter_min
# scatters up and "star" below it; the builder picks by scatter range.
LEGACY_VARIANT_ATTRS = {
    "tower_scatter_min": ("tower", "scatter_min"),
    "tower_precharge_spots": ("tower", "precharge_spots"),
    "tower_precharge_value": ("tower", "precharge_value"),
    "star_precharge_spots": ("star", "precharge_spots"),
    "star_precharge_value": ("star", "precharge_value"),
}
BUILDER_ONLY = {"bonus_variants", "definition"}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plain(value):
    """Comparable structure: objects -> their attributes, keys kept in order."""
    if isinstance(value, dict):
        return [(repr(k), plain(v)) for k, v in value.items()]
    if isinstance(value, (list, tuple)):
        return [type(value).__name__, [plain(v) for v in value]]
    if isinstance(value, set):
        return ["set", sorted(repr(v) for v in value)]
    if hasattr(value, "__dict__"):
        return [type(value).__name__, plain(vars(value))]
    return value


def diff(a, b, path="", out=None, limit=20):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if type(a) is not type(b):
        out.append(f"{path}: type {type(a).__name__} != {type(b).__name__}")
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append(f"{path}: {a!r} != {b!r}")
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    game_id = sys.argv[1]
    sys.path[:0] = [str(MATH_SDK)]

    fork = load_module("fork_game_config", ROOT / "game" / "math" / game_id / "game_config.py").GameConfig()
    builder_mod = load_module("ct_config_builder", ROOT / "core" / "math" / "cluster_tumble" / "config_builder.py")
    built = builder_mod.build(game_id)()

    fork_vars, built_vars = vars(fork), vars(built)
    problems = []

    variants = {v["id"]: v for v in built_vars.get("bonus_variants", [])}
    for attr, (vid, key) in LEGACY_VARIANT_ATTRS.items():
        if attr in fork_vars:
            got = variants.get(vid, {}).get(key)
            if got != fork_vars[attr]:
                problems.append(f"{attr}: fork {fork_vars[attr]!r} != builder bonus_variants[{vid}].{key} {got!r}")
    star, tower = variants.get("star"), variants.get("tower")
    if star and tower and not (star["scatter_max"] + 1 == tower["scatter_min"] == fork_vars.get("tower_scatter_min")):
        problems.append("variant selection: star range must end right below tower_scatter_min")

    fork_keys = [k for k in fork_vars if k not in LEGACY_VARIANT_ATTRS]
    built_keys = [k for k in built_vars if k not in BUILDER_ONLY]
    if fork_keys != built_keys:
        problems.append(f"attribute order/set differs:\n  fork    {fork_keys}\n  builder {built_keys}")
    for key in fork_keys:
        if key in built_vars:
            problems += diff(plain(fork_vars[key]), plain(built_vars[key]), key)

    # Optimizer setup: fork game_optimization.py vs core optimization_builder.py (+ reshape spec).
    fork_opt = load_module("fork_game_optimization", ROOT / "game" / "math" / game_id / "game_optimization.py")
    core_opt = load_module("ct_optimization_builder", ROOT / "core" / "math" / "cluster_tumble" / "optimization_builder.py")
    fork_opt.OptimizationSetup(fork)
    core_opt.OptimizationSetup(built)
    problems += diff(plain(fork.opt_params), plain(built.opt_params), "opt_params")
    fork_reshape = getattr(fork_opt, "RESHAPE", {})
    core_reshape = core_opt.reshape_specs(built.definition["math"]["targets"])
    if fork_reshape != core_reshape:
        problems.append(f"reshape: fork {fork_reshape} != builder {core_reshape}")

    if problems:
        print("DIFF", game_id)
        for p in problems:
            print(" ", p)
        sys.exit(1)
    print(f"IDENTICAL: {len(fork_keys)} attributes + {len(LEGACY_VARIANT_ATTRS)} variant settings + optimizer setup ({len(built.opt_params)} modes) + reshape ({game_id})")


if __name__ == "__main__":
    main()
