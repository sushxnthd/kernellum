import inspect
import json

from scripts import similarity_asic_transfer_route as common
from scripts import similarity_runtime_headroom_canary as canary


def test_frozen_matrix_is_exact_and_opened_only():
    assert canary.SEED == 373
    assert canary.GEOMETRIES == (
        ("opened_canary", 7, 10),
        ("opened_canary", 10, 7),
    )
    assert canary.CAP_MARGIN == 31
    assert canary.SLEW_MARGIN == 25
    assert canary.RATIO_MARGIN == 20
    assert canary.STAGE_TIMEOUT_SECONDS == 7200
    assert len(canary.expected_identities()) == 12


def test_structural_reference_covers_every_route_identity():
    keys = {
        (platform, topology, rows, cols)
        for platform, topology, _, rows, cols in canary.expected_identities()
    }
    assert set(canary.STRUCTURE) == keys
    assert all(dff > 0 and area > 0 for dff, area in canary.STRUCTURE.values())


def test_common_route_timeout_remains_backward_compatible():
    run_stage = inspect.signature(common.run_stage)
    route_one = inspect.signature(common.route_one)
    assert run_stage.parameters["timeout_seconds"].default == 3600
    assert route_one.parameters["stage_timeout_seconds"].default == 3600


def test_patch_manifest_freezes_timeout_and_margins(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    final = scripts / "final_outputs.tcl"
    antenna = scripts / "global_route.tcl"
    final.write_text("prefix\n" + canary.FINAL_REMOVED + "suffix\n")
    antenna.write_text("prefix\n" + canary.ANTENNA_REMOVED + "suffix\n")
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    manifest = tmp_path / "manifest.json"
    canary.patch_qualified_flow(tmp_path, manifest)
    record = json.loads(manifest.read_text())
    assert record["workflow_source_sha"] == "b" * 40
    assert record["native_stage_timeout_seconds"] == 7200
    assert record["cap_margin"] == 31
    assert record["slew_margin"] == 25
    assert record["antenna_ratio_margin"] == 20
    assert record["canary_seed"] == 373
    assert record["geometries"] == [[7, 10], [10, 7]]
    assert len(record["patches"]) == 2
