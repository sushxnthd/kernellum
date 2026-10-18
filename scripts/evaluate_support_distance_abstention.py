#!/usr/bin/env python3
"""Frozen truth-blind support-distance screen on the opened shifted cohort."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from evaluate_sign_anchor_shifted import DOMAINS, NOISES, SEEDS, SHAPES, dataset


def canonical(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def auc(scores, labels):
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=bool)
    pos, neg = scores[labels], scores[~labels]
    if not len(pos) or not len(neg):
        return None
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))


def score_batch(x, z):
    xx = np.sqrt(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2))
    np.fill_diagonal(xx, np.inf)
    r_train = max(float(np.median(np.min(xx, axis=1))), 1e-12)
    zx = np.sqrt(np.sum((z[:, None, :] - x[None, :, :]) ** 2, axis=2))
    support = float(np.quantile(np.min(zx, axis=1) / r_train, 0.95))
    center = np.mean(x, axis=0)
    train_radius = max(float(np.median(np.linalg.norm(x - center, axis=1))), 1e-12)
    shell = float(np.quantile(np.linalg.norm(z - center, axis=1) / train_radius, 0.95))
    lo, hi = np.min(x, axis=0), np.max(x, axis=0)
    excursion = np.maximum(np.maximum(lo - z, z - hi), 0.0)
    box = float(np.quantile(np.linalg.norm(excursion, axis=1) / r_train, 0.95))
    return support, shell, box


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archived-result", type=Path, required=True)
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    rows = []
    domain_index = {name: i for i, name in enumerate(DOMAINS)}
    for shape in SHAPES:
        for d in (3, 5):
            for seed in SEEDS:
                for noise in NOISES:
                    x, _y, tests = dataset(shape, d, seed, noise)
                    for domain in DOMAINS:
                        z = tests[domain][0]
                        support, shell, box = score_batch(x, z)
                        key = [shape, d, seed, noise, domain]
                        random_score = int.from_bytes(
                            hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).digest()[:8],
                            "big",
                        ) / 2**64
                        rows.append({
                            "key": key,
                            "scores": {
                                "support_distance": support,
                                "shell_radius": shell,
                                "coordinate_excursion": box,
                                "domain_order": float(domain_index[domain]),
                                "deterministic_random": random_score,
                            },
                        })

    decisions = {
        "schema": "kernellum.support-distance-decisions.v1",
        "classification": "OPENED_COHORT_TRUTH_BLIND_SCORES",
        "quantile": 0.95,
        "rejection_budget": 16,
        "rows": rows,
    }
    args.decisions.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    archived = json.loads(args.archived_result.read_text())
    labels = {}
    for row in archived["rows"]:
        for domain in DOMAINS:
            labels[tuple(row["key"] + [domain])] = row["scores"][domain]["single"] > 5
    if len(labels) != 48 or sum(labels.values()) != 11:
        raise RuntimeError("archived label cardinality does not match frozen protocol")

    methods = list(rows[0]["scores"])
    evaluations = {}
    canonical_key = lambda row: tuple(row["key"])
    for method in methods:
        ranked = sorted(rows, key=lambda r: (-r["scores"][method], canonical_key(r)))
        rejected = {tuple(r["key"]) for r in ranked[:16]}
        y = [labels[tuple(r["key"])] for r in rows]
        s = [r["scores"][method] for r in rows]
        rejected_cat = sum(labels[k] for k in rejected)
        retained_safe = sum((not label) and key not in rejected for key, label in labels.items())
        retained_inside = sum(key[-1] == "inside" and key not in rejected for key in labels)
        evaluations[method] = {
            "auroc": auc(s, y),
            "rejected_catastrophes": rejected_cat,
            "retained_safe": retained_safe,
            "retained_inside": retained_inside,
            "rejected_keys": [list(r["key"]) for r in ranked[:16]],
        }

    c = evaluations["support_distance"]
    gates = {
        "complete_and_prehashed": len(rows) == 48 and bool(decision_sha),
        "auroc": c["auroc"] >= 0.80,
        "tail_rejection": c["rejected_catastrophes"] >= 8,
        "safe_retention": c["retained_safe"] >= 25,
        "inside_retention": c["retained_inside"] >= 12,
        "beats_random": c["rejected_catastrophes"] >= evaluations["deterministic_random"]["rejected_catastrophes"] + 2,
        "beats_domain_order": c["rejected_catastrophes"] >= evaluations["domain_order"]["rejected_catastrophes"] + 1,
        "beats_shell_radius": c["rejected_catastrophes"] >= evaluations["shell_radius"]["rejected_catastrophes"] + 1,
    }
    payload = {
        "schema": "kernellum.support-distance-result.v1",
        "classification": "OPENED_COHORT_DEVELOPMENT",
        "decision_sha256": decision_sha,
        "cells": 48,
        "catastrophic_cells": 11,
        "accepted_cells": 32,
        "evaluations": evaluations,
        "gates": gates,
        "status": "ADVANCE_TO_PROSPECTIVE" if all(gates.values()) else "KILL_FIXED_SUPPORT_DISTANCE",
    }
    payload["canonical_sha256"] = canonical(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": payload["status"],
        "canonical_sha256": payload["canonical_sha256"],
        "decision_sha256": decision_sha,
        "evaluations": {m: {k: v[k] for k in ("auroc", "rejected_catastrophes", "retained_safe", "retained_inside")} for m, v in evaluations.items()},
        "gates": gates,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
