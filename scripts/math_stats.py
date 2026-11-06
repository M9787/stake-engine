"""Per-mode math stats for a math-sdk game: RTP, hit rate, win>cost, max win, quantiles,
Engine non-critical metrics, books<->lookup payout match, event types.

Usage (from stake\\): math-sdk\\env\\Scripts\\python.exe scripts\\math_stats.py seventh_veil [--brief] [--sessions] [--raw]
--raw reads the unit-weight lookup tables (pre-optimizer pool) instead of the published weights.
--sessions adds a session-survival check for spin modes: 100 base bets start, 20,000 sessions.
"""

import json
import os
import sys

import numpy as np
import zstandard as zstd

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
GAME = ARGS[0] if ARGS else "seventh_veil"
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "math-sdk", "games", GAME)
PUB = os.path.join(ROOT, "library", "publish_files")

# Engine non-critical limits (studio.engine.io/docs/approval-guidelines/math-verification, 2026-10-28).
# One limit set for every game. Tail probabilities are raw (not scaled by cost); ETL and per-stake
# CVaR are divided by the mode cost. Std dev unit is not stated by Engine (PROJECT.md Q15): the
# pass value is std / cost; the raw std is printed beside it.
LIMITS = {
    "std_per_cost": 60.0,
    "cvar_per_stake": 700.0,
    "cvar_abs": 50_000.0,
    "p5k": 0.05,
    "p10k": 0.01,
    "p25k": 0.005,
    "p50k": 0.001,
    "p100k": 0.0005,
    "etl40": 0.9,
    "etl10k": 0.8,
    "etl_sum": 1.5,
    "etl_abs_sum": 10_000.0,
}
# Failure classes: failing several checks of one class counts once, across all modes.
CLASSES = {
    "volatility": ["std_per_cost"],
    "cvar": ["cvar_per_stake", "cvar_abs"],
    "etl": ["etl40", "etl10k", "etl_sum", "etl_abs_sum"],
    "tail_probability": ["p5k", "p10k", "p25k", "p50k", "p100k"],
}
MAX_PAYOUT_X = 100_000
MAX_COST_X = 5_000
RTP_BAND = (0.960, 0.967)

# Engine CRITICAL tests: the submission form blocks on any of these
# (stake-engine.com/docs/approval-guidelines/math-verification, fetched 2026-11-06).
CRIT_MAX_WIN_X = 1_000_000
CRIT_MAX_COST_X = 50_000
CRIT_MIN_STD_BASE = 0.6  # raw std of every 1.0x mode (at cost 1.0 raw std = std per cost)
# Engine guidance (not blocking): hit rate 1 in 50 or better, max win more often than 1 in 10M.
SOFT_MIN_HIT = 1 / 50
SOFT_MAX_WIN_1_IN = 10_000_000


def read_lookup(path):
    rows = []
    with open(path, encoding="UTF-8") as f:
        for line in f:
            sim_id, weight, payout = line.strip().split(",")
            rows.append((int(sim_id), int(weight), int(payout)))
    return rows


def read_books(path):
    payouts, types, bonus_ids = {}, set(), set()
    with open(path, "rb") as fh:
        data = zstd.ZstdDecompressor().stream_reader(fh).read().decode("utf-8")
    for line in data.splitlines():
        if not line.strip():
            continue
        book = json.loads(line)
        payouts[book["id"]] = book["payoutMultiplier"]
        for ev in book["events"]:
            types.add(ev["type"])
            if ev["type"] == "freeSpinTrigger":
                bonus_ids.add(book["id"])
    return payouts, types, bonus_ids


def cvar(dist, total, alpha=0.999):
    """Mean win in the top (1-alpha) tail."""
    tail = total * (1 - alpha)
    acc, value = 0.0, 0.0
    for win, w in sorted(dist.items(), reverse=True):
        take = min(w, tail - acc)
        if take <= 0:
            break
        value += win * take
        acc += take
    return value / tail


def mode_stats(mode):
    name, cost = mode["name"], mode["cost"]
    # Always the published (optimized) weights. --raw reads the unit-weight table in
    # library\lookup_tables instead (pre-optimizer pool). The old "newer file wins" rule
    # picked the raw table after a sims-only run (SV_SKIP_OPT / SV_REUSE_WEIGHTS), M6a 2026-11-06.
    pub_lut = os.path.join(PUB, mode["weights"])
    raw_lut = os.path.join(ROOT, "library", "lookup_tables", f"lookUpTable_{name}.csv")
    lut = raw_lut if "--raw" in sys.argv else pub_lut
    rows = read_lookup(lut)
    total = sum(w for _, w, _ in rows)
    dist = {}
    for _, w, p in rows:
        dist[p / 100] = dist.get(p / 100, 0) + w
    rtp = sum(win * w for win, w in dist.items()) / total / cost
    hit = sum(w for win, w in dist.items() if win > 0) / total
    over_cost = sum(w for win, w in dist.items() if win > cost) / total
    mean = sum(win * w for win, w in dist.items()) / total
    std = (sum((win - mean) ** 2 * w for win, w in dist.items()) / total) ** 0.5
    tail = {f"p{k}k": sum(w for win, w in dist.items() if win >= k * 1000) / total for k in (5, 10, 25, 50, 100)}
    etl40_abs = sum(win * w for win, w in dist.items() if win > 40 * cost) / total
    etl10k_abs = sum(win * w for win, w in dist.items() if win > 10000) / total
    cv = cvar(dist, total)
    metrics = {
        "std_per_cost": std / cost,
        "cvar_per_stake": cv / cost,
        "cvar_abs": cv,
        **tail,
        "etl40": etl40_abs / cost,
        "etl10k": etl10k_abs / cost,
        "etl_sum": (etl40_abs + etl10k_abs) / cost,
        "etl_abs_sum": etl40_abs + etl10k_abs,
    }
    p_at_least = {f">={x}x": sum(w for win, w in dist.items() if win >= x) / total for x in (100, 500, 1000)}
    max_win = max(dist)
    max_prob = dist[max_win] / total
    ordered = sorted(((win, w) for win, w in dist.items()), key=lambda x: x[0])
    quant = {}
    for q in (0.5, 0.9, 0.99, 0.999):
        acc = 0
        for win, w in ordered:
            acc += w
            if acc / total >= q:
                quant[q] = win
                break
    payouts, types, bonus_ids = read_books(os.path.join(PUB, mode["events"]))
    bonus_w = sum(w for i, w, _ in rows if i in bonus_ids)
    match = all(payouts.get(i) == p for i, _, p in rows) and len(payouts) == len(rows)
    fails = {k: round(v, 4) for k, v in metrics.items() if v > LIMITS[k] * (1 + 1e-9)}
    if not RTP_BAND[0] <= rtp <= RTP_BAND[1] + 1e-9:
        fails["rtp_band"] = round(rtp, 5)
    return {
        "mode": name,
        "cost": cost,
        "rtp": round(rtp, 5),
        "hit_rate": round(hit, 4),
        "win_gt_cost": round(over_cost, 4),
        "max_win_x": max_win,
        "max_win_1_in": round(1 / max_prob) if max_prob else None,
        "bonus_1_in": round(total / bonus_w, 1) if bonus_w else None,
        "quantiles_x": {str(k): v for k, v in quant.items()},
        "min_win_x": min(win for win in dist),
        "p_win_lt_20pct_cost": round(sum(w for win, w in dist.items() if win < 0.2 * cost) / total, 4),
        "p_win_lt_20x": round(sum(w for win, w in dist.items() if win < 20) / total, 4),
        "p_at_least_1_in": {k: (round(1 / v) if v else None) for k, v in p_at_least.items()},
        "std_raw": round(std, 2),
        "engine_metrics": {k: round(v, 6) for k, v in metrics.items()},
        "engine_fails": fails,
        "books_match_lookup": match,
        "event_types": sorted(types),
        "_rows": rows,
    }


def sessions(rows, cost, start=100.0, n=20000, cap=2000, seed=7):
    """Sample sessions from the weighted lookup: bet `cost` base bets per spin until bust or cap."""
    rng = np.random.default_rng(seed)
    weights = np.array([w for _, w, _ in rows], dtype=np.float64)
    wins = np.array([p / 100 for _, _, p in rows], dtype=np.float64)
    probs = weights / weights.sum()
    bal = np.full(n, start)
    alive = np.ones(n, dtype=bool)
    spins = np.full(n, cap)
    streak = np.zeros(n, dtype=np.int32)
    longest = np.zeros(n, dtype=np.int32)
    for t in range(cap):
        idx = alive.nonzero()[0]
        if idx.size == 0:
            break
        win = wins[rng.choice(len(wins), size=idx.size, p=probs)]
        bal[idx] += win - cost
        if t < 200:
            streak[idx] = np.where(win == 0, streak[idx] + 1, 0)
            longest[idx] = np.maximum(longest[idx], streak[idx])
        bust = idx[bal[idx] < cost]
        spins[bust] = t + 1
        alive[bust] = False
    return {
        "median_spins": int(np.median(spins)),
        "p_survive_200": round(float((spins >= 200).mean()), 3),
        "dead_streak_200_median": int(np.median(longest)),
        "dead_streak_200_p90": int(np.percentile(longest, 90)),
    }


def main():
    with open(os.path.join(PUB, "index.json"), encoding="UTF-8") as f:
        index = json.load(f)
    results = [mode_stats(m) for m in index["modes"]]
    failed = sorted(c for c, keys in CLASSES.items() if any(k in r["engine_fails"] for r in results for k in keys))
    if any(r["max_win_x"] > MAX_PAYOUT_X for r in results):
        failed.append("max_payout")
    if any(r["cost"] > MAX_COST_X for r in results):
        failed.append("cost_multiplier")
    critical = []
    if min(r["cost"] for r in results) != 1.0:
        critical.append("cheapest mode cost is not 1.0x")
    for r in results:
        if r["cost"] == 1.0 and r["std_raw"] < CRIT_MIN_STD_BASE:
            critical.append(f"{r['mode']}: std {r['std_raw']} < {CRIT_MIN_STD_BASE}")
        if r["max_win_x"] > CRIT_MAX_WIN_X:
            critical.append(f"{r['mode']}: max win {r['max_win_x']}x > {CRIT_MAX_WIN_X}x")
        if r["cost"] > CRIT_MAX_COST_X:
            critical.append(f"{r['mode']}: cost {r['cost']}x > {CRIT_MAX_COST_X}x")
        if not RTP_BAND[0] <= r["rtp"] <= RTP_BAND[1] + 1e-9:
            critical.append(f"{r['mode']}: rtp {r['rtp']} outside {RTP_BAND}")
        if not r["books_match_lookup"]:
            critical.append(f"{r['mode']}: books payouts do not match lookup")
    soft = []
    for r in results:
        if r["hit_rate"] < SOFT_MIN_HIT:
            soft.append(f"{r['mode']}: hit rate {r['hit_rate']} below 1 in 50")
        if r["max_win_1_in"] and r["max_win_1_in"] > SOFT_MAX_WIN_1_IN:
            soft.append(f"{r['mode']}: max win 1 in {r['max_win_1_in']} rarer than 1 in 10M")
    for r in results:
        rows = r.pop("_rows")
        if "--sessions" in sys.argv and r["cost"] < 10:
            r["sessions_100bb"] = sessions(rows, r["cost"])
    if "--brief" in sys.argv:
        for r in results:
            print(r["mode"], "rtp", r["rtp"], "hit", r["hit_rate"], ">cost", r["win_gt_cost"],
                  "max", r["max_win_x"], "1in", r["max_win_1_in"], "bonus 1in", r["bonus_1_in"], "q", r["quantiles_x"],
                  "min", r["min_win_x"], "<20x", r["p_win_lt_20x"], "1in>=", r["p_at_least_1_in"], "std", r["std_raw"],
                  "fails", r["engine_fails"], "match", r["books_match_lookup"],
                  *(["sessions", r["sessions_100bb"]] if "sessions_100bb" in r else []))
        print("engine failed classes", len(failed), failed)
        print("engine critical tests", "PASS" if not critical else f"FAIL {critical}")
        print("engine guidance", "ok" if not soft else soft)
    else:
        print(json.dumps({"modes": results, "engine_failed_classes": failed, "critical_fails": critical, "soft_warnings": soft}, indent=1))
    if critical:
        sys.exit(1)


if __name__ == "__main__":
    main()
