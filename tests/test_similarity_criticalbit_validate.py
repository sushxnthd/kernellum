from scripts.similarity_criticalbit_validate import predicted_replica_overhead


def test_selective_replication_has_bounded_structural_overhead():
    assert predicted_replica_overhead(5, 8) == 68
    assert predicted_replica_overhead(8, 5) == 76


def test_replication_overhead_preserves_prior_90pct_dff_margin_prediction():
    # Frozen median DFF counts do not vary by route seed on these two shapes.
    # This is only a structural prediction; the diagnostic publishes actual
    # post-synthesis DFF counts and gates on those instead.
    old = {
        (5, 8): (1831, 2284),
        (8, 5): (1796, 2232),
    }
    for shape, (stride2, local) in old.items():
        predicted = stride2 + predicted_replica_overhead(*shape)
        assert stride2 < predicted <= .90 * local
