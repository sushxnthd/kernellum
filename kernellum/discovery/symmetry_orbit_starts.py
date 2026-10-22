"""Fail-closed start construction from certified antipodal Newton symmetry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class AntipodalStartRoute:
    activated: bool
    reason: str
    starts: tuple[tuple[float, ...], ...]
    residual_calls: int
    jacobian_calls: int


def route_antipodal_newton_starts(
    certificate: dict,
    signs,
    residual: Callable,
    jacobian: Callable,
) -> AntipodalStartRoute:
    """Construct both starts in each antipodal orbit from one Newton call.

    The producer must certify the algebraic identities. This boundary validates
    the certificate schema and exact finite sign action; any malformed or
    incomplete orbit falls back without evaluating the residual or Jacobian.
    """
    fallback = lambda reason: AntipodalStartRoute(False, reason, (), 0, 0)
    if not isinstance(certificate, dict):
        return fallback("INVALID_CERTIFICATE")
    required = {
        "passed": True,
        "symmetry": "global_sign",
        "residual_odd": True,
        "jacobian_even": True,
        "pairwise_disjoint": True,
    }
    if any(certificate.get(key) != value for key, value in required.items()):
        return fallback("FAILED_PROOF_OBLIGATION")
    array = np.asarray(signs, dtype=float)
    if array.ndim != 2 or len(array) == 0 or len(array) % 2 or not np.isfinite(array).all():
        return fallback("INVALID_ORBIT")
    if certificate.get("box_count") != len(array):
        return fallback("INCOMPLETE_ORBIT")
    keys = [tuple(row) for row in array]
    if len(set(keys)) != len(keys) or any(tuple(-row) not in set(keys) for row in array):
        return fallback("INVALID_ORBIT")

    starts = {}
    calls = 0
    for sign in array:
        key, opposite = tuple(sign), tuple(-sign)
        if key in starts:
            continue
        representative = sign if key > opposite else -sign
        try:
            matrix = np.asarray(jacobian(representative), dtype=float)
            value = np.asarray(residual(representative), dtype=float)
            start = representative - np.linalg.solve(matrix, value)
        except (ValueError, TypeError, np.linalg.LinAlgError):
            return fallback("NEWTON_CONSTRUCTION_FAILED")
        if start.shape != representative.shape or not np.isfinite(start).all():
            return fallback("NEWTON_CONSTRUCTION_FAILED")
        starts[tuple(representative)] = start
        starts[tuple(-representative)] = -start
        calls += 1
    ordered = tuple(tuple(float(value) for value in starts[key]) for key in keys)
    return AntipodalStartRoute(True, "CERTIFIED_ANTIPODAL_ORBITS", ordered, calls, calls)
