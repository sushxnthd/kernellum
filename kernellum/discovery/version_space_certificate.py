"""Fail-closed conditional prediction-envelope certificates.

The certificate proves a bound only under its explicit premise that the unknown
response belongs pointwise to the declared version space.  This module does not
infer that premise from finite training error.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Callable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class VerifiedProvenance:
    manifest_sha256: str
    hypothesis_class: str
    request_scope: str


def verify_provenance(
    manifest: bytes,
    expected_sha256: str,
    external_verifier: Callable[[Mapping[str, object]], bool],
) -> VerifiedProvenance:
    """Verify integrity and delegate the scientific premise to a domain checker."""
    digest = hashlib.sha256(manifest).hexdigest()
    if digest != expected_sha256:
        raise ValueError("provenance digest mismatch")
    payload = json.loads(manifest)
    if payload.get("schema") != "kernellum.hypothesis-class-provenance.v1":
        raise ValueError("unsupported provenance schema")
    hypothesis_class = payload.get("hypothesis_class")
    request_scope = payload.get("request_scope")
    if not isinstance(hypothesis_class, str) or not hypothesis_class:
        raise ValueError("missing hypothesis class")
    if not isinstance(request_scope, str) or not request_scope:
        raise ValueError("missing request scope")
    if not external_verifier(payload):
        raise ValueError("external provenance verifier rejected premise")
    return VerifiedProvenance(digest, hypothesis_class, request_scope)


def _refusal(reason: str) -> dict[str, object]:
    return {"schema": "kernellum.envelope-decision.v1", "decision": "refuse", "reason": reason}


def issue_envelope_certificate(
    predictions: Sequence[Sequence[float]],
    selected_prediction: Sequence[float],
    *,
    scale: float,
    tolerance: float,
    provenance: VerifiedProvenance | None,
) -> dict[str, object]:
    """Issue a conditional worst-case RMSE certificate or refuse.

    If the premise ``truth[i] in [lower[i], upper[i]]`` holds for every request
    point, the selected prediction's normalized RMSE is at most ``bound``.
    """
    if provenance is None:
        return _refusal("missing_verified_hypothesis_class_provenance")
    bank = np.asarray(predictions, dtype=float)
    selected = np.asarray(selected_prediction, dtype=float)
    if bank.ndim != 2 or bank.shape[0] == 0 or selected.ndim != 1 or bank.shape[1] != selected.size:
        return _refusal("malformed_prediction_bank")
    if not np.all(np.isfinite(bank)) or not np.all(np.isfinite(selected)):
        return _refusal("nonfinite_prediction")
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(tolerance) or tolerance < 0:
        return _refusal("invalid_scale_or_tolerance")
    lower = bank.min(axis=0)
    upper = bank.max(axis=0)
    if np.any(selected < lower) or np.any(selected > upper):
        return _refusal("selected_prediction_outside_envelope")
    worst_error = np.maximum(selected - lower, upper - selected)
    bound = float(np.sqrt(np.mean(worst_error**2)) / scale)
    if bound > tolerance:
        return _refusal("conditional_bound_exceeds_tolerance")
    payload: dict[str, object] = {
        "schema": "kernellum.envelope-decision.v1",
        "decision": "certify_conditional",
        "premise": "unknown_response_is_pointwise_inside_declared_version_space",
        "hypothesis_class": provenance.hypothesis_class,
        "request_scope": provenance.request_scope,
        "provenance_sha256": provenance.manifest_sha256,
        "normalized_rmse_upper_bound": bound,
        "tolerance": float(tolerance),
        "points": int(selected.size),
        "models": int(bank.shape[0]),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload["certificate_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return payload

