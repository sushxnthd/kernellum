import csv
import subprocess
from pathlib import Path
from unittest.mock import patch

from scripts.similarity_asic_transfer_route import (
    DISCOVERY_GEOMETRIES,
    FIELDS,
    HOLDOUT_GEOMETRIES,
    SEEDS,
    geometries,
    parse_finish,
    parse_synthesis,
    parse_wire_length,
    run_stage,
)
from scripts.similarity_asic_transfer_validate import (
    evaluate,
    expected_keys,
    functional_marker_exists,
    route_csv_paths,
)


def make_row(platform, split, topology, seed, rows, cols, period, dffs):
    row = {field: "" for field in FIELDS}
    row.update({
        "platform": platform,
        "split": split,
        "topology": topology,
        "rows": rows,
        "cols": cols,
        "pe_count": rows * cols,
        "sqrt_pe": (rows * cols) ** 0.5,
        "seed": seed,
        "attempted": True,
        "route_ok": True,
        "period_min_ns": period,
        "fmax_mhz": 1000.0 / period,
        "critical_path_delay_ns": period + 0.1,
        "setup_violations": 0,
        "hold_violations": 0,
        "max_slew_violations": 0,
        "max_fanout_violations": 0,
        "max_cap_violations": 0,
        "drc_count": 0,
        "total_cells": 1000 + rows * cols * 10 + dffs,
        "dff_cells": dffs,
        "cell_area_um2": 2000.0 + rows * cols * 100.0 + dffs,
        "wire_length_um": 5000.0 + rows * cols * 200.0 + dffs,
        "gds_sha256": "a" * 64,
        "odb_sha256": "b" * 64,
        "spef_sha256": "c" * 64,
        "netlist_sha256": "d" * 64,
        "elapsed_sec": 1.0,
    })
    return row


def passing_rows():
    rows = []
    seed_scale = {11: 0.999, 29: 1.0, 47: 1.001}
    for platform in ("nangate45", "sky130hd"):
        for split, row_count, col_count in geometries(platform):
            sqrt_pe = (row_count * col_count) ** 0.5
            nangate_q = 0.01 + 0.01 * sqrt_pe
            q = nangate_q if platform == "nangate45" else 0.005 + 1.1 * nangate_q
            if split == "holdout":
                q += 0.002 if row_count < col_count else -0.002
            for seed in SEEDS:
                broadcast_period = (8.0 if platform == "nangate45" else 12.0) * seed_scale[seed]
                local_period = broadcast_period * (1.0 - q)
                broadcast_dffs = 100 + row_count * col_count
                local_dffs = broadcast_dffs + row_count * col_count * 2
                rows.append(make_row(
                    platform, split, "broadcast", seed, row_count, col_count,
                    broadcast_period, broadcast_dffs,
                ))
                rows.append(make_row(
                    platform, split, "local", seed, row_count, col_count,
                    local_period, local_dffs,
                ))
    return rows


def test_frozen_route_matrix_has_96_unique_implementations():
    assert len(expected_keys()) == 96
    assert len(DISCOVERY_GEOMETRIES) == 6
    assert len(HOLDOUT_GEOMETRIES) == 4
    assert SEEDS == (11, 29, 47)
    assert (3, 3) not in DISCOVERY_GEOMETRIES + HOLDOUT_GEOMETRIES


def test_synthetic_passing_dataset_satisfies_every_frozen_gate():
    result = evaluate(passing_rows(), functional_passed=True)
    assert result["attempted_routes"] == 96
    assert result["successful_routes"] == 96
    assert result["claim_supported"]
    assert all(result["gates"].values())


def test_functional_failure_cannot_be_rescued_by_physical_results():
    result = evaluate(passing_rows(), functional_passed=False)
    assert not result["gates"]["functional_equivalence"]
    assert not result["claim_supported"]


def test_downloaded_artifact_subdirectories_are_discovered(tmp_path: Path):
    route_directory = tmp_path / "route-artifact" / "results"
    route_directory.mkdir(parents=True)
    route_csv = route_directory / "similarity_asic_transfer_nangate45_broadcast_s11.csv"
    with route_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(make_row(
            "nangate45", "discovery", "broadcast", 11, 2, 4, 8.0, 108,
        ))

    marker = tmp_path / "functional-artifact" / "results"
    marker.mkdir(parents=True)
    (marker / "similarity_asic_transfer_functional_passed").touch()

    assert route_csv_paths(tmp_path) == [route_csv]
    assert functional_marker_exists(tmp_path)


def test_report_parsers_use_final_route_endpoints(tmp_path: Path):
    finish = tmp_path / "6_finish.rpt"
    finish.write_text(
        "clk period_min = 7.25 fmax = 137.93\n"
        "setup violation count 0\n"
        "hold violation count 0\n"
        "max slew violation count 0\n"
        "max fanout violation count 0\n"
        "max cap violation count 0\n"
        "finish critical path delay\n--------------------------\n7.41\n",
        encoding="utf-8",
    )
    assert parse_finish(finish)["period_min_ns"] == 7.25

    synthesis = tmp_path / "synth_stat.txt"
    synthesis.write_text(
        "  123 x 1 y cells\n"
        "  32 x 1 y sky130_fd_sc_hd__dfxtp_1\n"
        "Chip area for module 'top': 456.75\n",
        encoding="utf-8",
    )
    parsed = parse_synthesis(synthesis)
    assert parsed["total_cells"] == 123
    assert parsed["dff_cells"] == 32
    assert parsed["cell_area_um2"] == 456.75

    route_log = tmp_path / "5_2_route.log"
    route_log.write_text(
        "Total wire length = 100.0 um.\nTotal wire length = 125.5 um.\n",
        encoding="utf-8",
    )
    assert parse_wire_length(route_log) == 125.5


def test_timeout_bytes_are_preserved_in_null_route_log(tmp_path: Path):
    log = tmp_path / "driver.log"
    timeout = subprocess.TimeoutExpired(["route"], 3600, output=b"partial output\n")
    with patch("scripts.similarity_asic_transfer_route.subprocess.run", side_effect=timeout):
        assert run_stage(["route"], log, "frozen route") == 124
    assert "partial output\n\nTIMEOUT\n" in log.read_text(encoding="utf-8")
