import json

from scripts import similarity_antenna_margin_canary as canary


def test_frozen_matrix_is_exact_and_opened_only():
    assert canary.SEED == 277
    assert (canary.ROWS, canary.COLS) == (10, 5)
    assert canary.RATIO_MARGIN == 20
    assert len(canary.expected_identities()) == 6


def test_structural_reference_covers_matrix():
    keys = {(platform, topology) for platform, topology, *_ in canary.expected_identities()}
    assert set(canary.STRUCTURE) == keys
    assert all(dff > 0 and area > 0 for dff, area in canary.STRUCTURE.values())


def test_patch_is_exact_and_auditable(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    final = scripts / "final_outputs.tcl"
    global_route = scripts / "global_route.tcl"
    final.write_text("prefix\n" + canary.FINAL_REMOVED + "suffix\n", encoding="utf-8")
    global_route.write_text("prefix\n" + canary.ANTENNA_REMOVED + "suffix\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_SHA", "f" * 40)
    manifest = tmp_path / "manifest.json"
    canary.patch_flow(tmp_path, manifest)
    record = json.loads(manifest.read_text(encoding="utf-8"))
    assert record["workflow_source_sha"] == "f" * 40
    assert record["antenna_ratio_margin"] == 20
    assert len(record["patches"]) == 2
    assert canary.FINAL_REMOVED not in final.read_text(encoding="utf-8")
    assert canary.ANTENNA_REMOVED not in global_route.read_text(encoding="utf-8")
    assert canary.ANTENNA_REPLACEMENT in global_route.read_text(encoding="utf-8")
