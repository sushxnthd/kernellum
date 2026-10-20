#!/usr/bin/env python3
"""External FTrig basin-coverage experiment.

Reimplements the residual benchmark in Riley, Webb, and Baker's public
DeflatedGaussNewton repository.  The experiment compares equal-budget start
sets; it does not reimplement or claim priority over their deflation method.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import qmc


A = 35184372088832 / 3125302502557517
B = 70368744177664 / 2778046668940015
C = 281474976710656 / 2778046668940015
D = 1125899906842624 / 2778046668940015
E = 140737488355328 / 8681395840437547
F = 140737488355328 / 3125302502557517
U_ROOTS = np.array([-1 / np.sqrt(A), -1 / np.sqrt(B), -1 / np.sqrt(C), 0.0,
                    1 / np.sqrt(C), 1 / np.sqrt(B), 1 / np.sqrt(A)])
V_ROOTS = np.array([-1 / np.sqrt(D), -1 / np.sqrt(F), -1 / np.sqrt(E),
                    1 / np.sqrt(E), 1 / np.sqrt(F), 1 / np.sqrt(D)])


def residual_z(z: np.ndarray) -> np.ndarray:
    x, y = z
    u, v = x + y, x - y
    return np.array([
        -10 * u * (A * u * u - 1) * (B * u * u - 1) * (C * u * u - 1),
        -10 * (D * v * v - 1) * (E * v * v - 1) * (F * v * v - 1),
        x * x / 100 + y * y / 100 + 10,
    ])


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


def root_lattice() -> np.ndarray:
    return np.array([[(u + v) / 2, (u - v) / 2] for u in U_ROOTS for v in V_ROOTS])


def generic_grid() -> np.ndarray:
    return np.array([[x, y] for x in np.linspace(-10, 10, 7)
                     for y in np.linspace(-10, 10, 6)])


def starts(kind: str, rng: np.random.Generator) -> np.ndarray:
    if kind == "root_lattice":
        return root_lattice()
    if kind == "grid":
        return generic_grid()
    if kind == "random":
        return rng.uniform(-10, 10, size=(42, 2))
    if kind == "lhs":
        sampler = qmc.LatinHypercube(d=2, seed=rng)
        return qmc.scale(sampler.random(42), [-10, -10], [10, 10])
    raise ValueError(kind)


def cluster(points: list[np.ndarray], values: list[float], tol: float = 2e-4):
    order = np.argsort(values)
    centers, center_values = [], []
    for idx in order:
        p = points[idx]
        if all(np.linalg.norm(p - c) > tol for c in centers):
            centers.append(p)
            center_values.append(values[idx])
    return centers, center_values


def run_method(kind: str, seed: int, transform: Transform) -> dict:
    rng = np.random.default_rng(seed)
    latent_starts = starts(kind, rng)
    points, values, nfev = [], [], 0
    for z0 in latent_starts:
        x0 = transform.forward(z0)
        fit = least_squares(residual_x, x0, args=(transform,), method="trf",
                            xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=3000)
        zhat = transform.inverse(fit.x)
        points.append(zhat)
        values.append(float(np.dot(fit.fun, fit.fun)))
        nfev += fit.nfev
    centers, center_values = cluster(points, values)
    return {
        "method": kind,
        "seed": seed,
        "starts": 42,
        "distinct_minima": len(centers),
        "coverage_fraction": len(centers) / 42,
        "best_objective": min(center_values),
        "median_objective": float(np.median(center_values)),
        "nfev": nfev,
        "centers": [[float(v) for v in c] for c in centers],
    }


def make_transforms() -> list[Transform]:
    # Fixed before the confirmation run. Identity is development; the other
    # eight are untouched affine metamorphs of the published objective.
    out = [Transform(0.0, 1.0, 1.0, 0.0, 0.0)]
    rng = np.random.default_rng(20261020)
    for _ in range(8):
        out.append(Transform(float(rng.uniform(-np.pi, np.pi)),
                             float(rng.uniform(0.45, 2.2)),
                             float(rng.uniform(0.45, 2.2)),
                             float(rng.uniform(-3, 3)),
                             float(rng.uniform(-3, 3))))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/residual_root_lattice.json"))
    args = parser.parse_args()
    methods = ["root_lattice", "grid", "lhs", "random"]
    records = []
    for transform_id, transform in enumerate(make_transforms()):
        repetitions = 1 if transform_id == 0 else 1
        for repetition in range(repetitions):
            for method in methods:
                record = run_method(method, 1000 * transform_id + repetition, transform)
                record["transform_id"] = transform_id
                record["split"] = "development" if transform_id == 0 else "confirmation"
                record["transform"] = asdict(transform)
                records.append(record)
    root = [r for r in records if r["method"] == "root_lattice"]
    controls = [r for r in records if r["method"] != "root_lattice"]
    result = {
        "source": {
            "repository": "AlbanBloorRiley/DeflatedGaussNewton",
            "commit": "615c185f3d61f044eab7cfd27f97f698ff341d8f",
            "paper_arxiv": "2409.14438",
            "source_file_sha": "0083087a71d2314d6c49c5ba152297e72d75fad8",
        },
        "frozen_prediction": "42 factor-root starts recover all 42 minima on identity and all 8 affine metamorphs",
        "records": records,
        "summary": {
            "root_full_coverage": sum(r["distinct_minima"] == 42 for r in root),
            "root_trials": len(root),
            "control_full_coverage": sum(r["distinct_minima"] == 42 for r in controls),
            "control_trials": len(controls),
            "root_mean_coverage": float(np.mean([r["coverage_fraction"] for r in root])),
            "control_mean_coverage": float(np.mean([r["coverage_fraction"] for r in controls])),
            "root_mean_nfev": float(np.mean([r["nfev"] for r in root])),
            "control_mean_nfev": float(np.mean([r["nfev"] for r in controls])),
        },
    }
    canonical = json.dumps(result, indent=2, sort_keys=True) + "\n"
    result["payload_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
