#!/usr/bin/env python3
"""Generate one high-dimensional truth-blind adversarial boundary manifest.

This stage is intentionally incapable of evaluating requested-input truth.
It serializes training observations, request coordinates, solver winners and
the unchanged prediction-envelope receipt. Outcome joining belongs to a later,
separately committed evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernellum.discovery.solver_equivalence import certify_prediction_envelope
from scripts.evaluate_sign_anchor_shifted import cfit, independent_fit, maximin, predict, shell

FAMILIES = ("exp_affine", "exp_concave")
SIGNS = (1, -1)
GRID = tuple(range(-48, 49))
DIMS = (5, 7)
SEEDS = (6101, 6107)
REQUEST_DOMAINS = ("inside", "near_shell", "far_shell")


def canonical(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _truth_factory(rng, dimension, seed):
    center = rng.uniform(-0.30, 0.30, dimension)
    q = np.linalg.qr(rng.normal(size=(dimension, dimension)))[0]
    curvature = (q * rng.uniform(0.7, 4.8, dimension)) @ q.T
    direction = rng.normal(size=dimension)
    direction /= max(float(np.linalg.norm(direction)), 1e-12)
    sign = 1.0 if seed == SEEDS[0] else -1.0

    def truth(z):
        u = z - center
        quad = np.einsum("ni,ij,nj->n", u, curvature, u)
        ridge = z @ direction
        return sign * (1.0 + quad) ** -1.25 * (1.0 + 0.15 * np.sin(2.4 * ridge))

    return truth


def base_instance(dimension, seed):
    if dimension not in DIMS or seed not in SEEDS:
        raise ValueError("dimension/seed outside frozen factorial")
    rng = np.random.default_rng(seed + 100 * dimension + 60000)
    truth = _truth_factory(rng, dimension, seed)
    pool = rng.uniform(-1.0, 1.0, (192, dimension))
    ids = maximin(pool, 24)
    x_train = pool[ids]
    clean = truth(x_train)
    scale = max(float(np.std(clean)), 1e-12)
    y_base = clean + 0.20 * scale * rng.normal(size=24)
    requests = {
        "inside": rng.uniform(-1.0, 1.0, (192, dimension)),
        "near_shell": shell(rng, 192, dimension, 1.0, 1.7),
        "far_shell": shell(rng, 192, dimension, 1.7, 3.4),
    }
    # Deliberately return no truth closure or request labels.
    return x_train, y_base, requests


def perturbation_direction(x_train):
    columns = [x_train[:, j] for j in range(x_train.shape[1])]
    for j in range(x_train.shape[1]):
        for k in range(j, x_train.shape[1]):
            columns.append(x_train[:, j] * x_train[:, k])
    features = np.column_stack(columns)
    features -= np.mean(features, axis=0, keepdims=True)
    u, _, _ = np.linalg.svd(features, full_matrices=False)
    direction = u[:, 0]
    direction -= float(np.mean(direction))
    direction /= max(float(np.linalg.norm(direction)), 1e-12)
    nz = np.flatnonzero(np.abs(direction) > 1e-14)
    if not nz.size:
        raise RuntimeError("degenerate frozen perturbation direction")
    if direction[int(nz[0])] < 0:
        direction = -direction
    return direction


def fit_winner(x_train, y_train, bank):
    fitted, failures = [], []
    fitter = cfit if bank == "candidate" else independent_fit
    for sign in SIGNS:
        for family in FAMILIES:
            try:
                model = fitter(x_train, y_train, sign, family)
                model["kind"] = bank
                fitted.append(model)
            except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                failures.append({"sign": sign, "family": family, "reason": str(exc)})
    if not fitted:
        raise RuntimeError(f"{bank} bank empty: {failures}")
    return min(fitted, key=lambda row: row["cv"]), failures


def winner_summary(model):
    return {
        "solver": model["kind"],
        "sign": int(model["sign"]),
        "family": model["family"],
        "cv": float(model["cv"]),
    }


def scan_base(dimension, seed):
    x_train, y_base, requests = base_instance(dimension, seed)
    direction = perturbation_direction(x_train)
    y_scale_base = max(float(np.std(y_base)), 1e-12)
    request_matrix = np.concatenate([requests[key] for key in REQUEST_DOMAINS], axis=0)
    rows = []
    for index in GRID:
        y_train = y_base + (index / 48.0) * (0.45 * y_scale_base) * direction
        candidate, candidate_failures = fit_winner(x_train, y_train, "candidate")
        independent, independent_failures = fit_winner(x_train, y_train, "independent")
        y_scale = max(float(np.std(y_train)), 1e-12)
        candidate_prediction = predict(candidate, request_matrix)
        independent_prediction = predict(independent, request_matrix)
        receipt = certify_prediction_envelope(
            candidate_prediction,
            independent_prediction,
            y_scale=y_scale,
            candidate_cv=candidate["cv"],
            independent_cv=independent["cv"],
        )
        lower = "independent" if independent["cv"] < candidate["cv"] else "candidate"
        rows.append({
            "grid_index": index,
            "y_train": y_train.tolist(),
            "candidate": winner_summary(candidate),
            "independent": winner_summary(independent),
            "candidate_failures": candidate_failures,
            "independent_failures": independent_failures,
            "lower_cv_solver": lower,
            "normalized_cv_gap": abs(float(candidate["cv"]) - float(independent["cv"]))
                / max(min(float(candidate["cv"]), float(independent["cv"])), 1e-12),
            "prediction_rms": receipt.prediction_rms,
            "prediction_max": receipt.prediction_max,
            "accepted": receipt.accepted,
            "selected_solver": receipt.selected_solver,
            "scope": receipt.scope,
        })
        print(dimension, seed, index, lower, receipt.prediction_rms, flush=True)

    for position, row in enumerate(rows):
        previous = rows[position - 1] if position else None
        row["boundary_event"] = bool(previous) and (
            row["candidate"]["sign"] != previous["candidate"]["sign"]
            or row["candidate"]["family"] != previous["candidate"]["family"]
            or row["independent"]["sign"] != previous["independent"]["sign"]
            or row["independent"]["family"] != previous["independent"]["family"]
            or row["lower_cv_solver"] != previous["lower_cv_solver"]
        )

    eligible = [row for row in rows if row["lower_cv_solver"] == "independent"]
    eligible.sort(key=lambda row: (
        not row["boundary_event"],
        row["normalized_cv_gap"],
        -row["prediction_rms"],
        -row["prediction_max"],
        abs(row["grid_index"]),
        row["grid_index"],
    ))
    selected = eligible[:6]
    return {
        "schema": "kernellum.adversarial-boundary-high-dim-base-manifest.v1",
        "classification": "PROSPECTIVE_TRUTH_BLIND",
        "protocol_commit": "b9f1b892e33c5d37144e969d44e20eef610f4ea7",
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "base": {"dimension": dimension, "seed": seed},
        "thresholds": {"prediction_rms": 0.5, "prediction_max": 4.0},
        "grid_size": len(GRID),
        "eligible_count": len(eligible),
        "selected_count": len(selected),
        "status": "PASS" if len(selected) == 6 else "FAIL_INSUFFICIENT_ELIGIBLE",
        "x_train": x_train.tolist(),
        "y_base": y_base.tolist(),
        "perturbation_direction": direction.tolist(),
        "request_inputs": {key: requests[key].tolist() for key in REQUEST_DOMAINS},
        "selected": selected,
        "forbidden_fields": ["request_truth", "scores", "harmful_switch"],
    }


def assert_truth_blind(payload):
    encoded = json.dumps(payload, sort_keys=True)
    forbidden = ("request_truth", '"truth"', '"scores"', "harmful_switch")
    # The explicit forbidden_fields declaration is allowed; no data key may use it.
    probe = dict(payload)
    probe.pop("forbidden_fields", None)
    encoded = json.dumps(probe, sort_keys=True)
    for token in forbidden:
        if token in encoded:
            raise AssertionError(f"truth-blind manifest contains forbidden token: {token}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimension", type=int, choices=DIMS, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = scan_base(args.dimension, args.seed)
    assert_truth_blind(payload)
    payload["canonical_sha256"] = canonical(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "base": payload["base"],
        "eligible_count": payload["eligible_count"],
        "selected_count": payload["selected_count"],
        "canonical_sha256": payload["canonical_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
