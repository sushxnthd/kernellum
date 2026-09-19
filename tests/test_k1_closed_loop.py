from kernellum.k1.closed_loop import (
    RoutedObservation,
    active_proposals,
    expanded_pool,
    feature_distance,
    predict_fmax,
    random_controls,
)
from kernellum.k1.model import K1Architecture
from kernellum.workload import tiny_transformer_suite


def _seed_observations():
    return [
        RoutedObservation(K1Architecture("r04_c04_k16", 4, 4, 16), 44.04),
        RoutedObservation(K1Architecture("r04_c08_k32", 4, 8, 32), 42.43),
        RoutedObservation(K1Architecture("r08_c04_k32", 8, 4, 32), 44.51),
        RoutedObservation(K1Architecture("r08_c08_k16", 8, 8, 16), 39.61),
        RoutedObservation(K1Architecture("r08_c08_k32", 8, 8, 32), 36.33),
        RoutedObservation(K1Architecture("r08_c08_k64", 8, 8, 64), 33.17),
        RoutedObservation(K1Architecture("r08_c12_k32", 8, 12, 32), 33.68),
        RoutedObservation(K1Architecture("r12_c08_k32", 12, 8, 32), 32.63),
        RoutedObservation(K1Architecture("r10_c10_k32", 10, 10, 32), 34.69),
    ]


def test_expanded_pool_size_and_budget_math():
    pool = expanded_pool()
    assert len(pool) == 172
    assert all(a.pe_count <= 120 for a in pool)
    assert 17 / len(pool) <= 0.10


def test_surrogate_exact_on_seen_architecture():
    obs = _seed_observations()
    pred, uncertainty = predict_fmax(obs[0].arch, obs)
    assert abs(pred - obs[0].fmax_mhz) < 1e-12
    assert uncertainty == 0.0


def test_feature_distance_is_symmetric():
    a = K1Architecture("a", 4, 8, 32)
    b = K1Architecture("b", 8, 4, 32)
    assert abs(feature_distance(a, b) - feature_distance(b, a)) < 1e-12


def test_active_and_random_arms_are_disjoint_and_deterministic():
    obs = _seed_observations()
    workloads = tiny_transformer_suite()
    active = active_proposals(obs, workloads, n=4)
    controls_a = random_controls(obs, active, n=4)
    controls_b = random_controls(obs, active, n=4)
    active_names = {x["arch"].name for x in active}
    random_names = {x.name for x in controls_a}
    seen = {x.arch.name for x in obs}
    assert len(active_names) == 4
    assert len(random_names) == 4
    assert active_names.isdisjoint(random_names)
    assert active_names.isdisjoint(seen)
    assert random_names.isdisjoint(seen)
    assert [x.name for x in controls_a] == [x.name for x in controls_b]
