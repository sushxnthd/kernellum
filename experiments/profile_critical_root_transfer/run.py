#!/usr/bin/env python3
"""Frozen Freudenstein--Roth profile-critical-root transfer experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.polynomial import Polynomial
from scipy.optimize import least_squares
from scipy.stats import qmc


P1 = Polynomial([-13.0, -2.0, 5.0, -1.0])
P2 = Polynomial([-29.0, -14.0, 1.0, 1.0])
DOMAIN_LO = np.array([-20.0, -5.0])
DOMAIN_HI = np.array([20.0, 5.0])


def residual_z(z: np.ndarray) -> np.ndarray:
    x, y = z
    return np.array([x + P1(y), x + P2(y)])


def objective(z: np.ndarray) -> float:
    r = residual_z(z)
    return float(r @ r)


def profile_candidates() -> np.ndarray:
    mean = (P1 + P2) / 2
    diff = P1 - P2
    profile = diff * diff / 2
    roots = profile.deriv().roots()
    ys = sorted(float(r.real) for r in roots
                if abs(r.imag) < 1e-9 and profile.deriv(2)(r.real) > 1e-8)
    return np.array([[-mean(y), y] for y in ys])


@dataclass(frozen=True)
class Transform:
    angle: float
    scale_1: float
    scale_2: float
    shift_1: float
    shift_2: float

    def matrix(self) -> np.ndarray:
        c, s = np.cos(self.angle), np.sin(self.angle)
        return np.array([[c, -s], [s, c]]) @ np.diag([self.scale_1, self.scale_2])

    def forward(self, z: np.ndarray) -> np.ndarray:
        return self.matrix() @ z + np.array([self.shift_1, self.shift_2])

    def inverse(self, x: np.ndarray) -> np.ndarray:
        return np.linalg.solve(self.matrix(), x - np.array([self.shift_1, self.shift_2]))


def residual_x(x: np.ndarray, transform: Transform) -> np.ndarray:
    return residual_z(transform.inverse(x))


def transforms() -> list[Transform]:
    out = [Transform(0.0, 1.0, 1.0, 0.0, 0.0)]
    rng = np.random.default_rng(20261020)
    for _ in range(8):
        out.append(Transform(float(rng.uniform(-np.pi, np.pi)),
                             float(rng.uniform(0.45, 2.2)),
                             float(rng.uniform(0.45, 2.2)),
                             float(rng.uniform(-3, 3)),
                             float(rng.uniform(-3, 3))))
    return out


def generic_starts(kind: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if kind == "maximin":
        return np.array([DOMAIN_LO, DOMAIN_HI])
    if kind == "random":
        return rng.uniform(DOMAIN_LO, DOMAIN_HI, size=(2, 2))
    if kind == "lhs":
        return qmc.scale(qmc.LatinHypercube(2, seed=rng).random(2), DOMAIN_LO, DOMAIN_HI)
    raise ValueError(kind)


def run_starts(starts: np.ndarray, transform: Transform, truth: np.ndarray) -> dict:
    converged, nfev = [], 0
    for z0 in starts:
        fit = least_squares(residual_x, transform.forward(z0), args=(transform,),
                            method="trf", xtol=1e-12, ftol=1e-12, gtol=1e-12,
                            max_nfev=3000)
        converged.append(transform.inverse(fit.x))
        nfev += fit.nfev
    recovered = sorted({int(np.argmin(np.linalg.norm(truth - z, axis=1)))
                        for z in converged
                        if np.min(np.linalg.norm(truth - z, axis=1)) < 2e-3})
    values = [objective(z) for z in converged]
    return {"recovered": recovered, "coverage": len(recovered),
            "best_objective": min(values), "nfev": nfev}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("results/profile_critical_root_transfer.json"))
    args = parser.parse_args()
    candidates = profile_candidates()
    records = []
    for transform_id, transform in enumerate(transforms()):
        row = run_starts(candidates, transform, candidates)
        records.append({"method": "profile_roots", "transform_id": transform_id,
                        "repetition": 0, **row})
        row = run_starts(generic_starts("maximin", 0), transform, candidates)
        records.append({"method": "maximin", "transform_id": transform_id,
                        "repetition": 0, **row})
        for repetition in range(64):
            for method in ("lhs", "random"):
                seed = 100000 * transform_id + repetition
                row = run_starts(generic_starts(method, seed), transform, candidates)
                records.append({"method": method, "transform_id": transform_id,
                                "repetition": repetition, **row})

    def summary(method: str) -> dict:
        rows = [r for r in records if r["method"] == method]
        return {"trials": len(rows),
                "full_coverage": sum(r["coverage"] == 2 for r in rows),
                "catastrophes": sum(r["coverage"] < 2 for r in rows),
                "mean_coverage": float(np.mean([r["coverage"] / 2 for r in rows])),
                "mean_nfev": float(np.mean([r["nfev"] for r in rows])),
                "global_retained": sum(r["best_objective"] < 1e-16 for r in rows)}

    summaries = {m: summary(m) for m in ("profile_roots", "maximin", "lhs", "random")}
    killed = summaries["maximin"]["full_coverage"] == summaries["maximin"]["trials"]
    result = {
        "protocol": "profile-critical-root-transfer-v1",
        "source": {"name": "Freudenstein-Roth",
                   "reference": "More-Garbow-Hillstrom-1981",
                   "doi": "10.1145/355934.355936"},
        "frozen_prediction": "two profile roots cover both minima; no simple control is universal",
        "candidates": [[float(v) for v in z] for z in candidates],
        "candidate_objectives": [objective(z) for z in candidates],
        "records": records,
        "summary": summaries,
        "scientific_gate": "KILL_SIMPLE_CONTROL_MATCHES_COVERAGE" if killed else "PASS",
    }
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"summary": summaries, "scientific_gate": result["scientific_gate"]},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
