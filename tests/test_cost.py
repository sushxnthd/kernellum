from kernellum.architecture import Architecture
from kernellum.cost import Constraints, estimate
from kernellum.workload import GEMMWorkload

def test_estimate_positive_and_feasible():
    w = GEMMWorkload("x", 128, 312, 312)
    a = Architecture(16, 16, 8, 32, 32, 32, 128, "weight_stationary")
    e = estimate(w, a, Constraints())
    assert e.latency_ms > 0
    assert e.dsp == 256
    assert e.bram > 0
    assert e.feasible

def test_resource_constraint_rejects():
    w = GEMMWorkload("x", 128, 312, 312)
    a = Architecture(32, 32, 8, 32, 32, 32, 512, "output_stationary")
    e = estimate(w, a, Constraints(max_dsp=100, max_bram=600))
    assert not e.feasible
