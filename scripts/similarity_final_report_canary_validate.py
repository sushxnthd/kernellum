#!/usr/bin/env python3
"""All-required evaluator for the opened final-report integrity canary."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path


IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"


def positive(value: str) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--functional", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    csv_path = args.input / "similarity_final_report_canary.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    row = rows[0] if len(rows) == 1 else {}
    manifest = json.loads((args.input / "flow_patch_manifest.json").read_text(encoding="utf-8"))
    logs = list((args.input.parents[1] / "build" / "similarity_final_report_canary").rglob("driver.log"))
    driver = logs[0].read_text(encoding="utf-8", errors="replace") if len(logs) == 1 else ""
    functional_text = args.functional.read_text(encoding="utf-8", errors="replace")

    identity = (row.get("platform"), row.get("topology"), row.get("rows"),
                row.get("cols"), row.get("seed"))
    gates = {
        "signed_gemm_8x6": "KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows=8 cols=6" in functional_text,
        "exactly_one_frozen_identity": len(rows) == 1 and identity == (
            "sky130hd", "blocal", "8", "6", "173"),
        "route_and_evidence_complete": row.get("attempted", "").lower() == "true"
        and row.get("route_ok", "").lower() == "true" and not row.get("error_stage"),
        "all_electrical_and_drc_counts_zero": all(
            row.get(field) == "0" for field in (
                "setup_violations", "hold_violations", "max_slew_violations",
                "max_fanout_violations", "max_cap_violations", "drc_count"
            )
        ),
        "all_metrics_and_product_hashes_valid": all(
            positive(row.get(field, "")) for field in (
                "period_min_ns", "critical_path_delay_ns", "total_cells",
                "dff_cells", "cell_area_um2", "wire_length_um"
            )
        ) and all(
            re.fullmatch(r"[0-9a-f]{64}", row.get(field, "")) is not None for field in (
                "gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256"
            )
        ),
        "exact_single_gui_patch": manifest.get("orfs_image") == IMAGE
        and manifest.get("replacement_count") == 1
        and re.fullmatch(r"[0-9a-f]{64}", manifest.get("before_sha256", "")) is not None
        and re.fullmatch(r"[0-9a-f]{64}", manifest.get("after_sha256", "")) is not None
        and manifest.get("before_sha256") != manifest.get("after_sha256"),
        "driver_completed_without_signal_or_make_failure": len(logs) == 1
        and "===== native finish" in driver
        and "Signal 11 received" not in driver
        and "make: ***" not in driver,
    }
    result = {
        "schema_version": 1,
        "gates": gates,
        "canary_passed": all(gates.values()),
        "row": row,
        "patch_manifest": manifest,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gates": gates, "canary_passed": result["canary_passed"]}, indent=2))
    return 0 if result["canary_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
