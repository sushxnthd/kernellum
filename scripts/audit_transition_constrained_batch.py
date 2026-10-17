#!/usr/bin/env python3
"""Independent full-refit audit of transition-constrained batch evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from evaluate_sign_anchor_shifted import (
    DIMS, DOMAINS, NOISES, SEEDS, SHAPES, cfit, dataset, log_nmse, predict,
)

FAMILIES = ("exp_affine", "exp_concave")
ARMS = ("one_point_disagreement", "batch_disagreement_diversity", "batch_farthest_support")


def candidates(x, y):
    out = []
    for sign in (1, -1):
        for family in FAMILIES:
            try:
                out.append(cfit(x, y, sign, family))
            except (FloatingPointError, ValueError, np.linalg.LinAlgError):
                pass
    return out


def selections(x, y, z, models):
    matrix = np.asarray([predict(m, z) for m in models])
    disagreement = np.median(np.abs(matrix - np.median(matrix, axis=0)), axis=0) / max(float(np.std(y)), 1e-12)
    initial = np.min(np.linalg.norm(z[:, None, :] - x[None, :, :], axis=2), axis=1)
    first = int(np.argmax(disagreement))
    diverse = [first]
    while len(diverse) != 3:
        augmented = np.vstack((x, z[diverse]))
        radius = np.min(np.linalg.norm(z[:, None, :] - augmented[None, :, :], axis=2), axis=1)
        utility = disagreement * radius / max(float(initial.max()), 1e-12)
        utility[diverse] = -math.inf
        diverse.append(int(np.argmax(utility)))
    farthest = []
    while len(farthest) != 3:
        augmented = x if not farthest else np.vstack((x, z[farthest]))
        radius = np.min(np.linalg.norm(z[:, None, :] - augmented[None, :, :], axis=2), axis=1)
        radius[farthest] = -math.inf
        farthest.append(int(np.argmax(radius)))
    return {
        "one_point_disagreement": [first],
        "batch_disagreement_diversity": diverse,
        "batch_farthest_support": farthest,
        "transition_locked_batch": diverse,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    recorded_decisions = json.loads(args.decisions.read_text())
    recorded = json.loads(args.result.read_text())
    by_key = {tuple(row["key"]): row for row in recorded["rows"]}
    decision_by_key = {tuple(row["key"]): row for row in recorded_decisions["rows"]}
    checks, failures = 0, []

    def check(label, condition):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()
    check("decision_sha", decision_sha == recorded["decision_sha256"])
    totals = {name: 0 for name in recorded["total_catastrophes"]}
    unavailable = {name: 0 for name in recorded["unavailable_cells"]}

    for shape in SHAPES:
        for d in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, d, seed, noise)
                    original = candidates(x, y)
                    baseline = min(original, key=lambda m: m["cv"])
                    for domain in DOMAINS:
                        key = (shape, d, seed, noise, domain)
                        z, truth = tests[domain]
                        chosen = selections(x, y, z, original)
                        row, drow = by_key[key], decision_by_key[key]
                        check(f"{key}.indices", chosen == drow["selected_indices"] == row["selected_indices"])
                        expected = {"no_acquisition": log_nmse(predict(baseline, z), truth)}
                        for arm in ARMS:
                            idx = chosen[arm]
                            xa, ya = np.vstack((x, z[idx])), np.concatenate((y, truth[idx]))
                            fitted = candidates(xa, ya)
                            if fitted:
                                winner = min(fitted, key=lambda m: m["cv"])
                                mask = np.ones(len(z), dtype=bool); mask[idx] = False
                                expected[arm] = log_nmse(predict(winner, z[mask]), truth[mask])
                        idx = chosen["transition_locked_batch"]
                        xa, ya = np.vstack((x, z[idx])), np.concatenate((y, truth[idx]))
                        try:
                            locked = cfit(xa, ya, baseline["sign"], baseline["family"])
                            mask = np.ones(len(z), dtype=bool); mask[idx] = False
                            expected["transition_locked_batch"] = log_nmse(predict(locked, z[mask]), truth[mask])
                        except (FloatingPointError, ValueError, np.linalg.LinAlgError):
                            pass
                        check(f"{key}.availability", set(expected) == set(row["scores"]))
                        for arm, score in expected.items():
                            check(f"{key}.{arm}.score", np.isclose(score, row["scores"][arm], rtol=1e-10, atol=1e-10))
                        for arm in totals:
                            if arm not in expected:
                                unavailable[arm] += 1
                                totals[arm] += 1
                            elif expected[arm] > 5:
                                totals[arm] += 1

    check("totals", totals == recorded["total_catastrophes"])
    check("unavailable", unavailable == recorded["unavailable_cells"])
    without_digest = dict(recorded); without_digest.pop("canonical_sha256")
    raw = json.dumps(without_digest, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    check("canonical_digest", digest == recorded["canonical_sha256"])
    payload = {
        "schema": "kernellum.transition-constrained-batch-audit.v1",
        "checks": checks,
        "failures": failures,
        "decision_sha256": decision_sha,
        "result_canonical_sha256": digest,
        "status": "PASS" if not failures else "FAIL",
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
