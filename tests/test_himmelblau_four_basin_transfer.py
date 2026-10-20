import importlib.util
import sys
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "experiments/himmelblau_four_basin_transfer/run.py"
SPEC = importlib.util.spec_from_file_location("himmelblau_transfer", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_eliminant_yields_four_certified_zero_residual_minima():
    candidates = MODULE.eliminant_candidates()
    assert candidates.shape == (4, 2)
    assert all(np.linalg.norm(MODULE.residual_z(z)) < 1e-8 for z in candidates)
    assert all(abs(np.linalg.det(MODULE.jacobian_z(z))) > 1e-4 for z in candidates)


def test_greedy_maximin_is_deterministic_four_point_design():
    first = MODULE.greedy_maximin()
    second = MODULE.greedy_maximin()
    assert np.array_equal(first, second)
    assert first.shape == (4, 2)
