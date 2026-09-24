#!/usr/bin/env python3
"""Route one opened-data diagnostic shard for critical-bit replication."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts import similarity_asic_transfer_route as prior

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (53, 71, 89)
GEOMETRIES = (("opened_diagnostic", 5, 8), ("opened_diagnostic", 8, 5))
PLATFORMS = ("nangate45", "sky130hd")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--flow-root", type=Path, required=True)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    args = parser.parse_args()

    prior.BUILD = ROOT / "build" / "similarity_criticalbit_diagnostic"
    config = f"/work/asic/criticalbit/config_{args.platform}.mk"
    rows = []
    for split, row_count, col_count in GEOMETRIES:
        print(
            f"[criticalbit] {args.platform} seed={args.seed} "
            f"{row_count}x{col_count}", flush=True
        )
        row = prior.route_one(
            args.platform, split, "criticalbit", args.seed, row_count,
            col_count, args.flow_root.resolve(), args.qemu.resolve(), config,
        )
        rows.append(row)
        print(
            f"[criticalbit] route_ok={row['route_ok']} "
            f"period={row['period_min_ns']} error={row['error_stage']}",
            flush=True,
        )

    output = ROOT / "results" / (
        f"similarity_criticalbit_{args.platform}_s{args.seed}.csv"
    )
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=prior.FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
