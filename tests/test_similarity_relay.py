from scripts.similarity_relay_route import FANOUTS

def test_relay_schedule_is_54():
    assert sum((len(v)+2)*3 for v in FANOUTS.values()) == 54

def test_relay_fanouts_divide_n():
    for n,fs in FANOUTS.items():
        assert all(n % f == 0 for f in fs)
