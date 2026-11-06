import random

from game_executables import GameExecutables
from game_events import update_grid_mult_event, bonus_variant_event


class GameStateOverride(GameExecutables):
    """Game-specific overrides of universal state functions."""

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.bonus_variant = None
        # Base game grid charges only within one spin's tumble chain.
        self.reset_grid_mults()

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        """Pick the bonus variant from the trigger scatter count, then run it."""
        if self.count_special_symbols(scatter_key) >= self.config.tower_scatter_min:
            self.bonus_variant = "tower"
        else:
            self.bonus_variant = "star"
        super().run_freespin_from_base(scatter_key)

    def reset_fs_spin(self):
        super().reset_fs_spin()
        self.reset_grid_mults()
        bonus_variant_event(self, self.bonus_variant)
        if self.bonus_variant == "tower":
            self.precharge_grid(self.config.tower_precharge_spots, self.config.tower_precharge_value)
        elif self.bonus_variant == "star":
            self.precharge_grid(self.config.star_precharge_spots, self.config.star_precharge_value)

    def precharge_grid(self, count, value):
        """Bonus starts with `count` random spots charged at `value`, persistent for the bonus.
        Same random.sample call as before (RNG order unchanged, M6b proof in docs/07)."""
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
