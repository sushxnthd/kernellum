#!/usr/bin/env python3
"""Independent exact/accounting audit for the coupled-phi4 experiment."""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path


def main():
    data = json.loads(Path("results/coupled_phi4_certified_routing.json").read_text())
    checks = {}
    # Exact theorem margins over every frozen rational edge pattern.
    for row in data["rows"]:
        numerators = row["weights_numerators"]
        assert all(1 <= value <= 4 for value in numerators)
    inner_uncoupled = Fraction(21, 64)
    maximum_coupling = 2 * Fraction(4, 64) * Fraction(5, 2)
    checks["strict_face_margin"] = inner_uncoupled - maximum_coupling == Fraction(1, 64)
    checks["strict_jacobian_margin"] = Fraction(3) * Fraction(3, 4) ** 2 - 1 > 0
    checks["all_544_boxes_checked"] = data["certificate_checks"] == 17 * 32

    summary = data["summary"]
    structured = summary["certified_newton"]
    corners = summary["tensor_corners"]
    checks["structured_full_and_capped_complete"] = (
        structured["full_complete"] == structured["capped_complete"] == 17
    )
    checks["corner_full_but_capped_failure"] = (
        corners["full_complete"] == 17 and corners["capped_catastrophes"] == 17
    )
    complete_controls = [value for key, value in summary.items()
                         if key != "certified_newton" and value["full_complete"] == 17]
    best_control = min(value["total_end_to_end_evaluations"] for value in complete_controls)
    exact_reduction = Fraction(best_control - structured["total_end_to_end_evaluations"], best_control)
    checks["work_counts_recomputed"] = best_control == data["best_complete_control_work"]
    checks["reported_reduction_recomputed"] = abs(float(exact_reduction) - data["structured_work_reduction"]) < 1e-15
    checks["frozen_25_percent_gate_fails"] = exact_reduction < Fraction(1, 4) and not data["gate_pass"]
    checks["decision_preserved"] = data["decision"] == "KILL_OR_REFORMULATE"
    assert all(checks.values())
    result = {
        "independent_checks": checks,
        "exact_work_reduction": str(exact_reduction),
        "exact_work_reduction_percent": float(100 * exact_reduction),
        "status": "pass",
    }
    Path("results/coupled_phi4_certified_routing_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
