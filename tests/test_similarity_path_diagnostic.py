from scripts.similarity_path_diagnostic import SIZES

def test_path_diagnostic_schedule():
    assert SIZES == (3,5,7,9,11)
    assert len(SIZES)*5 == 25
