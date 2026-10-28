"""Optimizer targets for Seventh Veil. RTP values are fractions of mode cost; they sum to 0.965 per mode."""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructFenceBias,
    ConstructConditions,
    verify_optimization_input,
)

# mode: (wincap rtp, freegame rtp, freegame hit rate "1 in N", basegame rtp, basegame hit rate)
SPIN_TARGETS = {
    # Iteration 4 rebalance: RTP moved from the bonus into base hits so sessions last longer
    # (base hit 1 in 4 = 25%, avg base win ~2.5x). Keep avg base win >= ~2.3x: lower targets
    # sit below the raw median and the optimizer fails to converge (docs/07).
    # Task 11 (2026-10-28): wincap share raised so the max win is better than 1 in 10M
    # (odds = cap rtp x cost / 77,777); prophecy bonus 1 in 80 so it averages ~90x, near a Star buy.
    "base": (0.010, 0.324, 400, 0.631, 4.0),
    "omen": (0.008, 0.557, 150, 0.400, 5.0),
    "prophecy": (0.006, 0.559, 80, 0.400, 3.0),
}
# Task 11: lift for 500-1,000x and 1,000-5,000x bonus results (stream-sized mid wins). Base needs the
# strongest lift: its pool has the fewest bonus books in that range (docs/07 Results).
MID_WIN_LIFT = {
    "base": (4.0, 15.0),
    "omen": (2.0, 4.0),
    "prophecy": (2.0, 4.0),
}
# mode: (wincap rtp, freegame rtp)
BUY_TARGETS = {
    "star": (0.005, 0.960),
    "tower": (0.0004, 0.9646),
}
# mode: (min_m2m, scaling rules). Star damps sub-50x results and lifts 50-200x to raise its median.
# Results below the buy floor (game_config.buy_floor) are never simulated.
BUY_SHAPES = {
    "star": (1.0, [((10, 20), 0.15), ((20, 50), 0.5), ((50, 200), 4.0), ((5000, 77776), 0.5)]),
    "tower": (4, [((20, 50), 0.9), ((5000, 77776), 0.5)]),
}


def spin_parameters():
    # min_m2m 1.1 (not 4): base pays start at 1.2x and average ~2x, so the base-game
    # mean-to-median ratio is ~1.2-1.7. A floor of 4 would reject every candidate.
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


def buy_parameters(min_m2m=4):
    # min_m2m is a floor on mean/median: 4 pins the median near 0.25x of the buy price.
    # Star uses 1.0 so its median can move toward ~0.5-0.7x of the price.
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=min_m2m,
        max_m2m=8,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=[10, 20, 50],
        test_weights=[0.6, 0.2, 0.2],
        score_type="rtp",
    ).return_dict()


class OptimizationSetup:
    """Build per-mode optimizer conditions."""

    def __init__(self, game_config):
        self.game_config = game_config
        wincaps = {bm.get_name(): bm.get_wincap() for bm in game_config.bet_modes}
        params = {}
        for mode, (cap_rtp, fg_rtp, fg_hr, bg_rtp, bg_hr) in SPIN_TARGETS.items():
            params[mode] = {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=cap_rtp, av_win=wincaps[mode], search_conditions=wincaps[mode]
                    ).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=fg_rtp, hr=fg_hr, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=bg_hr, rtp=bg_rtp).return_dict(),
                },
                "scaling": ConstructScaling(
                    [
                        # Lift 1-6x base wins so more spins pay above the stake.
                        {"criteria": "basegame", "scale_factor": 4.0, "win_range": (1, 3), "probability": 1.0},
                        {"criteria": "basegame", "scale_factor": 2.0, "win_range": (3, 6), "probability": 1.0},
                        # Task 11: lift 500-5,000x bonus results (stream-sized mid wins); no mid-win damping.
                        {"criteria": "freegame", "scale_factor": MID_WIN_LIFT[mode][0], "win_range": (500, 1000), "probability": 1.0},
                        {"criteria": "freegame", "scale_factor": MID_WIN_LIFT[mode][1], "win_range": (1000, 5000), "probability": 1.0},
                        {"criteria": "freegame", "scale_factor": 0.8, "win_range": (5000, 20000), "probability": 1.0},
                    ]
                ).return_dict(),
                "parameters": spin_parameters(),
                "distribution_bias": ConstructFenceBias(
                    applied_criteria=["basegame"],
                    bias_ranges=[(1.0, 2.5)],
                    bias_weights=[0.5],
                ).return_dict(),
            }
        for mode, (cap_rtp, fg_rtp) in BUY_TARGETS.items():
            params[mode] = {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=cap_rtp, av_win=wincaps[mode], search_conditions=wincaps[mode]
                    ).return_dict(),
                    "freegame": ConstructConditions(rtp=fg_rtp, hr="x").return_dict(),
                },
                "scaling": ConstructScaling(
                    [
                        {"criteria": "freegame", "scale_factor": f, "win_range": r, "probability": 1.0}
                        for r, f in BUY_SHAPES[mode][1]
                    ]
                ).return_dict(),
                "parameters": buy_parameters(BUY_SHAPES[mode][0]),
            }
        self.game_config.opt_params = params
        verify_optimization_input(self.game_config, self.game_config.opt_params)
