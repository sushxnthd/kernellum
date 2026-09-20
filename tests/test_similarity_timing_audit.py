from pathlib import Path

def test_timing_audit_exists():
    assert Path("scripts/similarity_timing_audit.py").exists()
