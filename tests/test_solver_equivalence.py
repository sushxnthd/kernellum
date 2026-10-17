import numpy as np

from kernellum.discovery.solver_equivalence import certify_prediction_envelope


def test_equivalent_predictions_return_lower_cv_solver():
    receipt = certify_prediction_envelope(
        np.array([0.0, 1.0, 2.0]),
        np.array([0.1, 1.1, 1.9]),
        y_scale=1.0,
        candidate_cv=0.4,
        independent_cv=0.3,
    )
    assert receipt.accepted
    assert receipt.selected_solver == "independent"
    assert receipt.scope == "solver_invariance_not_model_correctness"


def test_wide_prediction_envelope_abstains():
    receipt = certify_prediction_envelope(
        np.zeros(3),
        np.array([0.0, 0.0, 5.0]),
        y_scale=1.0,
        candidate_cv=0.4,
        independent_cv=0.3,
    )
    assert not receipt.accepted
    assert receipt.selected_solver is None
    assert receipt.prediction_max == 5.0
