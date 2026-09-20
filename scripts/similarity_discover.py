#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "similarity_discovery"
OUT = ROOT / "results"

MODEL_SPECS = {
    "pe_only": ("pe_count",),
    "pe_logtile": ("pe_count", "log2_k_tile"),
    "pe_logtile_aniso": ("pe_count", "log2_k_tile", "anisotropy"),
    "pe_logtile_perim": ("pe_count", "log2_k_tile", "perimeter"),
    "sqrtpe_logtile_aniso": ("sqrt_pe", "log2_k_tile", "anisotropy"),
    "perim_maxdim_logtile": ("perimeter", "max_dim", "log2_k_tile"),
    "pe_logtile_aniso_interaction": (
        "pe_count",
        "log2_k_tile",
        "anisotropy",
        "pe_aniso",
    ),
}

SIMPLICITY_TOLERANCE_MAPE_POINTS = 0.50


def read_rows() -> list[dict]:
    rows = []
    for path in sorted(IN_DIR.glob("similarity_45k_shard_*.csv")):
        if path.stat().st_size == 0:
            continue
        with path.open() as f:
            rows.extend(csv.DictReader(f))
    if not rows:
        raise RuntimeError("no 45k discovery rows found")
    return rows


def enrich(row: dict) -> dict:
    r = float(row["rows"])
    c = float(row["cols"])
    p = float(row["pe_count"])
    out = dict(row)
    out.update({
        "rows": r,
        "cols": c,
        "k_tile": float(row["k_tile"]),
        "pe_count": p,
        "perimeter": float(row["perimeter"]),
        "anisotropy": float(row["anisotropy"]),
        "log2_k_tile": float(row["log2_k_tile"]),
        "sqrt_pe": math.sqrt(p),
        "max_dim": max(r, c),
        "pe_aniso": p * float(row["anisotropy"]),
        "fmax_mhz": float(row["fmax_mhz"]) if row["fmax_mhz"] else float("nan"),
    })
    return out


def design_matrix(rows: list[dict], terms: tuple[str, ...]) -> np.ndarray:
    return np.asarray(
        [[1.0] + [float(row[t]) for t in terms] for row in rows],
        dtype=float,
    )


def fit(rows: list[dict], terms: tuple[str, ...]) -> np.ndarray:
    X = design_matrix(rows, terms)
    y = np.asarray([1000.0 / float(r["fmax_mhz"]) for r in rows])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def predict_period(rows: list[dict], terms: tuple[str, ...], coef: np.ndarray) -> np.ndarray:
    return design_matrix(rows, terms) @ coef


def mape(actual: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs((pred - actual) / actual)) * 100.0)


def r2(actual: np.ndarray, pred: np.ndarray) -> float:
    ss_res = float(np.sum((actual - pred) ** 2))
    ss_tot = float(np.sum((actual - np.mean(actual)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot else 1.0


def rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        avg = (i + j - 1) / 2.0 + 1.0
        ranks[order[i:j]] = avg
        i = j
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rank(a), rank(b)
    if np.std(ra) == 0 or np.std(rb) == 0:
        return 1.0 if np.allclose(ra, rb) else 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def loocv(rows: list[dict], terms: tuple[str, ...]) -> dict:
    actual = np.asarray([1000.0 / float(r["fmax_mhz"]) for r in rows])
    pred = np.zeros(len(rows), dtype=float)
    for i in range(len(rows)):
        train = [r for j, r in enumerate(rows) if j != i]
        coef = fit(train, terms)
        pred[i] = predict_period([rows[i]], terms, coef)[0]
    return {
        "period_mape_pct": mape(actual, pred),
        "period_r2": r2(actual, pred),
        "period_spearman": spearman(actual, pred),
    }


def main() -> int:
    raw = read_rows()

    # Preserve every attempted route in a combined discovery CSV.
    combined = OUT / "similarity_45k_combined.csv"
    with combined.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)

    successful = [enrich(r) for r in raw if str(r["route_ok"]).lower() == "true"]
    if len(successful) < 40:
        raise RuntimeError(f"insufficient successful 45k routes: {len(successful)}")

    candidates = {}
    for name, terms in MODEL_SPECS.items():
        metrics = loocv(successful, terms)
        candidates[name] = {
            "terms": list(terms),
            "term_count": len(terms),
            **metrics,
        }

    best_mape = min(v["period_mape_pct"] for v in candidates.values())
    eligible = [
        (name, spec)
        for name, spec in candidates.items()
        if spec["period_mape_pct"] <= best_mape + SIMPLICITY_TOLERANCE_MAPE_POINTS
    ]
    eligible.sort(key=lambda item: (
        item[1]["term_count"],
        item[1]["period_mape_pct"],
        item[0],
    ))
    selected_name, selected_spec = eligible[0]
    terms = tuple(selected_spec["terms"])
    coef = fit(successful, terms)

    actual = np.asarray([1000.0 / float(r["fmax_mhz"]) for r in successful])
    fitted = predict_period(successful, terms, coef)

    # Raw-coordinate baseline frozen at the same time.
    baseline_terms = ("rows", "cols", "k_tile")
    baseline_coef = fit(successful, baseline_terms)

    frozen = {
        "response": "critical_period_ns",
        "equation_form": "period_ns = intercept + sum(coefficient_i * term_i)",
        "selected_model": selected_name,
        "terms": list(terms),
        "coefficients": [float(x) for x in coef],
        "selection_rule": (
            "lowest leave-one-out MAPE with a simplicity preference for the "
            "fewest terms within 0.50 percentage points of the minimum"
        ),
        "discovery_device": "45k",
        "successful_discovery_routes": len(successful),
        "attempted_discovery_routes": len(raw),
        "raw_baseline": {
            "terms": list(baseline_terms),
            "coefficients": [float(x) for x in baseline_coef],
        },
    }

    metrics = {
        "selected_model": selected_name,
        "selected_terms": list(terms),
        "successful_routes": len(successful),
        "attempted_routes": len(raw),
        "candidate_models": candidates,
        "in_sample_period_mape_pct": mape(actual, fitted),
        "in_sample_period_r2": r2(actual, fitted),
        "in_sample_period_spearman": spearman(actual, fitted),
    }

    (OUT / "similarity_frozen_law.json").write_text(json.dumps(frozen, indent=2) + "\n")
    (OUT / "similarity_discovery_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    print("SIMILARITY_DISCOVERY_LAW_BEGIN")
    print(json.dumps(frozen, indent=2))
    print("SIMILARITY_DISCOVERY_LAW_END")
    print("SIMILARITY_DISCOVERY_METRICS_BEGIN")
    print(json.dumps(metrics, indent=2))
    print("SIMILARITY_DISCOVERY_METRICS_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
