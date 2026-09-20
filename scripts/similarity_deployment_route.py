#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv

from scripts.similarity_utility_route import OUT, route_one

ARCHITECTURES = (
    ("r08_c11_k320", 8, 11, 320),
    ("r08_c11_k448", 8, 11, 448),
    ("r11_c08_k320", 11, 8, 320),
    ("r11_c08_k448", 11, 8, 448),
    ("r10_c13_k320", 10, 13, 320),
    ("r10_c13_k448", 10, 13, 448),
    ("r13_c10_k320", 13, 10, 320),
    ("r13_c10_k448", 13, 10, 448),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("selection", "deployment"), required=True)
    parser.add_argument("--topology", choices=("broadcast", "local"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    allowed = (35, 36, 37) if args.phase == "selection" else (38, 39, 40)
    if args.seed not in allowed:
        raise SystemExit("seed not allowed for phase")
    if args.phase == "selection" and args.topology != "broadcast":
        raise SystemExit("selection phase is broadcast-only")

    rows = []
    for name, nr, nc, kt in ARCHITECTURES:
        print(
            f"[deployment-confirm] {args.phase} {name} {args.topology} seed={args.seed}",
            flush=True,
        )
        row = route_one(name, nr, nc, kt, args.topology, args.seed)
        row["phase"] = args.phase
        rows.append(row)
        print(
            f"[deployment-confirm] ok={row['route_ok']} "
            f"fmax={row['routed_fmax_mhz']} dsp={row['synth_dsp']}",
            flush=True,
        )

    path = OUT / f"similarity_deployment_{args.phase}_{args.topology}_s{args.seed}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
