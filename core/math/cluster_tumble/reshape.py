"""Deterministic post-optimizer reshape of one mode's published lookup weights.

Why: the math-sdk optimizer builds its "low" candidates by weighting [min, mean/2] x150 and
everything above x0.0001 (optimization_program/src/main.rs:1112-1130), so a buy mode's median
is pinned just below mean/2 (skin #1 buy bonus: ~45-48x on a ~96x mean). Scaling rules cannot move it
(M6b iterations 1-4, docs/07). This step moves weight between three payout bands while keeping
the mode's mean (RTP) and the wincap rows exactly as they are. Each band keeps its inner shape.

Bands (non-wincap rows only): L = x < split, M = split <= x < hi_from, H = x >= hi_from.
Given the target mass of L, the masses of M and H follow from total weight and mean.
Unlike the optimizer, the result is a pure function of its input: re-running it is reproducible.
"""

import csv


def _read(path):
    with open(path, encoding="UTF-8", newline="") as f:
        return [(int(i), int(w), int(p)) for i, w, p in csv.reader(f)]


def reshape_lookup(path: str, wincap: float, split: float, below_mass: float, hi_from: float) -> dict:
    rows = _read(path)
    cap_payout = round(wincap * 100)
    total = sum(w for _, w, _ in rows)

    def band(p):
        if p == cap_payout:
            return "W"
        x = p / 100
        return "L" if x < split else ("M" if x < hi_from else "H")

    mass = {b: 0 for b in "LMHW"}
    wsum = {b: 0 for b in "LMHW"}
    for _, w, p in rows:
        b = band(p)
        mass[b] += w
        wsum[b] += w * p / 100
    mu = {b: (wsum[b] / mass[b] if mass[b] else 0.0) for b in "LMHW"}
    frac = {b: mass[b] / total for b in "LMHW"}
    mean = sum(wsum.values()) / total

    # Solve the M and H fractions for the target L fraction, keeping total and mean.
    rest = 1 - frac["W"] - below_mass
    f_h = (mean - frac["W"] * mu["W"] - below_mass * mu["L"] - rest * mu["M"]) / (mu["H"] - mu["M"])
    f_m = rest - f_h
    if min(f_m, f_h, below_mass) <= 0:
        raise ValueError(f"reshape infeasible for {path}: L={below_mass} M={f_m:.4f} H={f_h:.4f}")
    factor = {"L": below_mass / frac["L"], "M": f_m / frac["M"], "H": f_h / frac["H"], "W": 1.0}

    new_rows = [(i, max(1, round(w * factor[band(p)])) if w else 0, p) for i, w, p in rows]
    with open(path, "w", encoding="UTF-8", newline="") as f:
        for i, w, p in new_rows:
            f.write(f"{i},{w},{p}\n")

    new_total = sum(w for _, w, _ in new_rows)
    new_mean = sum(w * p / 100 for _, w, p in new_rows) / new_total
    acc, median = 0, None
    for _, w, p in sorted(new_rows, key=lambda r: r[2]):
        acc += w
        if acc / new_total >= 0.5:
            median = p / 100
            break
    return {
        "mean_before": round(mean, 4),
        "mean_after": round(new_mean, 4),
        "band_fraction_before": {b: round(frac[b], 4) for b in "LMHW"},
        "band_fraction_after": {"L": below_mass, "M": round(f_m, 4), "H": round(f_h, 4), "W": round(frac["W"], 6)},
        "median_after": median,
    }
