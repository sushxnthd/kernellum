#!/usr/bin/env python3
"""Independent exact and aggregate audit for phi4 antipodal batching."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from itertools import product
from pathlib import Path


def exact_residual(x, weights):
    out = [value**3 - value for value in x]
    for i, weight in enumerate(weights):
        delta = weight * (x[i] - x[i + 1])
        out[i] += delta
        out[i + 1] -= delta
    return out


def exact_jacobian(x, weights):
    matrix = [[Fraction(0) for _ in x] for _ in x]
    for i, value in enumerate(x):
        matrix[i][i] = 3 * value**2 - 1
    for i, weight in enumerate(weights):
        matrix[i][i] += weight
        matrix[i + 1][i + 1] += weight
        matrix[i][i + 1] -= weight
        matrix[i + 1][i] -= weight
    return matrix


def main():
    target = Path("results/phi4_orbit_certificate_amortization.json")
    data = json.loads(target.read_text())
    checks = {}
    predecessor = json.loads(Path("results/coupled_phi4_certified_routing.json").read_text())
    old = {tuple(row["weights_numerators"]) for row in predecessor["rows"]}
    new = {tuple(row) for row in data["regimes"]}
    checks["nineteen_disjoint_regimes"] = len(new) == 19 and not (old & new)

    exact_identities = 0
    signs = tuple(product((-1, 1), repeat=5))
    for numerators in new:
        weights = tuple(Fraction(value, 64) for value in numerators)
        for sign in signs:
            x = tuple(Fraction(value) for value in sign)
            negative = tuple(-value for value in x)
            fx = exact_residual(x, weights)
            fnegative = exact_residual(negative, weights)
            checks_here = all(left == -right for left, right in zip(fnegative, fx))
            checks_here &= exact_jacobian(negative, weights) == exact_jacobian(x, weights)
            assert checks_here
            exact_identities += 1
    checks["all_exact_orbit_identities"] = exact_identities == 19 * 32 == data["identity_checks"]
    checks["starts_and_behavior_identical"] = (
        data["max_start_mismatch"] == 0
        and data["batched_unbatched_behavior_identical"]
    )

    rows = data["rows"]
    rebuilt = {}
    for name in data["summary"]:
        subset = [row for row in rows if row["method"] == name]
        rebuilt[name] = {
            "regimes": len(subset),
            "full_complete": sum(row["full"]["coverage"] == 32 for row in subset),
            "capped_complete": sum(row["capped"]["coverage"] == 32 for row in subset),
            "capped_catastrophes": sum(row["capped"]["coverage"] < 32 for row in subset),
            "total_solver_evaluations": sum(row["full"]["evaluations"] for row in subset),
            "total_overhead": sum(row["certificate_start_overhead"] for row in subset),
            "total_end_to_end_evaluations": sum(row["end_to_end_evaluations"] for row in subset),
            "worst_best_objective": max(row["full"]["best_objective"] for row in subset),
        }
    checks["all_aggregates_recomputed"] = rebuilt == data["summary"]
    batched = rebuilt["orbit_batched_certified"]
    unbatched = rebuilt["unbatched_certified"]
    corners = rebuilt["tensor_corners"]
    reduction = Fraction(corners["total_end_to_end_evaluations"] - batched["total_end_to_end_evaluations"],
                         corners["total_end_to_end_evaluations"])
    checks["overhead_halved_only"] = (
        batched["total_solver_evaluations"] == unbatched["total_solver_evaluations"]
        and batched["total_overhead"] * 2 == unbatched["total_overhead"]
    )
    checks["safety_and_control_boundary"] = (
        batched["full_complete"] == batched["capped_complete"] == 19
        and batched["capped_catastrophes"] == 0
        and corners["full_complete"] == 19
        and corners["capped_catastrophes"] == 19
    )
    checks["exact_25_percent_gate_passes"] = (
        reduction >= Fraction(1, 4)
        and abs(float(reduction) - data["orbit_batched_work_reduction"]) < 1e-15
        and data["gate_pass"] and data["decision"] == "SURVIVES"
    )
    without_digest = dict(data)
    reported = without_digest.pop("pre_digest_sha256")
    canonical = json.dumps(without_digest, indent=2, sort_keys=True) + "\n"
    checks["primary_digest_recomputed"] = hashlib.sha256(canonical.encode()).hexdigest() == reported
    assert all(checks.values())
    result = {
        "protocol": "kernellum.phi4-orbit-certificate-amortization.audit.v1",
        "independent_checks": checks,
        "exact_work_reduction": str(reduction),
        "exact_work_reduction_percent": float(100 * reduction),
        "status": "pass",
    }
    Path("results/phi4_orbit_certificate_amortization_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
