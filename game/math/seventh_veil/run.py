"""Generate Seventh Veil books, lookup tables, configs and stats."""

import os

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
    run_conditions = {
        "run_sims": os.environ.get("SV_SKIP_SIMS") != "1",
        "run_optimization": True,
        "run_analysis": False,
        "run_format_checks": True,
    }
    # SV_MODES=star,tower limits the optimizer to some modes (retuning one mode).
    target_modes = os.environ.get("SV_MODES", ",".join(num_sim_args)).split(",")

    config = GameConfig()
    gamestate = GameState(config)
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

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
