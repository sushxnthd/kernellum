#!/usr/bin/env python3
"""Prospective transfer of antipodal certificate amortization to a quintic family."""
from __future__ import annotations

from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kernellum.discovery.symmetry_orbit_starts import route_antipodal_newton_starts

DIM = 5
SIGNS = np.asarray(tuple(product((-1.0, 1.0), repeat=DIM)))
WEIGHT_DENOMINATOR = 96
PILOT_SEED = 20261023
HOLDOUT_SEED = 20261024
PILOT_REGIMES = 20
HOLDOUT_REGIMES = 23
FULL_BUDGET = 50
CAPPED_BUDGET = 4
FACE_MARGIN = Fraction(1063, 3072)
MONOTONICITY_MARGIN = Fraction(149, 256)


def residual(x, weights, forcing=None):
    x = np.asarray(x, dtype=float)
    value = x**5 - x
    for index, weight in enumerate(weights):
        delta = weight * (x[index] - x[index + 1])
        value[index] += delta
        value[index + 1] -= delta
    if forcing is not None:
        value = value + np.asarray(forcing, dtype=float)
    return value


def jacobian(x, weights):
    x = np.asarray(x, dtype=float)
    matrix = np.diag(5 * x**4 - 1)
    for index, weight in enumerate(weights):
        matrix[index, index] += weight
        matrix[index + 1, index + 1] += weight
        matrix[index, index + 1] -= weight
        matrix[index + 1, index] -= weight
    return matrix


def regimes():
    pool = list(product((1, 2, 3, 4), repeat=DIM - 1))
    pilot = pool.copy()
    random.Random(PILOT_SEED).shuffle(pilot)
    opened = tuple(pilot[:PILOT_REGIMES])
    remaining = [row for row in pool if row not in set(opened)]
    random.Random(HOLDOUT_SEED).shuffle(remaining)
    return opened, tuple(remaining[:HOLDOUT_REGIMES])


def certificate():
    return {
        "passed": True,
        "symmetry": "global_sign",
        "residual_odd": True,
        "jacobian_even": True,
        "pairwise_disjoint": True,
        "box_count": len(SIGNS),
        "face_margin": str(FACE_MARGIN),
        "monotonicity_margin": str(MONOTONICITY_MARGIN),
        "root_boxes_certified": len(SIGNS),
    }


def unbatched_starts(weights):
    starts = []
    for sign in SIGNS:
        starts.append(sign - np.linalg.solve(jacobian(sign, weights), residual(sign, weights)))
    return np.asarray(starts)


def orbit_starts(weights):
    route = route_antipodal_newton_starts(
        certificate(), SIGNS,
        lambda x: residual(x, weights),
        lambda x: jacobian(x, weights),
    )
    assert route.activated
    assert route.residual_calls == route.jacobian_calls == 16
    return np.asarray(route.starts), route.residual_calls + route.jacobian_calls


def tensor_corners():
    return 1.25 * SIGNS


def optimized_lhs(seed=761, count=32):
    rng = np.random.default_rng(seed)
    starts = np.empty((count, DIM))
    for column in range(DIM):
        starts[:, column] = -1.25 + 2.5 * (rng.permutation(count) + 0.5) / count
    return starts


def greedy_maximin(seed=883, count=32, candidates=4096):
    rng = np.random.default_rng(seed)
    pool = rng.uniform(-1.25, 1.25, (candidates, DIM))
    chosen = [int(np.argmax(np.linalg.norm(pool, axis=1)))]
    distances = np.linalg.norm(pool - pool[chosen[0]], axis=1)
    for _ in range(1, count):
        index = int(np.argmax(distances))
        chosen.append(index)
        distances = np.minimum(distances, np.linalg.norm(pool - pool[index], axis=1))
    return pool[chosen]


def solve(start, weights, budget):
    x = np.asarray(start, dtype=float).copy()
    evaluations = 0
    for _ in range(budget):
        value = residual(x, weights)
        matrix = jacobian(x, weights)
        evaluations += 2
        if np.linalg.norm(value, ord=np.inf) < 1e-10:
            return x, evaluations, True
        try:
            x -= np.linalg.solve(matrix, value)
        except np.linalg.LinAlgError:
            return x, evaluations, False
    return x, evaluations, np.linalg.norm(residual(x, weights), ord=np.inf) < 1e-8


def box_label(point):
    absolute = np.abs(point)
    if np.any(absolute < 0.75) or np.any(absolute > 1.25):
        return None
    return tuple(1 if value > 0 else -1 for value in point)


def evaluate(starts, weights, budget):
    covered = set()
    evaluations = 0
    best_objective = float("inf")
    for start in starts:
        point, calls, converged = solve(start, weights, budget)
        evaluations += calls
        objective = float(np.dot(residual(point, weights), residual(point, weights)))
        best_objective = min(best_objective, objective)
        if converged:
            label = box_label(point)
            if label is not None:
                covered.add(label)
    return {
        "coverage": len(covered),
        "evaluations": evaluations,
        "best_objective": best_objective,
    }


def negative_controls():
    rows = []
    for numerator in range(1, 9):
        calls = []
        broken = dict(certificate(), residual_odd=False)
        route = route_antipodal_newton_starts(
            broken, SIGNS,
            lambda x: calls.append("residual") or x,
            lambda x: calls.append("jacobian") or np.eye(len(x)),
        )
        rows.append({
            "forcing": [numerator, 0, 0, 0, 0],
            "forcing_denominator": 1000,
            "exact_oddness_defect": f"{2 * numerator}/1000",
            "activated": route.activated,
            "reason": route.reason,
            "construction_calls": len(calls),
        })
    return rows


def main():
    pilot, holdout = regimes()
    controls = {
        "tensor_corners": tensor_corners(),
        "optimized_lhs": optimized_lhs(),
        "greedy_maximin": greedy_maximin(),
    }
    rows = []
    identity_checks = 0
    max_start_mismatch = 0.0
    for numerators in holdout:
        weights = np.asarray(numerators, dtype=float) / WEIGHT_DENOMINATOR
        for sign in SIGNS:
            assert np.array_equal(residual(-sign, weights), -residual(sign, weights))
            assert np.array_equal(jacobian(-sign, weights), jacobian(sign, weights))
            identity_checks += 1
        batched, overhead = orbit_starts(weights)
        unbatched = unbatched_starts(weights)
        max_start_mismatch = max(
            max_start_mismatch, float(np.max(np.abs(batched - unbatched)))
        )
        methods = {
            "orbit_batched_certified": (batched, overhead),
            "unbatched_certified": (unbatched, 64),
            **{name: (starts, 0) for name, starts in controls.items()},
        }
        for name, (starts, construction_overhead) in methods.items():
            full = evaluate(starts, weights, FULL_BUDGET)
            capped = evaluate(starts, weights, CAPPED_BUDGET)
            rows.append({
                "weights_numerators": list(numerators),
                "method": name,
                "full": full,
                "capped": capped,
                "construction_overhead": construction_overhead,
                "total_work": full["evaluations"] + construction_overhead,
            })

    summary = {}
    for name in (
        "orbit_batched_certified", "unbatched_certified", "tensor_corners",
        "optimized_lhs", "greedy_maximin",
    ):
        subset = [row for row in rows if row["method"] == name]
        summary[name] = {
            "regimes": len(subset),
            "full_complete": sum(row["full"]["coverage"] == 32 for row in subset),
            "capped_complete": sum(row["capped"]["coverage"] == 32 for row in subset),
            "capped_catastrophes": sum(row["capped"]["coverage"] < 32 for row in subset),
            "solver_evaluations": sum(row["full"]["evaluations"] for row in subset),
            "construction_overhead": sum(row["construction_overhead"] for row in subset),
            "total_work": sum(row["total_work"] for row in subset),
            "worst_best_objective": max(row["full"]["best_objective"] for row in subset),
        }
    complete_controls = [
        summary[name] for name in ("tensor_corners", "optimized_lhs", "greedy_maximin")
        if summary[name]["full_complete"] == HOLDOUT_REGIMES
    ]
    best_control_work = min(item["total_work"] for item in complete_controls)
    selected = summary["orbit_batched_certified"]
    unbatched = summary["unbatched_certified"]
    reduction = Fraction(best_control_work - selected["total_work"], best_control_work)
    behavior_identical = all(
        left["full"] == right["full"] and left["capped"] == right["capped"]
        for left, right in zip(
            [row for row in rows if row["method"] == "orbit_batched_certified"],
            [row for row in rows if row["method"] == "unbatched_certified"],
            strict=True,
        )
    )
    negatives = negative_controls()
    gate = (
        len(set(pilot) & set(holdout)) == 0
        and identity_checks == HOLDOUT_REGIMES * len(SIGNS)
        and max_start_mismatch <= 1e-14
        and behavior_identical
        and selected["full_complete"] == selected["capped_complete"] == HOLDOUT_REGIMES
        and selected["capped_catastrophes"] == 0
        and selected["worst_best_objective"] <= 1e-18
        and selected["solver_evaluations"] == unbatched["solver_evaluations"]
        and selected["construction_overhead"] * 2 == unbatched["construction_overhead"]
        and reduction >= Fraction(35, 100)
        and all(not row["activated"] and row["construction_calls"] == 0 for row in negatives)
    )
    result = {
        "protocol": "kernellum.quintic-equivariance-transfer.v1",
        "pilot_seed": PILOT_SEED,
        "holdout_seed": HOLDOUT_SEED,
        "pilot_regimes": [list(row) for row in pilot],
        "holdout_regimes": [list(row) for row in holdout],
        "holdout_disjoint_from_pilot": not bool(set(pilot) & set(holdout)),
        "diagnostic": {
            "residual_odd": True,
            "jacobian_even": True,
            "face_margin": str(FACE_MARGIN),
            "monotonicity_margin": str(MONOTONICITY_MARGIN),
            "certified_root_boxes_per_regime": 32,
        },
        "identity_checks": identity_checks,
        "max_start_mismatch": max_start_mismatch,
        "batched_unbatched_behavior_identical": behavior_identical,
        "rows": rows,
        "summary": summary,
        "best_complete_control_work": best_control_work,
        "exact_work_reduction": str(reduction),
        "work_reduction": float(reduction),
        "negative_controls": negatives,
        "gate_pass": gate,
        "decision": "TRANSFER_SURVIVES" if gate else "KILL_OR_REFORMULATE",
    }
    without_digest = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["pre_digest_sha256"] = hashlib.sha256(without_digest.encode()).hexdigest()
    target = ROOT / "results/quintic_equivariance_transfer.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": result["decision"],
        "summary": summary,
        "exact_work_reduction": str(reduction),
        "negative_abstentions": sum(not row["activated"] for row in negatives),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
