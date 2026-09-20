from scripts.similarity_functional_route import ARCHITECTURES
from scripts.similarity_functional_validate import K_VALUES, law_tax_ns


def test_frozen_functional_route_count():
    assert len(ARCHITECTURES) == 9
    assert len(ARCHITECTURES) * 2 * 3 == 54


def test_frozen_policy_grid():
    assert K_VALUES == (8, 16, 32, 64, 128, 256, 512, 1024, 3072)


def test_diagnostic_tax_is_positive_over_frozen_architectures():
    assert all(law_tax_ns(rows * cols) > 0 for _, rows, cols, _ in ARCHITECTURES)
