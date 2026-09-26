import json

from scripts import similarity_blocal_qualified_route as route
from scripts import similarity_blocal_qualified_validate as validate


def test_frozen_matrix_is_exact_and_fresh():
    assert route.GEOMETRIES == (
        ("discovery", 6, 10),
        ("discovery", 10, 6),
        ("holdout", 7, 10),
        ("holdout", 10, 7),
    )
    assert route.SEEDS == (293, 317, 347)
    assert route.RATIO_MARGIN == 20
    assert not ({(rows, cols) for _, rows, cols in route.GEOMETRIES}
                & route.EXCLUDED_GEOMETRIES)
    assert not (set(route.SEEDS) & route.EXCLUDED_SEEDS)
    assert len(validate.expected_identities()) == 72
    assert validate.HOLDOUT_SHAPES == ((7, 10), (10, 7))


def test_added_schema_is_exact():
    assert route.FIELDS[-6:] == route.EXTRA_FIELDS
    assert {
        "routed_cell_area_um2",
        "vectorless_power_w",
        "cap_slack_fraction",
        "slew_slack_fraction",
        "final_antenna_net_violations",
        "final_antenna_pin_violations",
    } == set(route.EXTRA_FIELDS)


def test_exact_two_patch_manifest(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    final = scripts / "final_outputs.tcl"
    antenna = scripts / "global_route.tcl"
    final.write_text("prefix\n" + route.patch_flow.__globals__["FINAL_REMOVED"] + "suffix\n")
    antenna.write_text("prefix\n" + route.patch_flow.__globals__["ANTENNA_REMOVED"] + "suffix\n")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    manifest = tmp_path / "manifest.json"
    route.patch_flow(tmp_path, manifest)
    record = json.loads(manifest.read_text())
    assert record["workflow_source_sha"] == "a" * 40
    assert record["antenna_ratio_margin"] == 20
    assert len(record["patches"]) == 2


def test_parse_added_physical_metrics(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "logs" / "5_2_route.log").write_text(
        "Design area 123.5 um^2 35% utilization.\n"
        "Found 0 net violations.\nFound 0 pin violations.\n"
    )
    (tmp_path / "reports" / "6_finish.rpt").write_text(
        "finish max_capacitance_check_slack_limit\n---\n0.25\n"
        "finish max_slew_check_slack_limit\n---\n0.30\n"
        "Total  1e-3  2e-3  3e-3  6e-3 100.0%\n"
    )
    row = {"route_ok": True, "error_stage": ""}
    route.add_physical_metrics(row, tmp_path)
    assert row["route_ok"] is True
    assert row["routed_cell_area_um2"] == 123.5
    assert row["vectorless_power_w"] == 0.006
    assert row["cap_slack_fraction"] == 0.25
    assert row["slew_slack_fraction"] == 0.30
    assert row["final_antenna_net_violations"] == 0
    assert row["final_antenna_pin_violations"] == 0
