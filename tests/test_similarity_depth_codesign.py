from scripts.similarity_depth_route import ARCHITECTURES
from scripts.similarity_depth_validate import K_VALUES, MATCHED_DEPTH_GEOMETRIES, law_tax_ns


def test_frozen_depth_route_count():
    assert len(ARCHITECTURES) == 8
    assert len(ARCHITECTURES) * 2 * 3 == 48
    assert len({name for name, _, _, _ in ARCHITECTURES}) == 8


def test_depth_space_is_new_and_deep():
    assert {k_tile for _, _, _, k_tile in ARCHITECTURES} == {128, 256}
    assert max(rows * cols for _, rows, cols, _ in ARCHITECTURES) == 140


def test_frozen_policy_grid_and_depth_pairs():
    assert K_VALUES == (8, 16, 32, 64, 128, 256, 512, 1024, 3072)
    assert MATCHED_DEPTH_GEOMETRIES == ((8, 8), (10, 12), (12, 10))


def test_frozen_tax_is_positive_over_depth_corpus():
    assert all(law_tax_ns(rows * cols) > 0 for _, rows, cols, _ in ARCHITECTURES)
