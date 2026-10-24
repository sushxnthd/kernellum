from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np


PATH = Path(__file__).parents[1] / "experiments/phi4_orbit_certificate_amortization/run.py"
SPEC = spec_from_file_location("phi4_orbit_amortization", PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_prospective_regimes_are_disjoint_from_predecessor():
    assert len(MODULE.prospective_weight_regimes()) == 19
    assert not (set(MODULE.prospective_weight_regimes()) & set(MODULE.weight_regimes()))


def test_residual_and_jacobian_symmetry_on_non_sign_points():
    points = [
        np.array([0.77, -1.13, 0.92, 1.21, -0.84]),
        np.array([-1.2, -0.8, 1.07, -0.96, 1.17]),
    ]
    for numerators in MODULE.prospective_weight_regimes():
        weights = np.asarray(numerators, dtype=float) / 64
        for point in points:
            np.testing.assert_array_equal(MODULE.residual(-point, weights),
                                          -MODULE.residual(point, weights))
            np.testing.assert_array_equal(MODULE.jacobian(-point, weights),
                                          MODULE.jacobian(point, weights))


def test_orbit_batching_reproduces_every_unbatched_start_exactly():
    for numerators in MODULE.prospective_weight_regimes():
        weights = np.asarray(numerators, dtype=float) / 64
        np.testing.assert_array_equal(MODULE.orbit_starts(weights),
                                      MODULE.structured_starts(weights))
