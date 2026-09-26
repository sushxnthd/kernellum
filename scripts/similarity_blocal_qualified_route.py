#!/usr/bin/env python3
"""Frozen shard runner for the flow-qualified prospective B-local study."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from scripts import similarity_asic_transfer_route as common
from scripts.similarity_antenna_margin_canary import patch_flow


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEEDS = (293, 317, 347)
GEOMETRIES = (
    ("discovery", 6, 10),
    ("discovery", 10, 6),
    ("holdout", 7, 10),
    ("holdout", 10, 7),
)
EXCLUDED_GEOMETRIES = {
    (3, 3), (7, 7), (2, 4), (4, 2), (3, 6), (6, 3), (5, 5),
    (3, 8), (8, 3), (5, 9), (9, 5), (4, 7), (7, 4), (5, 8),
    (8, 5), (6, 8), (8, 6), (6, 9), (9, 6), (5, 10), (10, 5),
    (7, 8), (8, 7),
}
EXCLUDED_SEEDS = {
    11, 29, 47, 53, 71, 89, 101, 131, 157, 173, 181, 211, 239, 263, 277,
}
RATIO_MARGIN = 20
EXTRA_FIELDS = (
    "routed_cell_area_um2",
    "vectorless_power_w",
    "cap_slack_fraction",
    "slew_slack_fraction",
    "final_antenna_net_violations",
    "final_antenna_pin_violations",
)
FIELDS = common.FIELDS + EXTRA_FIELDS


def require_last(pattern: str, text: str, label: str, flags: int = 0) -> str:
    values = re.findall(pattern, text, flags)
    if not values:
        raise ValueError(f"missing {label}")
    return values[-1]


def report_metric(text: str, name: str) -> float:
    match = re.search(
        rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text
    )
    if match is None:
        raise ValueError(f"missing {name}")
    return float(match.group(1))


def add_physical_metrics(row: dict[str, object], shard: Path) -> None:
    """Add post-route area, vectorless power and final electrical evidence."""
    for field in EXTRA_FIELDS:
        row[field] = ""
    if not row.get("route_ok"):
        return
    try:
        route_text = (shard / "logs" / "5_2_route.log").read_text(
            encoding="utf-8", errors="replace"
        )
        finish_text = (shard / "reports" / "6_finish.rpt").read_text(
            encoding="utf-8", errors="replace"
        )
        row["routed_cell_area_um2"] = float(require_last(
            r"Design area\s+([0-9.eE+-]+)\s+um\^2", route_text,
            "post-route design area",
        ))
        row["vectorless_power_w"] = float(require_last(
            r"^Total\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+"
            r"([0-9.eE+-]+)\s+100\.0%\s*$",
            finish_text, "vectorless total power", re.MULTILINE,
        ))
        row["cap_slack_fraction"] = report_metric(
            finish_text, "max_capacitance_check_slack_limit"
        )
        row["slew_slack_fraction"] = report_metric(
            finish_text, "max_slew_check_slack_limit"
        )
        row["final_antenna_net_violations"] = int(require_last(
            r"Found (\d+) net violations\.", route_text,
            "final antenna net count",
        ))
        row["final_antenna_pin_violations"] = int(require_last(
            r"Found (\d+) pin violations\.", route_text,
            "final antenna pin count",
        ))
        if any(float(row[field]) <= 0 for field in (
            "routed_cell_area_um2", "vectorless_power_w",
        )):
            raise ValueError("nonpositive added physical metric")
    except (OSError, TypeError, ValueError) as exc:
        row["route_ok"] = False
        row["error_stage"] = f"qualified_audit:{exc}"


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

    output_dir = ROOT / "results" / "similarity_blocal_qualified"
    manifest = output_dir / (
        f"flow_patch_{args.platform}_{args.topology}_s{args.seed}.json"
    )
    patch_flow(args.flow_root.resolve(), manifest)

    common.BUILD = ROOT / "build" / "similarity_blocal_qualified"
    family = "blocal" if args.topology == "blocal" else "controls"
    config = f"/work/asic/blocal_qualified/{family}_config_{args.platform}.mk"
    rows = []
    for split, row_count, col_count in GEOMETRIES:
        print(
            f"[B-local qualified prospective] {args.platform} {args.topology} "
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
        shard = (
            common.BUILD / args.platform / args.topology / f"s{args.seed}"
            / f"r{row_count}_c{col_count}"
        )
        add_physical_metrics(row, shard)
        rows.append(row)
        print(
            f"route_ok={row['route_ok']} period={row['period_min_ns']} "
            f"routed_area={row['routed_cell_area_um2']} "
            f"error={row['error_stage']}",
            flush=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / (
        f"similarity_blocal_qualified_{args.platform}_{args.topology}_s{args.seed}.csv"
    )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
