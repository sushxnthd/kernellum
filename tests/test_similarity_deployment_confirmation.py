from scripts.similarity_deployment_route import ARCHITECTURES
from scripts.similarity_deployment_validate import DEPLOYMENT_SEEDS, law_tax_ns


def test_frozen_deployment_route_count():
    assert len(ARCHITECTURES) == 8
    assert 8 * 3 + 8 * 2 * 3 == 72
    assert DEPLOYMENT_SEEDS == (38, 39, 40)


def test_deployment_corpus_is_new():
    assert len({name for name, _, _, _ in ARCHITECTURES}) == 8
    assert {k_tile for _, _, _, k_tile in ARCHITECTURES} == {320, 448}
    assert {rows * cols for _, rows, cols, _ in ARCHITECTURES} == {88, 130}
    assert all(law_tax_ns(rows * cols) > 0 for _, rows, cols, _ in ARCHITECTURES)
