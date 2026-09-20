from scripts.similarity_route_shard import architecture_pool


def test_similarity_pool_sizes_are_frozen():
    assert len(architecture_pool("45k")) == 172
    assert len(architecture_pool("85k")) == 172
    assert len(architecture_pool("25k")) == 100


def test_similarity_25k_subset_is_low_capacity():
    assert all(r * c <= 48 for r, c, _ in architecture_pool("25k"))
