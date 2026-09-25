#!/usr/bin/env python3
"""Independent audit of the archived final-report integrity canary.

This checker intentionally does not import the frozen runner or evaluator. It
recomputes every preregistered gate from the original Actions ZIPs and checks
the decisive native logs and reports directly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import tempfile
import zipfile
from pathlib import Path


FROZEN_SHA = "be86ce64ff13a1d1d789b8e3d7a1f476eba437f9"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
ROUTE_ZIP = "similarity-final-report-canary-route.zip"
FUNCTIONAL_ZIP = "similarity-final-report-canary-functional.zip"
EXPECTED_ZIP_DIGESTS = {
    ROUTE_ZIP: "c06f2e0407027f92eedc510758c99ec0e71e73ba86a6136a67823db3204c42e3",
    FUNCTIONAL_ZIP: "00233bbd628c8a0eab546db149ab5687955f446ba72d3669cb6ba498d40cec03",
}
REMOVED = """# Save a final image if openroad is compiled with the gui
if { [ord::openroad_gui_compiled] } {
  gui::show \"source $::env(SCRIPTS_DIR)/save_images.tcl\" false
}
"""
REPLACEMENT = "# Optional GUI images intentionally disabled for deterministic headless evidence.\n"
COUNTS = {
    "setup_violations": "setup violation count",
    "hold_violations": "hold violation count",
    "max_slew_violations": "max slew violation count",
    "max_fanout_violations": "max fanout violation count",
    "max_cap_violations": "max cap violation count",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def one(root: Path, name: str) -> Path:
    paths = list(root.rglob(name))
    if len(paths) != 1:
        raise ValueError(f"expected one {name}, found {len(paths)}")
    return paths[0]


def positive(value: str) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def report_count(report: str, label: str) -> int | None:
    match = re.search(rf"^{re.escape(label)}\s+(\d+)\s*$", report, re.MULTILINE)
    return int(match.group(1)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    zips = {path.name: path for path in args.artifacts.glob("*.zip")}
    zip_digests = {name: sha256(path) for name, path in sorted(zips.items())}
    with tempfile.TemporaryDirectory() as work:
        extracted = Path(work)
        route = extracted / "route"
        functional = extracted / "functional"
        route.mkdir()
        functional.mkdir()
        with zipfile.ZipFile(zips[ROUTE_ZIP]) as archive:
            archive.extractall(route)
        with zipfile.ZipFile(zips[FUNCTIONAL_ZIP]) as archive:
            archive.extractall(functional)

        with one(route, "similarity_final_report_canary.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        row = rows[0] if len(rows) == 1 else {}
        manifest = json.loads(one(route, "flow_patch_manifest.json").read_text())
        frozen = json.loads(one(route, "summary.json").read_text())
        driver = one(route, "driver.log").read_text(encoding="utf-8", errors="replace")
        finish = one(route, "6_finish.rpt").read_text(encoding="utf-8", errors="replace")
        route_log = one(route, "5_2_route.log").read_text(encoding="utf-8", errors="replace")
        drc_report = one(route, "5_route_drc.rpt")
        functional_log = one(functional, "tb_8x6.log").read_text(
            encoding="utf-8", errors="replace"
        )

        identity = (
            row.get("platform"), row.get("topology"), row.get("rows"),
            row.get("cols"), row.get("seed"),
        )
        report_counts = {
            field: report_count(finish, label) for field, label in COUNTS.items()
        }
        csv_zero = all(row.get(field) == "0" for field in (*COUNTS, "drc_count"))
        report_zero = all(value == 0 for value in report_counts.values())
        route_ended_clean = (
            "[INFO DRT-0198] Complete detail routing." in route_log
            and re.search(r"\[INFO DRT-0199\]\s+Number of violations = 0\.", route_log)
            is not None
            and "[INFO ANT-0002] Found 0 net violations." in route_log
            and "[INFO ANT-0001] Found 0 pin violations." in route_log
            and drc_report.stat().st_size == 0
        )
        manifest_exact = (
            manifest.get("schema_version") == 1
            and manifest.get("orfs_image") == IMAGE
            and manifest.get("workflow_source_sha") == FROZEN_SHA
            and manifest.get("target") == "flow/scripts/final_outputs.tcl"
            and manifest.get("replacement_count") == 1
            and manifest.get("removed_text") == REMOVED
            and manifest.get("replacement_text") == REPLACEMENT
            and re.fullmatch(r"[0-9a-f]{64}", manifest.get("before_sha256", ""))
            is not None
            and re.fullmatch(r"[0-9a-f]{64}", manifest.get("after_sha256", ""))
            is not None
            and manifest.get("before_sha256") != manifest.get("after_sha256")
        )
        gates = {
            "original_artifact_digests_match_actions": (
                set(zips) == set(EXPECTED_ZIP_DIGESTS)
                and zip_digests == EXPECTED_ZIP_DIGESTS
            ),
            "signed_gemm_8x6": (
                "KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows=8 cols=6"
                in functional_log
            ),
            "exactly_one_frozen_identity": (
                len(rows) == 1
                and identity == ("sky130hd", "blocal", "8", "6", "173")
            ),
            "route_and_evidence_complete": (
                row.get("attempted", "").lower() == "true"
                and row.get("route_ok", "").lower() == "true"
                and not row.get("error_stage")
            ),
            "all_electrical_and_drc_counts_zero": (
                csv_zero and report_zero and route_ended_clean
            ),
            "all_metrics_and_product_hashes_valid": (
                all(positive(row.get(field, "")) for field in (
                    "period_min_ns", "critical_path_delay_ns", "total_cells",
                    "dff_cells", "cell_area_um2", "wire_length_um",
                ))
                and all(re.fullmatch(r"[0-9a-f]{64}", row.get(field, ""))
                        is not None for field in (
                            "gds_sha256", "odb_sha256", "spef_sha256",
                            "netlist_sha256",
                        ))
            ),
            "exact_single_gui_patch": manifest_exact,
            "driver_completed_without_signal_or_make_failure": (
                "===== native finish" in driver
                and "Signal 11 received" not in driver
                and "make: ***" not in driver
            ),
        }
        frozen_gates = frozen.get("gates", {})
        comparable = {key: gates[key] for key in frozen_gates}
        result = {
            "schema_version": 1,
            "frozen_source_sha": FROZEN_SHA,
            "artifact_zip_sha256": zip_digests,
            "gates": gates,
            "independent_canary_passed": all(gates.values()),
            "frozen_evaluator_agreement": (
                frozen.get("canary_passed") is True
                and comparable == frozen_gates
            ),
            "row": row,
            "report_counts": report_counts,
            "patch_manifest": manifest,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "gates": gates,
            "independent_canary_passed": result["independent_canary_passed"],
            "frozen_evaluator_agreement": result["frozen_evaluator_agreement"],
        }, indent=2))
        return 0 if (
            result["independent_canary_passed"]
            and result["frozen_evaluator_agreement"]
        ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
