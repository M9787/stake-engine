r"""One place that maps a game id to its files (docs/10 section 1). Every tool takes --game <gameId>.

    from gamectx import Game, game_arg
    g = Game(game_arg())          # default: seventh_veil (Oracle of Sevens)

Paths:
    skin        skins/<skin>/                       game.json, text/, math/reels, math/lookups
    library     math-sdk/games/<id>/library/        math output (books, lookups, configs)
    fe_config   library/configs/config_fe_<id>.json
    gen_web     build/<id>/web/                     generated web data for the $skin alias (M10)
    web_src     core/web/cluster-tumble/src         only for games whose generated config.ts and stories
                                                    still live inside the core app (until M10 slices 10.4/10.7)
    sdk_app     web-sdk/apps/cluster-tumble/        synced copy the dev server and builds run from (one app)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GAME = "seventh_veil"
# One core web app for every game (M10 slice 10.2b). Games listed here still keep their generated
# config.ts and stories inside the core app's src (removed by slices 10.4/10.7).
CORE_WEB_APP = "cluster-tumble"
CORE_WEB = ROOT / "core" / "web" / CORE_WEB_APP
GENERATED_IN_APP: set = set()  # since M10 slice 10.7 nothing generated lives in the app source


def game_arg(argv=None, default=DEFAULT_GAME):
    argv = sys.argv if argv is None else argv
    if "--game" in argv:
        i = argv.index("--game")
        if i + 1 >= len(argv):
            sys.exit("--game needs a game id, e.g. --game seventh_veil")
        return argv[i + 1]
    return default


def find_skin(game_id: str) -> Path:
    for gpath in sorted((ROOT / "skins").glob("*/game.json")):
        g = json.loads(gpath.read_text(encoding="utf-8"))
        if g.get("identity", {}).get("gameId") == game_id:
            return gpath.parent
    known = [json.loads(p.read_text(encoding="utf-8"))["identity"]["gameId"] for p in (ROOT / "skins").glob("*/game.json")]
    sys.exit(f"No skin has identity.gameId '{game_id}'. Known games: {', '.join(sorted(known)) or 'none'}")


class Game:
    def __init__(self, game_id: str):
        self.id = game_id
        self.skin = find_skin(game_id)
        self.gdef = json.loads((self.skin / "game.json").read_text(encoding="utf-8"))
        self.library = ROOT / "math-sdk" / "games" / game_id / "library"
        self.publish = self.library / "publish_files"
        self.fe_config = self.library / "configs" / f"config_fe_{game_id}.json"
        self.gen_web = ROOT / "build" / game_id / "web"
        self.web_src = CORE_WEB / "src" if game_id in GENERATED_IN_APP else None
        self.sdk_app = ROOT / "web-sdk" / "apps" / CORE_WEB_APP

    @property
    def config_ts(self) -> Path:
        """Where config.ts goes: the $skin folder (imported as $skin/config since M10 slice 10.5)."""
        return self.gen_web / "config.ts"

    def text(self, lang: str = "en") -> dict:
        path = self.skin / "text" / f"{lang}.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def fe(self) -> dict:
        if not self.fe_config.exists():
            sys.exit(f"Math output missing: {self.fe_config.relative_to(ROOT)}. Build the math first (PROJECT.md section 7).")
        return json.loads(self.fe_config.read_text(encoding="utf-8"))
