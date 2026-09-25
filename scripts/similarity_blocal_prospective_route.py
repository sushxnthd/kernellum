#!/usr/bin/env python3
"""Frozen shard runner for the fresh B-local ASIC confirmation cohort."""

import argparse
import csv
from pathlib import Path

from scripts import similarity_asic_transfer_route as common

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEEDS = (101, 131, 157)
GEOMETRIES = (("discovery", 6, 8), ("discovery", 8, 6),
              ("holdout", 6, 9), ("holdout", 9, 6))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--platform", choices=PLATFORMS, required=True)
    p.add_argument("--topology", choices=TOPOLOGIES, required=True)
    p.add_argument("--seed", choices=SEEDS, type=int, required=True)
    p.add_argument("--flow-root", type=Path, required=True)
    p.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    args = p.parse_args()
    common.BUILD = ROOT / "build" / "similarity_blocal_prospective"
    family = "blocal" if args.topology == "blocal" else "repair_canary"
    config = f"/work/asic/{family}/config_{args.platform}.mk"
    rows = []
    for split, r, c in GEOMETRIES:
        print(f"[B-local confirmation] {args.platform} {args.topology} "
              f"seed={args.seed} {split} {r}x{c}", flush=True)
        row = common.route_one(args.platform, split, args.topology,
                               args.seed, r, c, args.flow_root.resolve(),
                               args.qemu.resolve(), config)
        rows.append(row)
        print(f"route_ok={row['route_ok']} period={row['period_min_ns']} "
              f"error={row['error_stage']}", flush=True)
    output = ROOT / "results" / f"similarity_blocal_prospective_{args.platform}_{args.topology}_s{args.seed}.csv"
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=common.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
