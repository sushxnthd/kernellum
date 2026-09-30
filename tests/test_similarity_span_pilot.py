from pathlib import Path

def test_span_pilot_files_present():
    assert Path("scripts/similarity_span_constraints.py").exists()
    assert Path("scripts/similarity_span_pilot.py").exists()
    assert Path("docs/SIMILARITY_SPAN_PILOT.md").exists()
