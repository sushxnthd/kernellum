#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from kernellum.k1.model import K1Architecture, predicted_cycles


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
LAW_PATH = OUT / "similarity_frozen_law.json"

HELDOUT_MN = (80, 112, 160, 224, 320, 448)
HELDOUT_K = (160, 224, 320, 448)


def read_device(device: str) -> tuple[list[dict], list[dict]]:
    directory = OUT / f"similarity_{device}"
    raw = []
    for path in sorted(directory.glob(f"similarity_{device}_shard_*.csv")):
        if path.stat().st_size == 0:
            continue
        with path.open() as f:
            raw.extend(csv.DictReader(f))
    if not raw:
        raise RuntimeError(f"no {device} rows found")

    combined = OUT / f"similarity_{device}_combined.csv"
    with combined.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)

    return raw, [enrich(r) for r in raw if str(r["route_ok"]).lower() == "true"]


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
        "fmax_mhz": float(row["fmax_mhz"]),
    })
    return out


def matrix(rows: list[dict], terms: list[str]) -> np.ndarray:
    return np.asarray([[1.0] + [float(r[t]) for t in terms] for r in rows], dtype=float)


def predict_period(rows: list[dict], terms: list[str], coef: list[float]) -> np.ndarray:
    return matrix(rows, terms) @ np.asarray(coef, dtype=float)


def mape(a: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean(np.abs((p - a) / a)) * 100.0)


def r2(a: np.ndarray, p: np.ndarray) -> float:
    ss_res = float(np.sum((a - p) ** 2))
    ss_tot = float(np.sum((a - np.mean(a)) ** 2))
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


def evaluate(rows: list[dict], terms: list[str], coef: list[float]) -> dict:
    actual_period = np.asarray([1000.0 / r["fmax_mhz"] for r in rows])
    pred_period = predict_period(rows, terms, coef)
    pred_fmax = 1000.0 / pred_period
    actual_fmax = np.asarray([r["fmax_mhz"] for r in rows])
    return {
        "n": len(rows),
        "period_mape_pct": mape(actual_period, pred_period),
        "period_r2": r2(actual_period, pred_period),
        "fmax_mape_pct": mape(actual_fmax, pred_fmax),
        "fmax_r2": r2(actual_fmax, pred_fmax),
        "fmax_spearman": spearman(actual_fmax, pred_fmax),
    }


def family(arch: dict) -> str:
    p = int(float(arch["pe_count"]))
    if p <= 32:
        bucket = "low"
    elif p <= 64:
        bucket = "medium"
    elif p <= 96:
        bucket = "high"
    else:
        bucket = "very-high"
    return f"{bucket}_k{int(float(arch['k_tile']))}"


def arch_obj(row: dict) -> K1Architecture:
    return K1Architecture(
        row["name"],
        int(float(row["rows"])),
        int(float(row["cols"])),
        int(float(row["k_tile"])),
    )


def workload_validation(rows85: list[dict], law: dict) -> dict:
    terms = law["terms"]
    coef = law["coefficients"]
    pred_period = predict_period(rows85, terms, coef)

    enriched = []
    for row, period in zip(rows85, pred_period):
        rr = dict(row)
        rr["pred_fmax_mhz"] = 1000.0 / period
        enriched.append(rr)

    # Fixed-clock cycle heuristic uses only the architecture cycle model.
    # Largest-array heuristic chooses max PE count with K_TILE=32 when possible.
    largest_candidates = [r for r in rows85 if int(float(r["k_tile"])) == 32]
    if not largest_candidates:
        largest_candidates = rows85
    largest_arch = max(
        largest_candidates,
        key=lambda r: (int(float(r["pe_count"])), -abs(int(float(r["rows"])) - int(float(r["cols"])))),
    )

    output_rows = []
    law_family_hits = 0
    fixed_family_hits = 0
    largest_family_hits = 0
    law_exact_hits = 0
    law_regrets = []
    fixed_regrets = []
    largest_regrets = []

    for m in HELDOUT_MN:
        for n in HELDOUT_MN:
            for k in HELDOUT_K:
                scored = []
                for row in enriched:
                    arch = arch_obj(row)
                    cycles = predicted_cycles(m, n, k, arch)
                    actual_latency = cycles / (float(row["fmax_mhz"]) * 1e3)
                    predicted_latency = cycles / (float(row["pred_fmax_mhz"]) * 1e3)
                    fixed_latency = cycles / (100.0 * 1e3)
                    scored.append((row, actual_latency, predicted_latency, fixed_latency))

                actual_best = min(scored, key=lambda x: x[1])
                law_best = min(scored, key=lambda x: x[2])
                fixed_best = min(scored, key=lambda x: x[3])
                largest_entry = next(x for x in scored if x[0]["name"] == largest_arch["name"])

                actual_latency = actual_best[1]
                law_regret = 100.0 * (law_best[1] / actual_latency - 1.0)
                fixed_regret = 100.0 * (fixed_best[1] / actual_latency - 1.0)
                largest_regret = 100.0 * (largest_entry[1] / actual_latency - 1.0)

                actual_family = family(actual_best[0])
                law_family = family(law_best[0])
                fixed_family = family(fixed_best[0])
                largest_family = family(largest_entry[0])

                law_family_hits += law_family == actual_family
                fixed_family_hits += fixed_family == actual_family
                largest_family_hits += largest_family == actual_family
                law_exact_hits += law_best[0]["name"] == actual_best[0]["name"]
                law_regrets.append(law_regret)
                fixed_regrets.append(fixed_regret)
                largest_regrets.append(largest_regret)

                output_rows.append({
                    "m": m,
                    "n": n,
                    "k": k,
                    "actual_best": actual_best[0]["name"],
                    "actual_family": actual_family,
                    "law_best": law_best[0]["name"],
                    "law_family": law_family,
                    "fixed_best": fixed_best[0]["name"],
                    "fixed_family": fixed_family,
                    "largest_best": largest_entry[0]["name"],
                    "largest_family": largest_family,
                    "law_regret_pct": law_regret,
                    "fixed_regret_pct": fixed_regret,
                    "largest_regret_pct": largest_regret,
                })

    path = OUT / "similarity_workload_validation.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    total = len(output_rows)
    law_acc = law_family_hits / total
    fixed_acc = fixed_family_hits / total
    largest_acc = largest_family_hits / total
    best_baseline_acc = max(fixed_acc, largest_acc)

    return {
        "heldout_workloads": total,
        "law_exact_architecture_accuracy": law_exact_hits / total,
        "law_family_accuracy": law_acc,
        "fixed_clock_family_accuracy": fixed_acc,
        "largest_array_family_accuracy": largest_acc,
        "family_accuracy_margin_over_best_baseline_points": 100.0 * (law_acc - best_baseline_acc),
        "law_mean_routed_regret_pct": float(np.mean(law_regrets)),
        "law_median_routed_regret_pct": float(np.median(law_regrets)),
        "law_max_routed_regret_pct": float(np.max(law_regrets)),
        "fixed_clock_mean_regret_pct": float(np.mean(fixed_regrets)),
        "largest_array_mean_regret_pct": float(np.mean(largest_regrets)),
    }


def main() -> int:
    law = json.loads(LAW_PATH.read_text())
    _, rows85 = read_device("85k")
    _, rows25 = read_device("25k")

    law85 = evaluate(rows85, law["terms"], law["coefficients"])
    law25 = evaluate(rows25, law["terms"], law["coefficients"])

    baseline = law["raw_baseline"]
    baseline85 = evaluate(rows85, baseline["terms"], baseline["coefficients"])
    baseline25 = evaluate(rows25, baseline["terms"], baseline["coefficients"])

    workloads = workload_validation(rows85, law)

    criteria = {
        "discovery_mape_limit_pct": 8.0,
        "heldout_85_mape_limit_pct": 12.0,
        "heldout_25_mape_limit_pct": 15.0,
        "heldout_rank_min": 0.90,
        "workload_family_accuracy_min": 0.70,
        "workload_family_margin_min_points": 15.0,
        "workload_mean_regret_max_pct": 5.0,
    }

    discovery_metrics = json.loads((OUT / "similarity_discovery_metrics.json").read_text())
    discovery_mape = discovery_metrics["candidate_models"][law["selected_model"]]["period_mape_pct"]

    raw_baseline_85_mape = baseline85["period_mape_pct"]
    raw_baseline_25_mape = baseline25["period_mape_pct"]
    law_beats_raw_both = (
        law85["period_mape_pct"] < raw_baseline_85_mape
        and law25["period_mape_pct"] < raw_baseline_25_mape
    )

    pass_flags = {
        "discovery_mape": discovery_mape <= criteria["discovery_mape_limit_pct"],
        "heldout_85_mape": law85["period_mape_pct"] <= criteria["heldout_85_mape_limit_pct"],
        "heldout_25_mape": law25["period_mape_pct"] <= criteria["heldout_25_mape_limit_pct"],
        "heldout_rank": min(law85["fmax_spearman"], law25["fmax_spearman"]) >= criteria["heldout_rank_min"],
        "beats_raw_baseline_both_devices": law_beats_raw_both,
        "workload_family_accuracy": workloads["law_family_accuracy"] >= criteria["workload_family_accuracy_min"],
        "workload_family_margin": workloads["family_accuracy_margin_over_best_baseline_points"] >= criteria["workload_family_margin_min_points"],
        "workload_regret": workloads["law_mean_routed_regret_pct"] <= criteria["workload_mean_regret_max_pct"],
    }

    result = {
        "frozen_law": law,
        "criteria": criteria,
        "45k_discovery_loocv_period_mape_pct": discovery_mape,
        "85k_heldout": law85,
        "25k_heldout": law25,
        "raw_coordinate_baseline_85k": baseline85,
        "raw_coordinate_baseline_25k": baseline25,
        "workload_validation": workloads,
        "pass_flags": pass_flags,
        "timing_law_gate_pass": all([
            pass_flags["discovery_mape"],
            pass_flags["heldout_85_mape"],
            pass_flags["heldout_25_mape"],
            pass_flags["heldout_rank"],
            pass_flags["beats_raw_baseline_both_devices"],
        ]),
        "full_similarity_breakthrough_gate_pass": all(pass_flags.values()),
    }

    (OUT / "similarity_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print("SIMILARITY_VALIDATION_BEGIN")
    print(json.dumps(result, indent=2))
    print("SIMILARITY_VALIDATION_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
