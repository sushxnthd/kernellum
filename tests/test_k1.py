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


def test_local_transport_charges_exact_wavefront_drain_per_chunk():
    broadcast = K1Architecture("b", 8, 12, 32, "broadcast")
    local = K1Architecture("l", 8, 12, 32, "local")
    m, n, k = 8, 12, 64
    chunks = 2
    expected_extra = chunks * (8 + 12 - 1)
    assert predicted_cycles(m, n, k, local) - predicted_cycles(m, n, k, broadcast) == expected_extra


def test_unknown_transport_is_rejected():
    bad = K1Architecture("bad", 4, 4, 16, "teleport")
    try:
        predicted_cycles(4, 4, 16, bad)
    except ValueError as exc:
        assert "transport" in str(exc)
    else:
        raise AssertionError("unknown transport must fail")


def test_spearman_known_cases():
    assert abs(spearman([1, 2, 3], [10, 20, 30]) - 1.0) < 1e-12
    assert abs(spearman([1, 2, 3], [30, 20, 10]) + 1.0) < 1e-12
