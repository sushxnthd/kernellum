#!/usr/bin/env python3
"""Frozen opened-data canary for pre-detailed-route antenna margin."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path

from scripts import similarity_asic_transfer_route as common
from scripts.similarity_final_report_canary import IMAGE


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEED = 277
ROWS, COLS = 10, 5
RATIO_MARGIN = 20
FINAL_TARGET = "scripts/final_outputs.tcl"
FINAL_REMOVED = """# Save a final image if openroad is compiled with the gui
if { [ord::openroad_gui_compiled] } {
  gui::show \"source $::env(SCRIPTS_DIR)/save_images.tcl\" false
}
"""
FINAL_REPLACEMENT = """# Optional GUI images intentionally disabled for deterministic headless evidence.
"""
ANTENNA_TARGET = "scripts/global_route.tcl"
ANTENNA_REMOVED = "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT)\n"
ANTENNA_REPLACEMENT = (
    "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT) "
    f"-ratio_margin {RATIO_MARGIN}\n"
)
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
    ("nangate45", "blocal"): (2492, 69830.32),
    ("nangate45", "broadcast"): (1674, 65164.148),
    ("nangate45", "local"): (2846, 71538.306),
    ("sky130hd", "blocal"): (2492, 327550.3968),
    ("sky130hd", "broadcast"): (1674, 308686.0544),
    ("sky130hd", "local"): (2846, 337062.0192),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_flow(flow_root: Path, manifest_path: Path) -> None:
    patches = []
    for target_name, removed, replacement in (
        (FINAL_TARGET, FINAL_REMOVED, FINAL_REPLACEMENT),
        (ANTENNA_TARGET, ANTENNA_REMOVED, ANTENNA_REPLACEMENT),
    ):
        target = flow_root / target_name
        before = target.read_bytes()
        needle = removed.encode()
        count = before.count(needle)
        if count != 1:
            raise RuntimeError(f"expected one frozen block in {target_name}, found {count}")
        after = before.replace(needle, replacement.encode(), 1)
        target.write_bytes(after)
        patches.append({
            "target": f"flow/{target_name}",
            "replacement_count": count,
            "before_sha256": digest(before),
            "after_sha256": digest(after),
            "removed_text": removed,
            "replacement_text": replacement,
        })
    manifest = {
        "schema_version": 1,
        "orfs_image": IMAGE,
        "workflow_source_sha": os.environ.get("GITHUB_SHA", "local"),
        "antenna_ratio_margin": RATIO_MARGIN,
        "patches": patches,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return row["platform"], row["topology"], int(row["seed"]), int(row["rows"]), int(row["cols"])


def expected_identities() -> set[tuple[str, str, int, int, int]]:
    return {(p, t, SEED, ROWS, COLS) for p in PLATFORMS for t in TOPOLOGIES}


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
        )
    except (KeyError, TypeError, ValueError):
        return False


def metric(text: str, name: str) -> float | None:
    found = re.search(rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text)
    return float(found.group(1)) if found else None


def evaluate(root: Path) -> dict[str, object]:
    csvs = sorted(root.rglob("similarity_antenna_margin_*.csv"))
    rows: list[dict[str, str]] = []
    for path in csvs:
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    identities = [identity(row) for row in rows]
    exact = (
        len(csvs) == 6 and len(rows) == 6 and len(set(identities)) == 6
        and set(identities) == expected_identities()
    )

    sources = sorted(root.rglob("source_sha.txt"))
    source_sha = sources[0].read_text(encoding="utf-8").strip() if len(sources) == 1 else ""
    functional_logs = sorted(root.rglob("tb_10x5.log"))
    functional = (
        len(functional_logs) == 1
        and "KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows=10 cols=5"
        in functional_logs[0].read_text(encoding="utf-8", errors="replace")
    )

    manifests = sorted(root.rglob("flow_patch_antenna_margin_*.json"))
    manifest_records = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    expected_patches = [(FINAL_TARGET, FINAL_REMOVED, FINAL_REPLACEMENT),
                        (ANTENNA_TARGET, ANTENNA_REMOVED, ANTENNA_REPLACEMENT)]
    manifest_ok = len(manifests) == 6
    for record in manifest_records:
        manifest_ok &= (
            record.get("schema_version") == 1
            and record.get("orfs_image") == IMAGE
            and record.get("workflow_source_sha") == source_sha
            and record.get("antenna_ratio_margin") == RATIO_MARGIN
            and len(record.get("patches", [])) == 2
        )
        for patch, (target, removed, replacement) in zip(record.get("patches", []), expected_patches):
            manifest_ok &= (
                patch.get("target") == f"flow/{target}"
                and patch.get("replacement_count") == 1
                and patch.get("removed_text") == removed
                and patch.get("replacement_text") == replacement
                and bool(re.fullmatch(r"[0-9a-f]{64}", patch.get("before_sha256", "")))
                and bool(re.fullmatch(r"[0-9a-f]{64}", patch.get("after_sha256", "")))
            )

    drivers = sorted(root.rglob("driver.log"))
    driver_ok = len(drivers) == 6 and all(
        "===== native finish" in (text := path.read_text(encoding="utf-8", errors="replace"))
        and "Signal 11 received" not in text and "make: ***" not in text
        for path in drivers
    )

    reports = sorted(root.rglob("6_finish.rpt"))
    report_records = []
    report_ok = len(reports) == 6
    for path in reports:
        text = path.read_text(encoding="utf-8", errors="replace")
        cap = metric(text, "max_capacitance_check_slack_limit")
        slew = metric(text, "max_slew_check_slack_limit")
        okay = cap is not None and cap >= 0.02 and slew is not None and slew >= 0.02
        report_ok &= okay
        report_records.append({"file": path.as_posix(), "cap_slack_fraction": cap,
                               "slew_slack_fraction": slew, "pass": okay})

    drc_reports = sorted(root.rglob("5_route_drc.rpt"))
    drc_ok = len(drc_reports) == 6 and all(not path.read_text(encoding="utf-8").strip() for path in drc_reports)
    route_logs = sorted(root.rglob("5_2_route.log"))
    antenna_records = []
    antenna_ok = len(route_logs) == 6
    detailed_route_ok = len(route_logs) == 6
    for path in route_logs:
        text = path.read_text(encoding="utf-8", errors="replace")
        nets = [int(value) for value in re.findall(r"Found (\d+) net violations\.", text)]
        pins = [int(value) for value in re.findall(r"Found (\d+) pin violations\.", text)]
        drc = [int(value) for value in re.findall(r"Number of violations = (\d+)\.", text)]
        okay = bool(nets) and bool(pins) and nets[-1] == 0 and pins[-1] == 0
        antenna_ok &= okay
        detailed_route_ok &= bool(drc) and drc[-1] == 0
        antenna_records.append({
            "file": path.as_posix(),
            "final_net_violations": nets[-1] if nets else None,
            "final_pin_violations": pins[-1] if pins else None,
            "pass": okay,
        })

    structure_ok = exact and all(
        (int(row["dff_cells"]), float(row["cell_area_um2"]))
        == STRUCTURE[(row["platform"], row["topology"])]
        for row in rows
    )
    gates = {
        "signed_gemm_10x5": functional,
        "exactly_six_shards_and_rows": exact,
        "six_exact_headless_and_ratio_margin_manifests": manifest_ok,
        "six_native_finishes_without_crash": driver_ok,
        "six_rows_complete_electrically_clean_and_hashed": exact and all(clean(row) for row in rows),
        "six_finish_reports_ge_2pct_cap_and_slew_headroom": report_ok,
        "six_detailed_route_drc_reports_and_logs_clean": drc_ok and detailed_route_ok,
        "six_final_antenna_checks_zero_net_and_pin": antenna_ok,
        "six_rows_preserve_exact_dff_and_synthesis_area": structure_ok,
    }
    return {
        "schema_version": 1,
        "role": "opened-data antenna-flow qualification only; cannot confirm architecture",
        "source_sha": source_sha,
        "planned": 6,
        "attempted": len(rows),
        "clean": sum(clean(row) for row in rows),
        "gates": gates,
        "canary_pass": all(gates.values()),
        "reports": report_records,
        "antenna_reports": antenna_records,
        "rows": rows,
        "patch_manifests": manifest_records,
    }


def route(args: argparse.Namespace) -> int:
    output_dir = ROOT / "results" / "similarity_antenna_margin_canary"
    manifest = output_dir / f"flow_patch_antenna_margin_{args.platform}_{args.topology}.json"
    patch_flow(args.flow_root.resolve(), manifest)
    common.BUILD = ROOT / "build" / "similarity_antenna_margin_canary"
    family = "blocal" if args.topology == "blocal" else "controls"
    config = f"/work/asic/electrical_margin_canary/{family}_config_{args.platform}.mk"
    row = common.route_one(
        args.platform, "opened_canary", args.topology, SEED, ROWS, COLS,
        args.flow_root.resolve(), args.qemu.resolve(), config,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"similarity_antenna_margin_{args.platform}_{args.topology}_s{SEED}.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=common.FIELDS)
        writer.writeheader()
        writer.writerow(row)
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
        output = ROOT / "results" / "similarity_antenna_margin_canary_summary.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in result.items()
                          if key not in {"rows", "reports", "antenna_reports", "patch_manifests"}}, indent=2))
        return 0 if result["canary_pass"] else 1
    if args.platform is None or args.topology is None or args.flow_root is None:
        parser.error("routing requires platform, topology and flow-root")
    return route(args)


if __name__ == "__main__":
    raise SystemExit(main())
