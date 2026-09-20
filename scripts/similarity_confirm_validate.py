#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

MODELS = {
    "sqrt": {
        "intercept": 14.104151375868376,
        "slope": 1.722605870482421,
        "feature": "sqrt_pe",
    },
    "linear_pe": {
        "intercept": 18.602356969344182,
        "slope": 0.14970963713526794,
        "feature": "pe_count",
    },
    "perimeter": {
        "intercept": 14.456684505987951,
        "slope": 0.7273119635481695,
        "feature": "perimeter",
    },
}


def load_device(device: str) -> list[dict]:
    directory = OUT / f"similarity_confirm_{device}"
    rows = []
    for p in sorted(directory.glob(f"similarity_confirm_{device}_shard_*.csv")):
        if p.stat().st_size:
            with p.open() as f:
                rows.extend(csv.DictReader(f))
    if not rows:
        raise RuntimeError(f"no confirmation rows for {device}")
    combined = OUT / f"similarity_confirm_{device}_combined.csv"
    with combined.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def success(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if str(r["route_ok"]).lower() != "true":
            continue
        q = dict(r)
        for key in ("rows", "cols", "k_tile", "pe_count", "sqrt_pe", "perimeter", "fmax_mhz", "period_ns"):
            q[key] = float(q[key])
        out.append(q)
    return out


def predict(rows: list[dict], model: dict) -> np.ndarray:
    return np.asarray([
        model["intercept"] + model["slope"] * float(r[model["feature"]])
        for r in rows
    ], dtype=float)


def metrics(rows: list[dict], model: dict) -> dict:
    actual = np.asarray([float(r["period_ns"]) for r in rows], dtype=float)
    pred = predict(rows, model)
    ape = np.abs((pred - actual) / actual) * 100.0
    spe = (pred - actual) / actual * 100.0
    return {
        "n": len(rows),
        "mape_pct": float(np.mean(ape)),
        "median_ape_pct": float(np.median(ape)),
        "signed_bias_pct": float(np.mean(spe)),
        "within_10pct_fraction": float(np.mean(ape <= 10.0)),
        "max_ape_pct": float(np.max(ape)),
    }


def orientation_differences(rows: list[dict]) -> dict:
    lookup = {(int(r["rows"]), int(r["cols"]), int(r["k_tile"])): r for r in rows}
    diffs = []
    seen = set()
    for key, r in lookup.items():
        rr, cc, tt = key
        rev = (cc, rr, tt)
        if rr == cc or rev not in lookup:
            continue
        pair = tuple(sorted((key, rev)))
        if pair in seen:
            continue
        seen.add(pair)
        a = float(r["period_ns"])
        b = float(lookup[rev]["period_ns"])
        diffs.append(abs(a-b) / ((a+b)/2.0) * 100.0)
    return {
        "matched_pairs": len(diffs),
        "median_abs_period_difference_pct": float(np.median(diffs)) if diffs else None,
        "mean_abs_period_difference_pct": float(np.mean(diffs)) if diffs else None,
        "max_abs_period_difference_pct": float(np.max(diffs)) if diffs else None,
    }


def exponent_scan(rows: list[dict]) -> dict:
    pe = np.asarray([float(r["pe_count"]) for r in rows])
    y = np.asarray([float(r["period_ns"]) for r in rows])
    best = None
    for p in np.linspace(0.10, 1.00, 91):
        x = pe ** p
        X = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = X @ coef
        score = float(np.mean(np.abs((pred-y)/y)) * 100.0)
        item = {"p": float(p), "intercept": float(coef[0]), "slope": float(coef[1]), "mape_pct": score}
        if best is None or score < best["mape_pct"]:
            best = item
    return best


def main() -> int:
    devices = {}
    all_success = []
    all_attempted = 0
    for dev in ("25k", "45k", "85k"):
        raw = load_device(dev)
        good = success(raw)
        all_attempted += len(raw)
        all_success.extend(good)
        devices[dev] = {
            "attempted": len(raw),
            "successful": len(good),
            "sqrt": metrics(good, MODELS["sqrt"]),
            "linear_pe": metrics(good, MODELS["linear_pe"]),
            "perimeter": metrics(good, MODELS["perimeter"]),
            "orientation": orientation_differences(good),
        }

    pooled = {
        "sqrt": metrics(all_success, MODELS["sqrt"]),
        "linear_pe": metrics(all_success, MODELS["linear_pe"]),
        "perimeter": metrics(all_success, MODELS["perimeter"]),
        "orientation": orientation_differences(all_success),
        "exponent_diagnostic": exponent_scan(all_success),
    }

    sqrt_better_devices = sum(
        devices[d]["sqrt"]["mape_pct"] < devices[d]["linear_pe"]["mape_pct"]
        for d in devices
    )
    pass_flags = {
        "device_mape": all(devices[d]["sqrt"]["mape_pct"] <= 7.0 for d in devices),
        "pooled_mape": pooled["sqrt"]["mape_pct"] <= 5.5,
        "beats_both_pooled": (
            pooled["sqrt"]["mape_pct"] < pooled["linear_pe"]["mape_pct"]
            and pooled["sqrt"]["mape_pct"] < pooled["perimeter"]["mape_pct"]
        ),
        "beats_linear_on_two_devices": sqrt_better_devices >= 2,
        "device_bias": all(abs(devices[d]["sqrt"]["signed_bias_pct"]) <= 3.0 for d in devices),
        "orientation_robust": (
            pooled["orientation"]["matched_pairs"] >= 8
            and pooled["orientation"]["median_abs_period_difference_pct"] <= 8.0
        ),
        "ninety_percent_within_10pct": pooled["sqrt"]["within_10pct_fraction"] >= 0.90,
    }

    result = {
        "frozen_laws": MODELS,
        "attempted_routes": all_attempted,
        "successful_routes": len(all_success),
        "devices": devices,
        "pooled": pooled,
        "pass_flags": pass_flags,
        "square_root_law_confirmed": all(pass_flags.values()),
        "claim_boundary": (
            "Confirmation supports only this regular INT8 tiled systolic RTL family "
            "under the ECP5/Yosys/nextpnr flow. It is not yet a universal FPGA law."
        ),
    }

    (OUT / "similarity_confirmation_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print("SIMILARITY_CONFIRMATION_BEGIN")
    print(json.dumps(result, indent=2))
    print("SIMILARITY_CONFIRMATION_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
