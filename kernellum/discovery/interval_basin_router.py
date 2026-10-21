"""Fail-closed routing for independently generated interval basin certificates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntervalBasinRoute:
    activated: bool
    route: str
    reason: str
    certified_boxes: int
    starts: tuple[tuple[float, float], ...]


def route_interval_basin_certificate(certificate: dict, expected_boxes: int) -> IntervalBasinRoute:
    """Activate structured starts only for a complete, disjoint exact certificate.

    The certificate producer owns interval evaluation. This boundary validates
    the proof obligations and emits box centers; malformed or partial evidence
    always routes to the generic fallback.
    """
    fallback = lambda reason: IntervalBasinRoute(False, "generic_fallback", reason, 0, ())
    if not isinstance(certificate, dict):
        return fallback("MALFORMED_CERTIFICATE")
    if certificate.get("arithmetic") not in {
        "fractions.Fraction outward intervals", "decimal outward intervals"
    }:
        return fallback("UNTRUSTED_ARITHMETIC")
    boxes = certificate.get("boxes")
    if not isinstance(boxes, list) or len(boxes) != expected_boxes:
        return fallback("INCOMPLETE_BOX_SET")
    if certificate.get("box_count") != expected_boxes or not certificate.get("pairwise_disjoint"):
        return fallback("INCOMPLETE_OR_OVERLAPPING")
    starts = []
    identifiers = set()
    for box in boxes:
        if not isinstance(box, dict) or box.get("id") in identifiers:
            return fallback("MALFORMED_BOX")
        identifiers.add(box["id"])
        checks = box.get("checks")
        if not isinstance(checks, dict) or set(checks) != {
            "u_left_negative", "u_right_positive", "v_lower_negative",
            "v_upper_positive", "hessian_pd"
        } or not all(value is True for value in checks.values()):
            return fallback("FAILED_PROOF_OBLIGATION")
        try:
            u0, u1 = map(float, box["u"])
            v0, v1 = map(float, box["v"])
        except (KeyError, TypeError, ValueError):
            return fallback("MALFORMED_BOX")
        if not (u0 < u1 and v0 < v1):
            return fallback("MALFORMED_BOX")
        u, v = (u0 + u1) / 2, (v0 + v1) / 2
        starts.append(((u + v) / 2, (u - v) / 2))
    if certificate.get("passed") is not True:
        return fallback("CERTIFICATE_NOT_PASSED")
    return IntervalBasinRoute(True, "interval_box_centers", "CERTIFIED", len(boxes), tuple(starts))
