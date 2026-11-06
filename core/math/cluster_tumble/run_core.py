"""Generate books, lookup tables, configs and checks for a cluster_tumble game.

Called by the game shim (math-sdk/games/<id>/run.py):  run_core.main("<id>")
Sim counts and thread pins come from game.json math.sims / math.run.

Environment switches (CT_*; the older SV_* names still work):
  CT_SKIP_SIMS=1        reuse existing books, only re-run the optimizer (fast retune)
  CT_SKIP_OPT=1         skip the Rust optimizer (determinism proof)
  CT_REUSE_WEIGHTS=<dir> copy frozen lookUpTable_<mode>_0.csv from <dir> into publish_files before
                        configs are written (the optimizer is not deterministic: weights are frozen)
  CT_MODES=a,b          limit the optimizer to some modes
"""

import json
import os
import platform
import shutil
import sys

from games.core_cluster_tumble.gamestate import GameState
from games.core_cluster_tumble.optimization_builder import OptimizationSetup, reshape_specs
from games.core_cluster_tumble.reshape import reshape_lookup
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs
from utils.rgs_verification import execute_all_tests


def env(name: str):
    return os.environ.get(f"CT_{name}", os.environ.get(f"SV_{name}"))


def main(game_id: str, game_config_class):
    config = game_config_class()
    gdef = config.definition
    run = gdef["math"]["run"]
    num_threads = run["threads"]
    rust_threads = run.get("rustThreads", num_threads)
    batching_size = run["batching"]
    compression = True
    profiling = False
    num_sim_args = {m["name"]: int(gdef["math"]["sims"][m["name"]]) for m in gdef["modes"]}

    reuse_weights = env("REUSE_WEIGHTS")
    run_conditions = {
        "run_sims": env("SKIP_SIMS") != "1",
        "run_optimization": env("SKIP_OPT") != "1" and not reuse_weights,
        "run_format_checks": True,
    }
    target_modes = (env("MODES") or ",".join(num_sim_args)).split(",")

    gamestate = GameState(config)

    # Run pins for tools/golden/snapshot.py: book order depends on threads and batching,
    # force-key order on PYTHONHASHSEED.
    if run_conditions["run_sims"]:
        import zstandard

        os.makedirs(config.library_path, exist_ok=True)
        with open(os.path.join(config.library_path, "run_meta.json"), "w", encoding="UTF-8") as f:
            json.dump(
                {
                    "python": platform.python_version(),
                    "hash_randomization": sys.flags.hash_randomization,
                    "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
                    "zstandard": zstandard.__version__,
                    "num_threads": num_threads,
                    "batching_size": batching_size,
                    "num_sim_args": num_sim_args,
                },
                f,
                indent=2,
            )
    if run_conditions["run_optimization"]:
        from optimization_program.run_script import OptimizationExecution

        OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(gamestate, config, num_sim_args, batching_size, num_threads, compression, profiling)

    if reuse_weights:
        for mode in num_sim_args:
            src = os.path.join(reuse_weights, f"lookUpTable_{mode}_0.csv")
            if not os.path.exists(src):
                raise FileNotFoundError(f"CT_REUSE_WEIGHTS: missing {src}")
            shutil.copyfile(src, os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv"))

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        # Deterministic reshape of fresh optimizer output only (never of frozen weights).
        for mode, spec in reshape_specs(gdef["math"]["targets"]).items():
            if mode in target_modes:
                lut = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
                print(f"reshape {mode}:", reshape_lookup(lut, wincap=config.wincap, **spec))
        generate_configs(gamestate)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
