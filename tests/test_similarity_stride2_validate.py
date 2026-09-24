"""Check the frozen prospective evaluator on complete data and physical nulls."""

import csv
import json
import sys

from scripts.similarity_asic_transfer_route import (
    DISCOVERY_GEOMETRIES, FIELDS, HOLDOUT_GEOMETRIES, SEEDS as OLD_SEEDS,
)
from scripts.similarity_stride2_route import GEOMETRIES, PLATFORMS, SEEDS, TOPOLOGIES
from scripts.similarity_stride2_validate import expected_keys, main, summarize


def plausible_rows():
    rows = []
    for platform in PLATFORMS:
        for topology in TOPOLOGIES:
            for seed in SEEDS:
                for split, height, width in GEOMETRIES:
                    row = dict.fromkeys(FIELDS, "")
                    row.update({
                        "platform": platform, "topology": topology, "seed": str(seed),
                        "split": split, "rows": str(height), "cols": str(width),
                        "attempted": "True", "route_ok": "True",
                        "period_min_ns": {"broadcast": "2.0", "local": "1.7", "stride2": "1.75"}[topology],
                        "cell_area_um2": {"broadcast": "100", "local": "120", "stride2": "105"}[topology],
                        "dff_cells": {"broadcast": "100", "local": "200", "stride2": "150"}[topology],
                        "total_cells": "200", "wire_length_um": "1000",
                        "gds_sha256": "a" * 64, "odb_sha256": "a" * 64,
                        "spef_sha256": "a" * 64, "netlist_sha256": "a" * 64,
                    })
                    for field in (
                        "setup_violations", "hold_violations", "max_slew_violations",
                        "max_fanout_violations", "max_cap_violations", "drc_count",
                    ):
                        row[field] = "0"
                    rows.append(row)
    return rows


def test_new_geometry_and_seed_firewall():
    prior = set(DISCOVERY_GEOMETRIES + HOLDOUT_GEOMETRIES)
    assert len({(r, c) for _, r, c in GEOMETRIES}) == 4
    assert {(r, c) for _, r, c in GEOMETRIES}.isdisjoint(prior)
    assert set(SEEDS).isdisjoint(OLD_SEEDS)
    assert sum(split == "discovery" for split, _, _ in GEOMETRIES) == 2
    assert sum(split == "holdout" for split, _, _ in GEOMETRIES) == 2


def test_full_matrix_supports_claim_only_with_functional_equivalence():
    rows = plausible_rows()
    assert len(expected_keys()) == len(rows) == 72
    result = summarize(rows, True)
    assert result["claim_supported"]
    assert result["complete_triples"] == 24
    assert len(result["points"]) == 8
    assert not summarize(rows, False)["claim_supported"]


def test_duplicate_missing_and_electrical_null_each_reject_claim():
    rows = plausible_rows()
    assert not summarize(rows[:-1] + [rows[0]], True)["gates"]["exactly_72_unique_attempts"]
    rows[0]["max_cap_violations"] = "1"
    result = summarize(rows, True)
    assert result["attempted"] == 72
    assert result["clean"] == 71
    assert not result["gates"]["all_72_final_routes_clean"]
    assert not result["claim_supported"]


def test_nonfinite_metric_remains_a_reportable_null():
    rows = plausible_rows()
    rows[0]["cell_area_um2"] = "inf"
    result = summarize(rows, True)
    assert result["clean"] == 71
    assert not result["claim_supported"]
    json.dumps(result, allow_nan=False)


def test_artifact_layout_and_missing_functional_marker(tmp_path, monkeypatch):
    artifacts = tmp_path / "download"
    output = tmp_path / "summary.json"
    rows = plausible_rows()
    for platform in PLATFORMS:
        for topology in TOPOLOGIES:
            for seed in SEEDS:
                shard = artifacts / f"similarity-stride2-route-{platform}-{topology}-s{seed}"
                shard.mkdir(parents=True)
                with (shard / f"similarity_stride2_{platform}_{topology}_s{seed}.csv").open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=FIELDS)
                    writer.writeheader()
                    writer.writerows(row for row in rows if
                                     row["platform"] == platform
                                     and row["topology"] == topology
                                     and row["seed"] == str(seed))
    marker = artifacts / "similarity-stride2-functional" / "similarity_stride2_functional_passed"
    marker.parent.mkdir()
    marker.touch()
    monkeypatch.setattr(sys, "argv", ["validate", "--input", str(artifacts), "--output", str(output)])
    assert main() == 0
    assert json.loads(output.read_text())["claim_supported"]
    marker.unlink()
    assert main() == 1
    assert json.loads(output.read_text())["gates"]["functional_equivalence"] is False
