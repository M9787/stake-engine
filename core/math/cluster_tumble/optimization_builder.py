"""Optimizer setup (math-sdk optimization_program) built from game.json math.targets.

Same structure as the hand-written setup of skin #1 (game/math/<id>/game_optimization.py):
spin modes get wincap / 0 / freegame / basegame conditions, base-game scaling, mid-win lift and a
base-game fence bias; buy modes get wincap / freegame conditions and their own scaling.
ConstructParameters values are core presets (docs/10 section 2: optimizer internals are core).
"""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructFenceBias,
    ConstructConditions,
    verify_optimization_input,
)

# Freegame scaling for spin modes: the two midWinLift factors apply to these ranges, then a damp.
MID_WIN_RANGES = ((500, 1000), (1000, 5000))
HIGH_DAMP = ((5000, 20000), 0.8)


def spin_parameters():
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=1.1,
        max_m2m=8,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=[50, 100, 200],
        test_weights=[0.3, 0.4, 0.3],
        score_type="rtp",
    ).return_dict()


def buy_parameters(min_m2m=4, max_m2m=8):
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=min_m2m,
        max_m2m=max_m2m,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=[10, 20, 50],
        test_weights=[0.6, 0.2, 0.2],
        score_type="rtp",
    ).return_dict()


def _rule(criteria, rng, factor):
    return {"criteria": criteria, "scale_factor": factor, "win_range": tuple(rng), "probability": 1.0}


def reshape_specs(targets: dict) -> dict:
    """mode -> reshape_lookup kwargs, for modes with a post-optimizer reshape."""
    return {
        mode: {"split": t["reshape"]["split"], "below_mass": t["reshape"]["belowMass"], "hi_from": t["reshape"]["hiFrom"]}
        for mode, t in targets.items()
        if t.get("reshape")
    }


class OptimizationSetup:
    """Build per-mode optimizer conditions from game_config.definition (game.json)."""

    def __init__(self, game_config):
        self.game_config = game_config
        targets = game_config.definition["math"]["targets"]
        wincaps = {bm.get_name(): bm.get_wincap() for bm in game_config.bet_modes}
        params = {}
        for mode, t in targets.items():
            wincap = ConstructConditions(rtp=t["wincapRtp"], av_win=wincaps[mode], search_conditions=wincaps[mode]).return_dict()
            if t["kind"] == "spin":
                lift = t["midWinLift"]
                params[mode] = {
                    "conditions": {
                        "wincap": wincap,
                        "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                        "freegame": ConstructConditions(
                            rtp=t["freegameRtp"], hr=t["bonusOneIn"], search_conditions={"symbol": "scatter"}
                        ).return_dict(),
                        "basegame": ConstructConditions(hr=t["hitOneIn"], rtp=t["basegameRtp"]).return_dict(),
                    },
                    "scaling": ConstructScaling(
                        [
                            *[_rule("basegame", rng, f) for rng, f in t["baseScaling"]],
                            _rule("freegame", MID_WIN_RANGES[0], lift[0]),
                            _rule("freegame", MID_WIN_RANGES[1], lift[1]),
                            _rule("freegame", HIGH_DAMP[0], HIGH_DAMP[1]),
                        ]
                    ).return_dict(),
                    "parameters": spin_parameters(),
                    "distribution_bias": ConstructFenceBias(
                        applied_criteria=["basegame"],
                        bias_ranges=[(1.0, 2.5)],
                        bias_weights=[0.5],
                    ).return_dict(),
                }
            else:
                params[mode] = {
                    "conditions": {
                        "wincap": wincap,
                        "freegame": ConstructConditions(rtp=t["freegameRtp"], hr="x").return_dict(),
                    },
                    "scaling": ConstructScaling([_rule("freegame", rng, f) for rng, f in t["scaling"]]).return_dict(),
                    "parameters": buy_parameters(t["minM2m"], t["maxM2m"]),
                }
        self.game_config.opt_params = params
        verify_optimization_input(self.game_config, self.game_config.opt_params)
