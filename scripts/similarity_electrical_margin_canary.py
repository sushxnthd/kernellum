#!/usr/bin/env python3
"""Frozen opened-data qualification of larger-shape electrical margins."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

from scripts import similarity_asic_transfer_route as common
from scripts.similarity_final_report_canary import IMAGE, REMOVED, REPLACEMENT, patch_flow


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEED = 263
GEOMETRIES = (("opened_canary", 10, 5), ("opened_canary", 7, 8), ("opened_canary", 8, 7))
VIOLATIONS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
)
POSITIVE = (
    "period_min_ns", "fmax_mhz", "critical_path_delay_ns", "total_cells",
    "dff_cells", "cell_area_um2", "wire_length_um",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")
STRUCTURE = {
    ("nangate45", "blocal", 10, 5): (2492, 69830.32),
    ("nangate45", "blocal", 7, 8): (2733, 78040.942),
    ("nangate45", "blocal", 8, 7): (2720, 77753.396),
    ("nangate45", "broadcast", 10, 5): (1674, 65164.148),
    ("nangate45", "broadcast", 7, 8): (1878, 73780.42),
    ("nangate45", "broadcast", 8, 7): (1858, 72784.516),
    ("nangate45", "local", 10, 5): (2846, 71538.306),
    ("nangate45", "local", 7, 8): (3136, 81224.696),
    ("nangate45", "local", 8, 7): (3078, 79961.196),
    ("sky130hd", "blocal", 10, 5): (2492, 327550.3968),
    ("sky130hd", "blocal", 7, 8): (2733, 370283.8816),
    ("sky130hd", "blocal", 8, 7): (2720, 366814.304),
    ("sky130hd", "broadcast", 10, 5): (1674, 308686.0544),
    ("sky130hd", "broadcast", 7, 8): (1878, 349639.0816),
    ("sky130hd", "broadcast", 8, 7): (1858, 341989.2448),
    ("sky130hd", "local", 10, 5): (2846, 337062.0192),
    ("sky130hd", "local", 7, 8): (3136, 381772.4),
    ("sky130hd", "local", 8, 7): (3078, 373515.7312),
}


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return row["platform"], row["topology"], int(row["seed"]), int(row["rows"]), int(row["cols"])


def expected_identities() -> set[tuple[str, str, int, int, int]]:
    return {(p, t, SEED, r, c) for p in PLATFORMS for t in TOPOLOGIES for _, r, c in GEOMETRIES}


def number(value: str) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def clean(row: dict[str, str]) -> bool:
    try:
        return (
            row["attempted"].lower() == "true"
            and row["route_ok"].lower() == "true"
            and not row["error_stage"]
            and all(row[x] != "" and int(row[x]) == 0 for x in VIOLATIONS)
            and all(number(row[x]) for x in POSITIVE)
            and all(re.fullmatch(r"[0-9a-f]{64}", row[x]) for x in HASHES)
        )
    except (KeyError, TypeError, ValueError):
        return False


def metric(text: str, name: str) -> float | None:
    found = re.search(rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text)
    return float(found.group(1)) if found else None


def evaluate(root: Path) -> dict[str, object]:
    csvs = sorted(root.rglob("similarity_electrical_margin_*.csv"))
    rows: list[dict[str, str]] = []
    for path in csvs:
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    expected = expected_identities()
    identities = [identity(row) for row in rows]
    exact = len(csvs) == 6 and len(rows) == 18 and len(set(identities)) == 18 and set(identities) == expected
    clean_rows = [row for row in rows if clean(row)]

    reports = []
    for path in sorted(root.rglob("6_finish.rpt")):
        match = re.search(r"(nangate45|sky130hd)/(broadcast|local|blocal)/s263/r(10|7|8)_c(5|8|7)/reports/6_finish\.rpt$", path.as_posix())
        if not match:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        reports.append({
            "file": path.as_posix(),
            "platform": match.group(1), "topology": match.group(2),
            "rows": int(match.group(3)), "cols": int(match.group(4)),
            "cap_slack_fraction": metric(text, "max_capacitance_check_slack_limit"),
            "slew_slack_fraction": metric(text, "max_slew_check_slack_limit"),
        })
    drivers = sorted(root.rglob("driver.log"))
    driver_ok = len(drivers) == 18 and all(
        "===== native finish" in (text := path.read_text(encoding="utf-8", errors="replace"))
        and "Signal 11 received" not in text and "make: ***" not in text
        for path in drivers
    )
    manifests = sorted(root.rglob("flow_patch_electrical_margin_*.json"))
    manifest_records = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    sources = sorted(root.rglob("source_sha.txt"))
    source_sha = sources[0].read_text(encoding="utf-8").strip() if len(sources) == 1 else ""
    manifest_ok = len(manifests) == 6 and all(
        item.get("schema_version") == 1 and item.get("orfs_image") == IMAGE
        and item.get("workflow_source_sha") == source_sha
        and item.get("target") == "flow/scripts/final_outputs.tcl"
        and item.get("replacement_count") == 1
        and item.get("removed_text") == REMOVED and item.get("replacement_text") == REPLACEMENT
        for item in manifest_records
    )
    functional_logs = sorted(root.rglob("tb_*.log"))
    functional = (
        len(functional_logs) == 3
        and {p.name for p in functional_logs} == {"tb_10x5.log", "tb_7x8.log", "tb_8x7.log"}
        and all("KERNELLUM_BLOCAL_EQUIVALENCE_PASS" in p.read_text(encoding="utf-8") for p in functional_logs)
    )
    structure_ok = exact and all(
        (int(row["dff_cells"]), float(row["cell_area_um2"]))
        == STRUCTURE[(row["platform"], row["topology"], int(row["rows"]), int(row["cols"]))]
        for row in rows
    )
    headroom = (
        len(reports) == 18
        and all(item["cap_slack_fraction"] is not None and item["cap_slack_fraction"] >= 0.02 for item in reports)
        and all(item["slew_slack_fraction"] is not None and item["slew_slack_fraction"] >= 0.02 for item in reports)
    )
    gates = {
        "signed_gemm_functional_on_three_opened_shapes": functional,
        "exactly_six_shards_and_18_unique_rows": exact,
        "all_six_headless_patch_manifests_exact": manifest_ok,
        "all_18_native_finishes_and_reports": driver_ok and len(reports) == 18,
        "all_18_final_routes_electrically_and_drc_clean": exact and len(clean_rows) == 18,
        "all_18_preserve_exact_dff_and_synthesis_area": structure_ok,
        "all_18_leave_at_least_2pct_cap_and_slew_headroom": headroom,
    }
    return {
        "schema_version": 1,
        "role": "opened-data flow qualification only; cannot confirm architecture or rescue prior nulls",
        "source_sha": source_sha,
        "planned": 18, "attempted": len(rows), "clean": len(clean_rows),
        "gates": gates, "canary_pass": all(gates.values()),
        "reports": reports, "rows": rows, "patch_manifests": manifest_records,
    }


def route(args: argparse.Namespace) -> int:
    output_dir = ROOT / "results" / "similarity_electrical_margin_canary"
    manifest = output_dir / f"flow_patch_electrical_margin_{args.platform}_{args.topology}.json"
    patch_flow(args.flow_root.resolve(), manifest)
    common.BUILD = ROOT / "build" / "similarity_electrical_margin_canary"
    family = "blocal" if args.topology == "blocal" else "controls"
    config = f"/work/asic/electrical_margin_canary/{family}_config_{args.platform}.mk"
    rows = [
        common.route_one(args.platform, split, args.topology, SEED, r, c,
                         args.flow_root.resolve(), args.qemu.resolve(), config)
        for split, r, c in GEOMETRIES
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"similarity_electrical_margin_{args.platform}_{args.topology}_s{SEED}.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=common.FIELDS)
        writer.writeheader(); writer.writerows(rows)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=PLATFORMS)
    parser.add_argument("--topology", choices=TOPOLOGIES)
    parser.add_argument("--flow-root", type=Path)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    parser.add_argument("--evaluate", type=Path)
    args = parser.parse_args()
    if args.evaluate:
        result = evaluate(args.evaluate)
        output = ROOT / "results" / "similarity_electrical_margin_canary_summary.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k not in {"rows", "reports", "patch_manifests"}}, indent=2))
        return 0 if result["canary_pass"] else 1
    if args.platform is None or args.topology is None or args.flow_root is None:
        parser.error("routing requires platform, topology and flow-root")
    return route(args)


if __name__ == "__main__":
    raise SystemExit(main())
