#!/usr/bin/env python3
"""Independent checks for the frozen Freudenstein--Roth transfer."""

import json
import sys
from pathlib import Path

import numpy as np


def residual(z):
    x, y = z
    return np.array([x - 13 + 5*y*y - y**3 - 2*y,
                     x - 29 + y**3 + y*y - 14*y])


def hessian(z, h=1e-4):
    f = lambda q: float(residual(q) @ residual(q))
    z = np.asarray(z, float)
    out = np.empty((2, 2))
    for i in range(2):
        for j in range(2):
            ei = np.zeros(2); ej = np.zeros(2)
            ei[i] = h; ej[j] = h
            out[i, j] = (f(z+ei+ej)-f(z+ei-ej)-f(z-ei+ej)+f(z-ei-ej))/(4*h*h)
    return out


def main(path):
    data = json.loads(Path(path).read_text())
    cands = np.asarray(data["candidates"])
    s = data["summary"]
    checks = {
        "protocol": data["protocol"] == "profile-critical-root-transfer-v1",
        "two_candidates": cands.shape == (2, 2),
        "distinct_candidates": np.linalg.norm(cands[0]-cands[1]) > 1,
        "strict_hessians": all(np.min(np.linalg.eigvalsh(hessian(z))) > 1e-4 for z in cands),
        "structured_all": s["profile_roots"]["full_coverage"] == 9,
        "structured_global": s["profile_roots"]["global_retained"] == 9,
        "maximin_all": s["maximin"]["full_coverage"] == 9,
        "matched_budget": all(len(r["recovered"]) <= 2 for r in data["records"]),
        "kill_gate": data["scientific_gate"] == "KILL_SIMPLE_CONTROL_MATCHES_COVERAGE",
    }
    for name, passed in checks.items():
        print(("PASS" if passed else "FAIL"), name)
    print(f"{sum(checks.values())}/{len(checks)}")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/profile_critical_root_transfer.json")
