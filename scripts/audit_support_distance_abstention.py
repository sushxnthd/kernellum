#!/usr/bin/env python3
"""Independent audit of the frozen support-distance development screen."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from evaluate_sign_anchor_shifted import DOMAINS, dataset


def pair_auc(values, labels):
    positives = [v for v, y in zip(values, labels) if y]
    negatives = [v for v, y in zip(values, labels) if not y]
    wins = sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def recompute(key):
    shape, dimension, seed, noise, domain = key
    x, _y, tests = dataset(shape, dimension, seed, noise)
    z = tests[domain][0]
    train_nearest = []
    for i, point in enumerate(x):
        train_nearest.append(min(float(np.linalg.norm(point - other)) for j, other in enumerate(x) if i != j))
    scale = max(float(np.median(train_nearest)), 1e-12)
    requested_nearest = [min(float(np.linalg.norm(point - other)) for other in x) / scale for point in z]
    support = float(np.quantile(requested_nearest, 0.95))
    center = np.mean(x, axis=0)
    median_radius = max(float(np.median([np.linalg.norm(point - center) for point in x])), 1e-12)
    shell = float(np.quantile([np.linalg.norm(point - center) / median_radius for point in z], 0.95))
    lo, hi = np.min(x, axis=0), np.max(x, axis=0)
    excursions = []
    for point in z:
        outside = np.maximum(np.maximum(lo - point, point - hi), 0.0)
        excursions.append(float(np.linalg.norm(outside)) / scale)
    box = float(np.quantile(excursions, 0.95))
    domain_score = float(DOMAINS.index(domain))
    random_score = int.from_bytes(
        hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).digest()[:8], "big"
    ) / 2**64
    return {
        "support_distance": support,
        "shell_radius": shell,
        "coordinate_excursion": box,
        "domain_order": domain_score,
        "deterministic_random": random_score,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archived-result", type=Path, required=True)
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    decisions = json.loads(args.decisions.read_text())
    result = json.loads(args.result.read_text())
    archived = json.loads(args.archived_result.read_text())
    labels = {
        tuple(row["key"] + [domain]): row["scores"][domain]["single"] > 5
        for row in archived["rows"] for domain in DOMAINS
    }
    checks = []
    for row in decisions["rows"]:
        fresh = recompute(row["key"])
        for method, value in fresh.items():
            checks.append({
                "name": "score:" + "/".join(map(str, row["key"])) + ":" + method,
                "passed": bool(np.isclose(value, row["scores"][method], rtol=0, atol=1e-12)),
            })
    for method in decisions["rows"][0]["scores"]:
        ranked = sorted(decisions["rows"], key=lambda r: (-r["scores"][method], tuple(r["key"])))
        rejected = {tuple(r["key"]) for r in ranked[:16]}
        keys = [tuple(r["key"]) for r in decisions["rows"]]
        expected = {
            "auroc": pair_auc([r["scores"][method] for r in decisions["rows"]], [labels[k] for k in keys]),
            "rejected_catastrophes": sum(labels[k] for k in rejected),
            "retained_safe": sum((not y) and k not in rejected for k, y in labels.items()),
            "retained_inside": sum(k[-1] == "inside" and k not in rejected for k in labels),
        }
        for field, value in expected.items():
            observed = result["evaluations"][method][field]
            passed = np.isclose(value, observed, rtol=0, atol=1e-12) if isinstance(value, float) else value == observed
            checks.append({"name": f"aggregate:{method}:{field}", "passed": bool(passed)})
    checks.append({
        "name": "decision_sha256",
        "passed": hashlib.sha256(args.decisions.read_bytes()).hexdigest() == result["decision_sha256"],
    })
    payload = {
        "schema": "kernellum.support-distance-audit.v1",
        "checks": len(checks),
        "passed": sum(c["passed"] for c in checks),
        "failed": [c["name"] for c in checks if not c["passed"]],
        "status": "PASS" if all(c["passed"] for c in checks) else "FAIL",
    }
    payload["canonical_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
