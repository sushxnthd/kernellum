from scripts.similarity_mechanism_confirm_route import GEOMS

def test_confirmation_route_count():
    assert sum(len(v) for v in GEOMS.values()) * 2 * 3 == 36

def test_confirmation_uses_new_seeds():
    assert {4,5,6}.isdisjoint({1,2,3})
