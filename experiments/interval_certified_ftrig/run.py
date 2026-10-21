#!/usr/bin/env python3
"""Exact interval certificate plus prospective FTrig routing evaluation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from fractions import Fraction as Q
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import qmc


ROOT = Path(__file__).parents[2]
FT_PATH = ROOT / "experiments/residual_root_lattice/run.py"
SPEC = importlib.util.spec_from_file_location("interval_ft", FT_PATH)
FT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["interval_ft"] = FT
SPEC.loader.exec_module(FT)


class Interval:
    __slots__ = ("lo", "hi")

    def __init__(self, lo, hi=None):
        self.lo = Q(lo)
        self.hi = Q(lo if hi is None else hi)
        if self.lo > self.hi:
            raise ValueError("reversed interval")

    def __add__(self, other):
        other = as_interval(other)
        return Interval(self.lo + other.lo, self.hi + other.hi)

    __radd__ = __add__

    def __neg__(self):
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + (-as_interval(other))

    def __rsub__(self, other):
        return as_interval(other) - self

    def __mul__(self, other):
        other = as_interval(other)
        products = (self.lo * other.lo, self.lo * other.hi,
                    self.hi * other.lo, self.hi * other.hi)
        return Interval(min(products), max(products))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = as_interval(other)
        if other.lo <= 0 <= other.hi:
            raise ZeroDivisionError("interval spans zero")
        return self * Interval(1 / other.hi, 1 / other.lo)

    def square(self):
        values = (self.lo * self.lo, self.hi * self.hi)
        return Interval(0 if self.lo <= 0 <= self.hi else min(values), max(values))


def as_interval(value):
    return value if isinstance(value, Interval) else Interval(value)


def poly_mul(left, right):
    out = [Q(0)] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i + j] += a * b
    return out


def poly_derivative(poly):
    return [Q(index) * poly[index] for index in range(1, len(poly))]


def poly_eval(poly, value):
    out = Interval(0)
    for coefficient in reversed(poly):
        out = out * value + coefficient
    return out


A = Q(35184372088832, 3125302502557517)
B = Q(70368744177664, 2778046668940015)
C = Q(281474976710656, 2778046668940015)
D = Q(1125899906842624, 2778046668940015)
E = Q(140737488355328, 8681395840437547)
F = Q(140737488355328, 3125302502557517)
PI_LO = Q(314159265358979323846264338327950288419716939937510, 10**50)
PI_HI = Q(314159265358979323846264338327950288419716939937511, 10**50)
RADIUS = Q(1, 200)
U_MULTIPLES = (Q(-3), Q(-2), Q(-1), Q(0), Q(1), Q(2), Q(3))
V_MULTIPLES = (Q(-5, 2), Q(-3, 2), Q(-1, 2), Q(1, 2), Q(3, 2), Q(5, 2))


def product_factors(coefficients, leading_u=False):
    poly = [Q(1)]
    for coefficient in coefficients:
        poly = poly_mul(poly, [Q(-1), Q(0), coefficient])
    squared = poly_mul(poly, poly)
    return poly_mul([Q(0), Q(0), Q(100)], squared) if leading_u else [Q(100) * x for x in squared]


FU = product_factors((A, B, C), leading_u=True)
FV = product_factors((D, E, F))
FU_1, FU_2 = poly_derivative(FU), poly_derivative(poly_derivative(FU))
FV_1, FV_2 = poly_derivative(FV), poly_derivative(poly_derivative(FV))


def pi_multiple(multiplier):
    endpoints = (multiplier * PI_LO, multiplier * PI_HI)
    return Interval(min(endpoints), max(endpoints))


def expanded(center, radius=None):
    if radius is None:
        radius = RADIUS
    return Interval(center.lo - radius, center.hi + radius)


def radial(u, v):
    return Interval(10) + (u.square() + v.square()) / 200


def grad_u(u, v):
    return poly_eval(FU_1, u) + radial(u, v) * u / 50


def grad_v(u, v):
    return poly_eval(FV_1, v) + radial(u, v) * v / 50


def hessian(u, v):
    r = radial(u, v)
    huu = poly_eval(FU_2, u) + u.square() / 5000 + r / 50
    hvv = poly_eval(FV_2, v) + v.square() / 5000 + r / 50
    huv = u * v / 5000
    return huu, hvv, huv


def exact_certificate():
    boxes = []
    for u_index, u_multiplier in enumerate(U_MULTIPLES):
        for v_index, v_multiplier in enumerate(V_MULTIPLES):
            u = expanded(pi_multiple(u_multiplier))
            v = expanded(pi_multiple(v_multiplier))
            left, right = Interval(u.lo), Interval(u.hi)
            lower, upper = Interval(v.lo), Interval(v.hi)
            gu_left, gu_right = grad_u(left, v), grad_u(right, v)
            gv_lower, gv_upper = grad_v(u, lower), grad_v(u, upper)
            huu, hvv, huv = hessian(u, v)
            cross = max(abs(huv.lo), abs(huv.hi))
            determinant_lower = huu.lo * hvv.lo - cross * cross
            checks = {
                "u_left_negative": gu_left.hi < 0,
                "u_right_positive": gu_right.lo > 0,
                "v_lower_negative": gv_lower.hi < 0,
                "v_upper_positive": gv_upper.lo > 0,
                "hessian_pd": huu.lo > 0 and hvv.lo > 0 and determinant_lower > 0,
            }
            boxes.append({
                "id": f"u{u_index}-v{v_index}",
                "u_multiplier": str(u_multiplier), "v_multiplier": str(v_multiplier),
                "u": [float(u.lo), float(u.hi)], "v": [float(v.lo), float(v.hi)],
                "checks": checks,
                "margins": {
                    "minus_u_left_upper": float(-gu_left.hi),
                    "u_right_lower": float(gu_right.lo),
                    "minus_v_lower_upper": float(-gv_lower.hi),
                    "v_upper_lower": float(gv_upper.lo),
                    "huu_lower": float(huu.lo), "hvv_lower": float(hvv.lo),
                    "determinant_lower": float(determinant_lower),
                },
            })
    disjoint = True
    for i, first in enumerate(boxes):
        for second in boxes[i + 1:]:
            u_overlap = max(first["u"][0], second["u"][0]) <= min(first["u"][1], second["u"][1])
            v_overlap = max(first["v"][0], second["v"][0]) <= min(first["v"][1], second["v"][1])
            disjoint &= not (u_overlap and v_overlap)
    passed = len(boxes) == 42 and disjoint and all(all(box["checks"].values()) for box in boxes)
    return {"arithmetic": "fractions.Fraction outward intervals", "radius": float(RADIUS),
            "boxes": boxes, "box_count": len(boxes), "pairwise_disjoint": disjoint,
            "passed": bool(passed)}


@dataclass(frozen=True)
class Transform:
    angle: float
    scale_1: float
    scale_2: float
    shift_1: float
    shift_2: float


def transforms(seed, count):
    rng = np.random.default_rng(seed)
    return [Transform(float(rng.uniform(-np.pi, np.pi)), float(rng.uniform(0.45, 2.2)),
                      float(rng.uniform(0.45, 2.2)), float(rng.uniform(-3, 3)),
                      float(rng.uniform(-3, 3))) for _ in range(count)]


def root_lattice():
    return FT.root_lattice()


def optimized_lhs(seed):
    sampler = qmc.LatinHypercube(d=2, seed=seed, optimization="random-cd")
    return qmc.scale(sampler.random(42), [-10, -10], [10, 10])


def greedy_maximin():
    axis = np.linspace(-10, 10, 81)
    candidates = np.array([[x, y] for x in axis for y in axis])
    selected = [0]  # deterministic corner anchor
    minimum = np.sum((candidates - candidates[0]) ** 2, axis=1)
    for _ in range(41):
        index = int(np.argmax(minimum))
        selected.append(index)
        minimum = np.minimum(minimum, np.sum((candidates - candidates[index]) ** 2, axis=1))
    return candidates[selected]


def starts(method, seed):
    if method == "root_lattice":
        return root_lattice()
    if method == "grid":
        return FT.generic_grid()
    if method == "optimized_lhs":
        return optimized_lhs(seed)
    if method == "greedy_maximin":
        return greedy_maximin()
    raise ValueError(method)


def box_id(z):
    u, v = z[0] + z[1], z[0] - z[1]
    u_distances = [abs(u - float(multiplier * np.pi)) for multiplier in U_MULTIPLES]
    v_distances = [abs(v - float(multiplier * np.pi)) for multiplier in V_MULTIPLES]
    ui, vi = int(np.argmin(u_distances)), int(np.argmin(v_distances))
    if u_distances[ui] <= float(RADIUS) and v_distances[vi] <= float(RADIUS):
        return f"u{ui}-v{vi}"
    return None


def run_method(method, seed, transform):
    ft_transform = FT.Transform(**asdict(transform))
    found, objectives, nfev = set(), [], 0
    for z0 in starts(method, seed):
        fit = least_squares(FT.residual_x, ft_transform.forward(z0), args=(ft_transform,),
                            method="trf", xtol=1e-12, ftol=1e-12, gtol=1e-12,
                            max_nfev=3000)
        zhat = ft_transform.inverse(fit.x)
        identifier = box_id(zhat)
        if identifier is not None:
            found.add(identifier)
        objectives.append(float(np.dot(fit.fun, fit.fun)))
        nfev += int(fit.nfev)
    return {"method": method, "starts": 42, "certified_boxes_recovered": len(found),
            "coverage": len(found) / 42, "best_objective": min(objectives),
            "median_objective": float(np.median(objectives)), "nfev": nfev,
            "box_ids": sorted(found)}


def prospective_records():
    methods = ("root_lattice", "grid", "optimized_lhs", "greedy_maximin")
    records = []
    for transform_id, transform in enumerate(transforms(20261023, 16)):
        for method in methods:
            records.append({"transform_id": transform_id, "transform": asdict(transform),
                            **run_method(method, 1000 + transform_id, transform)})
    return records


def fleet_replay():
    prior = json.loads((ROOT / "results/certificate_conditioned_selector.json").read_text())
    records = []
    for row in prior["records"]:
        if row["family"] != "ftrig":
            records.append(row)
            continue
        transform = Transform(**prior["transforms"][row["transform_id"]])
        selector = run_method("root_lattice", row["transform_id"], transform)
        records.append({**row, "activated": True, "certificate": "interval_box_complete",
                        "selector": selector})
    selector_nfev = sum(row["selector"]["nfev"] for row in records)
    baseline_nfev = sum(row["baseline"]["nfev"] for row in records)
    coverage_losses = sum((row["selector"].get("coverage", row["selector"].get("coverage_fraction"))) <
                          (row["baseline"].get("coverage", row["baseline"].get("coverage_fraction")))
                          for row in records)
    objective_losses = sum(row["selector"]["best_objective"] > row["baseline"]["best_objective"] + 1e-12
                           for row in records)
    return {"records": records, "summary": {"trials": len(records),
            "selector_nfev": selector_nfev, "baseline_nfev": baseline_nfev,
            "evaluation_reduction": 1 - selector_nfev / baseline_nfev,
            "coverage_losses": int(coverage_losses), "objective_losses": int(objective_losses)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results/interval_certified_ftrig.json")
    args = parser.parse_args()
    certificate = exact_certificate()
    records = prospective_records()
    root = [row for row in records if row["method"] == "root_lattice"]
    grid = [row for row in records if row["method"] == "grid"]
    controls = [row for row in records if row["method"] != "root_lattice"]
    ftrig_reduction = 1 - sum(row["nfev"] for row in root) / sum(row["nfev"] for row in grid)
    prospective = {
        "transform_seed": 20261023, "transform_count": 16, "records": records,
        "summary": {
            "root_full_coverage": sum(row["certified_boxes_recovered"] == 42 for row in root),
            "root_trials": len(root),
            "control_full_coverage": sum(row["certified_boxes_recovered"] == 42 for row in controls),
            "control_trials": len(controls),
            "root_nfev": sum(row["nfev"] for row in root),
            "grid_nfev": sum(row["nfev"] for row in grid),
            "ftrig_grid_reduction": ftrig_reduction,
            "objective_losses_vs_grid": sum(r["best_objective"] > g["best_objective"] + 1e-12
                                              for r, g in zip(root, grid)),
        },
    }
    fleet = fleet_replay()
    gates = {
        "certificate": certificate["passed"],
        "prospective_coverage": prospective["summary"]["root_full_coverage"] == 16,
        "prospective_objective": prospective["summary"]["objective_losses_vs_grid"] == 0,
        "ftrig_savings": ftrig_reduction >= 0.35,
        "fleet_safety": fleet["summary"]["coverage_losses"] == 0 and fleet["summary"]["objective_losses"] == 0,
        "fleet_savings": fleet["summary"]["evaluation_reduction"] >= 0.25,
    }
    result = {"protocol": "interval-certified-ftrig-v1", "certificate": certificate,
              "prospective": prospective, "fleet_replay": fleet, "gates": gates,
              "scientific_gate": "PASS" if all(gates.values()) else "KILL"}
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"certificate": {k: certificate[k] for k in ("box_count", "pairwise_disjoint", "passed")},
                      "prospective": prospective["summary"], "fleet": fleet["summary"],
                      "gates": gates, "scientific_gate": result["scientific_gate"]}, indent=2, sort_keys=True))
    raise SystemExit(0 if result["scientific_gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
