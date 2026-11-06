from copy import deepcopy

UPDATE_GRID = "updateGrid"
BONUS_VARIANT = "bonusVariant"


def update_grid_mult_event(gamestate):
    """Pass updated position multipliers after a win.
    0 = empty, 1 = marked (sigil, no multiplier), >=2 = charged multiplier."""
    event = {
        "index": len(gamestate.book.events),
        "type": UPDATE_GRID,
        "gridMultipliers": deepcopy(gamestate.position_multipliers),
    }
    gamestate.book.add_event(event)


def bonus_variant_event(gamestate, variant: str):
    """Tell the frontend which bonus variant is starting (id from game.json)."""
    event = {
        "index": len(gamestate.book.events),
        "type": BONUS_VARIANT,
        "variant": variant,
    }
    gamestate.book.add_event(event)
