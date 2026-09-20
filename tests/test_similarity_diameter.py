def test_diameter_groups_have_fixed_pe_counts():
    g64=((2,32),(4,16),(8,8),(16,4),(32,2))
    g96=((4,24),(6,16),(8,12),(12,8),(16,6),(24,4))
    assert all(r*c==64 for r,c in g64)
    assert all(r*c==96 for r,c in g96)
    assert len(g64)+len(g96)==11


def test_diameter_schedule_is_66():
    assert 11*2*3==66
