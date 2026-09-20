#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from kernellum.k1.model import K1Architecture, predicted_cycles
from kernellum.workload import tiny_transformer_suite
from scripts.similarity_deployment_route import ARCHITECTURES
from scripts.similarity_functional_validate import law_tax_ns

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "results" / "similarity_deployment_download"
OUT = ROOT / "results"
DEPLOYMENT_SEEDS = (38, 39, 40)


def latency(workload, arch_tuple, topology: str, fmax_mhz: float) -> float:
    name, nr, nc, kt = arch_tuple
    arch = K1Architecture(name, nr, nc, kt, topology)
    return predicted_cycles(workload.m, workload.n, workload.k, arch) / (fmax_mhz * 1e3)


def main() -> int:
    import numpy as np

    sim_passed = (IN / "similarity_deployment_simulation_passed").exists()
    raw = []
    for path in sorted(IN.glob("similarity_deployment_*.csv")):
        with path.open() as handle:
            raw.extend(csv.DictReader(handle))
    if not raw:
        raise RuntimeError("no deployment-confirmation rows found")

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

    selection_groups = defaultdict(list)
    deployment_groups = defaultdict(list)
    for row in successful:
        key = (row["name"], row["topology"])
        if row["phase"] == "selection":
            selection_groups[key].append(row)
        else:
            deployment_groups[key].append(row)

    selection_timing = {}
    for name, nr, nc, kt in ARCHITECTURES:
        group = selection_groups.get((name, "broadcast"), [])
        if group:
            selection_timing[name] = {
                "period_ns": float(np.median([row["routed_period_ns"] for row in group])),
                "fmax_mhz": float(np.median([row["routed_fmax_mhz"] for row in group])),
            }

    workloads = tiny_transformer_suite()
    selections = []
    arch_by_name = {item[0]: item for item in ARCHITECTURES}
    for workload in workloads:
        candidates = []
        for arch_tuple in ARCHITECTURES:
            name, nr, nc, kt = arch_tuple
            broadcast = selection_timing.get(name)
            if not broadcast:
                continue
            b_pred = latency(workload, arch_tuple, "broadcast", broadcast["fmax_mhz"])
            predicted_local_fmax = 1000.0 / (
                broadcast["period_ns"] - law_tax_ns(nr * nc)
            )
            l_pred = latency(workload, arch_tuple, "local", predicted_local_fmax)
            candidates.extend([
                (b_pred, name, "broadcast"),
                (l_pred, name, "local"),
            ])
        predicted_ms, name, topology = min(candidates)
        selections.append({
            "workload": workload.name,
            "selected_arch": name,
            "selected_topology": topology,
            "selection_predicted_ms": predicted_ms,
        })
    selection_lookup = {row["workload"]: row for row in selections}

    deployment_workloads = []
    seed_summaries = []
    for seed in DEPLOYMENT_SEEDS:
        timing = {
            (row["name"], row["topology"]): row
            for row in successful
            if row["phase"] == "deployment" and row["seed"] == seed
        }
        evaluated = []
        for workload in workloads:
            choice = selection_lookup[workload.name]
            chosen_arch = arch_by_name[choice["selected_arch"]]
            chosen = timing[(choice["selected_arch"], choice["selected_topology"])]
            guided = latency(
                workload, chosen_arch, choice["selected_topology"], chosen["routed_fmax_mhz"]
            )
            broadcast_candidates = []
            oracle_candidates = []
            for arch_tuple in ARCHITECTURES:
                name = arch_tuple[0]
                for topology in ("broadcast", "local"):
                    point = timing.get((name, topology))
                    if not point:
                        continue
                    actual = latency(workload, arch_tuple, topology, point["routed_fmax_mhz"])
                    oracle_candidates.append((actual, name, topology))
                    if topology == "broadcast":
                        broadcast_candidates.append((actual, name))
            baseline, baseline_name = min(broadcast_candidates)
            oracle, oracle_name, oracle_topology = min(oracle_candidates)
            evaluated.append({
                "seed": seed,
                "workload": workload.name,
                "selected_arch": choice["selected_arch"],
                "selected_topology": choice["selected_topology"],
                "guided_actual_ms": guided,
                "broadcast_baseline_ms": baseline,
                "broadcast_baseline_arch": baseline_name,
                "oracle_ms": oracle,
                "oracle_arch": oracle_name,
                "oracle_topology": oracle_topology,
                "improvement_pct": (baseline / guided - 1.0) * 100.0,
                "oracle_regret_pct": (guided / oracle - 1.0) * 100.0,
            })
        deployment_workloads.extend(evaluated)
        seed_summaries.append({
            "seed": seed,
            "workload_count": len(evaluated),
            "nonworse_count": sum(row["improvement_pct"] >= -1e-9 for row in evaluated),
            "mean_improvement_pct": float(np.mean([row["improvement_pct"] for row in evaluated])),
            "mean_oracle_regret_pct": float(np.mean([row["oracle_regret_pct"] for row in evaluated])),
        })

    pairs = []
    for name, nr, nc, kt in ARCHITECTURES:
        bg = deployment_groups.get((name, "broadcast"), [])
        lg = deployment_groups.get((name, "local"), [])
        if not bg or not lg:
            continue
        bp = float(np.median([row["routed_period_ns"] for row in bg]))
        lp = float(np.median([row["routed_period_ns"] for row in lg]))
        bff = float(np.median([row["synth_ff"] for row in bg]))
        lff = float(np.median([row["synth_ff"] for row in lg]))
        bbram = float(np.median([row["synth_bram"] for row in bg]))
        lbram = float(np.median([row["synth_bram"] for row in lg]))
        pairs.append({
            "name": name,
            "rows": nr,
            "cols": nc,
            "k_tile": kt,
            "observed_tax_ns": bp - lp,
            "predicted_tax_ns": law_tax_ns(nr * nc),
            "local_ff_overhead_pct": (lff / bff - 1.0) * 100.0,
            "local_bram_overhead_pct": (lbram / bbram - 1.0) * 100.0,
        })

    positive_tax = sum(row["observed_tax_ns"] > 0 for row in pairs)
    overall_improvement = float(np.mean([row["improvement_pct"] for row in deployment_workloads]))
    overall_regret = float(np.mean([row["oracle_regret_pct"] for row in deployment_workloads]))
    local_selections = sum(row["selected_topology"] == "local" for row in selections)
    deep_selections = sum(arch_by_name[row["selected_arch"]][3] == 448 for row in selections)
    deep_contract_selections = sum(
        row["workload"].endswith("ffn_contract")
        and arch_by_name[row["selected_arch"]][3] == 448
        for row in selections
    )
    flags = {
        "functional_simulation": sim_passed,
        "route_success": len(successful) >= 70,
        "dsp_exact": all(row["synth_dsp"] == row["pe_count"] for row in successful),
        "selection_local": local_selections == 12,
        "positive_tax": len(pairs) == 8 and positive_tax >= 7,
        "per_seed_nonworse": all(row["workload_count"] == 12 and row["nonworse_count"] == 12 for row in seed_summaries),
        "per_seed_improvement": all(row["mean_improvement_pct"] >= 8.0 for row in seed_summaries),
        "overall_improvement": overall_improvement >= 10.0,
        "per_seed_oracle_regret": all(row["mean_oracle_regret_pct"] <= 7.0 for row in seed_summaries),
        "overall_oracle_regret": overall_regret <= 5.0,
        "deep_selection": deep_contract_selections == 3,
        "resource_reporting": len(pairs) == 8,
    }
    result = {
        "functional_simulation_passed": sim_passed,
        "attempted_routes": len(rows),
        "successful_routes": len(successful),
        "selection_local_count": local_selections,
        "selection_k448_count": deep_selections,
        "selection_k448_contract_count": deep_contract_selections,
        "positive_tax_pairs": positive_tax,
        "deployment_mean_improvement_pct": overall_improvement,
        "deployment_mean_oracle_regret_pct": overall_regret,
        "seed_summaries": seed_summaries,
        "mean_local_ff_overhead_pct": float(np.mean([row["local_ff_overhead_pct"] for row in pairs])),
        "mean_local_bram_overhead_pct": float(np.mean([row["local_bram_overhead_pct"] for row in pairs])),
        "flags": flags,
        "deployment_confirmation_gate_pass": all(flags.values()),
    }
    (OUT / "similarity_deployment_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    for path, data in (
        (OUT / "similarity_deployment_combined.csv", rows),
        (OUT / "similarity_deployment_selections.csv", selections),
        (OUT / "similarity_deployment_workloads.csv", deployment_workloads),
        (OUT / "similarity_deployment_seed_summary.csv", seed_summaries),
        (OUT / "similarity_deployment_pairs.csv", pairs),
    ):
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
