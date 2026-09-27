#!/usr/bin/env python3
"""Frozen opened-data canary for native runtime and final cap headroom."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

from scripts import similarity_asic_transfer_route as common
from scripts.similarity_antenna_margin_canary import (
    ANTENNA_REMOVED,
    ANTENNA_REPLACEMENT,
    ANTENNA_TARGET,
    FINAL_REMOVED,
    FINAL_REPLACEMENT,
    FINAL_TARGET,
    IMAGE,
    patch_flow,
)
from scripts.similarity_blocal_qualified_route import (
    FIELDS,
    add_physical_metrics,
)


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEED = 373
GEOMETRIES = (("opened_canary", 7, 10), ("opened_canary", 10, 7))
CAP_MARGIN = 31
SLEW_MARGIN = 25
RATIO_MARGIN = 20
STAGE_TIMEOUT_SECONDS = 7200
VIOLATIONS = (
    "setup_violations",
    "hold_violations",
    "max_slew_violations",
    "max_fanout_violations",
    "max_cap_violations",
    "drc_count",
)
POSITIVE = (
    "period_min_ns",
    "fmax_mhz",
    "critical_path_delay_ns",
    "total_cells",
    "dff_cells",
    "cell_area_um2",
    "wire_length_um",
    "routed_cell_area_um2",
    "vectorless_power_w",
    "elapsed_sec",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")
STRUCTURE = {
    ("nangate45", "blocal", 7, 10): (3425, 98385.154),
    ("nangate45", "blocal", 10, 7): (3415, 96487.776),
    ("nangate45", "broadcast", 7, 10): (2334, 92517.992),
    ("nangate45", "broadcast", 10, 7): (2314, 91591.248),
    ("nangate45", "local", 7, 10): (3946, 100701.748),
    ("nangate45", "local", 10, 7): (3880, 99536.402),
    ("sky130hd", "blocal", 7, 10): (3425, 461906.7552),
    ("sky130hd", "blocal", 10, 7): (3415, 455850.9472),
    ("sky130hd", "broadcast", 7, 10): (2334, 433724.7264),
    ("sky130hd", "broadcast", 10, 7): (2314, 428609.8208),
    ("sky130hd", "local", 7, 10): (3946, 472873.5232),
    ("sky130hd", "local", 10, 7): (3880, 472732.1376),
}


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"],
        row["topology"],
        int(row["seed"]),
        int(row["rows"]),
        int(row["cols"]),
    )


def expected_identities() -> set[tuple[str, str, int, int, int]]:
    return {
        (platform, topology, SEED, rows, cols)
        for platform in PLATFORMS
        for topology in TOPOLOGIES
        for _, rows, cols in GEOMETRIES
    }


def positive(value: str) -> bool:
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
            and all(row[field] != "" and int(row[field]) == 0 for field in VIOLATIONS)
            and all(positive(row[field]) for field in POSITIVE)
            and all(re.fullmatch(r"[0-9a-f]{64}", row[field]) for field in HASHES)
            and int(row["final_antenna_net_violations"]) == 0
            and int(row["final_antenna_pin_violations"]) == 0
        )
    except (KeyError, TypeError, ValueError):
        return False


def metric(text: str, name: str) -> float | None:
    found = re.search(
        rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text
    )
    return float(found.group(1)) if found else None


def patch_qualified_flow(flow_root: Path, manifest_path: Path) -> None:
    patch_flow(flow_root, manifest_path)
    record = json.loads(manifest_path.read_text(encoding="utf-8"))
    record.update({
        "native_stage_timeout_seconds": STAGE_TIMEOUT_SECONDS,
        "cap_margin": CAP_MARGIN,
        "slew_margin": SLEW_MARGIN,
        "canary_seed": SEED,
        "geometries": [[rows, cols] for _, rows, cols in GEOMETRIES],
    })
    manifest_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def evaluate(root: Path) -> dict[str, object]:
    csvs = sorted(root.rglob("similarity_runtime_headroom_*.csv"))
    rows: list[dict[str, str]] = []
    for path in csvs:
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    identities = [identity(row) for row in rows]
    exact = (
        len(csvs) == 12
        and len(rows) == 12
        and len(set(identities)) == 12
        and set(identities) == expected_identities()
    )

    sources = sorted(root.rglob("source_sha.txt"))
    source_sha = (
        sources[0].read_text(encoding="utf-8").strip()
        if len(sources) == 1
        else ""
    )
    functional_logs = sorted(root.rglob("tb_*.log"))
    functional = (
        len(functional_logs) == 2
        and {path.name for path in functional_logs} == {"tb_7x10.log", "tb_10x7.log"}
        and all(
            "KERNELLUM_BLOCAL_EQUIVALENCE_PASS" in path.read_text(
                encoding="utf-8", errors="replace"
            )
            for path in functional_logs
        )
    )

    manifests = sorted(root.rglob("flow_patch_runtime_headroom_*.json"))
    manifest_records = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    expected_patches = (
        (FINAL_TARGET, FINAL_REMOVED, FINAL_REPLACEMENT),
        (ANTENNA_TARGET, ANTENNA_REMOVED, ANTENNA_REPLACEMENT),
    )
    manifest_ok = len(manifest_records) == 12
    for record in manifest_records:
        manifest_ok &= (
            record.get("schema_version") == 1
            and record.get("orfs_image") == IMAGE
            and record.get("workflow_source_sha") == source_sha
            and record.get("antenna_ratio_margin") == RATIO_MARGIN
            and record.get("native_stage_timeout_seconds") == STAGE_TIMEOUT_SECONDS
            and record.get("cap_margin") == CAP_MARGIN
            and record.get("slew_margin") == SLEW_MARGIN
            and record.get("canary_seed") == SEED
            and record.get("geometries") == [[7, 10], [10, 7]]
            and len(record.get("patches", [])) == 2
        )
        for patch, (target, removed, replacement) in zip(
            record.get("patches", []), expected_patches
        ):
            manifest_ok &= (
                patch.get("target") == f"flow/{target}"
                and patch.get("replacement_count") == 1
                and patch.get("removed_text") == removed
                and patch.get("replacement_text") == replacement
                and bool(re.fullmatch(r"[0-9a-f]{64}", patch.get("before_sha256", "")))
                and bool(re.fullmatch(r"[0-9a-f]{64}", patch.get("after_sha256", "")))
            )

    drivers = sorted(root.rglob("driver.log"))
    driver_ok = len(drivers) == 12
    for path in drivers:
        text = path.read_text(encoding="utf-8", errors="replace")
        driver_ok &= (
            "===== native finish" in text
            and "TIMEOUT" not in text
            and "Signal 11 received" not in text
            and "make: ***" not in text
        )

    reports = sorted(root.rglob("6_finish.rpt"))
    report_records = []
    headroom_ok = len(reports) == 12
    for path in reports:
        text = path.read_text(encoding="utf-8", errors="replace")
        cap = metric(text, "max_capacitance_check_slack_limit")
        slew = metric(text, "max_slew_check_slack_limit")
        okay = cap is not None and cap >= 0.02 and slew is not None and slew >= 0.02
        headroom_ok &= okay
        report_records.append({
            "file": path.as_posix(),
            "cap_slack_fraction": cap,
            "slew_slack_fraction": slew,
            "pass": okay,
        })

    drc_reports = sorted(root.rglob("5_route_drc.rpt"))
    drc_ok = len(drc_reports) == 12 and all(
        not path.read_text(encoding="utf-8").strip() for path in drc_reports
    )
    route_logs = sorted(root.rglob("5_2_route.log"))
    route_records = []
    route_ok = len(route_logs) == 12
    for path in route_logs:
        text = path.read_text(encoding="utf-8", errors="replace")
        nets = [int(value) for value in re.findall(r"Found (\d+) net violations\.", text)]
        pins = [int(value) for value in re.findall(r"Found (\d+) pin violations\.", text)]
        drc = [int(value) for value in re.findall(r"Number of violations = (\d+)\.", text)]
        okay = bool(nets) and bool(pins) and bool(drc) and nets[-1] == pins[-1] == drc[-1] == 0
        route_ok &= okay
        route_records.append({
            "file": path.as_posix(),
            "final_net_violations": nets[-1] if nets else None,
            "final_pin_violations": pins[-1] if pins else None,
            "final_drc_violations": drc[-1] if drc else None,
            "pass": okay,
        })

    structure_ok = exact and all(
        (int(row["dff_cells"]), float(row["cell_area_um2"]))
        == STRUCTURE[(
            row["platform"], row["topology"], int(row["rows"]), int(row["cols"])
        )]
        for row in rows
    )
    gates = {
        "signed_gemm_on_two_opened_shapes": functional,
        "exactly_six_shards_and_12_unique_rows": exact,
        "all_12_exact_qualified_patch_and_runtime_manifests": manifest_ok,
        "all_12_native_finishes_without_timeout_crash_or_make_failure": driver_ok,
        "all_12_rows_complete_electrically_clean_and_hashed": exact and all(clean(row) for row in rows),
        "all_12_finish_reports_ge_2pct_cap_and_slew_headroom": headroom_ok,
        "all_12_detailed_route_and_final_antenna_checks_clean": drc_ok and route_ok,
        "all_12_rows_preserve_exact_dff_and_synthesis_area": structure_ok,
    }
    return {
        "schema_version": 1,
        "role": "opened-data runtime/headroom flow qualification only; cannot confirm architecture or rescue prior nulls",
        "source_sha": source_sha,
        "planned": 12,
        "attempted": len(rows),
        "clean": sum(clean(row) for row in rows),
        "gates": gates,
        "canary_pass": all(gates.values()),
        "reports": report_records,
        "route_reports": route_records,
        "rows": rows,
        "patch_manifests": manifest_records,
    }


def route(args: argparse.Namespace) -> int:
    output_dir = ROOT / "results" / "similarity_runtime_headroom_canary"
    manifest = output_dir / (
        f"flow_patch_runtime_headroom_{args.platform}_{args.topology}_"
        f"r{args.rows}_c{args.cols}.json"
    )
    patch_qualified_flow(args.flow_root.resolve(), manifest)
    common.BUILD = ROOT / "build" / "similarity_runtime_headroom_canary"
    family = "blocal" if args.topology == "blocal" else "controls"
    config = f"/work/asic/runtime_headroom_canary/{family}_config_{args.platform}.mk"
    geometry = next(
        (item for item in GEOMETRIES if item[1:] == (args.rows, args.cols)),
        None,
    )
    if geometry is None:
        raise ValueError(f"unfrozen geometry {args.rows}x{args.cols}")
    split, row_count, col_count = geometry
    row = common.route_one(
        args.platform,
        split,
        args.topology,
        SEED,
        row_count,
        col_count,
        args.flow_root.resolve(),
        args.qemu.resolve(),
        config,
        stage_timeout_seconds=STAGE_TIMEOUT_SECONDS,
    )
    shard = (
        common.BUILD
        / args.platform
        / args.topology
        / f"s{SEED}"
        / f"r{row_count}_c{col_count}"
    )
    add_physical_metrics(row, shard)
    print(
        f"[runtime/headroom canary] {args.platform} {args.topology} "
        f"{row_count}x{col_count} route_ok={row['route_ok']} "
        f"error={row['error_stage']}",
        flush=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / (
        f"similarity_runtime_headroom_{args.platform}_{args.topology}_s{SEED}_"
        f"r{row_count}_c{col_count}.csv"
    )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=PLATFORMS)
    parser.add_argument("--topology", choices=TOPOLOGIES)
    parser.add_argument("--flow-root", type=Path)
    parser.add_argument("--rows", type=int)
    parser.add_argument("--cols", type=int)
    parser.add_argument(
        "--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static")
    )
    parser.add_argument("--evaluate", type=Path)
    args = parser.parse_args()
    if args.evaluate:
        result = evaluate(args.evaluate)
        output = ROOT / "results" / "similarity_runtime_headroom_canary_summary.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            key: value
            for key, value in result.items()
            if key not in {"rows", "reports", "route_reports", "patch_manifests"}
        }, indent=2))
        return 0 if result["canary_pass"] else 1
    if any(value is None for value in (
        args.platform, args.topology, args.flow_root, args.rows, args.cols
    )):
        parser.error("routing requires platform, topology, rows, cols and flow-root")
    return route(args)


if __name__ == "__main__":
    raise SystemExit(main())
