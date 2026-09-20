#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "similarity_arithmetic_download"
OUT = ROOT / "results"


def load_rows() -> list[dict]:
    rows = []
    for p in sorted(IN_DIR.glob("similarity_arithmetic_*.csv")):
        with p.open() as f:
            rows.extend(csv.DictReader(f))
    if not rows:
        raise RuntimeError("no arithmetic replication rows found")
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
        groups[(r["device"], r["backend"], r["rows"])].append(r)
    points = []
    for (dev, backend, n), rs in sorted(groups.items()):
        periods = np.asarray([r["period_ns"] for r in rs], dtype=float)
        points.append({
            "device": dev,
            "backend": backend,
            "n": n,
            "pe_count": n*n,
            "sqrt_pe": float(n),
            "seeds": len(rs),
            "median_period_ns": float(np.median(periods)),
            "mean_period_ns": float(np.mean(periods)),
            "seed_cv_pct": float(np.std(periods, ddof=1)/np.mean(periods)*100.0) if len(periods)>1 else 0.0,
        })
    return points


def fit(train: list[dict], feature: str) -> tuple[float,float]:
    x = np.asarray([float(p[feature]) for p in train], dtype=float)
    y = np.asarray([float(p["median_period_ns"]) for p in train], dtype=float)
    X = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(coef[0]), float(coef[1])


def evaluate(points: list[dict], coef: tuple[float,float], feature: str) -> dict:
    a,b = coef
    actual = np.asarray([p["median_period_ns"] for p in points], dtype=float)
    pred = np.asarray([a + b*float(p[feature]) for p in points], dtype=float)
    ape = np.abs((pred-actual)/actual)*100.0
    spe = (pred-actual)/actual*100.0
    return {
        "n": len(points),
        "mape_pct": float(np.mean(ape)),
        "signed_bias_pct": float(np.mean(spe)),
        "max_ape_pct": float(np.max(ape)),
        "within_10pct_fraction": float(np.mean(ape <= 10.0)),
    }


def exponent_scan(points: list[dict]) -> dict:
    pe = np.asarray([p["pe_count"] for p in points], dtype=float)
    y = np.asarray([p["median_period_ns"] for p in points], dtype=float)
    best = None
    for power in np.linspace(0.10,1.00,91):
        x = pe ** power
        X = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(X,y,rcond=None)
        pred = X @ coef
        mape = float(np.mean(np.abs((pred-y)/y))*100.0)
        item={"p":float(power),"intercept":float(coef[0]),"slope":float(coef[1]),"mape_pct":mape}
        if best is None or mape < best["mape_pct"]:
            best=item
    return best


def main() -> int:
    raw = clean(load_rows())
    success = [r for r in raw if r["route_ok"]]
    points = median_points(success)

    backends={}
    flags={}
    for backend in ("dsp","lut"):
        p_backend=[p for p in points if p["backend"]==backend]
        train=[p for p in p_backend if p["device"]=="45k"]
        h25=[p for p in p_backend if p["device"]=="25k"]
        h85=[p for p in p_backend if p["device"]=="85k"]

        sqrt_coef=fit(train,"sqrt_pe")
        linear_coef=fit(train,"pe_count")
        sqrt25=evaluate(h25,sqrt_coef,"sqrt_pe")
        sqrt85=evaluate(h85,sqrt_coef,"sqrt_pe")
        lin25=evaluate(h25,linear_coef,"pe_count")
        lin85=evaluate(h85,linear_coef,"pe_count")

        comb_sqrt_mape=(sqrt25["mape_pct"]*sqrt25["n"]+sqrt85["mape_pct"]*sqrt85["n"])/(sqrt25["n"]+sqrt85["n"])
        comb_lin_mape=(lin25["mape_pct"]*lin25["n"]+lin85["mape_pct"]*lin85["n"])/(lin25["n"]+lin85["n"])
        combined_bias=(sqrt25["signed_bias_pct"]*sqrt25["n"]+sqrt85["signed_bias_pct"]*sqrt85["n"])/(sqrt25["n"]+sqrt85["n"])

        backends[backend]={
            "sqrt_45k_fit":{"intercept":sqrt_coef[0],"slope":sqrt_coef[1]},
            "linear_45k_fit":{"intercept":linear_coef[0],"slope":linear_coef[1]},
            "sqrt_25k":sqrt25,
            "sqrt_85k":sqrt85,
            "linear_25k":lin25,
            "linear_85k":lin85,
            "combined_heldout_sqrt_mape_pct":comb_sqrt_mape,
            "combined_heldout_linear_mape_pct":comb_lin_mape,
            "combined_heldout_sqrt_bias_pct":combined_bias,
            "median_seed_cv_pct":float(np.median([p["seed_cv_pct"] for p in p_backend])),
            "exponent_diagnostic":exponent_scan(p_backend),
        }

    dsp_exact=all(r["synth_dsp"]==r["pe_count"] for r in success if r["backend"]=="dsp")
    lut_zero=all(r["synth_dsp"]==0 for r in success if r["backend"]=="lut")

    flags={
        "route_success":len(success)>=52,
        "dsp_mapping_exact":dsp_exact,
        "lut_mapping_zero_dsp":lut_zero,
        "85k_mape":all(backends[b]["sqrt_85k"]["mape_pct"]<=10.0 for b in ("dsp","lut")),
        "25k_mape":all(backends[b]["sqrt_25k"]["mape_pct"]<=12.0 for b in ("dsp","lut")),
        "sqrt_beats_linear":all(
            backends[b]["combined_heldout_sqrt_mape_pct"] <
            backends[b]["combined_heldout_linear_mape_pct"]
            for b in ("dsp","lut")
        ),
        "heldout_bias":all(abs(backends[b]["combined_heldout_sqrt_bias_pct"])<=6.0 for b in ("dsp","lut")),
        "seed_stability":all(backends[b]["median_seed_cv_pct"]<=6.0 for b in ("dsp","lut")),
    }

    result={
        "attempted_routes":len(raw),
        "successful_routes":len(success),
        "backends":backends,
        "flags":flags,
        "arithmetic_backend_replication_pass":all(flags.values()),
        "claim_boundary":(
            "A pass shows the square-root model class transfers across ECP5 DSP-backed "
            "and LUT-forced implementations of the same broadcast INT8 MAC fabric."
        ),
    }

    with (OUT/"similarity_arithmetic_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(raw[0]))
        w.writeheader(); w.writerows(raw)

    with (OUT/"similarity_arithmetic_points.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(points[0]))
        w.writeheader(); w.writerows(points)

    (OUT/"similarity_arithmetic_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
