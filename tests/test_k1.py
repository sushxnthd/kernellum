from kernellum.k1 import K1Architecture, candidate_set, predicted_cycles, spearman


def test_candidate_set_is_frozen_and_unique():
    cs = candidate_set()
    assert len(cs) == 9
    assert len({c.name for c in cs}) == 9
    assert max(c.pe_count for c in cs) <= 100


def test_predicted_cycles_rewards_parallel_tiles():
    small = K1Architecture("small", 4, 4, 32)
    large = K1Architecture("large", 8, 8, 32)
    assert predicted_cycles(128, 312, 312, large) < predicted_cycles(128, 312, 312, small)


def test_k_tile_reduces_chunk_control_overhead():
    k16 = K1Architecture("k16", 8, 8, 16)
    k64 = K1Architecture("k64", 8, 8, 64)
    assert predicted_cycles(128, 312, 312, k64) < predicted_cycles(128, 312, 312, k16)


def test_spearman_known_cases():
    assert abs(spearman([1, 2, 3], [10, 20, 30]) - 1.0) < 1e-12
    assert abs(spearman([1, 2, 3], [30, 20, 10]) + 1.0) < 1e-12
