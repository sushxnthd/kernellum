#!/usr/bin/env python3
"""Independent Decimal-interval audit; imports neither runner nor certificate."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, localcontext
from pathlib import Path


PREC = 90


def down(fn):
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND_FLOOR
        return +fn()


def up(fn):
    with localcontext() as ctx:
        ctx.prec = PREC
        ctx.rounding = ROUND_CEILING
        return +fn()


class I:
    def __init__(self, lo, hi=None):
        self.lo, self.hi = D(lo), D(lo if hi is None else hi)
        assert self.lo <= self.hi

    def __add__(self, other):
        other = interval(other)
        return I(down(lambda: self.lo + other.lo), up(lambda: self.hi + other.hi))

    __radd__ = __add__

    def __neg__(self):
        return I(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + (-interval(other))

    def __rsub__(self, other):
        return interval(other) - self

    def __mul__(self, other):
        other = interval(other)
        lows = [down(lambda a=a, b=b: a * b) for a in (self.lo, self.hi)
                for b in (other.lo, other.hi)]
        highs = [up(lambda a=a, b=b: a * b) for a in (self.lo, self.hi)
                 for b in (other.lo, other.hi)]
        return I(min(lows), max(highs))

    __rmul__ = __mul__

    def reciprocal(self):
        assert not self.lo <= 0 <= self.hi
        return I(down(lambda: D(1) / self.hi), up(lambda: D(1) / self.lo))

    def __truediv__(self, other):
        return self * interval(other).reciprocal()

    def square(self):
        lows = [down(lambda a=a: a * a) for a in (self.lo, self.hi)]
        highs = [up(lambda a=a: a * a) for a in (self.lo, self.hi)]
        return I(D(0) if self.lo <= 0 <= self.hi else min(lows), max(highs))


def interval(value):
    return value if isinstance(value, I) else I(value)


def ratio(numerator, denominator):
    return I(numerator) / denominator


def mul(left, right):
    out = [I(0) for _ in range(len(left) + len(right) - 1)]
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i + j] = out[i + j] + a * b
    return out


def derivative(poly):
    return [poly[index] * index for index in range(1, len(poly))]


def evaluate(poly, value):
    out = I(0)
    for coefficient in reversed(poly):
        out = out * value + coefficient
    return out


def objective_poly(coefficients, leading_u):
    poly = [I(1)]
    for coefficient in coefficients:
        poly = mul(poly, [I(-1), I(0), coefficient])
    squared = mul(poly, poly)
    if leading_u:
        return mul([I(0), I(0), I(100)], squared)
    return [item * 100 for item in squared]


A = ratio(35184372088832, 3125302502557517)
B = ratio(70368744177664, 2778046668940015)
C = ratio(281474976710656, 2778046668940015)
D0 = ratio(1125899906842624, 2778046668940015)
E = ratio(140737488355328, 8681395840437547)
F = ratio(140737488355328, 3125302502557517)
FU = objective_poly((A, B, C), True)
FV = objective_poly((D0, E, F), False)
FU1, FU2 = derivative(FU), derivative(derivative(FU))
FV1, FV2 = derivative(FV), derivative(derivative(FV))
PI = I("3.14159265358979323846264338327950288419716939937510",
       "3.14159265358979323846264338327950288419716939937511")
RADIUS = D(1) / D(200)
US = (D(-3), D(-2), D(-1), D(0), D(1), D(2), D(3))
VS = (D(-5) / 2, D(-3) / 2, D(-1) / 2, D(1) / 2, D(3) / 2, D(5) / 2)


def radius(u, v):
    return I(10) + (u.square() + v.square()) / 200


def certify_box(um, vm):
    uc, vc = PI * um, PI * vm
    u, v = I(uc.lo - RADIUS, uc.hi + RADIUS), I(vc.lo - RADIUS, vc.hi + RADIUS)
    gu_l = evaluate(FU1, I(u.lo)) + radius(I(u.lo), v) * I(u.lo) / 50
    gu_r = evaluate(FU1, I(u.hi)) + radius(I(u.hi), v) * I(u.hi) / 50
    gv_l = evaluate(FV1, I(v.lo)) + radius(u, I(v.lo)) * I(v.lo) / 50
    gv_r = evaluate(FV1, I(v.hi)) + radius(u, I(v.hi)) * I(v.hi) / 50
    r = radius(u, v)
    huu = evaluate(FU2, u) + u.square() / 5000 + r / 50
    hvv = evaluate(FV2, v) + v.square() / 5000 + r / 50
    huv = u * v / 5000
    cross = max(abs(huv.lo), abs(huv.hi))
    det = down(lambda: huu.lo * hvv.lo - cross * cross)
    checks = (gu_l.hi < 0, gu_r.lo > 0, gv_l.hi < 0, gv_r.lo > 0,
              huu.lo > 0, hvv.lo > 0, det > 0)
    return all(checks), (u.lo, u.hi, v.lo, v.hi)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.primary.read_text())
    certified = [certify_box(u, v) for u in US for v in VS]
    boxes = [box for passed, box in certified if passed]
    disjoint = all((a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])
                   for i, a in enumerate(boxes) for b in boxes[i + 1:])
    copy = dict(data)
    observed_hash = copy.pop("payload_sha256")
    canonical = json.dumps(copy, indent=2, sort_keys=True) + "\n"
    tests = {
        "independent_decimal_boxes": len(boxes) == 42,
        "independent_disjointness": disjoint,
        "primary_certificate": data["certificate"]["passed"] and data["certificate"]["box_count"] == 42,
        "prospective_root_coverage": data["prospective"]["summary"]["root_full_coverage"] == 16,
        "prospective_controls": data["prospective"]["summary"]["control_full_coverage"] == 0,
        "prospective_savings": data["prospective"]["summary"]["ftrig_grid_reduction"] >= 0.35,
        "fleet_safety": data["fleet_replay"]["summary"]["coverage_losses"] == 0 and
                        data["fleet_replay"]["summary"]["objective_losses"] == 0,
        "fleet_savings": data["fleet_replay"]["summary"]["evaluation_reduction"] >= 0.25,
        "all_primary_gates": all(data["gates"].values()) and data["scientific_gate"] == "PASS",
        "payload_hash": hashlib.sha256(canonical.encode()).hexdigest() == observed_hash,
    }
    result = {"schema": "interval-certified-ftrig-audit-v1", "tests": tests,
              "passed": sum(tests.values()), "total": len(tests),
              "status": "PASS" if all(tests.values()) else "FAIL"}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
