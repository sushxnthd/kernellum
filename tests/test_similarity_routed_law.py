from scripts.similarity_routed_route import DISC,HOLD

def test_route_counts():
    discovery=sum(len(v) for v in DISC.values())*2*3
    holdout=sum(len(v) for v in HOLD.values())*2*3
    assert discovery==60
    assert holdout==36
    assert discovery+holdout==96
