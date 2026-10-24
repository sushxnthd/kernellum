import numpy as np

from kernellum.discovery.symmetry_orbit_starts import route_antipodal_newton_starts


SIGNS = np.asarray([
    [-1.0, -1.0], [-1.0, 1.0], [1.0, -1.0], [1.0, 1.0]
])
CERTIFICATE = {
    "passed": True,
    "symmetry": "global_sign",
    "residual_odd": True,
    "jacobian_even": True,
    "pairwise_disjoint": True,
    "box_count": 4,
}


def test_certified_orbits_halve_newton_construction_calls():
    residual_calls = []
    jacobian_calls = []
    route = route_antipodal_newton_starts(
        CERTIFICATE,
        SIGNS,
        lambda x: residual_calls.append(tuple(x)) or (x**3 - x),
        lambda x: jacobian_calls.append(tuple(x)) or np.diag(3 * x**2 - 1),
    )
    assert route.activated
    assert route.residual_calls == route.jacobian_calls == 2
    assert len(residual_calls) == len(jacobian_calls) == 2
    starts = np.asarray(route.starts)
    np.testing.assert_array_equal(starts[0], -starts[3])
    np.testing.assert_array_equal(starts[1], -starts[2])


def test_incomplete_or_unproven_orbits_fail_before_evaluation():
    calls = []
    residual = lambda x: calls.append("residual") or x
    jacobian = lambda x: calls.append("jacobian") or np.eye(len(x))
    incomplete = dict(CERTIFICATE, box_count=6)
    assert not route_antipodal_newton_starts(incomplete, SIGNS, residual, jacobian).activated
    unproven = dict(CERTIFICATE, residual_odd=False)
    assert not route_antipodal_newton_starts(unproven, SIGNS, residual, jacobian).activated
    missing_pair = SIGNS[:-1]
    assert not route_antipodal_newton_starts(CERTIFICATE, missing_pair, residual, jacobian).activated
    assert calls == []


def test_singular_newton_system_fails_closed():
    route = route_antipodal_newton_starts(
        CERTIFICATE, SIGNS, lambda x: x, lambda x: np.zeros((len(x), len(x)))
    )
    assert not route.activated
    assert route.reason == "NEWTON_CONSTRUCTION_FAILED"
    assert route.starts == ()
