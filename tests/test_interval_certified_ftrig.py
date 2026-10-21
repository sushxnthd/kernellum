import importlib.util
import sys
from pathlib import Path


PATH = Path(__file__).parents[1] / "experiments/interval_certified_ftrig/run.py"
SPEC = importlib.util.spec_from_file_location("interval_certified_ftrig", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["interval_certified_ftrig"] = MODULE
SPEC.loader.exec_module(MODULE)


def test_exact_certificate_has_42_disjoint_strict_minimum_boxes():
    certificate = MODULE.exact_certificate()
    assert certificate["passed"]
    assert certificate["box_count"] == 42
    assert certificate["pairwise_disjoint"]
    assert all(all(box["checks"].values()) for box in certificate["boxes"])


def test_start_designs_have_equal_frozen_budget():
    for method in ("root_lattice", "grid", "optimized_lhs", "greedy_maximin"):
        assert MODULE.starts(method, 7).shape == (42, 2)


def test_certificate_fails_closed_when_radius_is_perturbed_too_wide():
    original = MODULE.RADIUS
    try:
        MODULE.RADIUS = MODULE.Q(1, 100)
        assert not MODULE.exact_certificate()["passed"]
    finally:
        MODULE.RADIUS = original
