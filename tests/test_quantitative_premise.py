import numpy as np

from kernellum.discovery.quantitative_premise import (
    empirical_lipschitz_lower_bound,
    issue_lipschitz_envelope,
    lipschitz_interval,
)


def test_empirical_bound_and_sharp_interval():
    x = np.array([[0.0], [2.0]])
    y = np.array([0.0, 2.0])
    assert empirical_lipschitz_lower_bound(x, y) == 1.0
    lower, upper = lipschitz_interval(x, y, np.array([[1.0], [3.0]]), 1.0)
    np.testing.assert_allclose(lower, [1.0, 1.0])
    np.testing.assert_allclose(upper, [1.0, 3.0])


def test_same_transcript_estimate_is_refused_even_if_verifier_returns_true():
    premise = {"hypothesis_class": "global_lipschitz", "request_scope": "test",
               "constant": 1.0, "source": "estimated_from_same_transcript"}
    result = issue_lipschitz_envelope([[0.0], [1.0]], [0.0, 1.0], [[2.0]], premise, lambda _: True)
    assert result["decision"] == "refuse"


def test_external_verified_premise_accepts_and_hashes():
    premise = {"hypothesis_class": "global_lipschitz", "request_scope": "registered domain",
               "constant": 2.0, "source": "external_physical_specification"}
    result = issue_lipschitz_envelope([[0.0], [1.0]], [0.0, 1.0], [[2.0]], premise, lambda p: p == premise)
    assert result["decision"] == "accept_conditional"
    assert result["lower"] == [-1.0]
    assert result["upper"] == [3.0]
    assert len(result["premise_sha256"]) == 64


def test_false_external_verifier_refuses():
    premise = {"hypothesis_class": "global_lipschitz", "request_scope": "test",
               "constant": 2.0, "source": "external"}
    assert issue_lipschitz_envelope([[0.0], [1.0]], [0.0, 1.0], [[2.0]], premise, lambda _: False)["decision"] == "refuse"
