#!/usr/bin/env python3
"""Independent Decimal audit of the robust FTrig coefficient boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, localcontext
from pathlib import Path


PREC = 110


def down(fn):
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = PREC, ROUND_FLOOR
        return +fn()


def up(fn):
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = PREC, ROUND_CEILING
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

    def __truediv__(self, other):
        other = interval(other)
        assert not other.lo <= 0 <= other.hi
        return self * I(down(lambda: D(1) / other.hi), up(lambda: D(1) / other.lo))

    def square(self):
        lows = [down(lambda a=a: a * a) for a in (self.lo, self.hi)]
        highs = [up(lambda a=a: a * a) for a in (self.lo, self.hi)]
        return I(D(0) if self.lo <= 0 <= self.hi else min(lows), max(highs))


def interval(value):
    return value if isinstance(value, I) else I(value)


def ratio(numerator, denominator):
    return I(down(lambda: D(numerator) / D(denominator)),
             up(lambda: D(numerator) / D(denominator)))


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
    return mul([I(0), I(0), I(100)], squared) if leading_u else [x * 100 for x in squared]


CENTERS = (
    ratio(35184372088832, 3125302502557517),
    ratio(70368744177664, 2778046668940015),
    ratio(281474976710656, 2778046668940015),
    ratio(1125899906842624, 2778046668940015),
    ratio(140737488355328, 8681395840437547),
    ratio(140737488355328, 3125302502557517),
)
PI = I("3.14159265358979323846264338327950288419716939937510",
       "3.14159265358979323846264338327950288419716939937511")
US = tuple(D(x) for x in (-3, -2, -1, 0, 1, 2, 3))
VS = tuple(D(x) / 2 for x in (-5, -3, -1, 1, 3, 5))
RADIUS = D(1) / 200


def certify_coefficients(coefficients):
    fu, fv = objective_poly(coefficients[:3], True), objective_poly(coefficients[3:], False)
    fu1, fu2 = derivative(fu), derivative(derivative(fu))
    fv1, fv2 = derivative(fv), derivative(derivative(fv))
    passing = 0
    for um in US:
        for vm in VS:
            uc, vc = PI * um, PI * vm
            u, v = I(uc.lo - RADIUS, uc.hi + RADIUS), I(vc.lo - RADIUS, vc.hi + RADIUS)
            left, right, lower, upper = I(u.lo), I(u.hi), I(v.lo), I(v.hi)
            radial = lambda a, b: I(10) + (a.square() + b.square()) / 200
            faces = (-evaluate(fu1, left).hi - (radial(left, v) * left / 50).hi,
                     (evaluate(fu1, right) + radial(right, v) * right / 50).lo,
                     -evaluate(fv1, lower).hi - (radial(u, lower) * lower / 50).hi,
                     (evaluate(fv1, upper) + radial(u, upper) * upper / 50).lo)
            r = radial(u, v)
            huu = evaluate(fu2, u) + u.square() / 5000 + r / 50
            hvv = evaluate(fv2, v) + v.square() / 5000 + r / 50
            huv = u * v / 5000
            cross = max(abs(huv.lo), abs(huv.hi))
            det = down(lambda: huu.lo * hvv.lo - cross * cross)
            passing += all(value > 0 for value in (*faces, huu.lo, hvv.lo, det))
    return passing


def certify(k):
    rho = D(1) / (D(2) ** k)
    coefficients = [I(down(lambda c=c: c.lo * (1 - rho)),
                      up(lambda c=c: c.hi * (1 + rho))) for c in CENTERS]
    return certify_coefficients(coefficients)


def exact_fraction(text):
    numerator, denominator = text.split("/") if "/" in text else (text, "1")
    return I(down(lambda: D(numerator) / D(denominator)),
             up(lambda: D(numerator) / D(denominator)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    primary = json.loads(args.primary.read_text())
    counts = {str(k): certify(k) for k in range(4, 25)}
    point_counts = [certify_coefficients([exact_fraction(value) for value in row["coefficients"]])
                    for row in primary["prospective"]["records"]]
    passing = [k for k, count in counts.items() if count == 42]
    largest_k = min(map(int, passing)) if passing else None
    copy = dict(primary)
    observed_hash = copy.pop("payload_sha256")
    canonical = json.dumps(copy, indent=2, sort_keys=True) + "\n"
    tests = {
        "independent_largest_pass": largest_k == 19,
        "independent_next_failure": counts["18"] == 18,
        "primary_largest_pass": primary["largest_passing"]["rho"] == "1/524288",
        "primary_next_failure": primary["next_larger_failing"]["rho"] == "1/262144",
        "payload_hash": hashlib.sha256(canonical.encode()).hexdigest() == observed_hash,
        "all_point_certificates": point_counts == [42] * 48,
        "prospective_no_root_catastrophes":
            primary["prospective"]["summary"]["unconditional_root_catastrophes"] == 0,
        "prospective_no_reduction":
            primary["prospective"]["summary"]["fail_closed_catastrophes"] == 0,
        "primary_gate_killed": primary["gates"]["catastrophe_reduction"] is False,
    }
    result = {"schema": "robust-ftrig-coefficient-boundary-audit-v1",
              "passing_box_counts_by_k": counts,
              "prospective_point_passing_box_counts": point_counts, "tests": tests,
              "passed": sum(tests.values()), "total": len(tests),
              "status": "PASS" if all(tests.values()) else "FAIL"}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
