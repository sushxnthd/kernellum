import copy
import importlib.util
import sys
from pathlib import Path

from kernellum.discovery.interval_basin_router import route_interval_basin_certificate


PATH = Path(__file__).parents[1] / "experiments/interval_certified_ftrig/run.py"
SPEC = importlib.util.spec_from_file_location("router_interval_ftrig", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["router_interval_ftrig"] = MODULE
SPEC.loader.exec_module(MODULE)


def test_routes_complete_exact_certificate_to_42_centers():
    route = route_interval_basin_certificate(MODULE.exact_certificate(), 42)
    assert route.activated
    assert route.route == "interval_box_centers"
    assert route.certified_boxes == len(route.starts) == 42


def test_fails_closed_on_one_false_proof_obligation():
    certificate = copy.deepcopy(MODULE.exact_certificate())
    certificate["boxes"][0]["checks"]["hessian_pd"] = False
    route = route_interval_basin_certificate(certificate, 42)
    assert not route.activated
    assert route.reason == "FAILED_PROOF_OBLIGATION"


def test_fails_closed_on_missing_or_overlapping_box_claim():
    certificate = copy.deepcopy(MODULE.exact_certificate())
    certificate["pairwise_disjoint"] = False
    assert not route_interval_basin_certificate(certificate, 42).activated
    certificate = copy.deepcopy(MODULE.exact_certificate())
    certificate["boxes"].pop()
    assert not route_interval_basin_certificate(certificate, 42).activated
