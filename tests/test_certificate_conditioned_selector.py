import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "experiments/certificate_conditioned_selector/run.py"
SPEC = importlib.util.spec_from_file_location("certificate_selector", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_certificates_activate_only_complete_polynomial_paths():
    certificates = MODULE.certificates()
    assert certificates["freudenstein_roth"]["passed"]
    assert certificates["himmelblau"]["passed"]
    assert not certificates["ftrig"]["passed"]


def test_prospective_transforms_are_frozen_and_distinct():
    first = MODULE.prospective_transforms()
    second = MODULE.prospective_transforms()
    assert first == second
    assert len(first) == len(set(first)) == 12
