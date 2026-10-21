#!/usr/bin/env python3
"""Exact coefficient-interval boundary for the certified FTrig route."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from fractions import Fraction as Q
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "experiments/interval_certified_ftrig/run.py"
SPEC = importlib.util.spec_from_file_location("robust_ftrig_base", SOURCE)
BASE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["robust_ftrig_base"] = BASE
SPEC.loader.exec_module(BASE)


COEFFICIENTS = (BASE.A, BASE.B, BASE.C, BASE.D, BASE.E, BASE.F)


def coefficient_interval(value: Q, rho: Q) -> BASE.Interval:
    return BASE.Interval(value * (1 - rho), value * (1 + rho))


def polynomials(rho: Q = Q(0), coefficients=None):
    uncertain = (tuple(coefficient_interval(value, rho) for value in COEFFICIENTS)
                 if coefficients is None else tuple(BASE.Interval(value) for value in coefficients))
    fu = BASE.product_factors(uncertain[:3], leading_u=True)
    fv = BASE.product_factors(uncertain[3:])
    return (BASE.poly_derivative(fu), BASE.poly_derivative(BASE.poly_derivative(fu)),
            BASE.poly_derivative(fv), BASE.poly_derivative(BASE.poly_derivative(fv)))


def certify(rho: Q = Q(0), coefficients=None) -> dict:
    fu1, fu2, fv1, fv2 = polynomials(rho, coefficients)
    boxes = []
    slacks = []
    for ui, um in enumerate(BASE.U_MULTIPLES):
        for vi, vm in enumerate(BASE.V_MULTIPLES):
            u = BASE.expanded(BASE.pi_multiple(um))
            v = BASE.expanded(BASE.pi_multiple(vm))
            left, right = BASE.Interval(u.lo), BASE.Interval(u.hi)
            lower, upper = BASE.Interval(v.lo), BASE.Interval(v.hi)
            gu_left = BASE.poly_eval(fu1, left) + BASE.radial(left, v) * left / 50
            gu_right = BASE.poly_eval(fu1, right) + BASE.radial(right, v) * right / 50
            gv_lower = BASE.poly_eval(fv1, lower) + BASE.radial(u, lower) * lower / 50
            gv_upper = BASE.poly_eval(fv1, upper) + BASE.radial(u, upper) * upper / 50
            radial = BASE.radial(u, v)
            huu = BASE.poly_eval(fu2, u) + u.square() / 5000 + radial / 50
            hvv = BASE.poly_eval(fv2, v) + v.square() / 5000 + radial / 50
            huv = u * v / 5000
            cross = max(abs(huv.lo), abs(huv.hi))
            determinant = huu.lo * hvv.lo - cross * cross
            local = (-gu_left.hi, gu_right.lo, -gv_lower.hi, gv_upper.lo,
                     huu.lo, hvv.lo, determinant)
            slacks.extend(local)
            boxes.append({
                "id": f"u{ui}-v{vi}",
                "passed": all(value > 0 for value in local),
                "minimum_signed_slack": float(min(local)),
            })
    return {
        "rho": str(rho),
        "rho_float": float(rho),
        "passed": all(box["passed"] for box in boxes),
        "box_count": len(boxes),
        "passing_boxes": sum(box["passed"] for box in boxes),
        "minimum_signed_slack": float(min(slacks)),
        "boxes": boxes,
    }


def frozen_draws(rho_pass: Q):
    rng = np.random.default_rng(20261024)
    denominator = 2**20
    rows = []
    for label, level in (("half", rho_pass / 2), ("boundary", rho_pass),
                         ("double", rho_pass * 2)):
        for draw in range(16):
            integers = rng.integers(-denominator, denominator + 1, size=6)
            deltas = tuple(level * Q(int(value), denominator) for value in integers)
            coefficients = tuple(center * (1 + delta)
                                 for center, delta in zip(COEFFICIENTS, deltas))
            rows.append({"level": label, "draw": draw,
                         "relative_deltas": [str(value) for value in deltas],
                         "coefficients": [str(value) for value in coefficients]})
    return rows


def residual(z, coefficients):
    x, y = z
    u, v = x + y, x - y
    a, b, c, d, e, f = coefficients
    return np.array([
        -10 * u * (a * u * u - 1) * (b * u * u - 1) * (c * u * u - 1),
        -10 * (d * v * v - 1) * (e * v * v - 1) * (f * v * v - 1),
        x * x / 100 + y * y / 100 + 10,
    ])


def run_method(method, seed, coefficients):
    starts = BASE.starts(method, seed)
    found, objectives, nfev = set(), [], 0
    for start in starts:
        fit = least_squares(residual, start, args=(coefficients,), method="trf",
                            xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=3000)
        identity = BASE.box_id(fit.x)
        if identity is not None:
            found.add(identity)
        objectives.append(float(np.dot(fit.fun, fit.fun)))
        nfev += fit.nfev
    return {"method": method, "coverage": len(found), "best_objective": min(objectives),
            "nfev": nfev}


def prospective(rho_pass: Q):
    draws = frozen_draws(rho_pass)
    methods = ("root_lattice", "grid", "optimized_lhs", "greedy_maximin")
    records = []
    for index, row in enumerate(draws):
        rational = tuple(Q(value) for value in row["coefficients"])
        floating = tuple(float(value) for value in rational)
        point_certificate = certify(coefficients=rational)
        outcomes = {method: run_method(method, 20261024 + index, floating)
                    for method in methods}
        best = min(outcome["best_objective"] for outcome in outcomes.values())
        for outcome in outcomes.values():
            outcome["objective_loss"] = outcome["best_objective"] - best > 1e-8
            outcome["catastrophe"] = outcome["coverage"] < 42 or outcome["objective_loss"]
        selected = outcomes["root_lattice"] if point_certificate["passed"] else outcomes["grid"]
        records.append({**row, "point_certificate_passed": point_certificate["passed"],
                        "point_passing_boxes": point_certificate["passing_boxes"],
                        "outcomes": outcomes,
                        "fail_closed": {"route": "root_lattice" if point_certificate["passed"] else "grid",
                                        **selected}})
    safe_root = [row for row in records if not row["outcomes"]["root_lattice"]["catastrophe"]]
    retained = sum(not row["fail_closed"]["catastrophe"] for row in safe_root)
    summary = {
        "trials": len(records),
        "point_certificate_passes": sum(row["point_certificate_passed"] for row in records),
        "unconditional_root_catastrophes": sum(row["outcomes"]["root_lattice"]["catastrophe"] for row in records),
        "fail_closed_catastrophes": sum(row["fail_closed"]["catastrophe"] for row in records),
        "safe_route_retention": retained / len(safe_root) if safe_root else 0.0,
        "root_total_nfev": sum(row["outcomes"]["root_lattice"]["nfev"] for row in records),
        "fail_closed_total_nfev": sum(row["fail_closed"]["nfev"] for row in records),
    }
    return {"seed": 20261024, "draws_frozen_as_exact_rationals": True,
            "records": records, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/robust_ftrig_coefficient_boundary.json")
    args = parser.parse_args()
    sweep = [certify(Q(1, 2**k)) for k in range(4, 25)]
    passing = [row for row in sweep if row["passed"]]
    largest = max(passing, key=lambda row: row["rho_float"]) if passing else None
    failing_larger = ([row for row in sweep if largest and not row["passed"]
                       and row["rho_float"] > largest["rho_float"]])
    next_failure = min(failing_larger, key=lambda row: row["rho_float"]) if failing_larger else None
    evaluation = prospective(Q(largest["rho"])) if largest else None
    gates = {
        "positive_common_radius": largest is not None,
        "boundary_bracketed": largest is not None and next_failure is not None,
        "all_42_boxes_at_pass": largest is not None and largest["passing_boxes"] == 42,
        "zero_false_accepts": evaluation is not None and all(
            not row["point_certificate_passed"] or not row["outcomes"]["root_lattice"]["catastrophe"]
            for row in evaluation["records"]),
        "safe_route_retention": evaluation is not None and evaluation["summary"]["safe_route_retention"] >= 0.75,
        "catastrophe_reduction": evaluation is not None and
            evaluation["summary"]["fail_closed_catastrophes"] <
            evaluation["summary"]["unconditional_root_catastrophes"],
    }
    result = {
        "schema": "robust-ftrig-coefficient-boundary-v1",
        "uncertainty": "independent relative intervals on A..F",
        "sweep": sweep,
        "largest_passing": largest,
        "next_larger_failing": next_failure,
        "prospective": evaluation,
        "gates": gates,
        "boundary_gate": "PASS" if all(gates.values()) else "KILL",
    }
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "largest_passing": None if largest is None else {
            key: largest[key] for key in ("rho", "rho_float", "minimum_signed_slack")},
        "next_larger_failing": None if next_failure is None else {
            key: next_failure[key] for key in ("rho", "rho_float", "passing_boxes",
                                                "minimum_signed_slack")},
        "gates": gates,
    }, indent=2, sort_keys=True))
    raise SystemExit(0 if all(gates.values()) else 1)


if __name__ == "__main__":
    main()
