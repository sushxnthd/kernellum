#!/usr/bin/env python3
"""Independent checks for the frozen Himmelblau four-basin transfer."""

import json
import sys
from pathlib import Path

import numpy as np


def residual(z):
    x, y = z
    return np.array([x*x+y-11, x+y*y-7])


def jacobian(z):
    x, y = z
    return np.array([[2*x, 1], [1, 2*y]])


def main(path):
    data = json.loads(Path(path).read_text())
    candidates = np.asarray(data["candidates"])
    summary = data["summary"]
    checks = {
        "protocol": data["protocol"] == "himmelblau-four-basin-transfer-v1",
        "four_candidates": candidates.shape == (4, 2),
        "distinct_candidates": min(np.linalg.norm(a-b) for i, a in enumerate(candidates)
                                    for b in candidates[i+1:]) > 1,
        "zero_residuals": all(np.linalg.norm(residual(z)) < 1e-8 for z in candidates),
        "full_rank_jacobians": all(abs(np.linalg.det(jacobian(z))) > 1e-4 for z in candidates),
        "strict_hessians": all(np.min(np.linalg.eigvalsh(2*jacobian(z).T@jacobian(z))) > 1e-4
                                for z in candidates),
        "structured_all": summary["eliminant_roots"]["full_coverage"] == 9,
        "structured_zero": summary["eliminant_roots"]["zero_retained"] == 9,
        "corner_maximin_all": summary["corner_maximin"]["full_coverage"] == 9,
        "greedy_maximin_all": summary["greedy_maximin"]["full_coverage"] == 9,
        "matched_budget": all(len(row["recovered"]) <= 4 for row in data["records"]),
        "kill_gate": data["scientific_gate"] == "KILL_MAXIMIN_MATCHES_COVERAGE",
    }
    for name, passed in checks.items():
        print(("PASS" if passed else "FAIL"), name)
    print(f"{sum(checks.values())}/{len(checks)}")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         "results/himmelblau_four_basin_transfer.json")
