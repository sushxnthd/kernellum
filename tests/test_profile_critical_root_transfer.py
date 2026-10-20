import importlib.util
import sys
from pathlib import Path

import numpy as np


PATH = Path(__file__).parents[1] / "experiments" / "profile_critical_root_transfer" / "run.py"
SPEC = importlib.util.spec_from_file_location("profile_roots", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_profile_certificate_emits_two_strict_minima():
    candidates = MODULE.profile_candidates()
    assert candidates.shape == (2, 2)
    assert min(MODULE.objective(z) for z in candidates) < 1e-20
    assert max(MODULE.objective(z) for z in candidates) > 40


def test_fixed_maximin_control_spans_both_basins():
    candidates = MODULE.profile_candidates()
    result = MODULE.run_starts(MODULE.generic_starts("maximin", 0),
                               MODULE.transforms()[0], candidates)
    assert result["coverage"] == 2
