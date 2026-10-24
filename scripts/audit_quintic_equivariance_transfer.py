#!/usr/bin/env python3
"""Independent rational and aggregate audit for quintic equivariance transfer."""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random


DIM = 5
PILOT_SEED = 20261023
HOLDOUT_SEED = 20261024


def exact_residual(x, weights):
    value = [item**5 - item for item in x]
    for index, weight in enumerate(weights):
        delta = weight * (x[index] - x[index + 1])
        value[index] += delta
        value[index + 1] -= delta
    return value


def exact_jacobian(x, weights):
    matrix = [[Fraction(0) for _ in x] for _ in x]
    for index, item in enumerate(x):
        matrix[index][index] = 5 * item**4 - 1
    for index, weight in enumerate(weights):
        matrix[index][index] += weight
        matrix[index + 1][index + 1] += weight
        matrix[index][index + 1] -= weight
        matrix[index + 1][index] -= weight
    return matrix


def independent_regimes():
    pool = list(product((1, 2, 3, 4), repeat=DIM - 1))
    pilot = pool.copy()
    random.Random(PILOT_SEED).shuffle(pilot)
    opened = tuple(pilot[:20])
    remaining = [row for row in pool if row not in set(opened)]
    random.Random(HOLDOUT_SEED).shuffle(remaining)
    return opened, tuple(remaining[:23])


def main():
    target = Path("results/quintic_equivariance_transfer.json")
    data = json.loads(target.read_text())
    checks = {}
    pilot, holdout = independent_regimes()
    checks["holdout_frozen_and_disjoint"] = (
        data["pilot_regimes"] == [list(row) for row in pilot]
        and data["holdout_regimes"] == [list(row) for row in holdout]
        and not (set(pilot) & set(holdout))
    )

    face_margin = Fraction(525, 1024) - Fraction(1, 6)
    monotonicity_margin = 5 * Fraction(3, 4)**4 - 1
    checks["exact_box_margins"] = (
        face_margin == Fraction(data["diagnostic"]["face_margin"]) == Fraction(1063, 3072)
        and monotonicity_margin == Fraction(data["diagnostic"]["monotonicity_margin"]) == Fraction(149, 256)
        and data["diagnostic"]["certified_root_boxes_per_regime"] == 32
    )

    identity_checks = 0
    rational_points = (
        tuple(Fraction(value) for value in (1, -1, 1, -1, 1)),
        tuple(Fraction(value, 5) for value in (4, -6, 7, 5, -3)),
    )
    for numerators in holdout:
        weights = tuple(Fraction(value, 96) for value in numerators)
        for point in rational_points:
            negative = tuple(-value for value in point)
            positive_residual = exact_residual(point, weights)
            negative_residual = exact_residual(negative, weights)
            assert all(left == -right for left, right in zip(negative_residual, positive_residual))
            assert exact_jacobian(negative, weights) == exact_jacobian(point, weights)
            identity_checks += 1
    checks["exact_equivariance_on_unseen_rationals"] = identity_checks == 23 * 2

    rebuilt = {}
    for name in data["summary"]:
        subset = [row for row in data["rows"] if row["method"] == name]
        rebuilt[name] = {
            "regimes": len(subset),
            "full_complete": sum(row["full"]["coverage"] == 32 for row in subset),
            "capped_complete": sum(row["capped"]["coverage"] == 32 for row in subset),
            "capped_catastrophes": sum(row["capped"]["coverage"] < 32 for row in subset),
            "solver_evaluations": sum(row["full"]["evaluations"] for row in subset),
            "construction_overhead": sum(row["construction_overhead"] for row in subset),
            "total_work": sum(row["total_work"] for row in subset),
            "worst_best_objective": max(row["full"]["best_objective"] for row in subset),
        }
    checks["all_aggregates_recomputed"] = rebuilt == data["summary"]
    selected = rebuilt["orbit_batched_certified"]
    unbatched = rebuilt["unbatched_certified"]
    tensor = rebuilt["tensor_corners"]
    reduction = Fraction(tensor["total_work"] - selected["total_work"], tensor["total_work"])
    checks["exact_fleet_gate"] = (
        reduction == Fraction(477, 1165)
        and reduction >= Fraction(35, 100)
        and data["exact_work_reduction"] == str(reduction)
        and abs(data["work_reduction"] - float(reduction)) < 1e-15
    )
    checks["safety_and_ablation"] = (
        selected["full_complete"] == selected["capped_complete"] == 23
        and selected["capped_catastrophes"] == 0
        and selected["solver_evaluations"] == unbatched["solver_evaluations"]
        and selected["construction_overhead"] * 2 == unbatched["construction_overhead"]
        and tensor["full_complete"] == 23 and tensor["capped_catastrophes"] == 23
        and data["batched_unbatched_behavior_identical"]
        and data["max_start_mismatch"] == 0
    )
    checks["forced_regimes_abstain_pre_evaluation"] = (
        len(data["negative_controls"]) == 8
        and all(
            not row["activated"]
            and row["reason"] == "FAILED_PROOF_OBLIGATION"
            and row["construction_calls"] == 0
            for row in data["negative_controls"]
        )
    )
    without_digest = dict(data)
    reported = without_digest.pop("pre_digest_sha256")
    canonical = json.dumps(without_digest, indent=2, sort_keys=True) + "\n"
    checks["primary_digest_recomputed"] = hashlib.sha256(canonical.encode()).hexdigest() == reported
    checks["reported_gate_consistent"] = data["gate_pass"] and data["decision"] == "TRANSFER_SURVIVES"
    assert all(checks.values()), checks
    result = {
        "protocol": "kernellum.quintic-equivariance-transfer.audit.v1",
        "checks": checks,
        "exact_work_reduction": str(reduction),
        "exact_work_reduction_percent": float(100 * reduction),
        "status": "pass",
    }
    Path("results/quintic_equivariance_transfer_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
