"""Fail-closed quantitative premises for sharp Lipschitz envelopes."""
from __future__ import annotations

import hashlib
import json
from typing import Callable, Mapping, Any

import numpy as np


def empirical_lipschitz_lower_bound(x, y) -> float:
    """Smallest L consistent with a finite transcript (not a certificate)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 2 or y.shape != (len(x),) or len(x) < 2:
        raise ValueError("need at least two aligned observations")
    distances = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
    differences = np.abs(y[:, None] - y[None, :])
    duplicate_conflict = (distances <= 1e-12) & (differences > 1e-12)
    if np.any(duplicate_conflict):
        raise ValueError("conflicting observations at duplicate input")
    mask = distances > 1e-12
    if not np.any(mask):
        return 0.0
    return float(np.max(differences[mask] / distances[mask]))


def lipschitz_interval(x, y, requests, constant: float) -> tuple[np.ndarray, np.ndarray]:
    """Sharp pointwise McShane--Whitney interval conditional on global L."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(requests, dtype=float)
    constant = float(constant)
    if x.ndim != 2 or z.ndim != 2 or x.shape[1] != z.shape[1] or y.shape != (len(x),):
        raise ValueError("malformed transcript or requests")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or not np.all(np.isfinite(z)):
        raise ValueError("nonfinite transcript or requests")
    if not np.isfinite(constant) or constant < 0:
        raise ValueError("Lipschitz constant must be finite and nonnegative")
    distances = np.linalg.norm(z[:, None, :] - x[None, :, :], axis=2)
    lower = np.max(y[None, :] - constant * distances, axis=1)
    upper = np.min(y[None, :] + constant * distances, axis=1)
    if np.any(lower > upper + 1e-10):
        raise ValueError("transcript violates declared Lipschitz constant")
    return lower, upper


def issue_lipschitz_envelope(
    x,
    y,
    requests,
    premise: Mapping[str, Any] | None,
    verifier: Callable[[Mapping[str, Any]], bool] | None,
) -> dict[str, Any]:
    """Issue a conditional envelope only for externally verified provenance."""
    if premise is None:
        return {"decision": "refuse", "reason": "missing quantitative premise"}
    source = premise.get("source")
    if source == "estimated_from_same_transcript":
        return {"decision": "refuse", "reason": "empirical constant is only a lower bound"}
    required = ("hypothesis_class", "request_scope", "constant", "source")
    if any(key not in premise for key in required):
        return {"decision": "refuse", "reason": "malformed quantitative premise"}
    if premise["hypothesis_class"] != "global_lipschitz":
        return {"decision": "refuse", "reason": "unsupported hypothesis class"}
    if verifier is None or not bool(verifier(premise)):
        return {"decision": "refuse", "reason": "premise not independently verified"}
    try:
        lower, upper = lipschitz_interval(x, y, requests, float(premise["constant"]))
    except (TypeError, ValueError) as exc:
        return {"decision": "refuse", "reason": str(exc)}
    canonical = json.dumps(dict(premise), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "decision": "accept_conditional",
        "premise_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "hypothesis_class": "global_lipschitz",
        "request_scope": premise["request_scope"],
        "constant": float(premise["constant"]),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
        "conditional_law": "truth is inside iff the verified global Lipschitz premise holds",
    }
