#!/usr/bin/env python3
"""Frozen shard runner for the prospective B-local replication cohort."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts import similarity_asic_transfer_route as common
from scripts.similarity_final_report_canary import patch_flow


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEEDS = (181, 211, 239)
GEOMETRIES = (
    ("discovery", 5, 10),
    ("discovery", 10, 5),
    ("holdout", 7, 8),
    ("holdout", 8, 7),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--topology", choices=TOPOLOGIES, required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--flow-root", type=Path, required=True)
    parser.add_argument(
        "--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static")
    )
    args = parser.parse_args()

    output_dir = ROOT / "results" / "similarity_blocal_replication"
    manifest = output_dir / (
        f"flow_patch_{args.platform}_{args.topology}_s{args.seed}.json"
    )
    patch_flow(args.flow_root.resolve(), manifest)

    common.BUILD = ROOT / "build" / "similarity_blocal_replication"
    family = "blocal" if args.topology == "blocal" else "repair_canary"
    config = f"/work/asic/{family}/config_{args.platform}.mk"
    rows = []
    for split, row_count, col_count in GEOMETRIES:
        print(
            f"[B-local replication] {args.platform} {args.topology} "
            f"seed={args.seed} {split} {row_count}x{col_count}",
            flush=True,
        )
        row = common.route_one(
            args.platform,
            split,
            args.topology,
            args.seed,
            row_count,
            col_count,
            args.flow_root.resolve(),
            args.qemu.resolve(),
            config,
        )
        rows.append(row)
        print(
            f"route_ok={row['route_ok']} period={row['period_min_ns']} "
            f"error={row['error_stage']}",
            flush=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / (
        f"similarity_blocal_replication_{args.platform}_{args.topology}_s{args.seed}.csv"
    )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=common.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
