#!/usr/bin/env python3
"""Independent audit of Kernellum electrical-margin canary artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

SOURCE_SHA = "bb9a8887be5411247afe59404652676d293d1cc8"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
REMOVED = "# Save a final image if openroad is compiled with the gui\nif { [ord::openroad_gui_compiled] } {\n  gui::show \"source $::env(SCRIPTS_DIR)/save_images.tcl\" false\n}\n"
REPLACEMENT = "# Optional GUI images intentionally disabled for deterministic headless evidence.\n"
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SHAPES = ((10, 5), (7, 8), (8, 7))
SEED = 263
EXPECTED = {(p, t, SEED, r, c) for p in PLATFORMS for t in TOPOLOGIES for r, c in SHAPES}
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
ARTIFACT_DIGESTS = {
    "similarity-electrical-margin-final-summary.zip": "ba7c86594dc66696c7000e1d9d564bccacffc1bfdb9c9da24450a802d0998cd6",
    "similarity-electrical-margin-functional.zip": "a56b6009c9a7d0a7b5d52dd4ff6fb9626234cc11493572924d21968d62208a2e",
    "similarity-electrical-margin-nangate45-blocal-s263.zip": "4357cb72e92365077bba8e3425b98b577482e0f4899bb79a36123964058f45e0",
    "similarity-electrical-margin-nangate45-broadcast-s263.zip": "679f007e1bd87cc14a7d3dadcb7abc43903a852306ad9c08124c124c5eb633d3",
    "similarity-electrical-margin-nangate45-local-s263.zip": "f0a31fe8ccd6b2b148ecd659f39738f0d4c5cc463004dfda13eb112c79cb8b12",
    "similarity-electrical-margin-sky130hd-blocal-s263.zip": "d13de7321d9f7d49986bc16d33b85faf67533c344ea9f0a9776a654af0e2df34",
    "similarity-electrical-margin-sky130hd-broadcast-s263.zip": "d2b9599d51c6ae1fffa98ed94d58824cd1f8f1e6a68e6e34a9fd5a8edc0bf8f5",
    "similarity-electrical-margin-sky130hd-local-s263.zip": "d59c08bc0ff16efdc4b2e24a18a51593555af77ccc1f9fd34212a09d3b46b9aa",
}
VIOLATION_FIELDS = ("setup_violations", "hold_violations", "max_slew_violations", "max_fanout_violations", "max_cap_violations", "drc_count")
POSITIVE_FIELDS = ("period_min_ns", "fmax_mhz", "critical_path_delay_ns", "total_cells", "dff_cells", "cell_area_um2", "wire_length_um")
PRODUCTS = {
    "gds_sha256": "6_final.gds",
    "odb_sha256": "6_final.odb",
    "spef_sha256": "6_final.spef",
    "netlist_sha256": "6_final.v",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def metric(text: str, name: str) -> float | None:
    found = re.search(rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text)
    return float(found.group(1)) if found else None


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return row["platform"], row["topology"], int(row["seed"]), int(row["rows"]), int(row["cols"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()

    zip_digests = {p.name: sha256(p) for p in sorted(args.artifacts.glob("*.zip"))}
    archive_gate = zip_digests == ARTIFACT_DIGESTS

    csvs = sorted(root.rglob("similarity_electrical_margin_*.csv"))
    rows: list[dict[str, str]] = []
    for path in csvs:
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    identities = [identity(row) for row in rows]
    matrix_gate = len(csvs) == 6 and len(rows) == 18 and len(set(identities)) == 18 and set(identities) == EXPECTED

    sources = sorted(root.rglob("source_sha.txt"))
    source_sha = sources[0].read_text(encoding="utf-8").strip() if len(sources) == 1 else ""
    functional_logs = sorted(root.rglob("tb_*.log"))
    functional_gate = (
        len(functional_logs) == 3
        and {p.name for p in functional_logs} == {"tb_10x5.log", "tb_7x8.log", "tb_8x7.log"}
        and all("KERNELLUM_BLOCAL_EQUIVALENCE_PASS" in p.read_text(encoding="utf-8", errors="replace") for p in functional_logs)
        and source_sha == SOURCE_SHA
    )

    manifests = sorted(root.rglob("flow_patch_electrical_margin_*.json"))
    manifest_records = [json.loads(p.read_text(encoding="utf-8")) for p in manifests]
    manifest_gate = len(manifests) == 6 and all(
        record == {
            "schema_version": 1,
            "orfs_image": IMAGE,
            "workflow_source_sha": SOURCE_SHA,
            "target": "flow/scripts/final_outputs.tcl",
            "replacement_count": 1,
            "before_sha256": "d7c98097030afd37d4c86d81286ebbb304a963427a7be69afa3d6ec045b57676",
            "after_sha256": "50d40ebf0fdb08a24805453bdfb3f26a0fb8fe959321b5a50cfa2905b82363d1",
            "removed_text": REMOVED,
            "replacement_text": REPLACEMENT,
        }
        for record in manifest_records
    )

    drivers = sorted(root.rglob("driver.log"))
    driver_gate = len(drivers) == 18 and all(
        "===== native finish" in (text := p.read_text(encoding="utf-8", errors="replace"))
        and "Signal 11 received" not in text and "make: ***" not in text
        for p in drivers
    )

    reports = sorted(root.rglob("6_finish.rpt"))
    drc_reports = sorted(root.rglob("5_route_drc.rpt"))
    route_logs = sorted(root.rglob("5_2_route.log"))
    evidence_gate = len(reports) == len(drc_reports) == len(route_logs) == 18 and all(p.stat().st_size == 0 for p in drc_reports)
    route_log_gate = len(route_logs) == 18
    antenna_findings = []
    for path in route_logs:
        text = path.read_text(encoding="utf-8", errors="replace")
        counts = [int(x) for x in re.findall(r"Number of violations = (\d+)\.", text)]
        route_log_gate &= bool(counts) and counts[-1] == 0
        nets = [int(x) for x in re.findall(r"Found (\d+) net violations\.", text)]
        pins = [int(x) for x in re.findall(r"Found (\d+) pin violations\.", text)]
        antenna_findings.append({
            "file": path.relative_to(root).as_posix(),
            "final_net_violations": nets[-1] if nets else None,
            "final_pin_violations": pins[-1] if pins else None,
        })

    report_records = []
    report_map = {}
    report_gate = len(reports) == 18
    for path in reports:
        match = re.search(r"/(nangate45|sky130hd)/(broadcast|local|blocal)/s263/r(10|7|8)_c(5|8|7)/reports/6_finish\.rpt$", path.as_posix())
        if not match:
            report_gate = False
            continue
        key = (match.group(1), match.group(2), SEED, int(match.group(3)), int(match.group(4)))
        text = path.read_text(encoding="utf-8", errors="replace")
        cap = metric(text, "max_capacitance_check_slack_limit")
        slew = metric(text, "max_slew_check_slack_limit")
        counts = {}
        for field, label in (("max_slew", "max slew"), ("max_fanout", "max fanout"), ("max_cap", "max cap"), ("setup", "setup"), ("hold", "hold")):
            found = re.search(rf"{label} violation count (\d+)", text)
            counts[field] = int(found.group(1)) if found else None
        okay = cap is not None and cap >= 0.02 and slew is not None and slew >= 0.02 and all(v == 0 for v in counts.values())
        report_gate &= okay
        report_map[key] = path
        report_records.append({"identity": list(key), "cap_headroom": cap, "slew_headroom": slew, "counts": counts, "pass": okay})

    row_gate = matrix_gate
    structure_gate = matrix_gate
    product_hash_gate = matrix_gate
    product_checks = []
    for row in rows:
        key = identity(row)
        row_gate &= (
            row.get("attempted", "").lower() == "true"
            and row.get("route_ok", "").lower() == "true"
            and row.get("error_stage", "") == ""
            and all(row.get(f, "") != "" and int(row[f]) == 0 for f in VIOLATION_FIELDS)
            and all(math.isfinite(float(row[f])) and float(row[f]) > 0 for f in POSITIVE_FIELDS)
        )
        structure_gate &= (int(row["dff_cells"]), float(row["cell_area_um2"])) == STRUCTURE[(key[0], key[1], key[3], key[4])]
        report_path = report_map.get(key)
        if report_path is None:
            product_hash_gate = False
            continue
        result_dir = report_path.parents[1] / "results"
        for field, name in PRODUCTS.items():
            path = result_dir / name
            actual = sha256(path) if path.is_file() and path.stat().st_size > 0 else None
            expected = row.get(field)
            matched = actual == expected
            product_hash_gate &= matched
            product_checks.append({"identity": list(key), "product": name, "expected": expected, "actual": actual, "pass": matched})

    gates = {
        "actions_artifact_digests_match": archive_gate,
        "source_sha_and_three_signed_gemm_logs": functional_gate,
        "six_shards_and_exact_18_row_matrix": matrix_gate,
        "six_exact_patch_manifests": manifest_gate,
        "18_native_finishes_without_crash": driver_gate,
        "18_finish_drc_and_route_logs_present": evidence_gate,
        "18_final_route_logs_end_with_zero_detailed_route_drc": route_log_gate,
        "18_finish_reports_zero_violations_and_ge_2pct_headroom": report_gate,
        "18_csv_rows_clean_with_positive_metrics": row_gate,
        "18_rows_preserve_frozen_dff_and_synthesis_area": structure_gate,
        "72_final_product_hashes_match_csv": product_hash_gate and len(product_checks) == 72,
    }
    result = {
        "schema_version": 1,
        "audit_role": "independent raw-artifact audit; opened-data flow qualification only",
        "source_sha": source_sha,
        "archive_digests": zip_digests,
        "counts": {
            "archives": len(zip_digests), "csv_shards": len(csvs), "rows": len(rows),
            "manifests": len(manifests), "functional_logs": len(functional_logs),
            "drivers": len(drivers), "finish_reports": len(reports),
            "drc_reports": len(drc_reports), "route_logs": len(route_logs),
            "product_hash_checks": len(product_checks),
        },
        "minimum_headroom": {
            "cap_fraction": min(r["cap_headroom"] for r in report_records),
            "slew_fraction": min(r["slew_headroom"] for r in report_records),
        },
        "supplemental_non_preregistered_observation": {
            "antenna_was_not_a_frozen_canary_gate": True,
            "all_route_logs_end_with_zero_antenna": all(
                item["final_net_violations"] == 0 and item["final_pin_violations"] == 0
                for item in antenna_findings
            ),
            "nonzero_or_missing_antenna_rows": [
                item for item in antenna_findings
                if item["final_net_violations"] != 0 or item["final_pin_violations"] != 0
            ],
        },
        "gates": gates,
        "independent_audit_pass": all(gates.values()),
        "reports": sorted(report_records, key=lambda x: x["identity"]),
        "product_checks": product_checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"reports", "product_checks", "archive_digests"}}, indent=2))
    return 0 if result["independent_audit_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
