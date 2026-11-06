r"""Quick in-memory check: hand-written fork vs core gamestate give identical books for the same seeds.

Usage:  math-sdk\env\Scripts\python.exe tools\golden\quick_books.py seventh_veil [sims_per_criteria]
Runs in seconds and writes nothing. It is a fast signal before the full proof
(snapshot.py --verify against golden.lock.json after a full run), not a replacement for it.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "math-sdk")]

from src.wins.win_manager import WinManager  # noqa: E402


def books(gamestate_cls, config, mode, criteria_list, n):
    gs = gamestate_cls(config)
    bm = next(b for b in config.bet_modes if b.get_name() == mode)
    out = []
    sim = 0
    for crit in criteria_list:
        for _ in range(n):
            gs.win_manager = WinManager(config.basegame_type, config.freegame_type, bm.get_wincap())
            gs.library, gs.recorded_events, gs.betmode, gs.num_sims = {}, {}, mode, n
            gs.criteria = crit
            gs.run_spin(sim, None)
            out.append(json.dumps(list(gs.library.values()), sort_keys=False))
            sim += 1
    return out


def main():
    game_id = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    # Fork: bare-import modules from game/math/<id> (its own folder first on sys.path).
    sys.path.insert(0, str(ROOT / "game" / "math" / game_id))
    import game_config as fork_cfg_mod  # noqa: E402
    import gamestate as fork_gs_mod  # noqa: E402
    from games.core_cluster_tumble.config_builder import build  # noqa: E402
    from games.core_cluster_tumble.gamestate import GameState as CoreGameState  # noqa: E402

    fork_cfg = fork_cfg_mod.GameConfig()
    core_cfg = build(game_id)()
    total = bad = 0
    for bm in fork_cfg.bet_modes:
        mode = bm.get_name()
        crits = [d._criteria for d in bm._distributions]
        a = books(fork_gs_mod.GameState, fork_cfg, mode, crits, n)
        b = books(CoreGameState, core_cfg, mode, crits, n)
        diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        total += len(a)
        bad += len(diff)
        print(f"{mode:9} {len(a)} books, {len(diff)} differ" + (f" (first sim {diff[0]})" if diff else ""))
    print(("IDENTICAL" if not bad else "DIFF") + f": {total - bad}/{total} books")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
