#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "similarity_fanout_download"
OUT = ROOT / "results"

FEATURES = ("fanout_geomean", "fanout_arithmean", "fanout_max")


def load_rows() -> list[dict]:
    rows = []
    for p in sorted(IN_DIR.glob("similarity_fanout_*.csv")):
        with p.open() as f:
            rows.extend(csv.DictReader(f))
    if not rows:
        raise RuntimeError("no fanout rows found")
    return rows


def clean(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        q = dict(r)
        for k in ("n", "seed", "a_fanout", "b_fanout", "pe_count",
                  "fanout_product", "synth_dsp"):
            q[k] = int(q[k])
        for k in ("fanout_geomean", "fanout_arithmean", "fanout_max"):
            q[k] = float(q[k])
        q["route_ok"] = str(q["route_ok"]).lower() == "true"
        if q["route_ok"]:
            q["fmax_mhz"] = float(q["fmax_mhz"])
            q["period_ns"] = float(q["period_ns"])
        out.append(q)
    return out


def median_points(success: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for r in success:
        groups[(r["n"], r["a_fanout"], r["b_fanout"])].append(r)

    points = []
    for (n, fa, fb), rs in sorted(groups.items()):
        periods = np.asarray([r["period_ns"] for r in rs], dtype=float)
        points.append({
            "n": n,
            "a_fanout": fa,
            "b_fanout": fb,
            "pe_count": n*n,
            "fanout_product": fa*fb,
            "fanout_geomean": float(np.sqrt(fa*fb)),
            "fanout_arithmean": 0.5*(fa+fb),
            "fanout_max": max(fa,fb),
            "seeds": len(rs),
            "median_period_ns": float(np.median(periods)),
            "mean_period_ns": float(np.mean(periods)),
            "seed_cv_pct": (
                float(np.std(periods, ddof=1)/np.mean(periods)*100.0)
                if len(periods) > 1 else 0.0
            ),
        })
    return points


def fit(points: list[dict], feature: str) -> np.ndarray:
    X = np.asarray(
        [[1.0, float(p["n"]), float(p[feature])] for p in points],
        dtype=float,
    )
    y = np.asarray([p["median_period_ns"] for p in points], dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def predict(points: list[dict], feature: str, coef: np.ndarray) -> np.ndarray:
    X = np.asarray(
        [[1.0, float(p["n"]), float(p[feature])] for p in points],
        dtype=float,
    )
    return X @ coef


def rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        ranks[order[i:j]] = (i+j-1)/2.0 + 1.0
        i = j
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rank(a), rank(b)
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 1.0 if np.allclose(ra, rb) else 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def evaluate(points: list[dict], feature: str, coef: np.ndarray) -> dict:
    actual = np.asarray([p["median_period_ns"] for p in points], dtype=float)
    pred = predict(points, feature, coef)
    ape = np.abs((pred-actual)/actual)*100.0
    return {
        "n": len(points),
        "mape_pct": float(np.mean(ape)),
        "max_ape_pct": float(np.max(ape)),
        "signed_bias_pct": float(np.mean((pred-actual)/actual)*100.0),
        "spearman": spearman(actual, pred),
        "within_10pct_fraction": float(np.mean(ape <= 10.0)),
    }


def swap_differences(points: list[dict]) -> list[float]:
    lookup = {(p["n"], p["a_fanout"], p["b_fanout"]): p for p in points}
    diffs = []
    seen = set()
    for p in points:
        key = (p["n"], p["a_fanout"], p["b_fanout"])
        rev = (p["n"], p["b_fanout"], p["a_fanout"])
        if key in seen or rev not in lookup or key == rev:
            continue
        q = lookup[rev]
        denom = 0.5*(p["median_period_ns"] + q["median_period_ns"])
        diffs.append(abs(p["median_period_ns"]-q["median_period_ns"])/denom*100.0)
        seen.add(key)
        seen.add(rev)
    return diffs


def equal_product_spreads(points: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for p in points:
        groups[(p["n"], p["fanout_product"])].append(p)
    out = []
    for (n, product), ps in sorted(groups.items()):
        if len(ps) < 2:
            continue
        vals = np.asarray([p["median_period_ns"] for p in ps], dtype=float)
        spread = (float(np.max(vals))-float(np.min(vals)))/float(np.median(vals))*100.0
        out.append({
            "n": n,
            "fanout_product": product,
            "group_size": len(ps),
            "spread_pct": spread,
        })
    return out


def extreme_penalties(points: list[dict]) -> dict:
    lookup = {(p["n"], p["a_fanout"], p["b_fanout"]): p for p in points}
    out = {}
    for n in (6, 8, 10):
        lo = lookup[(n,1,1)]["median_period_ns"]
        hi = lookup[(n,n,n)]["median_period_ns"]
        out[str(n)] = {
            "low_period_ns": lo,
            "high_period_ns": hi,
            "penalty_pct": (hi/lo-1.0)*100.0,
        }
    return out


def main() -> int:
    raw = clean(load_rows())
    success = [r for r in raw if r["route_ok"]]
    points = median_points(success)

    discovery = [p for p in points if p["n"] in (6,8)]
    heldout = [p for p in points if p["n"] == 10]

    models = {}
    for feature in FEATURES:
        coef = fit(discovery, feature)
        models[feature] = {
            "coefficients": {
                "intercept": float(coef[0]),
                "n_slope": float(coef[1]),
                "feature_slope": float(coef[2]),
            },
            "discovery": evaluate(discovery, feature, coef),
            "heldout": evaluate(heldout, feature, coef),
        }

    swaps = swap_differences(points)
    product_groups = equal_product_spreads(points)
    penalties = extreme_penalties(points)

    median_seed_cv = float(np.median([p["seed_cv_pct"] for p in points]))
    median_swap = float(np.median(swaps)) if swaps else float("inf")
    median_product_spread = (
        float(np.median([g["spread_pct"] for g in product_groups]))
        if product_groups else float("inf")
    )

    exact_dsp = all(r["synth_dsp"] == r["pe_count"] for r in success)

    gm = models["fanout_geomean"]
    am = models["fanout_arithmean"]
    mx = models["fanout_max"]

    flags = {
        "route_success": len(success) >= 138,
        "dsp_exact": exact_dsp,
        "seed_stability": median_seed_cv <= 5.0,
        "discovery_geomean_mape": gm["discovery"]["mape_pct"] <= 6.0,
        "heldout_geomean_mape": gm["heldout"]["mape_pct"] <= 8.0,
        "geomean_beats_alternatives": (
            gm["heldout"]["mape_pct"] < am["heldout"]["mape_pct"]
            and gm["heldout"]["mape_pct"] < mx["heldout"]["mape_pct"]
        ),
        "heldout_rank": gm["heldout"]["spearman"] >= 0.75,
        "positive_geomean_slope": gm["coefficients"]["feature_slope"] > 0.0,
        "swap_symmetry": median_swap <= 4.0,
        "equal_product_invariance": median_product_spread <= 6.0,
        "intervention_magnitude": all(
            penalties[str(n)]["penalty_pct"] >= 8.0 for n in (6,8,10)
        ),
    }

    result = {
        "attempted_routes": len(raw),
        "successful_routes": len(success),
        "point_count": len(points),
        "discovery_sizes": [6,8],
        "heldout_size": 10,
        "models": models,
        "median_seed_cv_pct": median_seed_cv,
        "median_abs_swap_difference_pct": median_swap,
        "equal_product_groups": product_groups,
        "median_equal_product_spread_pct": median_product_spread,
        "extreme_fanout_penalties": penalties,
        "flags": flags,
        "cross_fanout_gate_pass": all(flags.values()),
        "claim_boundary": (
            "A pass supports geometric-mean orthogonal operand fanout as a causal "
            "predictor of routed critical period in this controlled ECP5 INT8 MAC family."
        ),
    }

    with (OUT/"similarity_fanout_combined.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(raw[0]))
        w.writeheader()
        w.writerows(raw)

    with (OUT/"similarity_fanout_points.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(points[0]))
        w.writeheader()
        w.writerows(points)

    (OUT/"similarity_fanout_validation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
