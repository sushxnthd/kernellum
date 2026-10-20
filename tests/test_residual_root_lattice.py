import runpy
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "experiments" / "residual_root_lattice" / "run.py"
MODULE = runpy.run_path(str(MODULE_PATH))

U_ROOTS = MODULE["U_ROOTS"]
V_ROOTS = MODULE["V_ROOTS"]
generic_grid = MODULE["generic_grid"]
root_lattice = MODULE["root_lattice"]


def test_start_budgets_match():
    assert root_lattice().shape == (42, 2)
    assert generic_grid().shape == (42, 2)


def test_factor_root_counts_are_structural():
    assert len(U_ROOTS) == 7
    assert len(V_ROOTS) == 6
    assert len(set(U_ROOTS)) == 7
    assert len(set(V_ROOTS)) == 6
