"""Seventh Veil - 7x7 cluster-tumble game with a charged multiplier grid."""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Singleton Seventh Veil game configuration class."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "seventh_veil"
        self.provider_number = 0
        self.working_name = "Seventh Veil"
        self.provider_name = "seventh_veil_studio"
        self.game_name = "seventh_veil"
        self.wincap = 77777.0
        self.win_type = "cluster"
        self.rtp = 0.9650
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 7
        self.num_rows = [7] * self.num_reels

        # Paytable. H1-H4 = tarot (High Priestess, Tower, Moon, Magician),
        # L1-L4 = runes (Fehu, Ansuz, Raido, Kenaz). Clusters of 5+ pay.
        # Every pay is at least 1.2x: each hit beats the stake (no sub-stake "wins").
        # L4 appears only on the bonus reels (FR0); its pays mirror L3.
        t1, t2, t3, t4 = (5, 5), (6, 8), (9, 12), (13, 49)
        pay_group = {
            (t1, "H1"): 5.0,
            (t2, "H1"): 12.5,
            (t3, "H1"): 30.0,
            (t4, "H1"): 150.0,
            (t1, "H2"): 3.0,
            (t2, "H2"): 6.0,
            (t3, "H2"): 12.0,
            (t4, "H2"): 60.0,
            (t1, "H3"): 2.5,
            (t2, "H3"): 4.5,
            (t3, "H3"): 8.0,
            (t4, "H3"): 40.0,
            (t1, "H4"): 2.0,
            (t2, "H4"): 3.5,
            (t3, "H4"): 6.0,
            (t4, "H4"): 25.0,
            (t1, "L1"): 1.6,
            (t2, "L1"): 2.5,
            (t3, "L1"): 4.0,
            (t4, "L1"): 12.0,
            (t1, "L2"): 1.4,
            (t2, "L2"): 2.0,
            (t3, "L2"): 3.5,
            (t4, "L2"): 10.0,
            (t1, "L3"): 1.2,
            (t2, "L3"): 1.8,
            (t3, "L3"): 2.5,
            (t4, "L3"): 6.0,
            (t1, "L4"): 1.2,
            (t2, "L4"): 1.8,
            (t3, "L4"): 2.5,
            (t4, "L4"): 6.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        # S = Crystal Ball scatter. No wild in v1 (keeps clusters readable).
        self.special_symbols = {"wild": ["W"], "scatter": ["S"]}

        # Base: 3-4 scatters -> Star bonus, 5+ -> Tower bonus (see tower_scatter_min).
        self.freespin_triggers = {
            self.basegame_type: {3: 12, 4: 15, 5: 15, 6: 18, 7: 18, 8: 18},
            self.freegame_type: {3: 5, 4: 5, 5: 5, 6: 5, 7: 5, 8: 5},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }

        # Charged grid: marked -> x2 -> doubles on each hit, capped here.
        self.maximum_board_mult = 1024
        # Tower bonus: scatter count that selects it, and pre-charged spots at start.
        self.tower_scatter_min = 5
        self.tower_precharge_spots = 12
        self.tower_precharge_value = 2
        # Star bonus starts with a few charged spots too (iteration 4): lifts the weak end of
        # the Star distribution so fewer Star buys return a small fraction of their price.
        self.star_precharge_spots = 5
        # Buy floor (task 11, 2026-10-28): bought bonuses that pay less than this (x base bet) are
        # re-simulated, so the outcome pool holds no near-empty buys. Star 10x of 100x, Tower 40x of 400x.
        self.buy_floor = {"star": 10.0, "tower": 40.0}

        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        wincap = self.wincap
        fg_reels = {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}}
        cap_reels = {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1, "WCAP": 5}}
        base_only = {self.basegame_type: {"BR0": 1}}
        star_triggers = {3: 5, 4: 2}
        tower_triggers = {5: 3, 6: 1}
        any_triggers = {3: 20, 4: 6, 5: 2, 6: 1}

        def spin_mode(name, cost, quotas):
            """Fate tiers: same rules, different cost and bonus frequency."""
            q_cap, q_fg, q_zero, q_base = quotas
            return BetMode(
                name=name,
                cost=cost,
                rtp=self.rtp,
                max_win=wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=q_cap,
                        win_criteria=wincap,
                        conditions={
                            "reel_weights": cap_reels,
                            "scatter_triggers": {5: 1, 6: 1},
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=q_fg,
                        conditions={
                            "reel_weights": fg_reels,
                            "scatter_triggers": any_triggers,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=q_zero,
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": base_only,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=q_base,
                        conditions={
                            "reel_weights": base_only,
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            )

        def buy_mode(name, cost, triggers, q_cap):
            """Bonus buys: the player picks the bonus variant by picking the mode."""
            return BetMode(
                name=name,
                cost=cost,
                rtp=self.rtp,
                max_win=wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=q_cap,
                        win_criteria=wincap,
                        conditions={
                            "reel_weights": cap_reels,
                            "scatter_triggers": triggers,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=1 - q_cap,
                        conditions={
                            "reel_weights": fg_reels,
                            "scatter_triggers": triggers,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            )

        self.bet_modes = [
            spin_mode("base", 1.0, (0.001, 0.1, 0.45, 0.449)),
            spin_mode("omen", 1.25, (0.001, 0.2, 0.45, 0.349)),
            spin_mode("prophecy", 2.0, (0.001, 0.3, 0.40, 0.299)),
            buy_mode("star", 100.0, star_triggers, 0.001),
            buy_mode("tower", 400.0, tower_triggers, 0.002),
        ]
