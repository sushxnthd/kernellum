#!/usr/bin/env python3
"""Independent arithmetic and invariant checks for the FTrig result."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


A = 35184372088832 / 3125302502557517
B = 70368744177664 / 2778046668940015
C = 281474976710656 / 2778046668940015
D = 1125899906842624 / 2778046668940015
E = 140737488355328 / 8681395840437547
F = 140737488355328 / 3125302502557517


def objective(p):
    x, y = p
    u, v = x + y, x - y
    a = -10 * u * (A*u*u - 1) * (B*u*u - 1) * (C*u*u - 1)
    b = -10 * (D*v*v - 1) * (E*v*v - 1) * (F*v*v - 1)
    c = x*x/100 + y*y/100 + 10
    return a*a + b*b + c*c


def finite_hessian(p, h=1e-4):
    p = np.asarray(p, dtype=float)
    out = np.empty((2, 2))
    f0 = objective(p)
    for i in range(2):
        e = np.zeros(2); e[i] = h
        out[i, i] = (objective(p+e) - 2*f0 + objective(p-e)) / (h*h)
    e0, e1 = np.array([h, 0.0]), np.array([0.0, h])
    out[0, 1] = out[1, 0] = (objective(p+e0+e1) - objective(p+e0-e1)
                                  - objective(p-e0+e1) + objective(p-e0-e1)) / (4*h*h)
    return out


def main(path: str) -> None:
    data = json.loads(Path(path).read_text())
    rows = data["records"]
    checks = []
    checks.append(("36 records", len(rows) == 36))
    checks.append(("all budgets 42", all(r["starts"] == 42 for r in rows)))
    roots = [r for r in rows if r["method"] == "root_lattice"]
    controls = [r for r in rows if r["method"] != "root_lattice"]
    checks.append(("nine root trials", len(roots) == 9))
    checks.append(("root prediction", all(r["distinct_minima"] == 42 for r in roots)))
    checks.append(("confirmation separated", sum(r["split"] == "confirmation" for r in roots) == 8))
    checks.append(("control count", len(controls) == 27))
    checks.append(("coverage bounded", all(0 < r["coverage_fraction"] <= 1 for r in rows)))
    checks.append(("finite objectives", all(0 < r["best_objective"] < 1e6 for r in rows)))
    checks.append(("source pinned", data["source"]["commit"] == "615c185f3d61f044eab7cfd27f97f698ff341d8f"))
    # Re-evaluate the scalar objective without importing the runner.  Positive
    # finite-difference Hessians exclude converged saddles/maxima.
    root_centers = [c for r in roots for c in r["centers"]]
    checks.append(("378 root centers", len(root_centers) == 378))
    checks.append(("all centers finite", all(np.isfinite(objective(c)) for c in root_centers)))
    checks.append(("all centers strict minima",
                   all(np.linalg.eigvalsh(finite_hessian(c)).min() > 1e-3 for c in root_centers)))
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {label}")
    if not all(passed for _, passed in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/residual_root_lattice.json")
