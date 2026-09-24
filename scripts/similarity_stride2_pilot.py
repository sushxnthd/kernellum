#!/usr/bin/env python3
"""Route stride-two on a previously opened 7x7 plumbing geometry."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts import similarity_asic_transfer_route as prior

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=("nangate45", "sky130hd"))
    parser.add_argument("--flow-root", required=True, type=Path)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    args = parser.parse_args()
    prior.BUILD = ROOT / "build" / "similarity_stride2_pilot"
    row = prior.route_one(
        args.platform, "excluded_pilot", "stride2", 29, 7, 7,
        args.flow_root.resolve(), args.qemu.resolve(),
        f"/work/asic/stride2/config_{args.platform}.mk",
    )
    output = ROOT / "results" / f"similarity_stride2_pilot_{args.platform}.csv"
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=prior.FIELDS)
        writer.writeheader()
        writer.writerow(row)
    print(output, "route_ok=", row["route_ok"], "error_stage=", row["error_stage"])
    return 0 if row["route_ok"] and all(
        row[field] == 0 for field in (
            "setup_violations", "hold_violations", "max_slew_violations",
            "max_fanout_violations", "max_cap_violations", "drc_count",
        )
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
