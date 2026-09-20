from scripts.similarity_confirm_route_shard import architecture_pool


def test_confirmation_pool_sizes_are_frozen():
    assert len(architecture_pool("25k")) == 18
    assert len(architecture_pool("45k")) == 45
    assert len(architecture_pool("85k")) == 72


def test_confirmation_uses_unseen_odd_dimensions_and_tiles():
    for dev in ("25k", "45k", "85k"):
        for r, c, t in architecture_pool(dev):
            assert r % 2 == 1
            assert c % 2 == 1
            assert t in (12, 24, 48)
            assert r not in (2, 4, 6, 8, 10, 12, 14)
            assert c not in (2, 4, 6, 8, 10, 12, 14)
            assert t not in (8, 16, 32, 64)
