"""Generate Seventh Veil books, lookup tables, configs and stats."""

import os
import shutil

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    num_threads = 10
    rust_threads = 20
    batching_size = 50000
    compression = True
    profiling = False

    # Production counts (docs/07-math-spec.md): 1e5 in every mode (Engine guideline 100k-1M).
    num_sim_args = {
        "base": int(1e5),
        "omen": int(1e5),
        "prophecy": int(1e5),
        "star": int(1e5),
        "tower": int(1e5),
    }

    # SV_SKIP_SIMS=1 reuses existing books and only re-runs the optimizer (fast retune).
    # SV_SKIP_OPT=1 skips the Rust optimizer (determinism proof; frozen weights).
    # SV_REUSE_WEIGHTS=<dir> copies frozen lookUpTable_<mode>_0.csv from <dir> into
    # publish_files before configs are written, so index.json and config_fe use them.
    # The optimizer is not deterministic (thread_rng), so frozen weights are reused, never recomputed.
    reuse_weights = os.environ.get("SV_REUSE_WEIGHTS")
    run_conditions = {
        "run_sims": os.environ.get("SV_SKIP_SIMS") != "1",
        "run_optimization": os.environ.get("SV_SKIP_OPT") != "1" and not reuse_weights,
        "run_analysis": False,
        "run_format_checks": True,
    }
    # SV_MODES=star,tower limits the optimizer to some modes (retuning one mode).
    target_modes = os.environ.get("SV_MODES", ",".join(num_sim_args)).split(",")

    config = GameConfig()
    gamestate = GameState(config)

    # Run pins for tools\golden\snapshot.py: book order depends on threads and batching
    # (write_data.py concatenates thread x repeat), force-key order on PYTHONHASHSEED.
    if run_conditions["run_sims"]:
        import json
        import platform
        import sys
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
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    if reuse_weights:
        for mode in num_sim_args:
            src = os.path.join(reuse_weights, f"lookUpTable_{mode}_0.csv")
            if not os.path.exists(src):
                raise FileNotFoundError(f"SV_REUSE_WEIGHTS: missing {src}")
            shutil.copyfile(src, os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv"))

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        # Deterministic reshape of fresh optimizer output only (never of frozen weights).
        from game_optimization import RESHAPE
        from reshape import reshape_lookup

        for mode, spec in RESHAPE.items():
            if mode in target_modes:
                lut = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
                print(f"reshape {mode}:", reshape_lookup(lut, wincap=config.wincap, **spec))
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
