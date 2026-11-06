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
    # M6b: omen/prophecy move 0.05 RTP from the bonus into base wins (bonus odds unchanged,
    # so the "1 in 150" / "1 in 80" texts stay true; average bonus pays a little less).
    "omen": (0.008, 0.507, 150, 0.450, 5.0),
    # Iter 3: prophecy base hit 1 in 3 -> 1 in 4. At 1 in 3 the average hit is 2.7x bet vs a 2x cost,
    # so few hits beat the cost (iter 2: 3.7%). At 1 in 4 the average hit is 3.6x bet.
    # Iter 4 (1 in 5, sub-cost damp 0.05) fell back to win>cost 4.7%; final = iter 3 (1 in 4): 6.3%, session 161.
    "prophecy": (0.006, 0.509, 80, 0.450, 4.0),
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
# mode: (min_m2m, max_m2m, scaling rules). Star damps sub-50x results and lifts 50-200x to raise its median.
# M6b (owner Q28, 2026-11-06): star median target ~60x. max_m2m caps mean/median per candidate
# (optimization_program main.rs:1209-1214); star mean ~96x, so 1.7 forces a median >= ~57x.
# Results below the buy floor (game_config.buy_floor) are never simulated.
BUY_SHAPES = {
    # Iter 1 (max_m2m 1.7 alone) moved the median only 43 -> 45x: the pig check runs before scaling.
    # Iter 2: damp 10-50x harder, lift 50-200x, and damp 200-1,000x so RTP is not refilled below 20x.
    # Iter 2 -> median 45x with a hole: P(<50x)=0.59 but P(<100x)=0.61 (weight piled at 40-50x and 150-200x).
    # Iter 3: lift 50-100x hard, keep 100-200x mild.
    # Iter 3 -> 46.6x, iter 4 -> 45.7x: the optimizer pins the median just below mean/2 (main.rs:1112-1130),
    # whatever the scaling. Final: iter 2 shape (fewest results under 20x), then RESHAPE below sets the median.
    "star": (1.0, 2.0, [((10, 20), 0.05), ((20, 50), 0.25), ((50, 200), 5.0), ((200, 1000), 0.7), ((5000, 77776), 0.5)]),
    "tower": (4, 8, [((20, 50), 0.9), ((5000, 77776), 0.5)]),
}

# Base-game scaling per spin mode: (win_range in bet multiples, scale_factor).
# Base: lift 1-6x wins so more spins pay above the stake.
# M6b (owner Q28): omen (cost 1.25) and prophecy (cost 2) lift wins just above their cost and
# damp wins below it, so more spins pay more than they cost; the bonus stays the main draw.
BASE_SCALING = {
    "base": [((1, 3), 4.0), ((3, 6), 2.0)],
    # Iter 2: iter 1 (0.5 / 4.0 / 2.0) moved prophecy win>cost only 2.7% -> 3.1%.
    "omen": [((1, 1.25), 0.2), ((1.25, 3), 8.0), ((3, 6), 3.0)],
    "prophecy": [((1, 2), 0.2), ((2, 4), 8.0), ((4, 8), 3.0)],
}

# Post-optimizer reshape (reshape.py), applied only right after a fresh optimizer run, never to
# frozen weights. star (owner Q28, median ~60x): P(<60x) = 0.47, so the median is >= 60x; the
# 60-200x and 200x+ bands absorb the rest with the mean (RTP) and wincap rows unchanged.
RESHAPE = {
    # hi_from 200 was infeasible: star has almost no weight above 200x (4.6%, mean 254x) to absorb
    # the mean. At 100: 60-100x grows 2.4% -> 13.7% (fills the optimizer's 50-100x hole), 100x+ 43% -> 39%.
    # below_mass 0.47 gave a median of 74.9x (overshoots ~60x); 0.495 puts it just above 60x.
    "star": {"split": 60, "below_mass": 0.495, "hi_from": 100},
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


def buy_parameters(min_m2m=4, max_m2m=8):
    # min_m2m is a floor on mean/median: 4 pins the median near 0.25x of the buy price.
    # Star uses 1.0 so its median can move toward ~0.5-0.7x of the price.
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
                        *[
                            {"criteria": "basegame", "scale_factor": f, "win_range": r, "probability": 1.0}
                            for r, f in BASE_SCALING[mode]
                        ],
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
                        for r, f in BUY_SHAPES[mode][2]
                    ]
                ).return_dict(),
                "parameters": buy_parameters(BUY_SHAPES[mode][0], BUY_SHAPES[mode][1]),
            }
        self.game_config.opt_params = params
        verify_optimization_input(self.game_config, self.game_config.opt_params)
