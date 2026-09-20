from scripts.similarity_functional_validate import law_tax_ns
from scripts.similarity_portfolio_route import (
    ARCHITECTURES,
    DEPLOYMENT_SEEDS,
    SELECTION_SEEDS,
)
from scripts.similarity_portfolio_validate import (
    MAX_OVERALL_REGRET_PCT,
    MAX_SEED_REGRET_PCT,
    MIN_REGRET_REDUCTION_PP,
    PORTFOLIO_SIZE,
)


def test_frozen_portfolio_route_count():
    assert len(ARCHITECTURES) == 8
    assert len(SELECTION_SEEDS) == 3
    assert len(DEPLOYMENT_SEEDS) == 3
    assert 8 * 3 + 8 * 2 * 3 == 72
    assert PORTFOLIO_SIZE == 2


def test_portfolio_corpus_is_new():
    assert len({name for name, _, _, _ in ARCHITECTURES}) == 8
    assert {k_tile for _, _, _, k_tile in ARCHITECTURES} == {352, 480}
    assert {rows * cols for _, rows, cols, _ in ARCHITECTURES} == {108, 150}
    assert SELECTION_SEEDS == (41, 42, 43)
    assert DEPLOYMENT_SEEDS == (44, 45, 46)
    assert all(law_tax_ns(rows * cols) > 0 for _, rows, cols, _ in ARCHITECTURES)


def test_portfolio_thresholds_are_frozen():
    assert MAX_SEED_REGRET_PCT == 5.0
    assert MAX_OVERALL_REGRET_PCT == 3.0
    assert MIN_REGRET_REDUCTION_PP == 1.0
