#!/usr/bin/env python3
"""Independent recomputation of one-point disagreement acquisition results."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from evaluate_sign_anchor_shifted import DIMS, DOMAINS, FLOOR, NOISES, SEEDS, SHAPES, dataset
from kernellum.discovery.additive_response import fit_exp, value_jacobian

ACQUISITIONS = ("disagreement", "deterministic_random", "nearest_support", "farthest_support")
METHODS = ("no_acquisition",) + ACQUISITIONS
FAMILIES = ("exp_affine", "exp_concave")


def fit_one(x, y, sign, family):
    amplitude = max(float(np.max(np.abs(y))), 1e-12)
    theta = fit_exp(x, sign * y / amplitude, family)
    loo = []
    for held in range(len(x)):
        mask = np.arange(len(x)) != held
        loo_amplitude = max(float(np.max(np.abs(y[mask]))), 1e-12)
        loo_theta = fit_exp(x[mask], sign * y[mask] / loo_amplitude, family)
        normalized = value_jacobian(loo_theta, x[held : held + 1], family, 700)[0][0]
        loo.append(sign * loo_amplitude * normalized)
    scale = max(float(np.std(y)), 1e-12)
    return {"theta": theta, "amplitude": amplitude, "sign": sign, "family": family,
            "cv": float(np.mean(((y - np.asarray(loo)) / scale) ** 2))}


def bank(x, y):
    models = []
    for sign in (1, -1):
        for family in FAMILIES:
            try:
                models.append(fit_one(x, y, sign, family))
            except (FloatingPointError, ValueError, np.linalg.LinAlgError):
                pass
    if not models:
        raise FloatingPointError("independent bank empty")
    return models


def predict(model, x):
    normalized = value_jacobian(model["theta"], x, model["family"], 700)[0]
    return model["sign"] * model["amplitude"] * normalized


def log_nmse(prediction, truth):
    return math.log(max(float(np.mean((prediction - truth) ** 2)), 1e-300)) - math.log(max(float(np.var(truth)), 1e-30))


def geomean(log_values):
    return math.exp(sum(max(value, FLOOR) for value in log_values) / len(log_values))


def choices(x, y, z, models, key):
    matrix = np.stack([predict(model, z) for model in models])
    med = np.median(matrix, axis=0)
    score = np.median(np.abs(matrix - med), axis=0) / max(float(np.std(y)), 1e-12)
    distance = np.min(np.linalg.norm(z[:, None, :] - x[None, :, :], axis=2), axis=1)
    random_index = int.from_bytes(hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).digest()[:8], "big") % len(z)
    return {
        "disagreement": int(np.argmax(score)),
        "deterministic_random": random_index,
        "nearest_support": int(np.argmin(distance)),
        "farthest_support": int(np.argmax(distance)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    expected_decisions = json.loads(args.decisions.read_text())
    expected_result = json.loads(args.result.read_text())
    expected_decision_rows = {tuple(row["key"]): row for row in expected_decisions["rows"]}
    expected_result_rows = {tuple(row["key"]): row for row in expected_result["rows"]}

    checks = passed = 0
    reproduced = []
    failures = []
    for shape in SHAPES:
        for d in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, d, seed, noise)
                    original = bank(x, y)
                    baseline = min(original, key=lambda model: model["cv"])
                    for domain in DOMAINS:
                        z, truth = tests[domain]
                        key = (shape, d, seed, noise, domain)
                        selected = choices(x, y, z, original, list(key))
                        checks += 1
                        if selected == expected_decision_rows[key]["selected_indices"]:
                            passed += 1
                        else:
                            failures.append({"key": list(key), "field": "selected_indices"})
                        scores = {"no_acquisition": log_nmse(predict(baseline, z), truth)}
                        for method, index in selected.items():
                            x_aug = np.concatenate([x, z[index : index + 1]], axis=0)
                            y_aug = np.concatenate([y, truth[index : index + 1]], axis=0)
                            winner = min(bank(x_aug, y_aug), key=lambda model: model["cv"])
                            mask = np.arange(len(z)) != index
                            scores[method] = log_nmse(predict(winner, z[mask]), truth[mask])
                        for method in METHODS:
                            checks += 1
                            if abs(scores[method] - expected_result_rows[key]["scores"][method]) <= 1e-10:
                                passed += 1
                            else:
                                failures.append({"key": list(key), "field": "score", "method": method,
                                                 "expected": expected_result_rows[key]["scores"][method], "actual": scores[method]})
                        reproduced.append({"key": list(key), "scores": scores})

    metrics = {}
    for domain in DOMAINS:
        rows = [row for row in reproduced if row["key"][-1] == domain]
        metrics[domain] = {
            "geometric_nmse": {method: geomean([row["scores"][method] for row in rows]) for method in METHODS},
            "catastrophic": {method: sum(row["scores"][method] > 5 for row in rows) for method in METHODS},
        }
    for domain in DOMAINS:
        for kind in ("geometric_nmse", "catastrophic"):
            for method in METHODS:
                checks += 1
                actual = metrics[domain][kind][method]
                expected = expected_result["metrics"][domain][kind][method]
                ok = actual == expected if kind == "catastrophic" else abs(actual - expected) <= 1e-8 * max(1.0, abs(expected))
                if ok:
                    passed += 1
                else:
                    failures.append({"field": kind, "domain": domain, "method": method,
                                     "expected": expected, "actual": actual})

    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()
    checks += 1
    if decision_sha == expected_result["decision_sha256"]:
        passed += 1
    else:
        failures.append({"field": "decision_sha256"})

    payload = {
        "schema": "kernellum.disagreement-acquisition-audit.v1",
        "checks": checks,
        "passed": passed,
        "failures": failures,
        "decision_sha256": decision_sha,
        "status": "PASS" if passed == checks and not failures else "FAIL",
    }
    body = dict(payload)
    payload["canonical_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
