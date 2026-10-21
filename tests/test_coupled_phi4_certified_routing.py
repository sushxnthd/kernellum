from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np


PATH = Path(__file__).parents[1] / "experiments/coupled_phi4_certified_routing/run.py"
SPEC = spec_from_file_location("coupled_phi4_run", PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_analytic_jacobian_matches_central_difference():
    weights = np.array([1, 2, 3, 4], dtype=float) / 64
    point = np.array([0.9, -1.1, 1.0, -0.8, 1.2])
    step = 1e-6
    numeric = np.column_stack([
        (MODULE.residual(point + np.eye(5)[i] * step, weights)
         - MODULE.residual(point - np.eye(5)[i] * step, weights)) / (2 * step)
        for i in range(5)
    ])
    np.testing.assert_allclose(MODULE.jacobian(point, weights), numeric, atol=1e-8)


def test_all_frozen_roots_stay_in_certified_boxes():
    for numerators in MODULE.weight_regimes():
        weights = np.asarray(numerators, dtype=float) / 64
        roots = MODULE.reference_roots(weights)
        assert np.all(MODULE.SIGNS * roots >= 0.75)
        assert np.all(MODULE.SIGNS * roots <= 1.25)


def test_one_newton_refinement_reduces_every_residual():
    for numerators in MODULE.weight_regimes():
        weights = np.asarray(numerators, dtype=float) / 64
        starts = MODULE.structured_starts(weights)
        for sign, start in zip(MODULE.SIGNS, starts, strict=True):
            before = np.linalg.norm(MODULE.residual(sign, weights))
            after = np.linalg.norm(MODULE.residual(start, weights))
            assert after <= before
            if before > 0:
                assert after < before
