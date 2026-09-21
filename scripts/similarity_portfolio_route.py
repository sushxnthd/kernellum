#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv

from scripts.similarity_utility_route import OUT, route_one

ARCHITECTURES = (
    ("r09_c12_k352", 9, 12, 352),
    ("r09_c12_k480", 9, 12, 480),
    ("r12_c09_k352", 12, 9, 352),
    ("r12_c09_k480", 12, 9, 480),
    ("r10_c15_k352", 10, 15, 352),
    ("r10_c15_k480", 10, 15, 480),
    ("r15_c10_k352", 15, 10, 352),
    ("r15_c10_k480", 15, 10, 480),
)
SELECTION_SEEDS = (41, 42, 43)
DEPLOYMENT_SEEDS = (44, 45, 46)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("selection", "deployment"), required=True)
    parser.add_argument("--topology", choices=("broadcast", "local"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    allowed = SELECTION_SEEDS if args.phase == "selection" else DEPLOYMENT_SEEDS
    if args.seed not in allowed:
        raise SystemExit("seed not allowed for phase")
    if args.phase == "selection" and args.topology != "broadcast":
        raise SystemExit("selection phase is broadcast-only")

    rows = []
    for name, nr, nc, kt in ARCHITECTURES:
        print(
            f"[portfolio-confirm] {args.phase} {name} {args.topology} seed={args.seed}",
            flush=True,
        )
        row = route_one(name, nr, nc, kt, args.topology, args.seed)
        row["phase"] = args.phase
        rows.append(row)
        print(
            f"[portfolio-confirm] ok={row['route_ok']} "
            f"fmax={row['routed_fmax_mhz']} dsp={row['synth_dsp']}",
            flush=True,
        )

    path = OUT / f"similarity_portfolio_{args.phase}_{args.topology}_s{args.seed}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
