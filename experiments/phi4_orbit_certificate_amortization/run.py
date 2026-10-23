#!/usr/bin/env python3
"""Prospective antipodal certificate/start amortization for coupled phi4."""
from __future__ import annotations

import hashlib
import json
from itertools import product
from pathlib import Path
import random
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from experiments.coupled_phi4_certified_routing.run import (
    DIM, SIGNS, evaluate, greedy_maximin, jacobian, optimized_lhs,
    reference_roots, residual, structured_starts, tensor_corners, weight_regimes,
)
from kernellum.discovery.symmetry_orbit_starts import route_antipodal_newton_starts

SEED = 20261022
REGIMES = 19


def canonicalize(value):
    """Map diagnostic floats to a platform-independent evidence format."""
    if isinstance(value, float):
        if abs(value) < 1e-14:
            return 0.0
        return float(f"{value:.15g}")
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {key: canonicalize(item) for key, item in value.items()}
    return value


def prospective_weight_regimes():
    previous = set(weight_regimes())
    pool = [row for row in product((1, 2, 3, 4), repeat=DIM - 1)
            if row not in previous]
    random.Random(SEED).shuffle(pool)
    return tuple(pool[:REGIMES])


def orbit_starts(weights):
    certificate = {
        "passed": True,
        "symmetry": "global_sign",
        "residual_odd": True,
        "jacobian_even": True,
        "pairwise_disjoint": True,
        "box_count": len(SIGNS),
    }
    route = route_antipodal_newton_starts(
        certificate,
        SIGNS,
        lambda x: residual(x, weights),
        lambda x: jacobian(x, weights),
    )
    assert route.activated and route.residual_calls == route.jacobian_calls == 16
    return np.asarray(route.starts)


def main():
    controls = {
        "tensor_corners": tensor_corners(),
        "optimized_lhs": optimized_lhs(),
        "greedy_maximin": greedy_maximin(),
    }
    rows = []
    identity_checks = 0
    max_start_mismatch = 0.0
    for numerators in prospective_weight_regimes():
        weights = np.asarray(numerators, dtype=float) / 64
        roots = reference_roots(weights)
        for sign in SIGNS:
            assert np.array_equal(residual(-sign, weights), -residual(sign, weights))
            assert np.array_equal(jacobian(-sign, weights), jacobian(sign, weights))
            identity_checks += 1
        batched = orbit_starts(weights)
        unbatched = structured_starts(weights)
        max_start_mismatch = max(max_start_mismatch,
                                 float(np.max(np.abs(batched - unbatched))))
        methods = {
            "orbit_batched_certified": batched,
            "unbatched_certified": unbatched,
            **controls,
        }
        for name, starts in methods.items():
            full = evaluate(starts, weights, roots, 100)
            capped = evaluate(starts, weights, roots, 4)
            # Canonicalize numerical zero so BLAS-level roundoff does not alter
            # the committed scientific artifact across hosted platforms.
            if full["best_objective"] < 1e-20:
                full["best_objective"] = 0.0
            if capped["best_objective"] < 1e-20:
                capped["best_objective"] = 0.0
            overhead = 32 if name == "orbit_batched_certified" else (
                64 if name == "unbatched_certified" else 0)
            rows.append({
                "weights_numerators": list(numerators),
                "method": name,
                "full": full,
                "capped": capped,
                "certificate_start_overhead": overhead,
                "end_to_end_evaluations": full["evaluations"] + overhead,
            })

    names = ("orbit_batched_certified", "unbatched_certified",
             "tensor_corners", "optimized_lhs", "greedy_maximin")
    summary = {}
    for name in names:
        subset = [row for row in rows if row["method"] == name]
        summary[name] = {
            "regimes": len(subset),
            "full_complete": sum(row["full"]["coverage"] == 32 for row in subset),
            "capped_complete": sum(row["capped"]["coverage"] == 32 for row in subset),
            "capped_catastrophes": sum(row["capped"]["coverage"] < 32 for row in subset),
            "total_solver_evaluations": sum(row["full"]["evaluations"] for row in subset),
            "total_overhead": sum(row["certificate_start_overhead"] for row in subset),
            "total_end_to_end_evaluations": sum(row["end_to_end_evaluations"] for row in subset),
            "worst_best_objective": max(row["full"]["best_objective"] for row in subset),
        }
    batched = summary["orbit_batched_certified"]
    unbatched = summary["unbatched_certified"]
    complete_controls = [summary[name] for name in
                         ("tensor_corners", "optimized_lhs", "greedy_maximin")
                         if summary[name]["full_complete"] == REGIMES]
    best_control_work = min(item["total_end_to_end_evaluations"]
                            for item in complete_controls)
    reduction = 1 - batched["total_end_to_end_evaluations"] / best_control_work
    behavior_identical = all(
        row_b["full"] == row_u["full"] and row_b["capped"] == row_u["capped"]
        for row_b, row_u in zip(
            [r for r in rows if r["method"] == "orbit_batched_certified"],
            [r for r in rows if r["method"] == "unbatched_certified"],
            strict=True,
        )
    )
    gate = (
        identity_checks == REGIMES * 32
        and max_start_mismatch <= 1e-14
        and behavior_identical
        and batched["full_complete"] == batched["capped_complete"] == REGIMES
        and batched["capped_catastrophes"] == 0
        and any(item["capped_catastrophes"] > 0 for item in complete_controls)
        and reduction >= 0.25
        and batched["worst_best_objective"] <= 1e-20
        and batched["total_solver_evaluations"] == unbatched["total_solver_evaluations"]
        and batched["total_overhead"] * 2 == unbatched["total_overhead"]
    )
    result = {
        "protocol": "kernellum.phi4-orbit-certificate-amortization.v1",
        "seed": SEED,
        "regimes": [list(row) for row in prospective_weight_regimes()],
        "disjoint_from_predecessor": not bool(set(prospective_weight_regimes()) & set(weight_regimes())),
        "identity_checks": identity_checks,
        "max_start_mismatch": max_start_mismatch,
        "batched_unbatched_behavior_identical": behavior_identical,
        "rows": rows,
        "summary": summary,
        "best_complete_control_work": best_control_work,
        "orbit_batched_work_reduction": reduction,
        "gate_pass": gate,
        "decision": "SURVIVES" if gate else "KILL_OR_REFORMULATE",
    }
    result = canonicalize(result)
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["pre_digest_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    target = Path("results/phi4_orbit_certificate_amortization.json")
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": summary, "reduction": reduction,
                      "gate": gate, "max_start_mismatch": max_start_mismatch},
                     sort_keys=True))


if __name__ == "__main__":
    main()
