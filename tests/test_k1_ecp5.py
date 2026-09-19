from kernellum.k1.ecp5 import predicted_dp16kd, predicted_mult18x18d
from kernellum.k1.model import K1Architecture


def test_k1_ecp5_model_matches_routed_evidence():
    cases = [
        (K1Architecture("a", 4, 4, 16), 16, 2),
        (K1Architecture("b", 4, 8, 32), 32, 3),
        (K1Architecture("c", 8, 4, 32), 32, 3),
        (K1Architecture("d", 8, 8, 16), 64, 4),
        (K1Architecture("e", 8, 8, 32), 64, 4),
        (K1Architecture("f", 8, 8, 64), 64, 4),
        (K1Architecture("g", 8, 12, 32), 96, 5),
        (K1Architecture("h", 12, 8, 32), 96, 5),
        (K1Architecture("i", 10, 10, 32), 100, 6),
        (K1Architecture("j", 10, 12, 64), 120, 6),
        (K1Architecture("k", 8, 14, 64), 112, 6),
    ]
    for arch, dsp, bram in cases:
        assert predicted_mult18x18d(arch) == dsp
        assert predicted_dp16kd(arch) == bram

# CI-only validation marker
