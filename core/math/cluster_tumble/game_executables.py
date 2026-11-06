from games.core_cluster_tumble.game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from games.core_cluster_tumble.game_events import update_grid_mult_event
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """Game dependent grouped functions."""

    def reset_grid_mults(self):
        """Initialize all grid position multipliers."""
        self.position_multipliers = [
            [0 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)
        ]

    def update_grid_mults(self):
        """Charged grid. A win on an empty spot marks it (1, no multiplier).
        A win on a marked spot charges it to x2; each later win doubles it up to the cap."""
        if self.win_data["totalWin"] > 0:
            cap = self.config.maximum_board_mult
            for win in self.win_data["wins"]:
                for pos in win["positions"]:
                    value = self.position_multipliers[pos["reel"]][pos["row"]]
                    if value == 0:
                        value = 1
                    elif value == 1:
                        value = 2
                    else:
                        value = min(value * 2, cap)
                    self.position_multipliers[pos["reel"]][pos["row"]] = value
            update_grid_mult_event(self)

    def get_clusters_update_wins(self):
        """Find clusters on board and update win manager."""
        clusters = Cluster.get_clusters(self.board, "wild")
        return_data = {
            "totalWin": 0,
            "wins": [],
        }
        self.board, self.win_data = self.evaluate_clusters_with_grid(
            config=self.config,
            board=self.board,
            clusters=clusters,
            pos_mult_grid=self.position_multipliers,
            global_multiplier=self.global_multiplier,
            return_data=return_data,
        )

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}
