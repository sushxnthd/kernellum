#!/usr/bin/env python3
"""Independent raw-artifact audit for runtime/headroom canary run 36281577690."""

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


RUN_ID = 36281577690
SOURCE_SHA = "8eb81e96eb1a33ed7f5e0759dece9b365fb52a5a"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
EXPECTED_ZIPS = {
    "similarity-runtime-headroom-final-summary.zip": "8802afe0748438281a4084f1a84cc697d1fe17977c98d38e3e3da9c7cc0a623d",
    "similarity-runtime-headroom-functional.zip": "6c3c095f762868ea88ba1c3c25e7acdb80c5ac31190939da75371d5a11096b18",
    "similarity-runtime-headroom-nangate45-blocal-s373-r10c7.zip": "eb5eb1464c0b3fa7de1f8a2c2dc85f2520ee160608c4940b11a6d9fbbb20e812",
    "similarity-runtime-headroom-nangate45-blocal-s373-r7c10.zip": "46ff7720d5b55731e8f0388a6b79701b33a79397feed51ba86a64f2472b8ce56",
    "similarity-runtime-headroom-nangate45-broadcast-s373-r10c7.zip": "f19f4db2b06367de0c69bb847db9e5f66a800b6c5f76ee74c5889b07f1c2a8bc",
    "similarity-runtime-headroom-nangate45-broadcast-s373-r7c10.zip": "74305103abb4899c242e4f634eef99d0fef71fee43934276fd4812ee1c0016eb",
    "similarity-runtime-headroom-nangate45-local-s373-r10c7.zip": "94a695db4d902f2244da245a585619aa2278fed8b102d08ea87c6cdca49ee06c",
    "similarity-runtime-headroom-nangate45-local-s373-r7c10.zip": "5c7f874f951ae0386eea3dd39b82cd1ea135b063aac463adfd441cd12b1d13df",
    "similarity-runtime-headroom-sky130hd-blocal-s373-r10c7.zip": "8a6a2f6a34212068691392eeed7f2f8dc04d18d160c2f6701c43fe033dac27d7",
    "similarity-runtime-headroom-sky130hd-blocal-s373-r7c10.zip": "0a9217732a874d09484922f22a3d2618ae15faa80b665b0c86c7ec6e1e900c47",
    "similarity-runtime-headroom-sky130hd-broadcast-s373-r10c7.zip": "470ccc432f2a13cc2836a0520a357dfc51d4d921e980765c2311c01f8f00373d",
    "similarity-runtime-headroom-sky130hd-broadcast-s373-r7c10.zip": "f178fc53d5690945158ed2f285851eef8a32d79d167802c695bfe2e40b6c55bb",
    "similarity-runtime-headroom-sky130hd-local-s373-r10c7.zip": "d6d6f51094dba7ef6d198811182196e45a2edf18c6e254b2bc5635761db5b7f3",
    "similarity-runtime-headroom-sky130hd-local-s373-r7c10.zip": "9d4ce50abaab7347edb0e1e29272b16b61f18490163527a66aba1ee431bab5aa",
}
EXPECTED_SOURCE_HASHES = {
    "docs/SIMILARITY_RUNTIME_HEADROOM_CANARY.md": "7da2478331f07d200af8b3524e2350b7f921cb92b69c8f9675b775e103bf2ebd",
    "scripts/similarity_runtime_headroom_canary.py": "2ed9fb5b2f94d6e6de70730d0e7e47f574bc91237d94ee89fd933ef796f38e9d",
    "scripts/similarity_asic_transfer_route.py": "e332b794334e00cbabe2caccdc16e7bb2873e2b32ea337434a78eb668caca17e",
    "scripts/similarity_antenna_margin_canary.py": "74c8210fc72623e5a904770e211f3cbad577417f9931ca67e905a1e2e1903078",
    "scripts/similarity_blocal_qualified_route.py": "809379ccaa43519875ba18f44f97370502209cf18b79855e630fa0a67295333e",
    "asic/runtime_headroom_canary/blocal_config_nangate45.mk": "2ad94350df98d4a5a61e1d48dab2dfcb72e117d45a9257145ca236aa9a255004",
    "asic/runtime_headroom_canary/blocal_config_sky130hd.mk": "fce5737d6d780f75feca96362f81644ccf0189dbee00558dd6535626bae0b78c",
    "asic/runtime_headroom_canary/controls_config_nangate45.mk": "93ea177cb3a7bf331c213ca1b61f8b993aa6b7aecf48d90d5d8ff0c304430af8",
    "asic/runtime_headroom_canary/controls_config_sky130hd.mk": "7b8ed0a0a75e926ff93dfea5174988b36aa2af18218902d56f85c0e956f612bf",
    "rtl/kernellum_mac_array.sv": "6863f5e01d83d2833805a41824b0d1ef2bd6c92cc5c6626af6566c99037a77e6",
    "rtl/kernellum_local_mac_array.sv": "9e01f43a09d43ad62ca6582d87902b32c3691b8117dddaf0be7f542d157201ff",
    "rtl/kernellum_blocal_mac_array.sv": "7cdd3223ac401ec9c9df5a792cb41f2e754262dbd2c6fad103752fce7afdc766",
    "rtl/similarity_asic_transfer_top.sv": "28159be6fffb2a74e15f64db6c013b018948c54546f43ec142a77070005bfc78",
    "rtl/similarity_asic_transfer_blocal.sv": "1f6bd084dab5e368f34dee5c44fb6ca12a68860b4b26fff2f78b85277d50552a",
}
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
EXPECTED_IDS = {
    (platform, topology, 373, rows, cols)
    for platform in ("nangate45", "sky130hd")
    for topology in ("broadcast", "local", "blocal")
    for rows, cols in ((7, 10), (10, 7))
}
VIOLATIONS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
)
POSITIVE = (
    "period_min_ns", "fmax_mhz", "critical_path_delay_ns", "total_cells",
    "dff_cells", "cell_area_um2", "wire_length_um", "routed_cell_area_um2",
    "vectorless_power_w", "elapsed_sec",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")
HEX64 = re.compile(r"[0-9a-f]{64}")
FINAL_REMOVED = (
    "# Save a final image if openroad is compiled with the gui\n"
    "if { [ord::openroad_gui_compiled] } {\n"
    "  gui::show \"source $::env(SCRIPTS_DIR)/save_images.tcl\" false\n"
    "}\n"
)
FINAL_REPLACEMENT = (
    "# Optional GUI images intentionally disabled for deterministic headless evidence.\n"
)
ANTENNA_REMOVED = (
    "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT)\n"
)
ANTENNA_REPLACEMENT = (
    "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT) "
    "-ratio_margin 20\n"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def one(root: Path, pattern: str) -> Path:
    paths = sorted(root.rglob(pattern))
    require(len(paths) == 1, f"expected one {pattern}, found {len(paths)}")
    return paths[0]


def finish_number(text: str, name: str) -> float:
    match = re.search(rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text)
    require(match is not None, f"missing finish metric {name}")
    return float(match.group(1))


def finish_count(text: str, name: str, label: str) -> int:
    match = re.search(
        rf"finish {re.escape(name)}\s*\n-+\s*\n{re.escape(label)} (\d+)", text
    )
    require(match is not None, f"missing finish count {name}")
    return int(match.group(1))


def audit(zip_dir: Path) -> dict[str, object]:
    zip_paths = {path.name: path for path in zip_dir.glob("*.zip")}
    require(set(zip_paths) == set(EXPECTED_ZIPS), "artifact ZIP set mismatch")
    zip_digests = {name: sha256(path) for name, path in sorted(zip_paths.items())}
    require(zip_digests == EXPECTED_ZIPS, "artifact ZIP digest mismatch")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name, path in zip_paths.items():
            destination = root / name.removesuffix(".zip")
            destination.mkdir()
            with zipfile.ZipFile(path) as archive:
                require(archive.testzip() is None, f"corrupt ZIP member in {name}")
                archive.extractall(destination)

        require(one(root, "source_sha.txt").read_text().strip() == SOURCE_SHA,
                "source SHA mismatch")
        source_hashes = {}
        for line in one(root, "source_hashes.txt").read_text().splitlines():
            digest, name = line.split(maxsplit=1)
            source_hashes[name] = digest
        require(source_hashes == EXPECTED_SOURCE_HASHES, "source hash manifest mismatch")

        functional_logs = sorted(root.rglob("tb_*.log"))
        require({path.name for path in functional_logs} == {"tb_7x10.log", "tb_10x7.log"},
                "functional log set mismatch")
        for rows, cols in ((7, 10), (10, 7)):
            text = one(root, f"tb_{rows}x{cols}.log").read_text(errors="replace")
            require(f"KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows={rows} cols={cols}" in text,
                    f"signed-GEMM marker missing for {rows}x{cols}")

        csvs = sorted(root.rglob("similarity_runtime_headroom_*.csv"))
        require(len(csvs) == 12, f"expected 12 CSVs, found {len(csvs)}")
        rows: list[dict[str, str]] = []
        for path in csvs:
            with path.open(newline="", encoding="utf-8") as handle:
                rows.extend(csv.DictReader(handle))
        require(len(rows) == 12, f"expected 12 rows, found {len(rows)}")
        identities = {
            (row["platform"], row["topology"], int(row["seed"]),
             int(row["rows"]), int(row["cols"])) for row in rows
        }
        require(identities == EXPECTED_IDS, "route identity matrix mismatch")
        for row in rows:
            require(row["split"] == "opened_canary", "split mismatch")
            require(row["attempted"].lower() == "true" and row["route_ok"].lower() == "true",
                    "unattempted or failed route")
            require(row["error_stage"] == "", "unexpected route error stage")
            require(all(int(row[field]) == 0 for field in VIOLATIONS),
                    "CSV electrical or DRC violation")
            require(all(math.isfinite(float(row[field])) and float(row[field]) > 0
                        for field in POSITIVE), "non-positive route metric")
            require(all(HEX64.fullmatch(row[field]) for field in HASHES),
                    "invalid product digest")
            require(int(row["final_antenna_net_violations"]) == 0 and
                    int(row["final_antenna_pin_violations"]) == 0,
                    "CSV final antenna violation")
            require(float(row["cap_slack_fraction"]) >= 0.02 and
                    float(row["slew_slack_fraction"]) >= 0.02,
                    "CSV headroom below two percent")
            expected_dff, expected_area = STRUCTURE[
                (row["platform"], row["topology"], int(row["rows"]), int(row["cols"]))
            ]
            require(int(row["dff_cells"]) == expected_dff, "DFF mismatch")
            require(float(row["cell_area_um2"]) == expected_area,
                    "synthesis-area mismatch")

        manifests = sorted(root.rglob("flow_patch_runtime_headroom_*.json"))
        require(len(manifests) == 12, "manifest count mismatch")
        for path in manifests:
            manifest = json.loads(path.read_text())
            require(manifest["schema_version"] == 1, "manifest schema mismatch")
            require(manifest["orfs_image"] == IMAGE, "ORFS image mismatch")
            require(manifest["workflow_source_sha"] == SOURCE_SHA, "manifest SHA mismatch")
            require(manifest["native_stage_timeout_seconds"] == 7200,
                    "stage timeout mismatch")
            require(manifest["cap_margin"] == 31 and manifest["slew_margin"] == 25,
                    "electrical margin mismatch")
            require(manifest["antenna_ratio_margin"] == 20, "antenna margin mismatch")
            require(manifest["canary_seed"] == 373, "canary seed mismatch")
            require(manifest["geometries"] == [[7, 10], [10, 7]], "geometry mismatch")
            patches = manifest["patches"]
            require(len(patches) == 2 and [patch["replacement_count"] for patch in patches] == [1, 1],
                    "patch count mismatch")
            require(patches[0]["target"] == "flow/scripts/final_outputs.tcl" and
                    patches[0]["removed_text"] == FINAL_REMOVED and
                    patches[0]["replacement_text"] == FINAL_REPLACEMENT,
                    "headless-report patch mismatch")
            require(patches[1]["target"] == "flow/scripts/global_route.tcl" and
                    patches[1]["removed_text"] == ANTENNA_REMOVED and
                    patches[1]["replacement_text"] == ANTENNA_REPLACEMENT,
                    "antenna patch mismatch")
            require(all(HEX64.fullmatch(patch["before_sha256"]) and
                        HEX64.fullmatch(patch["after_sha256"]) for patch in patches),
                    "invalid patch digest")

        drivers = sorted(root.rglob("driver.log"))
        require(len(drivers) == 12, "driver count mismatch")
        for path in drivers:
            text = path.read_text(errors="replace")
            require("===== native finish" in text, "native finish missing")
            require("TIMEOUT" not in text and "Signal 11 received" not in text and
                    "make: ***" not in text, "timeout, crash or make failure")

        reports = sorted(root.rglob("6_finish.rpt"))
        require(len(reports) == 12, "finish-report count mismatch")
        headroom = []
        for path in reports:
            text = path.read_text(errors="replace")
            cap = finish_number(text, "max_capacitance_check_slack_limit")
            slew = finish_number(text, "max_slew_check_slack_limit")
            require(cap >= 0.02 and slew >= 0.02, "raw-report headroom below two percent")
            counts = {
                "max_slew": finish_count(text, "max_slew_violation_count",
                                          "max slew violation count"),
                "max_fanout": finish_count(text, "max_fanout_violation_count",
                                            "max fanout violation count"),
                "max_cap": finish_count(text, "max_cap_violation_count",
                                         "max cap violation count"),
                "setup": finish_count(text, "setup_violation_count",
                                       "setup violation count"),
                "hold": finish_count(text, "hold_violation_count",
                                      "hold violation count"),
            }
            require(all(value == 0 for value in counts.values()),
                    "raw finish-report electrical violation")
            headroom.append({
                "file": path.relative_to(root).as_posix(),
                "cap_fraction": cap,
                "slew_fraction": slew,
                "violation_counts": counts,
            })

        drc_reports = sorted(root.rglob("5_route_drc.rpt"))
        require(len(drc_reports) == 12 and all(not path.read_text().strip()
                                               for path in drc_reports),
                "non-empty detailed-route DRC report")
        route_logs = sorted(root.rglob("5_2_route.log"))
        require(len(route_logs) == 12, "route-log count mismatch")
        route_results = []
        for path in route_logs:
            text = path.read_text(errors="replace")
            nets = [int(value) for value in re.findall(r"Found (\d+) net violations\.", text)]
            pins = [int(value) for value in re.findall(r"Found (\d+) pin violations\.", text)]
            drcs = [int(value) for value in re.findall(r"Number of violations = (\d+)\.", text)]
            require(nets and pins and drcs, "missing raw route evidence")
            require((nets[-1], pins[-1], drcs[-1]) == (0, 0, 0),
                    "final antenna or DRC violation")
            route_results.append({
                "file": path.relative_to(root).as_posix(),
                "net_violations": nets[-1],
                "pin_violations": pins[-1],
                "drc_violations": drcs[-1],
            })

        summary = json.loads(one(root, "similarity_runtime_headroom_canary_summary.json").read_text())
        require(summary["source_sha"] == SOURCE_SHA and summary["canary_pass"] is True,
                "official verdict mismatch")
        require(summary["planned"] == summary["attempted"] == summary["clean"] == 12,
                "official row-count mismatch")
        require(all(summary["gates"].values()), "official frozen gate is false")
        official_rows = sorted(summary["rows"], key=lambda row: (
            row["platform"], row["topology"], int(row["rows"]), int(row["cols"])
        ))
        raw_rows = sorted(rows, key=lambda row: (
            row["platform"], row["topology"], int(row["rows"]), int(row["cols"])
        ))
        require(official_rows == raw_rows, "official summary rows differ from raw CSV rows")

        extracted_digests = {
            path.relative_to(root).as_posix(): sha256(path)
            for path in sorted(root.rglob("*")) if path.is_file()
        }
        return {
            "schema_version": 1,
            "run_id": RUN_ID,
            "source_sha": SOURCE_SHA,
            "artifact_zip_sha256": zip_digests,
            "artifact_digests_match_github": True,
            "extracted_file_count": len(extracted_digests),
            "extracted_file_sha256": extracted_digests,
            "independent_gates": {
                "signed_gemm_on_both_shapes": True,
                "exact_12_row_matrix": True,
                "source_and_patch_identity": True,
                "all_12_native_finishes": True,
                "all_12_electrically_and_drc_clean": True,
                "all_12_at_least_two_percent_cap_and_slew_headroom": True,
                "all_12_final_antenna_clean": True,
                "exact_dff_and_synthesis_area": True,
                "official_summary_consistent": True,
            },
            "minimum_cap_headroom_fraction": min(item["cap_fraction"] for item in headroom),
            "minimum_slew_headroom_fraction": min(item["slew_fraction"] for item in headroom),
            "headroom": headroom,
            "final_antenna_and_drc": route_results,
            "verdict": "PASS",
            "interpretation": (
                "opened-data flow qualification only; not architectural confirmation, "
                "novelty evidence or a rescue of any prior null"
            ),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.zip_dir)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    compact = {key: value for key, value in result.items()
               if key not in {"extracted_file_sha256", "headroom", "final_antenna_and_drc"}}
    print(json.dumps(compact, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
