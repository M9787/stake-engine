"""Build a math-sdk GameConfig class from a game definition (skins/<id>/game.json).

Core rule (docs/10 section 2): everything game-specific comes from game.json; this file holds
only the cluster_tumble rules (cluster pays, mode flags, distribution layout). No skin literals.

Use in a game shim (math-sdk/games/<id>/game_config.py):
    from games.core_cluster_tumble.config_builder import build
    GameConfig = build("<id>")

build() returns a class, not an instance: rgs_verification.py reads module.GameConfig and
run.py calls GameConfig(). The class is a singleton like the hand-written configs.

Attribute names match the hand-written config of skin #1 (game/math/<id>/game_config.py),
except the per-variant settings, which live in `bonus_variants` (list, scatter range order).
tools/golden/compare_config.py proves both build the same config.
"""

import json
import os
import sys
from pathlib import Path

from src.config.betmode import BetMode
from src.config.config import Config
from src.config.distributions import Distribution

FAMILY = "cluster_tumble"
WIN_TYPE = "cluster"
SPECIAL_ROLES = ("wild", "scatter")  # special_symbols key order


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "skins").is_dir() and (parent / "core").is_dir():
            return parent
    raise FileNotFoundError("repo root with skins/ and core/ not found above " + str(here))


def find_game_json(game_id: str) -> Path:
    """game.json for a game id: $CT_GAME_JSON, else the skin whose identity.gameId matches."""
    env = os.environ.get("CT_GAME_JSON")
    if env:
        return Path(env)
    for path in sorted((_repo_root() / "skins").glob("*/game.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("identity", {}).get("gameId") == game_id:
            return path
    raise FileNotFoundError(f"no skins/*/game.json with identity.gameId == {game_id!r}")


def load_definition(game_id: str) -> dict:
    gdef = json.loads(find_game_json(game_id).read_text(encoding="utf-8"))
    if gdef["core"]["family"] != FAMILY:
        raise ValueError(f"{game_id}: core family {gdef['core']['family']!r}, this core is {FAMILY!r}")
    return gdef


def _counts(table: dict) -> dict:
    return {int(k): v for k, v in table.items()}


def build(game_id: str, module: str | None = None):
    """Return the GameConfig class for `game_id`.

    `module` is the module that binds the class as `GameConfig` (default: the caller's module).
    """
    gdef = load_definition(game_id)

    class GameConfig(Config):
        """Singleton game configuration built from game.json."""

        _instance = None
        definition = gdef

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

        def __init__(self):
            super().__init__()
            ident, board, math = gdef["identity"], gdef["board"], gdef["math"]
            self.game_id = ident["gameId"]
            self.provider_number = ident["providerNumber"]
            self.working_name = ident["workingName"]
            self.provider_name = ident["providerName"]
            self.game_name = ident["gameId"]
            self.wincap = float(math["wincap"])
            self.win_type = WIN_TYPE
            self.rtp = math["rtp"]
            self.construct_paths()

            self.num_reels = board["reels"]
            self.num_rows = [board["rows"]] * self.num_reels

            # Paytable: symbol order, then band order (same insertion order as a hand-written pay_group).
            bands = [tuple(b) for b in gdef["paytable"]["bands"]]
            pay_group = {}
            for sym in gdef["symbols"]:
                if sym["role"] == "pay":
                    for band, pay in zip(bands, gdef["paytable"]["pays"][sym["id"]]):
                        pay_group[(band, sym["id"])] = float(pay)
            self.paytable = self.convert_range_table(pay_group)

            self.include_padding = board.get("includePadding", True)
            self.special_symbols = {
                role: [s["id"] for s in gdef["symbols"] if s["role"] == role] for role in SPECIAL_ROLES
            }

            self.freespin_triggers = {
                self.basegame_type: _counts(gdef["freespinTriggers"]["basegame"]),
                self.freegame_type: _counts(gdef["freespinTriggers"]["freegame"]),
            }
            self.anticipation_triggers = {
                self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
                self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
            }

            grid = gdef["features"]["gridMultiplier"]
            self.maximum_board_mult = grid["cap"] if grid["enabled"] else 1
            # Bonus variants in scatter-range order: the trigger count picks the variant.
            self.bonus_variants = [
                {
                    "id": v["id"],
                    "scatter_min": v["scatterMin"],
                    "scatter_max": v["scatterMax"],
                    "precharge_spots": v["precharge"]["spots"],
                    "precharge_value": v["precharge"]["value"],
                }
                for v in sorted(gdef["features"]["bonusVariants"], key=lambda v: v["scatterMin"])
            ]
            variant_floor = {v["id"]: v.get("buyFloor") for v in gdef["features"]["bonusVariants"]}
            self.buy_floor = {
                m["name"]: float(variant_floor[m["variant"]])
                for m in gdef["modes"]
                if m["kind"] == "buy" and variant_floor.get(m["variant"]) is not None
            }

            self.reels = {}
            for rid, fname in gdef["reels"]["files"].items():
                self.reels[rid] = self.read_reels_csv(os.path.join(self.reels_path, fname))

            weights = {
                key: {self.basegame_type if k == "basegame" else self.freegame_type: v for k, v in rw.items()}
                for key, rw in gdef["reelWeights"].items()
            }
            # cap (forced max-win books) and baseOnly (no-bonus books) default to the bonus weights fg
            # (plan v3.3 M11.3): a small skin may give one weight set only.
            weights.setdefault("cap", weights["fg"])
            weights.setdefault("baseOnly", weights["fg"])
            self.bet_modes = [self._bet_mode(m, weights) for m in gdef["modes"]]

        def _bet_mode(self, m: dict, weights: dict) -> BetMode:
            wincap = self.wincap
            q = m["quotas"]
            trig = m["scatterTriggers"]
            if m["kind"] == "spin":
                is_feature, is_buybonus = True, False
                distributions = [
                    Distribution(
                        criteria="wincap",
                        quota=q["wincap"],
                        win_criteria=wincap,
                        conditions={
                            "reel_weights": weights["cap"],
                            "scatter_triggers": _counts(trig["wincap"]),
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=q["freegame"],
                        conditions={
                            "reel_weights": weights["fg"],
                            "scatter_triggers": _counts(trig["freegame"]),
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=q["zero"],
                        win_criteria=0.0,
                        conditions={
                            "reel_weights": weights["baseOnly"],
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=q["basegame"],
                        conditions={
                            "reel_weights": weights["baseOnly"],
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ]
            else:
                is_feature, is_buybonus = False, True
                triggers = _counts(trig["all"])
                distributions = [
                    Distribution(
                        criteria="wincap",
                        quota=q["wincap"],
                        win_criteria=wincap,
                        conditions={
                            "reel_weights": weights["cap"],
                            "scatter_triggers": triggers,
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=1 - q["wincap"],
                        conditions={
                            "reel_weights": weights["fg"],
                            "scatter_triggers": triggers,
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ]
            return BetMode(
                name=m["name"],
                cost=float(m["cost"]),
                rtp=self.rtp,
                max_win=wincap,
                auto_close_disabled=False,
                is_feature=is_feature,
                is_buybonus=is_buybonus,
                distributions=distributions,
            )

    GameConfig.__qualname__ = GameConfig.__name__ = "GameConfig"
    # Pickle finds a class by module + qualname. The class is made in this function, so point
    # __module__ at the caller (the shim's game_config module, which binds GameConfig at module
    # level). Without this, Windows spawn workers fail: "Can't pickle ... GameConfig".
    GameConfig.__module__ = module or sys._getframe(1).f_globals["__name__"]
    return GameConfig
