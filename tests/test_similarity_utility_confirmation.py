from scripts.similarity_functional_validate import K_VALUES
from scripts.similarity_utility_route import ARCHITECTURES
from scripts.similarity_utility_validate import MATCHED_GEOMETRIES, SEEDS, law_tax_ns


def test_frozen_utility_route_count():
    assert len(ARCHITECTURES) == 10
    assert len(ARCHITECTURES) * 2 * len(SEEDS) == 60
    assert SEEDS == (32, 33, 34)


def test_confirmation_corpus_is_new_and_unique():
    assert len({name for name, _, _, _ in ARCHITECTURES}) == 10
    assert {k_tile for _, _, _, k_tile in ARCHITECTURES} == {192, 384}
    assert {rows * cols for _, rows, cols, _ in ARCHITECTURES} == {81, 117, 143}


def test_frozen_grid_and_depth_pairs():
    assert K_VALUES == (8, 16, 32, 64, 128, 256, 512, 1024, 3072)
    assert MATCHED_GEOMETRIES == ((9, 9), (9, 13), (13, 9), (11, 13), (13, 11))


def test_frozen_tax_is_positive_over_confirmation_corpus():
    assert all(law_tax_ns(rows * cols) > 0 for _, rows, cols, _ in ARCHITECTURES)
