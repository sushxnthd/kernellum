#!/usr/bin/env python3
"""Independent raw-artifact audit for Kernellum antenna-margin canary run 36173718315."""

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

SOURCE_SHA = "952bc668d50222ecd274b72150b511f291aae61b"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
EXPECTED_ZIPS = {
    "final-summary.zip": "286ee8328622bab091b93689f5da0e41542db2b7335057c55afba07802adbd78",
    "functional.zip": "9a8074c3c36e4c6698d5edf3c99d2c45d4a30d46e785fbce4a9bc5a2e6a8533c",
    "nangate45-blocal.zip": "6748f18c386ea248711b21179e6c244e4ac27acc5d4fae75f5d0ce460325a763",
    "nangate45-broadcast.zip": "6259d82b09cb4581a0f26962204343c4064ac2fe04c5f76a0f7c710b39759872",
    "nangate45-local.zip": "13527c6b964845820d7410d865523cd79d9fb890a81d5d3c64dc8e8073b09135",
    "sky130hd-blocal.zip": "1b4cc8a204230bf327c6513323b13f4147384cffa85982b1bc7b6bae8d29af1d",
    "sky130hd-broadcast.zip": "850a5e9d9df2b69c359c318215549f91dcd9d299bf068c1786f52251d9c969c0",
    "sky130hd-local.zip": "ccc4bf443105d4482b80f55188fce2ba8d03ddc3d86f8e9e538197ba8e325ba7",
}
STRUCTURE = {
    ("nangate45", "blocal"): (2492, 69830.32),
    ("nangate45", "broadcast"): (1674, 65164.148),
    ("nangate45", "local"): (2846, 71538.306),
    ("sky130hd", "blocal"): (2492, 327550.3968),
    ("sky130hd", "broadcast"): (1674, 308686.0544),
    ("sky130hd", "local"): (2846, 337062.0192),
}
EXPECTED_IDS = {(p, t, 277, 10, 5) for p in ("nangate45", "sky130hd")
                for t in ("broadcast", "local", "blocal")}
VIOLATIONS = ("setup_violations", "hold_violations", "max_slew_violations",
              "max_fanout_violations", "max_cap_violations", "drc_count")
POSITIVE = ("period_min_ns", "fmax_mhz", "critical_path_delay_ns", "total_cells",
            "dff_cells", "cell_area_um2", "wire_length_um")
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")
HEX64 = re.compile(r"[0-9a-f]{64}")
ANTENNA_REPLACEMENT = (
    "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT) "
    "-ratio_margin 20\n"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def one(root: Path, pattern: str) -> Path:
    paths = sorted(root.rglob(pattern))
    if len(paths) != 1:
        raise AssertionError(f"expected one {pattern}, found {len(paths)}")
    return paths[0]


def finish_metric(text: str, name: str) -> float:
    match = re.search(rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text)
    if not match:
        raise AssertionError(f"missing finish metric {name}")
    return float(match.group(1))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def audit(zip_dir: Path) -> dict[str, object]:
    zip_paths = {p.name: p for p in zip_dir.glob("*.zip")}
    require(set(zip_paths) == set(EXPECTED_ZIPS), "artifact ZIP set mismatch")
    zip_digests = {name: sha256(path) for name, path in sorted(zip_paths.items())}
    require(zip_digests == EXPECTED_ZIPS, "artifact ZIP digest mismatch")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name, path in zip_paths.items():
            destination = root / name.removesuffix(".zip")
            destination.mkdir()
            with zipfile.ZipFile(path) as archive:
                archive.extractall(destination)

        source_sha = one(root, "source_sha.txt").read_text().strip()
        require(source_sha == SOURCE_SHA, "source SHA mismatch")
        functional_log = one(root, "tb_10x5.log").read_text(errors="replace")
        require("KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows=10 cols=5" in functional_log,
                "signed-GEMM evidence missing")

        csvs = sorted(root.rglob("similarity_antenna_margin_*.csv"))
        require(len(csvs) == 6, f"expected six CSVs, found {len(csvs)}")
        rows: list[dict[str, str]] = []
        for path in csvs:
            with path.open(newline="", encoding="utf-8") as handle:
                rows.extend(csv.DictReader(handle))
        require(len(rows) == 6, f"expected six rows, found {len(rows)}")
        identities = {(r["platform"], r["topology"], int(r["seed"]),
                       int(r["rows"]), int(r["cols"])) for r in rows}
        require(identities == EXPECTED_IDS, "route identity matrix mismatch")
        for row in rows:
            require(row["attempted"].lower() == "true" and row["route_ok"].lower() == "true",
                    "unattempted or failed route")
            require(row["error_stage"] == "", "unexpected route error stage")
            require(all(int(row[key]) == 0 for key in VIOLATIONS), "electrical/DRC violation")
            require(all(math.isfinite(float(row[key])) and float(row[key]) > 0 for key in POSITIVE),
                    "non-positive route metric")
            require(all(HEX64.fullmatch(row[key]) for key in HASHES), "invalid product digest")
            expected_dff, expected_area = STRUCTURE[(row["platform"], row["topology"])]
            require(int(row["dff_cells"]) == expected_dff, "DFF mismatch")
            require(float(row["cell_area_um2"]) == expected_area, "synthesis-area mismatch")

        manifests = sorted(root.rglob("flow_patch_antenna_margin_*.json"))
        require(len(manifests) == 6, "manifest count mismatch")
        for path in manifests:
            manifest = json.loads(path.read_text())
            require(manifest["schema_version"] == 1, "manifest schema mismatch")
            require(manifest["orfs_image"] == IMAGE, "ORFS image mismatch")
            require(manifest["workflow_source_sha"] == SOURCE_SHA, "manifest SHA mismatch")
            require(manifest["antenna_ratio_margin"] == 20, "ratio margin mismatch")
            patches = manifest["patches"]
            require(len(patches) == 2, "patch count mismatch")
            require([p["replacement_count"] for p in patches] == [1, 1],
                    "patch replacement count mismatch")
            require(patches[1]["target"] == "flow/scripts/global_route.tcl", "antenna target mismatch")
            require(patches[1]["replacement_text"] == ANTENNA_REPLACEMENT,
                    "antenna replacement mismatch")
            require(all(HEX64.fullmatch(p["before_sha256"]) and HEX64.fullmatch(p["after_sha256"])
                        for p in patches), "invalid patch digest")

        drivers = sorted(root.rglob("driver.log"))
        require(len(drivers) == 6, "driver count mismatch")
        for path in drivers:
            text = path.read_text(errors="replace")
            require("===== native finish" in text, "native finish missing")
            require("Signal 11 received" not in text and "make: ***" not in text,
                    "driver crash/make failure")

        reports = sorted(root.rglob("6_finish.rpt"))
        require(len(reports) == 6, "finish-report count mismatch")
        headroom: list[dict[str, object]] = []
        for path in reports:
            text = path.read_text(errors="replace")
            cap = finish_metric(text, "max_capacitance_check_slack_limit")
            slew = finish_metric(text, "max_slew_check_slack_limit")
            require(cap >= 0.02 and slew >= 0.02, "insufficient electrical headroom")
            headroom.append({"file": path.relative_to(root).as_posix(),
                             "cap_fraction": cap, "slew_fraction": slew})

        drc_reports = sorted(root.rglob("5_route_drc.rpt"))
        require(len(drc_reports) == 6 and all(not p.read_text().strip() for p in drc_reports),
                "non-empty detailed-route DRC report")
        route_logs = sorted(root.rglob("5_2_route.log"))
        require(len(route_logs) == 6, "route-log count mismatch")
        antenna: list[dict[str, object]] = []
        for path in route_logs:
            text = path.read_text(errors="replace")
            nets = [int(x) for x in re.findall(r"Found (\d+) net violations\.", text)]
            pins = [int(x) for x in re.findall(r"Found (\d+) pin violations\.", text)]
            drcs = [int(x) for x in re.findall(r"Number of violations = (\d+)\.", text)]
            require(nets and pins and drcs, "missing final route evidence")
            require((nets[-1], pins[-1], drcs[-1]) == (0, 0, 0),
                    "final antenna/DRC violation")
            antenna.append({"file": path.relative_to(root).as_posix(),
                            "net_violations": nets[-1], "pin_violations": pins[-1],
                            "drc_violations": drcs[-1]})

        summary = json.loads(one(root, "similarity_antenna_margin_canary_summary.json").read_text())
        require(summary["source_sha"] == SOURCE_SHA and summary["canary_pass"] is True,
                "official summary mismatch")
        require(summary["planned"] == 6 and summary["attempted"] == 6 and summary["clean"] == 6,
                "official row counts mismatch")
        require(all(summary["gates"].values()), "official frozen gate is false")

        extracted_digests = {
            p.relative_to(root).as_posix(): sha256(p)
            for p in sorted(root.rglob("*")) if p.is_file()
        }
        return {
            "schema_version": 1,
            "run_id": 36173718315,
            "source_sha": SOURCE_SHA,
            "artifact_zip_sha256": zip_digests,
            "artifact_digests_match_github": True,
            "extracted_file_count": len(extracted_digests),
            "extracted_file_sha256": extracted_digests,
            "independent_gates": {
                "signed_gemm": True,
                "exact_six_row_matrix": True,
                "source_and_patch_identity": True,
                "six_native_finishes": True,
                "all_electrical_and_drc_clean": True,
                "minimum_two_percent_cap_and_slew_headroom": True,
                "final_antenna_zero": True,
                "exact_dff_and_synthesis_area": True,
                "official_summary_consistent": True,
            },
            "minimum_cap_headroom_fraction": min(x["cap_fraction"] for x in headroom),
            "minimum_slew_headroom_fraction": min(x["slew_fraction"] for x in headroom),
            "headroom": headroom,
            "final_antenna_and_drc": antenna,
            "verdict": "PASS",
            "interpretation": "opened-data flow qualification only; not architectural confirmation",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.zip_dir)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {"extracted_file_sha256", "headroom", "final_antenna_and_drc"}},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
