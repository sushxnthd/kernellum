from scripts import similarity_electrical_margin_canary as canary


def test_frozen_matrix_is_exact_and_canary_only():
    assert canary.SEED == 263
    assert {(rows, cols) for _, rows, cols in canary.GEOMETRIES} == {(10, 5), (7, 8), (8, 7)}
    assert len(canary.expected_identities()) == 18


def test_structural_reference_covers_every_route_identity():
    keys = {
        (platform, topology, rows, cols)
        for platform, topology, _, rows, cols in canary.expected_identities()
    }
    assert set(canary.STRUCTURE) == keys
    assert all(dff > 0 and area > 0 for dff, area in canary.STRUCTURE.values())
