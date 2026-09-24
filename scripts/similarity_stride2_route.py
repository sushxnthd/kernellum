#!/usr/bin/env python3
"""Run one shard of a prospective three-topology ASIC transport study."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts import similarity_asic_transfer_route as prior

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (53, 71, 89)
GEOMETRIES = (
    ("discovery", 4, 7),
    ("discovery", 7, 4),
    ("holdout", 5, 8),
    ("holdout", 8, 5),
)
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "stride2")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--topology", choices=TOPOLOGIES, required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--flow-root", type=Path, required=True)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    args = parser.parse_args()

    prior.BUILD = ROOT / "build" / "similarity_stride2_study"
    config_family = "stride2" if args.topology == "stride2" else "repair_canary"
    config = f"/work/asic/{config_family}/config_{args.platform}.mk"
    results = []
    for split, rows, cols in GEOMETRIES:
        print(
            f"[stride2] {args.platform} {args.topology} seed={args.seed} "
            f"{split} {rows}x{cols}", flush=True
        )
        row = prior.route_one(
            args.platform, split, args.topology, args.seed, rows, cols,
            args.flow_root.resolve(), args.qemu.resolve(), config,
        )
        results.append(row)
        print(
            f"[stride2] route_ok={row['route_ok']} period={row['period_min_ns']} "
            f"error={row['error_stage']}", flush=True
        )

    output = ROOT / "results" / (
        f"similarity_stride2_{args.platform}_{args.topology}_s{args.seed}.csv"
    )
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=prior.FIELDS)
        writer.writeheader()
        writer.writerows(results)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
