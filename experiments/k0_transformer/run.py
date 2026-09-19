from __future__ import annotations
import json, time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from kernellum.architecture import Architecture
from kernellum.cost import Constraints, estimate
from kernellum.workload import tiny_transformer_suite
from kernellum.search import exhaustive_search, random_search, evolutionary_search
from kernellum.pareto import pareto_front

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

CONSTRAINTS = Constraints(max_dsp=512, max_bram=120, allowed_precisions=(8,))
BASELINE = Architecture(16, 16, 8, 32, 32, 32, 128, "weight_stationary")
BUDGETS = (64, 128, 256, 512)
SEEDS = (0, 1, 2, 3, 4)
PRIMARY_BUDGET = 256

def best_feasible(xs):
    xs = [x for x in xs if x.estimate.feasible]
    return min(xs, key=lambda x: x.objective) if xs else None

def main():
    workload_rows, efficiency_rows = [], []
    selected_exhaustive = None
    for wi, w in enumerate(tiny_transformer_suite()):
        t0 = time.perf_counter()
        exhaustive = exhaustive_search(w, CONSTRAINTS)
        t_exh = time.perf_counter() - t0
        b_exh = best_feasible(exhaustive)
        be = estimate(w, BASELINE, CONSTRAINTS)
        pf = pareto_front(exhaustive)

        if w.name == "s128_ffn_expand":
            selected_exhaustive = exhaustive
            pd.DataFrame([x.to_dict() for x in exhaustive]).to_csv(OUT / "s128_ffn_expand_full_space.csv", index=False)
            pd.DataFrame([x.to_dict() for x in pf]).to_csv(OUT / "s128_ffn_expand_pareto.csv", index=False)

        primary_evo = primary_random = None
        for budget in BUDGETS:
            for seed in SEEDS:
                rnd = random_search(w, CONSTRAINTS, budget, seed=1000*wi+seed)
                evo, hist = evolutionary_search(w, CONSTRAINTS, budget, seed=1000*wi+seed)
                br, bv = best_feasible(rnd), best_feasible(evo)
                for method, b in (("random", br), ("evolutionary", bv)):
                    efficiency_rows.append({
                        "workload": w.name,
                        "budget": budget,
                        "seed": seed,
                        "method": method,
                        "best_ms": b.estimate.latency_ms,
                        "latency_regret_pct": 100*(b.estimate.latency_ms/b_exh.estimate.latency_ms-1),
                        "objective_regret_pct": 100*(b.objective/b_exh.objective-1),
                        "hit_exact_optimum": abs(b.objective-b_exh.objective) < 1e-12,
                    })
                if budget == PRIMARY_BUDGET and seed == 0:
                    primary_evo, primary_random = bv, br
                    if w.name == "s128_ffn_expand":
                        (OUT / "s128_ffn_expand_evo_history.json").write_text(json.dumps(hist, indent=2))

        workload_rows.append({
            "workload": w.name,
            "macs_m": w.macs / 1e6,
            "space_size": len(exhaustive),
            "feasible_designs": sum(x.estimate.feasible for x in exhaustive),
            "pareto_designs": len(pf),
            "exhaustive_best_ms": b_exh.estimate.latency_ms,
            "primary_random_ms": primary_random.estimate.latency_ms,
            "primary_evolutionary_ms": primary_evo.estimate.latency_ms,
            "baseline_ms": be.latency_ms,
            "evo_vs_baseline_pct": 100*(1-primary_evo.estimate.latency_ms/be.latency_ms),
            "best_array": f"{primary_evo.architecture.array_rows}x{primary_evo.architecture.array_cols}",
            "best_tile": f"{primary_evo.architecture.tile_m}x{primary_evo.architecture.tile_n}x{primary_evo.architecture.tile_k}",
            "best_buffer_kb": primary_evo.architecture.buffer_kb,
            "best_dataflow": primary_evo.architecture.dataflow,
            "exhaustive_s": t_exh,
        })

    df = pd.DataFrame(workload_rows)
    eff = pd.DataFrame(efficiency_rows)
    df.to_csv(OUT / "benchmark_summary.csv", index=False)
    eff.to_csv(OUT / "search_efficiency.csv", index=False)
    grouped = eff.groupby(["method", "budget"]).agg(
        mean_latency_regret_pct=("latency_regret_pct", "mean"),
        median_latency_regret_pct=("latency_regret_pct", "median"),
        exact_optimum_rate=("hit_exact_optimum", "mean"),
    ).reset_index()
    grouped.to_csv(OUT / "search_efficiency_summary.csv", index=False)

    primary = grouped[grouped.budget == PRIMARY_BUDGET].set_index("method")
    aggregate = {
        "workloads": len(df),
        "search_space_per_workload": int(df.space_size.iloc[0]),
        "mean_feasible_designs": float(df.feasible_designs.mean()),
        "primary_budget": PRIMARY_BUDGET,
        "precision_bits": 8,
        "max_dsp": CONSTRAINTS.max_dsp,
        "max_bram": CONSTRAINTS.max_bram,
        "evolutionary_mean_latency_regret_pct": float(primary.loc["evolutionary", "mean_latency_regret_pct"]),
        "random_mean_latency_regret_pct": float(primary.loc["random", "mean_latency_regret_pct"]),
        "evolutionary_exact_optimum_rate": float(primary.loc["evolutionary", "exact_optimum_rate"]),
        "random_exact_optimum_rate": float(primary.loc["random", "exact_optimum_rate"]),
        "mean_evo_vs_fixed_baseline_pct": float(df.evo_vs_baseline_pct.mean()),
        "warning": "All performance values are analytical K0 estimates, not measured FPGA results.",
    }
    (OUT / "aggregate.json").write_text(json.dumps(aggregate, indent=2))

    if selected_exhaustive:
        feasible = [c for c in selected_exhaustive if c.estimate.feasible]
        pf = pareto_front(selected_exhaustive)
        plt.figure(figsize=(7, 5))
        plt.scatter([c.estimate.dsp for c in feasible], [c.estimate.latency_ms for c in feasible], s=5, alpha=0.18)
        plt.plot([c.estimate.dsp for c in pf], [c.estimate.latency_ms for c in pf], marker="o", markersize=3)
        plt.xlabel("DSP-equivalent units")
        plt.ylabel("Estimated latency (ms)")
        plt.title("K0 Pareto frontier: s128 FFN expansion, INT8")
        plt.tight_layout()
        plt.savefig(OUT / "pareto_s128_ffn_expand.png", dpi=180)
        plt.close()

    plt.figure(figsize=(7, 5))
    for method in ("random", "evolutionary"):
        g = grouped[grouped.method == method]
        plt.plot(g.budget, g.mean_latency_regret_pct, marker="o", label=method)
    plt.xlabel("Architecture evaluations")
    plt.ylabel("Mean latency regret vs exhaustive optimum (%)")
    plt.title("K0 sample efficiency across 12 Transformer GEMMs")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "search_efficiency.png", dpi=180)
    plt.close()
    print(json.dumps(aggregate, indent=2))

if __name__ == "__main__":
    main()
