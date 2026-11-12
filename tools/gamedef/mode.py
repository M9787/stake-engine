r"""Factory mode of one game (plan Factory v3, owner decision 2026-11-07): game.json release.mode.

    from mode import release_mode, rule_active, mode_arg
    m = release_mode(gdef)            # 'test' | 'release'; missing or unknown = 'release'
    rule_active(policy_rule, m)       # core\policy.v1.json row: "modes" lists where it applies (missing = both)

test     any assets allowed; the art rules our policy marks "modes": ["release"] (assets.test, provenance,
         humanEdit, signoff, complete) are off and not reported; no licence output. Every Stake rule still applies.
release  every rule (today's behaviour).
"""

import sys

MODES = ("test", "release")


def release_mode(gdef: dict) -> str:
    m = ((gdef or {}).get("release") or {}).get("mode")
    return m if m in MODES else "release"


def rule_active(rule: dict | None, mode: str) -> bool:
    """A policy row applies in `mode` unless its "modes" list leaves the mode out. Unknown rules apply."""
    return mode in ((rule or {}).get("modes") or MODES)


def mode_arg(gdef: dict, argv=None) -> str:
    """--mode test|release overrides game.json (used by tools\\gates\\gate.ps1); else release_mode(gdef)."""
    argv = sys.argv if argv is None else argv
    if "--mode" in argv:
        i = argv.index("--mode")
        if i + 1 >= len(argv) or argv[i + 1] not in MODES:
            sys.exit("--mode needs test or release")
        return argv[i + 1]
    return release_mode(gdef)
