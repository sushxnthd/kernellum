import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
PATH = ROOT / "experiments/robust_ftrig_coefficient_boundary/run.py"
SPEC = importlib.util.spec_from_file_location("robust_ftrig_boundary", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["robust_ftrig_boundary"] = MODULE
SPEC.loader.exec_module(MODULE)


def test_exact_dyadic_boundary():
    assert MODULE.certify(MODULE.Q(1, 2**19))["passing_boxes"] == 42
    assert MODULE.certify(MODULE.Q(1, 2**18))["passing_boxes"] == 18


def test_frozen_result_preserves_negative_gate():
    data = json.loads((ROOT / "results/robust_ftrig_coefficient_boundary.json").read_text())
    assert data["boundary_gate"] == "KILL"
    assert data["gates"]["catastrophe_reduction"] is False
    assert data["prospective"]["summary"]["unconditional_root_catastrophes"] == 0
    assert data["prospective"]["summary"]["fail_closed_catastrophes"] == 0
    assert data["prospective"]["summary"]["safe_route_retention"] == 1.0


def test_every_frozen_point_certificate_passes():
    data = json.loads((ROOT / "results/robust_ftrig_coefficient_boundary.json").read_text())
    assert len(data["prospective"]["records"]) == 48
    assert all(row["point_certificate_passed"] for row in data["prospective"]["records"])

