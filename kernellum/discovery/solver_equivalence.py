from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SolverEquivalenceReceipt:
    accepted: bool
    selected_solver: str | None
    prediction_rms: float
    prediction_max: float
    rms_threshold: float
    max_threshold: float
    scope: str = "solver_invariance_not_model_correctness"


def certify_prediction_envelope(
    candidate_predictions: np.ndarray,
    independent_predictions: np.ndarray,
    *,
    y_scale: float,
    candidate_cv: float,
    independent_cv: float,
    rms_threshold: float = 0.5,
    max_threshold: float = 4.0,
) -> SolverEquivalenceReceipt:
    """Certify behavioral equivalence on an explicit request set.

    The receipt only concerns the supplied predictions.  It does not certify
    that either model is scientifically correct or globally optimal.
    """
    candidate = np.asarray(candidate_predictions, dtype=float)
    independent = np.asarray(independent_predictions, dtype=float)
    if candidate.shape != independent.shape or candidate.size == 0:
        raise ValueError("prediction arrays must have the same nonempty shape")
    scale = max(float(y_scale), 1e-12)
    delta = (candidate - independent) / scale
    rms = float(np.sqrt(np.mean(delta * delta)))
    maximum = float(np.max(np.abs(delta)))
    accepted = rms <= float(rms_threshold) and maximum <= float(max_threshold)
    selected = None
    if accepted:
        selected = "independent" if float(independent_cv) < float(candidate_cv) else "candidate"
    return SolverEquivalenceReceipt(
        accepted=accepted,
        selected_solver=selected,
        prediction_rms=rms,
        prediction_max=maximum,
        rms_threshold=float(rms_threshold),
        max_threshold=float(max_threshold),
    )
