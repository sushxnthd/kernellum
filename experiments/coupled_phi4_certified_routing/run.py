#!/usr/bin/env python3
"""Frozen coupled-phi4 certificate routing experiment."""
from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path
import random

import numpy as np
from scipy.optimize import least_squares, root
from scipy.spatial.distance import pdist
from scipy.stats import qmc

DIM = 5
SEED = 20261021
BOUND = 1.25
SIGNS = np.asarray(tuple(product((-1.0, 1.0), repeat=DIM)))


def residual(x, weights):
    x = np.asarray(x, dtype=float)
    out = x**3 - x
    for i, weight in enumerate(weights):
        delta = weight * (x[i] - x[i + 1])
        out[i] += delta
        out[i + 1] -= delta
    return out


def jacobian(x, weights):
    x = np.asarray(x, dtype=float)
    matrix = np.diag(3 * x**2 - 1)
    for i, weight in enumerate(weights):
        matrix[i, i] += weight
        matrix[i + 1, i + 1] += weight
        matrix[i, i + 1] -= weight
        matrix[i + 1, i] -= weight
    return matrix


def weight_regimes():
    rng = random.Random(SEED)
    pool = list(product((1, 2, 3, 4), repeat=DIM - 1))
    rng.shuffle(pool)
    return ((2, 2, 2, 2),) + tuple(pool[:16])


def reference_roots(weights):
    roots = []
    for sign in SIGNS:
        solved = root(lambda x: residual(x, weights), sign,
                      jac=lambda x: jacobian(x, weights), method="hybr", tol=1e-12)
        assert solved.success and np.linalg.norm(residual(solved.x, weights), np.inf) < 1e-10
        roots.append(solved.x)
    roots = np.asarray(roots)
    assert np.min(pdist(roots, metric="chebyshev")) > 0.5
    return roots


def structured_starts(weights):
    starts = []
    for sign in SIGNS:
        # One deterministic Newton refinement, charged as one residual and one
        # Jacobian call per box in the end-to-end accounting.
        starts.append(sign - np.linalg.solve(jacobian(sign, weights), residual(sign, weights)))
    return np.asarray(starts)


def tensor_corners():
    return BOUND * SIGNS


def optimized_lhs():
    best, best_score = None, -1.0
    for candidate in range(128):
        points = qmc.LatinHypercube(DIM, seed=SEED + candidate).random(32)
        points = qmc.scale(points, [-BOUND] * DIM, [BOUND] * DIM)
        score = float(np.min(pdist(points)))
        if score > best_score:
            best, best_score = points, score
    return best


def greedy_maximin():
    pool = qmc.scale(qmc.Sobol(DIM, scramble=True, seed=SEED).random_base2(12),
                     [-BOUND] * DIM, [BOUND] * DIM)
    selected = [int(np.argmin(np.sum(pool**2, axis=1)))]
    nearest = np.linalg.norm(pool - pool[selected[0]], axis=1)
    for _ in range(31):
        index = int(np.argmax(nearest))
        selected.append(index)
        nearest = np.minimum(nearest, np.linalg.norm(pool - pool[index], axis=1))
    return pool[selected]


def evaluate(starts, weights, roots, max_nfev):
    covered = set()
    evaluations = 0
    best = float("inf")
    for start in starts:
        solved = least_squares(lambda x: residual(x, weights), start,
                               jac=lambda x: jacobian(x, weights),
                               xtol=1e-11, ftol=1e-11, gtol=1e-11,
                               max_nfev=max_nfev)
        evaluations += int(solved.nfev + solved.njev)
        objective = float(solved.fun @ solved.fun)
        best = min(best, objective)
        distances = np.max(np.abs(roots - solved.x), axis=1)
        match = int(np.argmin(distances))
        if distances[match] <= 1e-6 and objective <= 1e-20:
            covered.add(match)
    return {"coverage": len(covered), "evaluations": evaluations, "best_objective": best}


def main():
    controls = {"tensor_corners": tensor_corners(), "optimized_lhs": optimized_lhs(),
                "greedy_maximin": greedy_maximin()}
    rows = []
    certificate_checks = 0
    for numerators in weight_regimes():
        weights = np.asarray(numerators, dtype=float) / 64
        roots = reference_roots(weights)
        # Independent numerical consequences of the analytic box certificate.
        for sign, certified_root in zip(SIGNS, roots, strict=True):
            assert np.all(sign * certified_root >= 0.75)
            assert np.all(sign * certified_root <= 1.25)
            assert np.min(np.linalg.eigvalsh(jacobian(certified_root, weights))) > 0
            certificate_checks += 1
        methods = {"certified_newton": structured_starts(weights), **controls}
        for name, starts in methods.items():
            full = evaluate(starts, weights, roots, 100)
            capped = evaluate(starts, weights, roots, 4)
            overhead = 64 if name == "certified_newton" else 0
            rows.append({
                "weights_numerators": list(numerators), "method": name,
                "full": full, "capped": capped,
                "end_to_end_evaluations": full["evaluations"] + overhead,
                "certificate_overhead": overhead,
            })
    by_method = {}
    for name in ("certified_newton", "tensor_corners", "optimized_lhs", "greedy_maximin"):
        subset = [row for row in rows if row["method"] == name]
        by_method[name] = {
            "regimes": len(subset),
            "full_complete": sum(row["full"]["coverage"] == 32 for row in subset),
            "capped_complete": sum(row["capped"]["coverage"] == 32 for row in subset),
            "capped_catastrophes": sum(row["capped"]["coverage"] < 32 for row in subset),
            "total_end_to_end_evaluations": sum(row["end_to_end_evaluations"] for row in subset),
            "worst_best_objective": max(row["full"]["best_objective"] for row in subset),
        }
    structured = by_method["certified_newton"]
    complete_controls = [value for key, value in by_method.items()
                         if key != "certified_newton" and value["full_complete"] == 17]
    best_control_work = min(value["total_end_to_end_evaluations"] for value in complete_controls)
    reduction = 1 - structured["total_end_to_end_evaluations"] / best_control_work
    gate = (
        certificate_checks == 17 * 32
        and structured["full_complete"] == structured["capped_complete"] == 17
        and any(value["capped_catastrophes"] > 0 for value in complete_controls)
        and reduction >= 0.25
        and structured["worst_best_objective"] <= 1e-20
    )
    result = {
        "family": "five_site_open_chain_discrete_phi4_stationarity",
        "seed": SEED, "certificate_checks": certificate_checks,
        "rows": rows, "summary": by_method,
        "best_complete_control_work": best_control_work,
        "structured_work_reduction": reduction,
        "gate_pass": gate,
        "decision": "SURVIVES" if gate else "KILL_OR_REFORMULATE",
    }
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["pre_digest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    target = Path("results/coupled_phi4_certified_routing.json")
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": by_method, "reduction": reduction, "gate": gate}, sort_keys=True))


if __name__ == "__main__":
    main()
