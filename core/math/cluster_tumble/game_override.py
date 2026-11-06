import random

from games.core_cluster_tumble.game_executables import GameExecutables
from games.core_cluster_tumble.game_events import update_grid_mult_event, bonus_variant_event

# Abort a book after this many failed attempts in a row (hang guard, plan v3.3 C2). Skin #1's rarest
# criterion (wincap) needs far fewer; a skin that hits this has an unreachable target.
MAX_ATTEMPTS_PER_BOOK = 200_000


class GameStateOverride(GameExecutables):
    """Core overrides of universal state functions (cluster_tumble).

    Bonus variants come from game.json (config.bonus_variants, sorted by scatter range).
    RNG rule (docs/10 M8): same random.* calls, same arguments, same order as the hand-written skin #1 code,
    so a game built from the core writes the same books as its hand-written original.
    """

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.bonus_variant = None
        # Base game grid charges only within one spin's tumble chain.
        self.reset_grid_mults()

    def select_bonus_variant(self, scatter_count: int) -> dict:
        """The variant whose scatter range holds the count; below all ranges the first, above all the last."""
        variants = self.config.bonus_variants
        for variant in variants:
            if variant["scatter_min"] <= scatter_count <= variant["scatter_max"]:
                return variant
        return variants[-1] if scatter_count > variants[-1]["scatter_max"] else variants[0]

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        """Pick the bonus variant from the trigger scatter count, then run it."""
        self.bonus_variant = self.select_bonus_variant(self.count_special_symbols(scatter_key))["id"]
        super().run_freespin_from_base(scatter_key)

    def reset_fs_spin(self):
        super().reset_fs_spin()
        self.reset_grid_mults()
        bonus_variant_event(self, self.bonus_variant)
        variant = next((v for v in self.config.bonus_variants if v["id"] == self.bonus_variant), None)
        if variant and variant["precharge_spots"] > 0:
            self.precharge_grid(variant["precharge_spots"], variant["precharge_value"])

    def precharge_grid(self, count, value):
        """Bonus starts with `count` random spots charged at `value`, persistent for the bonus."""
        spots = [(r, c) for r in range(self.config.num_reels) for c in range(self.config.num_rows[r])]
        for reel, row in random.sample(spots, count):
            self.position_multipliers[reel][row] = value
        update_grid_mult_event(self)

    def assign_special_sym_function(self):
        pass

    def check_repeat(self) -> None:
        """Checks if the spin failed a criteria constraint at any point."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True

            floor = self.config.buy_floor.get(self.betmode)
            if floor is not None and self.criteria == "freegame" and self.final_win < floor:
                self.repeat = True

        # Hang guard (plan v3.3 C2): a criterion the board can hardly reach would loop for hours.
        # Counting attempts makes no RNG call, so books are unchanged.
        if self.repeat:
            self.ct_attempts = getattr(self, "ct_attempts", 0) + 1
            if self.ct_attempts > MAX_ATTEMPTS_PER_BOOK:
                raise RuntimeError(
                    f"Mode '{self.betmode}', outcome '{self.criteria}': no valid book after {MAX_ATTEMPTS_PER_BOOK:,} "
                    "attempts. The target is (nearly) unreachable on this board: lower the max win, raise its "
                    "quota, or change the reel strips."
                )
        else:
            self.ct_attempts = 0
