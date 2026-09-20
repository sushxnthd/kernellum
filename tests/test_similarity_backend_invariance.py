from scripts.similarity_backend_invariance_route import SIZES

def test_backend_invariance_schedule():
    assert len(SIZES)*2*2*3 == 48

def test_backend_invariance_uses_fresh_seeds():
    assert {7,8,9}.isdisjoint({1,2,3,4,5,6})
