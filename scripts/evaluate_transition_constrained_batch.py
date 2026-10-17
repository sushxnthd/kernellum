#!/usr/bin/env python3
"""Frozen transition-constrained batch acquisition screen on the opened cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy

from evaluate_disagreement_acquisition import fit_candidates
from evaluate_sign_anchor_shifted import (
    DIMS, DOMAINS, NOISES, SEEDS, SHAPES, cfit, dataset, geomean_log, log_nmse, predict,
)

METHODS = (
    "no_acquisition",
    "one_point_disagreement",
    "batch_disagreement_diversity",
    "batch_farthest_support",
    "transition_locked_batch",
)


def canonical(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def truth_blind_indices(x, y, z, models):
    predictions = np.stack([predict(model, z) for model in models])
    center = np.median(predictions, axis=0)
    disagreement = np.median(np.abs(predictions - center), axis=0) / max(float(np.std(y)), 1e-12)
    initial_nearest = np.min(np.linalg.norm(z[:, None, :] - x[None, :, :], axis=2), axis=1)
    distance_scale = max(float(initial_nearest.max()), 1e-12)

    first = int(np.argmax(disagreement))
    diverse = [first]
    while len(diverse) < 3:
        support = np.concatenate([x, z[diverse]], axis=0)
        nearest = np.min(np.linalg.norm(z[:, None, :] - support[None, :, :], axis=2), axis=1)
        score = disagreement * nearest / distance_scale
        score[diverse] = -math.inf
        diverse.append(int(np.argmax(score)))

    farthest = []
    while len(farthest) < 3:
        support = x if not farthest else np.concatenate([x, z[farthest]], axis=0)
        nearest = np.min(np.linalg.norm(z[:, None, :] - support[None, :, :], axis=2), axis=1)
        nearest[farthest] = -math.inf
        farthest.append(int(np.argmax(nearest)))

    return {
        "one_point_disagreement": [first],
        "batch_disagreement_diversity": diverse,
        "batch_farthest_support": farthest,
        "transition_locked_batch": diverse,
    }, {
        "disagreement_max": float(disagreement.max()),
        "initial_nearest_max": float(initial_nearest.max()),
    }


def score_unrestricted(x, y, z, truth, indices):
    x_aug = np.concatenate([x, z[indices]], axis=0)
    y_aug = np.concatenate([y, truth[indices]], axis=0)
    models, failures = fit_candidates(x_aug, y_aug)
    winner = min(models, key=lambda model: model["cv"])
    mask = np.ones(len(z), dtype=bool)
    mask[indices] = False
    return log_nmse(predict(winner, z[mask]), truth[mask]), winner, failures


def score_locked(x, y, z, truth, indices, baseline):
    x_aug = np.concatenate([x, z[indices]], axis=0)
    y_aug = np.concatenate([y, truth[indices]], axis=0)
    winner = cfit(x_aug, y_aug, baseline["sign"], baseline["family"])
    mask = np.ones(len(z), dtype=bool)
    mask[indices] = False
    return log_nmse(predict(winner, z[mask]), truth[mask]), winner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    cached, decision_rows = [], []
    for shape in SHAPES:
        for d in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, d, seed, noise)
                    models, failures = fit_candidates(x, y)
                    baseline = min(models, key=lambda model: model["cv"])
                    for domain in DOMAINS:
                        z = tests[domain][0]
                        key = [shape, d, seed, noise, domain]
                        indices, diagnostics = truth_blind_indices(x, y, z, models)
                        decision_rows.append({
                            "key": key,
                            "selected_indices": indices,
                            "diagnostics": diagnostics,
                            "pre_acquisition_winner": {
                                "sign": baseline["sign"], "family": baseline["family"], "cv": baseline["cv"],
                            },
                            "available_candidates": [
                                {"sign": m["sign"], "family": m["family"], "cv": m["cv"]} for m in models
                            ],
                            "failed_candidates": failures,
                        })
                        cached.append((key, x, y, tests[domain], baseline, indices))

    decisions = {
        "schema": "kernellum.transition-constrained-batch-decisions.v1",
        "classification": "OPENED_COHORT_TRUTH_BLIND_SELECTIONS",
        "protocol_commit": "441de576a32128f53f353587799cc7cdbadc6882",
        "rows": decision_rows,
    }
    args.decisions.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    rows, fit_failures = [], []
    for key, x, y, (z, truth), baseline, indices in cached:
        scores = {"no_acquisition": log_nmse(predict(baseline, z), truth)}
        winners = {
            "no_acquisition": {"sign": baseline["sign"], "family": baseline["family"], "cv": baseline["cv"]}
        }
        for method in ("one_point_disagreement", "batch_disagreement_diversity", "batch_farthest_support"):
            try:
                score, winner, failures = score_unrestricted(x, y, z, truth, indices[method])
                scores[method] = score
                winners[method] = {"sign": winner["sign"], "family": winner["family"], "cv": winner["cv"]}
                fit_failures.extend({"key": key, "method": method, **failure} for failure in failures)
            except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                fit_failures.append({"key": key, "method": method, "reason": str(exc)})
        try:
            score, winner = score_locked(x, y, z, truth, indices["transition_locked_batch"], baseline)
            scores["transition_locked_batch"] = score
            winners["transition_locked_batch"] = {
                "sign": winner["sign"], "family": winner["family"], "cv": winner["cv"]
            }
        except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
            fit_failures.append({"key": key, "method": "transition_locked_batch", "reason": str(exc)})
        rows.append({"key": key, "selected_indices": indices, "scores": scores, "winners": winners})
        print(key, scores, flush=True)

    raw_geometric = {}
    metrics = {}
    for domain in DOMAINS:
        domain_rows = [row for row in rows if row["key"][-1] == domain]
        raw_geometric[domain] = {
            method: (
                geomean_log([row["scores"][method] for row in domain_rows])
                if all(method in row["scores"] for row in domain_rows)
                else math.inf
            ) for method in METHODS
        }
        metrics[domain] = {
            "geometric_nmse": {
                method: (raw_geometric[domain][method] if math.isfinite(raw_geometric[domain][method]) else None)
                for method in METHODS
            },
            "catastrophic": {
                method: sum(row["scores"].get(method, math.inf) > 5 for row in domain_rows)
                for method in METHODS
            },
        }
    total = {method: sum(metrics[d]["catastrophic"][method] for d in DOMAINS) for method in METHODS}
    locked = "transition_locked_batch"
    controls = ("one_point_disagreement", "batch_disagreement_diversity", "batch_farthest_support")
    gates = {
        "decisions_complete_and_prehashed": len(decision_rows) == 48 and bool(decision_sha),
        "all_arms_complete": all(len(row["scores"]) == len(METHODS) for row in rows),
        "halves_total_catastrophes": total[locked] <= 5,
        "beats_each_acquisition_control_by_two": all(total[locked] <= total[c] - 2 for c in controls),
        "no_domain_excess": all(metrics[d]["catastrophic"][locked] <= metrics[d]["catastrophic"]["no_acquisition"] for d in DOMAINS),
        "halves_far_shell_catastrophes": metrics["far_shell"]["catastrophic"][locked] <= 3,
        "inside_noninferior": raw_geometric["inside"][locked] <= 1.10 * raw_geometric["inside"]["no_acquisition"],
        "near_no_worse_than_best_control": raw_geometric["near_shell"][locked] <= min(raw_geometric["near_shell"][c] for c in controls),
        "far_no_worse_than_best_control": raw_geometric["far_shell"][locked] <= min(raw_geometric["far_shell"][c] for c in controls),
    }
    transitions = {
        method: sum(
            method in row["winners"] and (
                row["winners"][method]["sign"] != row["winners"]["no_acquisition"]["sign"]
                or row["winners"][method]["family"] != row["winners"]["no_acquisition"]["family"]
            ) for row in rows
        ) for method in METHODS
    }
    unavailable = {method: sum(method not in row["scores"] for row in rows) for method in METHODS}
    payload = {
        "schema": "kernellum.transition-constrained-batch-result.v1",
        "classification": "OPENED_COHORT_DEVELOPMENT",
        "decision_sha256": decision_sha,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "cells": len(rows), "total_catastrophes": total, "model_class_transitions": transitions,
        "unavailable_cells": unavailable,
        "metrics": metrics, "gates": gates, "fit_failures": fit_failures, "rows": rows,
        "status": "ADVANCE_TO_PROSPECTIVE" if all(gates.values()) else "KILL_TRANSITION_LOCKED_BATCH",
    }
    payload["canonical_sha256"] = canonical(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in ("status", "canonical_sha256", "decision_sha256", "total_catastrophes", "model_class_transitions", "unavailable_cells", "metrics", "gates")}, indent=2))


if __name__ == "__main__":
    main()
