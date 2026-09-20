#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "similarity_mechanism_download"
OUT = ROOT / "results"


def load_rows() -> list[dict]:
    rows = []
    for p in sorted(IN_DIR.glob("similarity_mechanism_*.csv")):
        with p.open() as f:
            rows.extend(csv.DictReader(f))
    if not rows:
        raise RuntimeError("no mechanism rows found")
    return rows


def clean(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        q = dict(r)
        q["seed"] = int(q["seed"])
        q["rows"] = int(q["rows"])
        q["cols"] = int(q["cols"])
        q["pe_count"] = int(q["pe_count"])
        q["sqrt_pe"] = float(q["sqrt_pe"])
        q["synth_dsp"] = int(q["synth_dsp"])
        q["route_ok"] = str(q["route_ok"]).lower() == "true"
        if q["route_ok"]:
            q["fmax_mhz"] = float(q["fmax_mhz"])
            q["period_ns"] = float(q["period_ns"])
        out.append(q)
    return out


def median_points(success: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for r in success:
        groups[(r["device"], r["topology"], r["rows"])].append(r)

    points = []
    for (dev, topo, n), rs in sorted(groups.items()):
        periods = np.asarray([r["period_ns"] for r in rs], dtype=float)
        points.append({
            "device": dev,
            "topology": topo,
            "n": n,
            "pe_count": n*n,
            "sqrt_pe": float(n),
            "seeds": len(rs),
            "median_period_ns": float(np.median(periods)),
            "mean_period_ns": float(np.mean(periods)),
            "seed_cv_pct": float(np.std(periods, ddof=1) / np.mean(periods) * 100.0) if len(periods) > 1 else 0.0,
        })
    return points


def fit_interaction(points: list[dict]) -> dict:
    y = np.asarray([p["median_period_ns"] for p in points], dtype=float)
    X = []
    for p in points:
        X.append([
            1.0 if p["device"] == "25k" else 0.0,
            1.0 if p["device"] == "45k" else 0.0,
            1.0 if p["device"] == "85k" else 0.0,
            p["sqrt_pe"],
            1.0 if p["topology"] == "local" else 0.0,
            p["sqrt_pe"] if p["topology"] == "local" else 0.0,
        ])
    X = np.asarray(X, dtype=float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    return {
        "alpha_25k": float(coef[0]),
        "alpha_45k": float(coef[1]),
        "alpha_85k": float(coef[2]),
        "broadcast_slope_ns_per_sqrt_pe": float(coef[3]),
        "local_intercept_shift_ns": float(coef[4]),
        "interaction_delta_slope_ns_per_sqrt_pe": float(coef[5]),
        "local_slope_ns_per_sqrt_pe": float(coef[3] + coef[5]),
        "rmse_ns": float(np.sqrt(np.mean((pred-y)**2))),
    }


def main() -> int:
    raw = clean(load_rows())
    success = [r for r in raw if r["route_ok"]]
    points = median_points(success)
    model = fit_interaction(points)

    all_dsp_exact = all(r["synth_dsp"] == r["pe_count"] for r in success)
    median_cv = {
        topo: float(np.median([p["seed_cv_pct"] for p in points if p["topology"] == topo]))
        for topo in ("broadcast","local")
    }

    def point(dev: str, topo: str, n: int) -> dict:
        return next(p for p in points if p["device"] == dev and p["topology"] == topo and p["n"] == n)

    b121 = point("85k","broadcast",11)["median_period_ns"]
    l121 = point("85k","local",11)["median_period_ns"]
    improvement = (b121-l121)/b121*100.0

    bs = model["broadcast_slope_ns_per_sqrt_pe"]
    ls = model["local_slope_ns_per_sqrt_pe"]
    ds = model["interaction_delta_slope_ns_per_sqrt_pe"]

    flags = {
        "route_success": len(success) >= 57,
        "dsp_exact": all_dsp_exact,
        "broadcast_slope_present": bs >= 0.50,
        "local_slope_halved": ls <= 0.50 * bs,
        "large_array_improvement": improvement >= 15.0,
        "seed_stability": median_cv["broadcast"] <= 5.0 and median_cv["local"] <= 5.0,
        "negative_interaction": ds < 0.0,
    }

    result = {
        "attempted_routes": len(raw),
        "successful_routes": len(success),
        "all_successful_dsp_exact": all_dsp_exact,
        "point_count": len(points),
        "model": model,
        "median_seed_cv_pct": median_cv,
        "85k_11x11": {
            "broadcast_period_ns": b121,
            "local_period_ns": l121,
            "local_period_improvement_pct": improvement,
        },
        "flags": flags,
        "mechanism_gate_pass": all(flags.values()),
        "claim_boundary": (
            "A pass supports operand-distribution geometry as a major mediator of the "
            "sqrt(PE) timing penalty in this controlled ECP5 INT8 MAC fabric."
        ),
    }

    combined = OUT / "similarity_mechanism_combined.csv"
    with combined.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(raw[0]))
        w.writeheader()
        w.writerows(raw)

    pp = OUT / "similarity_mechanism_points.csv"
    with pp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(points[0]))
        w.writeheader()
        w.writerows(points)

    (OUT / "similarity_mechanism_validation.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
