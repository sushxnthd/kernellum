#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from kernellum.k1.model import K1Architecture, predicted_cycles
from kernellum.workload import tiny_transformer_suite
from scripts.similarity_depth_route import ARCHITECTURES
from scripts.similarity_functional_validate import K_VALUES, law_tax_ns

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "results" / "similarity_depth_download"
OUT = ROOT / "results"
MATCHED_DEPTH_GEOMETRIES = ((8, 8), (10, 12), (12, 10))


def latency_ms(
    m: int,
    n: int,
    k: int,
    name: str,
    rows: int,
    cols: int,
    k_tile: int,
    topology: str,
    fmax_mhz: float,
) -> float:
    arch = K1Architecture(name, rows, cols, k_tile, topology)
    return predicted_cycles(m, n, k, arch) / (fmax_mhz * 1e3)


def main() -> int:
    import numpy as np

    functional_simulation_passed = (
        IN / "similarity_depth_simulation_passed"
    ).exists()
    raw = []
    for path in sorted(IN.glob("similarity_depth_*.csv")):
        with path.open() as handle:
            raw.extend(csv.DictReader(handle))
    if not raw:
        raise RuntimeError("no depth-codesign route rows found")

    rows = []
    for item in raw:
        row = dict(item)
        for key in ("rows", "cols", "k_tile", "pe_count", "seed"):
            row[key] = int(row[key])
        row["route_ok"] = str(row["route_ok"]).lower() == "true"
        for key in ("synth_dsp", "synth_bram", "synth_lut4", "synth_ff"):
            row[key] = int(row[key]) if row[key] else 0
        if row["route_ok"]:
            row["routed_fmax_mhz"] = float(row["routed_fmax_mhz"])
            row["routed_period_ns"] = float(row["routed_period_ns"])
        rows.append(row)

    successful = [row for row in rows if row["route_ok"]]
    grouped = defaultdict(list)
    for row in successful:
        grouped[(row["name"], row["topology"])].append(row)

    points = []
    for name, nr, nc, kt in ARCHITECTURES:
        for topology in ("broadcast", "local"):
            group = grouped.get((name, topology), [])
            if not group:
                continue
            periods = np.asarray([row["routed_period_ns"] for row in group], float)
            fmax = np.asarray([row["routed_fmax_mhz"] for row in group], float)
            points.append({
                "name": name,
                "topology": topology,
                "rows": nr,
                "cols": nc,
                "k_tile": kt,
                "pe_count": nr * nc,
                "seed_count": len(group),
                "median_period_ns": float(np.median(periods)),
                "median_fmax_mhz": float(np.median(fmax)),
                "seed_cv_pct": float(np.std(periods, ddof=1) / np.mean(periods) * 100.0)
                if len(periods) > 1 else 0.0,
                "median_ff": float(np.median([row["synth_ff"] for row in group])),
                "median_bram": float(np.median([row["synth_bram"] for row in group])),
            })

    lookup = {(point["name"], point["topology"]): point for point in points}
    pairs = []
    for name, nr, nc, kt in ARCHITECTURES:
        broadcast = lookup.get((name, "broadcast"))
        local = lookup.get((name, "local"))
        if not broadcast or not local:
            continue
        observed = broadcast["median_period_ns"] - local["median_period_ns"]
        predicted = law_tax_ns(nr * nc)
        pairs.append({
            "name": name,
            "rows": nr,
            "cols": nc,
            "k_tile": kt,
            "pe_count": nr * nc,
            "broadcast_period_ns": broadcast["median_period_ns"],
            "local_period_ns": local["median_period_ns"],
            "observed_tax_ns": observed,
            "predicted_tax_ns": predicted,
            "abs_error_ns": abs(observed - predicted),
            "local_fmax_gain_pct":
                (local["median_fmax_mhz"] / broadcast["median_fmax_mhz"] - 1.0) * 100.0,
            "local_ff_overhead_pct":
                (local["median_ff"] / broadcast["median_ff"] - 1.0) * 100.0,
            "local_bram_overhead_pct":
                (local["median_bram"] / broadcast["median_bram"] - 1.0) * 100.0,
        })

    obs = np.asarray([pair["observed_tax_ns"] for pair in pairs], float)
    pred = np.asarray([pair["predicted_tax_ns"] for pair in pairs], float)
    law_mae = float(np.mean(np.abs(obs - pred))) if len(pairs) else float("inf")
    law_rmse = float(np.sqrt(np.mean((obs - pred) ** 2))) if len(pairs) else float("inf")
    law_corr = (
        float(np.corrcoef(obs, pred)[0, 1])
        if len(pairs) > 1 and np.std(obs) > 0 and np.std(pred) > 0 else 0.0
    )

    policy_rows = []
    crossovers = []
    for pair in pairs:
        name = pair["name"]
        nr, nc, kt = pair["rows"], pair["cols"], pair["k_tile"]
        broadcast = lookup[(name, "broadcast")]
        local = lookup[(name, "local")]
        predicted_local_period = broadcast["median_period_ns"] - pair["predicted_tax_ns"]
        predicted_local_fmax = 1000.0 / predicted_local_period
        actual_choices = {}
        for kval in K_VALUES:
            b_actual = latency_ms(
                nr, nc, kval, name, nr, nc, kt, "broadcast", broadcast["median_fmax_mhz"]
            )
            l_actual = latency_ms(
                nr, nc, kval, name, nr, nc, kt, "local", local["median_fmax_mhz"]
            )
            b_pred = b_actual
            l_pred = latency_ms(
                nr, nc, kval, name, nr, nc, kt, "local", predicted_local_fmax
            )
            predicted_choice = "local" if l_pred < b_pred else "broadcast"
            actual_choice = "local" if l_actual < b_actual else "broadcast"
            actual_choices[kval] = actual_choice
            chosen_actual = l_actual if predicted_choice == "local" else b_actual
            oracle_actual = min(l_actual, b_actual)
            policy_rows.append({
                "name": name,
                "k": kval,
                "predicted_choice": predicted_choice,
                "actual_choice": actual_choice,
                "choice_correct": predicted_choice == actual_choice,
                "regret_pct": (chosen_actual / oracle_actual - 1.0) * 100.0,
                "broadcast_latency_ms": b_actual,
                "local_latency_ms": l_actual,
            })
        if (
            any(actual_choices[k] == "broadcast" for k in (8, 16))
            and any(actual_choices[k] == "local" for k in (128, 256, 512, 1024, 3072))
        ):
            crossovers.append(name)

    choice_accuracy = (
        sum(row["choice_correct"] for row in policy_rows) / len(policy_rows)
        if policy_rows else 0.0
    )
    choice_mean_regret = (
        float(np.mean([row["regret_pct"] for row in policy_rows]))
        if policy_rows else float("inf")
    )

    workloads = tiny_transformer_suite()
    workload_rows = []
    for workload in workloads:
        broadcast_candidates = []
        guided_candidates = []
        oracle_candidates = []
        for name, nr, nc, kt in ARCHITECTURES:
            broadcast = lookup.get((name, "broadcast"))
            local = lookup.get((name, "local"))
            if not broadcast or not local:
                continue
            predicted_local_fmax = 1000.0 / (
                broadcast["median_period_ns"] - law_tax_ns(nr * nc)
            )
            b_actual = latency_ms(
                workload.m, workload.n, workload.k, name, nr, nc, kt,
                "broadcast", broadcast["median_fmax_mhz"]
            )
            l_actual = latency_ms(
                workload.m, workload.n, workload.k, name, nr, nc, kt,
                "local", local["median_fmax_mhz"]
            )
            l_pred = latency_ms(
                workload.m, workload.n, workload.k, name, nr, nc, kt,
                "local", predicted_local_fmax
            )
            broadcast_candidates.append((b_actual, name, "broadcast"))
            guided_candidates.extend([
                (b_actual, b_actual, name, "broadcast"),
                (l_pred, l_actual, name, "local"),
            ])
            oracle_candidates.extend([
                (b_actual, name, "broadcast"),
                (l_actual, name, "local"),
            ])

        baseline, baseline_name, _ = min(broadcast_candidates)
        _, guided_actual, guided_name, guided_topology = min(guided_candidates)
        oracle, oracle_name, oracle_topology = min(oracle_candidates)
        workload_rows.append({
            "workload": workload.name,
            "broadcast_baseline_ms": baseline,
            "broadcast_baseline_arch": baseline_name,
            "guided_actual_ms": guided_actual,
            "guided_arch": guided_name,
            "guided_topology": guided_topology,
            "oracle_ms": oracle,
            "oracle_arch": oracle_name,
            "oracle_topology": oracle_topology,
            "improvement_pct": (baseline / guided_actual - 1.0) * 100.0,
            "oracle_regret_pct": (guided_actual / oracle - 1.0) * 100.0,
        })

    depth_rows = []
    for nr, nc in MATCHED_DEPTH_GEOMETRIES:
        means = {}
        for kt in (128, 256):
            name = f"r{nr:02d}_c{nc:02d}_k{kt}"
            point = lookup.get((name, "local"))
            if not point:
                continue
            latencies = [
                latency_ms(
                    workload.m, workload.n, workload.k, name, nr, nc, kt,
                    "local", point["median_fmax_mhz"]
                )
                for workload in workloads
            ]
            means[kt] = float(np.mean(latencies))
        if len(means) == 2:
            depth_rows.append({
                "geometry": f"{nr}x{nc}",
                "k128_local_mean_ms": means[128],
                "k256_local_mean_ms": means[256],
                "k256_improvement_pct": (means[128] / means[256] - 1.0) * 100.0,
            })

    workload_nonworse = sum(row["improvement_pct"] >= -1e-9 for row in workload_rows)
    workload_guided_local = sum(row["guided_topology"] == "local" for row in workload_rows)
    workload_mean_improvement = (
        float(np.mean([row["improvement_pct"] for row in workload_rows]))
        if workload_rows else float("-inf")
    )
    workload_mean_oracle_regret = (
        float(np.mean([row["oracle_regret_pct"] for row in workload_rows]))
        if workload_rows else float("inf")
    )
    depth_dominance_count = sum(row["k256_improvement_pct"] > 0 for row in depth_rows)

    max_seed_cv = max((point["seed_cv_pct"] for point in points), default=float("inf"))
    positive_tax_count = sum(pair["observed_tax_ns"] > 0 for pair in pairs)
    mean_ff_overhead = (
        float(np.mean([pair["local_ff_overhead_pct"] for pair in pairs]))
        if pairs else float("inf")
    )
    mean_bram_overhead = (
        float(np.mean([pair["local_bram_overhead_pct"] for pair in pairs]))
        if pairs else float("inf")
    )
    flags = {
        "functional_simulation": functional_simulation_passed,
        "route_success": len(successful) >= 46,
        "dsp_exact": all(row["synth_dsp"] == row["pe_count"] for row in successful),
        "seed_stability": max_seed_cv <= 8.0,
        "positive_tax": len(pairs) == 8 and positive_tax_count >= 7,
        "law_mae": law_mae <= 1.50,
        "law_correlation": law_corr >= 0.60,
        "choice_accuracy": choice_accuracy >= 0.85,
        "choice_regret": choice_mean_regret <= 3.0,
        "crossover": len(crossovers) >= 6,
        "guided_selects_local": workload_guided_local >= 10,
        "workload_nonworse": workload_nonworse == 12,
        "workload_improvement": workload_mean_improvement >= 8.0,
        "workload_oracle_regret": workload_mean_oracle_regret <= 5.0,
        "depth_dominance": len(depth_rows) == 3 and depth_dominance_count == 3,
    }

    result = {
        "functional_simulation_passed": functional_simulation_passed,
        "attempted_routes": len(rows),
        "successful_routes": len(successful),
        "architecture_pairs": len(pairs),
        "max_seed_cv_pct": max_seed_cv,
        "positive_tax_pairs": positive_tax_count,
        "zero_shot_law_mae_ns": law_mae,
        "zero_shot_law_rmse_ns": law_rmse,
        "zero_shot_law_correlation": law_corr,
        "synthetic_choice_accuracy": choice_accuracy,
        "synthetic_choice_mean_regret_pct": choice_mean_regret,
        "crossover_architectures": crossovers,
        "workload_guided_local_count": workload_guided_local,
        "workload_nonworse_count": workload_nonworse,
        "workload_mean_improvement_pct": workload_mean_improvement,
        "workload_mean_oracle_regret_pct": workload_mean_oracle_regret,
        "depth_dominance_count": depth_dominance_count,
        "mean_local_ff_overhead_pct": mean_ff_overhead,
        "mean_local_bram_overhead_pct": mean_bram_overhead,
        "pairs": pairs,
        "flags": flags,
        "depth_codesign_gate_pass": all(flags.values()),
    }

    (OUT / "similarity_depth_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    for path, data in (
        (OUT / "similarity_depth_combined.csv", rows),
        (OUT / "similarity_depth_points.csv", points),
        (OUT / "similarity_depth_pairs.csv", pairs),
        (OUT / "similarity_depth_policy.csv", policy_rows),
        (OUT / "similarity_depth_workloads.csv", workload_rows),
        (OUT / "similarity_depth_comparison.csv", depth_rows),
    ):
        if data:
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(data[0]))
                writer.writeheader()
                writer.writerows(data)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
