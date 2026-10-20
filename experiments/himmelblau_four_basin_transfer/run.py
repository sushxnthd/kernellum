#!/usr/bin/env python3
"""Frozen four-basin transfer on the classical Himmelblau residual system."""

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


DOMAIN_LO = np.array([-5.0, -5.0])
DOMAIN_HI = np.array([5.0, 5.0])
ELIMINANT = Polynomial([114.0, 1.0, -22.0, 0.0, 1.0])


def residual_z(z: np.ndarray) -> np.ndarray:
    x, y = z
    return np.array([x*x + y - 11.0, x + y*y - 7.0])


def jacobian_z(z: np.ndarray) -> np.ndarray:
    x, y = z
    return np.array([[2*x, 1.0], [1.0, 2*y]])


def objective(z: np.ndarray) -> float:
    r = residual_z(z)
    return float(r @ r)


def eliminant_candidates() -> np.ndarray:
    roots = sorted(float(root.real) for root in ELIMINANT.roots()
                   if abs(root.imag) < 1e-9)
    candidates = np.array([[x, 11.0-x*x] for x in roots])
    return np.array([z for z in candidates if abs(np.linalg.det(jacobian_z(z))) > 1e-8])


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
        return np.linalg.solve(self.matrix(), x-np.array([self.shift_1, self.shift_2]))


def residual_x(x: np.ndarray, transform: Transform) -> np.ndarray:
    return residual_z(transform.inverse(x))


def transforms() -> list[Transform]:
    output = [Transform(0.0, 1.0, 1.0, 0.0, 0.0)]
    rng = np.random.default_rng(20261021)
    for _ in range(8):
        output.append(Transform(float(rng.uniform(-np.pi, np.pi)),
                                float(rng.uniform(0.45, 2.2)),
                                float(rng.uniform(0.45, 2.2)),
                                float(rng.uniform(-3.0, 3.0)),
                                float(rng.uniform(-3.0, 3.0))))
    return output


def greedy_maximin() -> np.ndarray:
    axis = np.linspace(-5.0, 5.0, 41)
    grid = np.array([(x, y) for x in axis for y in axis])
    chosen = [0]
    while len(chosen) < 4:
        distance = np.min(np.linalg.norm(grid[:, None, :]-grid[chosen][None, :, :], axis=2), axis=1)
        distance[chosen] = -1.0
        chosen.append(int(np.argmax(distance)))
    return grid[chosen]


def starts(kind: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if kind == "corner_maximin":
        return np.array([[-5.0, -5.0], [-5.0, 5.0], [5.0, -5.0], [5.0, 5.0]])
    if kind == "greedy_maximin":
        return greedy_maximin()
    if kind == "random":
        return rng.uniform(DOMAIN_LO, DOMAIN_HI, size=(4, 2))
    if kind == "lhs":
        return qmc.scale(qmc.LatinHypercube(2, seed=rng).random(4), DOMAIN_LO, DOMAIN_HI)
    raise ValueError(kind)


def run_starts(initial: np.ndarray, transform: Transform, truth: np.ndarray) -> dict:
    converged, nfev = [], 0
    for z0 in initial:
        fit = least_squares(residual_x, transform.forward(z0), args=(transform,),
                            method="trf", xtol=1e-12, ftol=1e-12, gtol=1e-12,
                            max_nfev=3000)
        converged.append(transform.inverse(fit.x))
        nfev += fit.nfev
    recovered = sorted({int(np.argmin(np.linalg.norm(truth-z, axis=1)))
                        for z in converged
                        if np.min(np.linalg.norm(truth-z, axis=1)) < 2e-3})
    values = [objective(z) for z in converged]
    return {"recovered": recovered, "coverage": len(recovered),
            "best_objective": min(values), "nfev": nfev}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("results/himmelblau_four_basin_transfer.json"))
    args = parser.parse_args()
    candidates = eliminant_candidates()
    records = []
    regimes = transforms()
    for transform_id, transform in enumerate(regimes):
        for method in ("eliminant_roots", "corner_maximin", "greedy_maximin"):
            initial = candidates if method == "eliminant_roots" else starts(method, 0)
            records.append({"method": method, "transform_id": transform_id, "repetition": 0,
                            **run_starts(initial, transform, candidates)})
        for repetition in range(64):
            for method in ("lhs", "random"):
                seed = 100000*transform_id+repetition
                records.append({"method": method, "transform_id": transform_id,
                                "repetition": repetition,
                                **run_starts(starts(method, seed), transform, candidates)})

    def summary(method: str) -> dict:
        rows = [row for row in records if row["method"] == method]
        return {"trials": len(rows),
                "full_coverage": sum(row["coverage"] == 4 for row in rows),
                "catastrophes": sum(row["coverage"] < 4 for row in rows),
                "mean_coverage": float(np.mean([row["coverage"]/4 for row in rows])),
                "mean_nfev": float(np.mean([row["nfev"] for row in rows])),
                "zero_retained": sum(row["best_objective"] < 1e-16 for row in rows)}

    methods = ("eliminant_roots", "corner_maximin", "greedy_maximin", "lhs", "random")
    summaries = {method: summary(method) for method in methods}
    universal_control = any(summaries[method]["full_coverage"] == summaries[method]["trials"]
                            for method in ("corner_maximin", "greedy_maximin"))
    structured_failure = summaries["eliminant_roots"]["full_coverage"] < len(regimes)
    if structured_failure:
        gate = "KILL_STRUCTURED_MISS"
    elif universal_control:
        gate = "KILL_MAXIMIN_MATCHES_COVERAGE"
    else:
        gate = "PASS"
    result = {
        "protocol": "himmelblau-four-basin-transfer-v1",
        "source": {"name": "Himmelblau function", "reference": "Himmelblau-1972",
                   "survey_doi": "10.1504/IJMMNO.2013.055204"},
        "frozen_prediction": "four eliminant roots cover all minima; no maximin control is universal",
        "eliminant_coefficients_ascending": [float(v) for v in ELIMINANT.coef],
        "candidates": [[float(v) for v in z] for z in candidates],
        "candidate_objectives": [objective(z) for z in candidates],
        "candidate_jacobian_determinants": [float(np.linalg.det(jacobian_z(z))) for z in candidates],
        "greedy_maximin_starts": starts("greedy_maximin", 0).tolist(),
        "transforms": [asdict(transform) for transform in regimes],
        "records": records,
        "summary": summaries,
        "scientific_gate": gate,
    }
    canonical = json.dumps(result, indent=2, sort_keys=True)+"\n"
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"summary": summaries, "scientific_gate": gate}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
