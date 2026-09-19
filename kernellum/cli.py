from __future__ import annotations
import argparse, json
from kernellum.cost import Constraints
from kernellum.workload import named_workload
from kernellum.search import evolutionary_search, random_search, exhaustive_search
from kernellum.pareto import pareto_front

def main():
    p = argparse.ArgumentParser(prog="kernellum", description="Kernellum K0 accelerator design-space search")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("--workload", choices=["qkv", "attn_out", "ffn_expand", "ffn_contract"], default="ffn_expand")
    s.add_argument("--seq", type=int, default=128)
    s.add_argument("--method", choices=["evolutionary", "random", "exhaustive"], default="evolutionary")
    s.add_argument("--budget", type=int, default=2000)
    s.add_argument("--max-dsp", type=int, default=1200)
    s.add_argument("--max-bram", type=int, default=600)
    s.add_argument("--max-latency-ms", type=float)
    s.add_argument("--precision", choices=["4", "8", "both"], default="both")
    s.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    w = named_workload(args.workload, args.seq)
    allowed = (4, 8) if args.precision == "both" else (int(args.precision),)
    c = Constraints(args.max_dsp, args.max_bram, args.max_latency_ms, allowed)
    if args.method == "evolutionary":
        cand, _ = evolutionary_search(w, c, args.budget, args.seed)
    elif args.method == "random":
        cand = random_search(w, c, args.budget, args.seed)
    else:
        cand = exhaustive_search(w, c)
    feasible = [x for x in cand if x.estimate.feasible]
    if not feasible:
        print(json.dumps({"workload": w.to_dict(), "feasible": 0, "evaluated": len(cand)}, indent=2))
        return
    best = min(feasible, key=lambda x: x.objective)
    pf = pareto_front(cand)
    print(json.dumps({
        "workload": w.to_dict(),
        "evaluated": len(cand),
        "feasible": len(feasible),
        "pareto": len(pf),
        "best": best.to_dict(),
        "warning": "Analytical estimate only; not FPGA measurement.",
    }, indent=2))

if __name__ == "__main__":
    main()
