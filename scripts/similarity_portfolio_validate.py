#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from kernellum.k1.model import K1Architecture, predicted_cycles
from kernellum.workload import tiny_transformer_suite
from scripts.similarity_functional_validate import law_tax_ns
from scripts.similarity_portfolio_route import ARCHITECTURES, DEPLOYMENT_SEEDS

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "results" / "similarity_portfolio_download"
OUT = ROOT / "results"

PORTFOLIO_SIZE = 2
MAX_SEED_REGRET_PCT = 5.0
MAX_OVERALL_REGRET_PCT = 3.0
MIN_REGRET_REDUCTION_PP = 1.0


def latency(workload, arch_tuple, topology: str, fmax_mhz: float) -> float:
    name, nr, nc, kt = arch_tuple
    arch = K1Architecture(name, nr, nc, kt, topology)
    return predicted_cycles(workload.m, workload.n, workload.k, arch) / (fmax_mhz * 1e3)


def main() -> int:
    import numpy as np

    sim_passed = (IN / "similarity_portfolio_simulation_passed").exists()
    raw = []
    for path in sorted(IN.glob("similarity_portfolio_*.csv")):
        with path.open() as handle:
            raw.extend(csv.DictReader(handle))
    if not raw:
        raise RuntimeError("no portfolio-confirmation rows found")

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
    arch_by_name = {item[0]: item for item in ARCHITECTURES}
    portfolios = []
    for workload in workloads:
        candidates = []
        for arch_tuple in ARCHITECTURES:
            name, nr, nc, kt = arch_tuple
            broadcast = selection_timing.get(name)
            if not broadcast:
                continue
            predicted_local_fmax = 1000.0 / (
                broadcast["period_ns"] - law_tax_ns(nr * nc)
            )
            predicted_ms = latency(workload, arch_tuple, "local", predicted_local_fmax)
            candidates.append((predicted_ms, name))
        ranked = sorted(candidates)[:PORTFOLIO_SIZE]
        portfolios.append({
            "workload": workload.name,
            "rank1_arch": ranked[0][1],
            "rank1_predicted_ms": ranked[0][0],
            "rank2_arch": ranked[1][1],
            "rank2_predicted_ms": ranked[1][0],
        })
    portfolio_lookup = {row["workload"]: row for row in portfolios}

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
            portfolio = portfolio_lookup[workload.name]
            member_names = (portfolio["rank1_arch"], portfolio["rank2_arch"])
            member_results = []
            for rank, name in enumerate(member_names, start=1):
                point = timing[(name, "local")]
                actual = latency(
                    workload, arch_by_name[name], "local", point["routed_fmax_mhz"]
                )
                member_results.append((actual, rank, name))
            guided, selected_rank, selected_name = min(member_results)
            rank1_actual = member_results[0][0]

            broadcast_candidates = []
            oracle_candidates = []
            for arch_tuple in ARCHITECTURES:
                name = arch_tuple[0]
                for topology in ("broadcast", "local"):
                    point = timing.get((name, topology))
                    if not point:
                        continue
                    actual = latency(
                        workload, arch_tuple, topology, point["routed_fmax_mhz"]
                    )
                    oracle_candidates.append((actual, name, topology))
                    if topology == "broadcast":
                        broadcast_candidates.append((actual, name))
            baseline, baseline_name = min(broadcast_candidates)
            oracle, oracle_name, oracle_topology = min(oracle_candidates)
            evaluated.append({
                "seed": seed,
                "workload": workload.name,
                "rank1_arch": member_names[0],
                "rank2_arch": member_names[1],
                "selected_rank": selected_rank,
                "selected_arch": selected_name,
                "selected_topology": "local",
                "portfolio_actual_ms": guided,
                "rank1_actual_ms": rank1_actual,
                "broadcast_baseline_ms": baseline,
                "broadcast_baseline_arch": baseline_name,
                "oracle_ms": oracle,
                "oracle_arch": oracle_name,
                "oracle_topology": oracle_topology,
                "portfolio_improvement_pct": (baseline / guided - 1.0) * 100.0,
                "portfolio_oracle_regret_pct": (guided / oracle - 1.0) * 100.0,
                "rank1_improvement_pct": (baseline / rank1_actual - 1.0) * 100.0,
                "rank1_oracle_regret_pct": (rank1_actual / oracle - 1.0) * 100.0,
            })
        deployment_workloads.extend(evaluated)
        seed_summaries.append({
            "seed": seed,
            "workload_count": len(evaluated),
            "portfolio_nonworse_count": sum(
                row["portfolio_improvement_pct"] >= -1e-9 for row in evaluated
            ),
            "portfolio_mean_improvement_pct": float(np.mean([
                row["portfolio_improvement_pct"] for row in evaluated
            ])),
            "portfolio_mean_oracle_regret_pct": float(np.mean([
                row["portfolio_oracle_regret_pct"] for row in evaluated
            ])),
            "rank1_mean_improvement_pct": float(np.mean([
                row["rank1_improvement_pct"] for row in evaluated
            ])),
            "rank1_mean_oracle_regret_pct": float(np.mean([
                row["rank1_oracle_regret_pct"] for row in evaluated
            ])),
            "rank2_choice_count": sum(row["selected_rank"] == 2 for row in evaluated),
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
    portfolio_improvement = float(np.mean([
        row["portfolio_improvement_pct"] for row in deployment_workloads
    ]))
    portfolio_regret = float(np.mean([
        row["portfolio_oracle_regret_pct"] for row in deployment_workloads
    ]))
    rank1_improvement = float(np.mean([
        row["rank1_improvement_pct"] for row in deployment_workloads
    ]))
    rank1_regret = float(np.mean([
        row["rank1_oracle_regret_pct"] for row in deployment_workloads
    ]))
    regret_reduction = rank1_regret - portfolio_regret
    rank2_choices = sum(row["selected_rank"] == 2 for row in deployment_workloads)
    portfolio_integrity = (
        len(portfolios) == 12
        and all(row["rank1_arch"] != row["rank2_arch"] for row in portfolios)
    )

    flags = {
        "functional_simulation": sim_passed,
        "route_success": len(successful) >= 70,
        "dsp_exact": all(row["synth_dsp"] == row["pe_count"] for row in successful),
        "portfolio_integrity": portfolio_integrity,
        "positive_tax": len(pairs) == 8 and positive_tax >= 7,
        "per_seed_nonworse": all(
            row["workload_count"] == 12 and row["portfolio_nonworse_count"] == 12
            for row in seed_summaries
        ),
        "per_seed_improvement": all(
            row["portfolio_mean_improvement_pct"] >= 8.0 for row in seed_summaries
        ),
        "overall_improvement": portfolio_improvement >= 10.0,
        "per_seed_oracle_regret": all(
            row["portfolio_mean_oracle_regret_pct"] <= MAX_SEED_REGRET_PCT
            for row in seed_summaries
        ),
        "overall_oracle_regret": portfolio_regret <= MAX_OVERALL_REGRET_PCT,
        "rank2_used": rank2_choices >= 1,
        "regret_reduction": regret_reduction >= MIN_REGRET_REDUCTION_PP,
        "resource_reporting": len(pairs) == 8,
    }
    result = {
        "functional_simulation_passed": sim_passed,
        "attempted_routes": len(rows),
        "successful_routes": len(successful),
        "portfolio_size": PORTFOLIO_SIZE,
        "positive_tax_pairs": positive_tax,
        "rank2_choice_count": rank2_choices,
        "portfolio_mean_improvement_pct": portfolio_improvement,
        "portfolio_mean_oracle_regret_pct": portfolio_regret,
        "rank1_mean_improvement_pct": rank1_improvement,
        "rank1_mean_oracle_regret_pct": rank1_regret,
        "portfolio_regret_reduction_pp": regret_reduction,
        "seed_summaries": seed_summaries,
        "mean_local_ff_overhead_pct": float(np.mean([
            row["local_ff_overhead_pct"] for row in pairs
        ])),
        "mean_local_bram_overhead_pct": float(np.mean([
            row["local_bram_overhead_pct"] for row in pairs
        ])),
        "flags": flags,
        "portfolio_confirmation_gate_pass": all(flags.values()),
    }
    (OUT / "similarity_portfolio_summary.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    for path, data in (
        (OUT / "similarity_portfolio_combined.csv", rows),
        (OUT / "similarity_portfolio_selections.csv", portfolios),
        (OUT / "similarity_portfolio_workloads.csv", deployment_workloads),
        (OUT / "similarity_portfolio_seed_summary.csv", seed_summaries),
        (OUT / "similarity_portfolio_pairs.csv", pairs),
    ):
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
