#!/usr/bin/env python3
"""Frozen one-point disagreement acquisition screen on the opened cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy

from evaluate_sign_anchor_shifted import (
    DIMS,
    DOMAINS,
    FLOOR,
    NOISES,
    SEEDS,
    SHAPES,
    cfit,
    dataset,
    geomean_log,
    log_nmse,
    predict,
)

ACQUISITIONS = ("disagreement", "deterministic_random", "nearest_support", "farthest_support")
METHODS = ("no_acquisition",) + ACQUISITIONS
FAMILIES = ("exp_affine", "exp_concave")


def canonical(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def fit_candidates(x, y):
    models, failures = [], []
    for sign in (1, -1):
        for family in FAMILIES:
            try:
                models.append(cfit(x, y, sign, family))
            except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                failures.append({"sign": sign, "family": family, "reason": str(exc)})
    if not models:
        raise FloatingPointError("all sign/family candidates failed")
    return models, failures


def choose_indices(x, y, z, models, key):
    predictions = np.stack([predict(model, z) for model in models])
    center = np.median(predictions, axis=0)
    disagreement = np.median(np.abs(predictions - center), axis=0) / max(float(np.std(y)), 1e-12)
    nearest = np.min(np.linalg.norm(z[:, None, :] - x[None, :, :], axis=2), axis=1)
    random_index = int.from_bytes(
        hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).digest()[:8], "big"
    ) % len(z)
    return {
        "disagreement": int(np.argmax(disagreement)),
        "deterministic_random": random_index,
        "nearest_support": int(np.argmin(nearest)),
        "farthest_support": int(np.argmax(nearest)),
    }, {
        "disagreement_max": float(disagreement.max()),
        "nearest_distance_min": float(nearest.min()),
        "nearest_distance_max": float(nearest.max()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cached = []
    decision_rows = []
    for shape in SHAPES:
        for d in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, d, seed, noise)
                    models, failures = fit_candidates(x, y)
                    for domain in DOMAINS:
                        z = tests[domain][0]
                        key = [shape, d, seed, noise, domain]
                        indices, diagnostics = choose_indices(x, y, z, models, key)
                        decision_rows.append({
                            "key": key,
                            "selected_indices": indices,
                            "diagnostics": diagnostics,
                            "available_candidates": [
                                {"sign": m["sign"], "family": m["family"], "cv": m["cv"]}
                                for m in models
                            ],
                            "failed_candidates": failures,
                        })
                        cached.append((key, x, y, tests[domain], models, indices))

    decisions = {
        "schema": "kernellum.disagreement-acquisition-decisions.v1",
        "classification": "OPENED_COHORT_TRUTH_BLIND_SELECTIONS",
        "protocol_commit": "c6318557d635b19598b80037554740f23eae6fd8",
        "evaluation_addendum_commit": "413dc742349c07c92bc98cbfdca0ee0d46582cf3",
        "rows": decision_rows,
    }
    args.decisions.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    result_rows = []
    fit_failures = []
    for key, x, y, (z, truth), original_models, indices in cached:
        baseline = min(original_models, key=lambda model: model["cv"])
        scores = {"no_acquisition": log_nmse(predict(baseline, z), truth)}
        winners = {"no_acquisition": {"sign": baseline["sign"], "family": baseline["family"], "cv": baseline["cv"]}}
        for method in ACQUISITIONS:
            idx = indices[method]
            x_aug = np.concatenate([x, z[idx : idx + 1]], axis=0)
            y_aug = np.concatenate([y, truth[idx : idx + 1]], axis=0)
            try:
                models, failures = fit_candidates(x_aug, y_aug)
                winner = min(models, key=lambda model: model["cv"])
                mask = np.arange(len(z)) != idx
                scores[method] = log_nmse(predict(winner, z[mask]), truth[mask])
                winners[method] = {"sign": winner["sign"], "family": winner["family"], "cv": winner["cv"]}
                fit_failures.extend({"key": key, "method": method, **failure} for failure in failures)
            except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                fit_failures.append({"key": key, "method": method, "reason": "acquisition unavailable: " + str(exc)})
        result_rows.append({"key": key, "selected_indices": indices, "scores": scores, "winners": winners})
        print(key, {m: scores.get(m) for m in METHODS}, flush=True)

    metrics = {}
    for domain in DOMAINS:
        domain_rows = [row for row in result_rows if row["key"][-1] == domain]
        metrics[domain] = {
            "geometric_nmse": {
                method: geomean_log([row["scores"][method] for row in domain_rows if method in row["scores"]])
                for method in METHODS
            },
            "catastrophic": {
                method: sum(row["scores"].get(method, math.inf) > 5 for row in domain_rows)
                for method in METHODS
            },
        }

    total_catastrophes = {
        method: sum(metrics[domain]["catastrophic"][method] for domain in DOMAINS) for method in METHODS
    }
    controls = ACQUISITIONS[1:]
    gates = {
        "decisions_complete_and_prehashed": len(decision_rows) == 48 and bool(decision_sha),
        "post_acquisition_complete": all(len(row["scores"]) == len(METHODS) for row in result_rows),
        "halves_catastrophes": total_catastrophes["disagreement"] <= 0.5 * total_catastrophes["no_acquisition"],
        "beats_each_control_by_two": all(
            total_catastrophes["disagreement"] <= total_catastrophes[control] - 2 for control in controls
        ),
        "no_domain_excess": all(
            metrics[domain]["catastrophic"]["disagreement"]
            <= metrics[domain]["catastrophic"]["no_acquisition"]
            for domain in DOMAINS
        ),
        "inside_noninferior": metrics["inside"]["geometric_nmse"]["disagreement"]
        <= 1.10 * metrics["inside"]["geometric_nmse"]["no_acquisition"],
        "near_beats_best_control": metrics["near_shell"]["geometric_nmse"]["disagreement"]
        <= 0.90 * min(metrics["near_shell"]["geometric_nmse"][control] for control in controls),
        "far_beats_best_control": metrics["far_shell"]["geometric_nmse"]["disagreement"]
        <= 0.90 * min(metrics["far_shell"]["geometric_nmse"][control] for control in controls),
    }
    payload = {
        "schema": "kernellum.disagreement-acquisition-result.v1",
        "classification": "OPENED_COHORT_DEVELOPMENT",
        "decision_sha256": decision_sha,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "cells": len(result_rows),
        "total_catastrophes": total_catastrophes,
        "metrics": metrics,
        "gates": gates,
        "fit_failures": fit_failures,
        "rows": result_rows,
        "status": "ADVANCE_TO_PROSPECTIVE" if all(gates.values()) else "KILL_ONE_POINT_DISAGREEMENT",
    }
    payload["canonical_sha256"] = canonical(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: payload[key] for key in ("status", "canonical_sha256", "decision_sha256", "total_catastrophes", "metrics", "gates")}, indent=2))


if __name__ == "__main__":
    main()
