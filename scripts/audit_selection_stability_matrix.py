#!/usr/bin/env python3
"""Independent audit for the frozen selection-stability matrix result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def pairwise_auc(scores: list[float], labels: list[bool]) -> float:
    positive = [score for score, label in zip(scores, labels) if label]
    negative = [score for score, label in zip(scores, labels) if not label]
    wins = 0.0
    for pos in positive:
        for neg in negative:
            wins += float(pos > neg) + 0.5 * float(pos == neg)
    return wins / (len(positive) * len(negative))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.result.read_text())
    rows = payload["rows"]
    scores = [float(row["score"]) for row in rows]
    labels = [bool(row["solver_dependent_label"]) for row in rows]
    positives = sum(labels)

    ranked = sorted(zip(scores, labels), reverse=True)
    top10_recall = sum(label for _, label in ranked[:10]) / positives
    cover_threshold = min(score for score, label in ranked if label)
    negatives = len(labels) - positives
    false_positives = sum((not label) and score >= cover_threshold for score, label in ranked)
    fpr = false_positives / negatives
    auc = pairwise_auc(scores, labels)

    canonical = dict(payload)
    recorded_digest = canonical.pop("canonical_sha256")
    encoded = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    computed_digest = hashlib.sha256(encoded).hexdigest()

    gates = {
        "auc_090": auc >= 0.90,
        "top10_all": top10_recall == 1.0,
        "fpr_le_025": fpr <= 0.25,
    }
    checks = {
        "auc_matches": abs(auc - payload["metrics"]["auc"]) < 1e-12,
        "top10_recall_matches": abs(top10_recall - payload["metrics"]["top10_recall"]) < 1e-12,
        "fpr_matches": abs(fpr - payload["metrics"]["false_positive_rate_at_full_recall"]) < 1e-12,
        "cover_threshold_matches": abs(cover_threshold - payload["metrics"]["cover_threshold"]) < 1e-12,
        "gates_match": gates == payload["gates"],
        "status_matches": payload["status"] == ("PASS" if all(gates.values()) else "FAIL"),
        "canonical_sha256_matches": computed_digest == recorded_digest,
    }
    audit = {
        "schema": "kernellum.selection_stability_matrix.audit.v1",
        "implementation": "independent_pairwise_audit",
        "metrics": {
            "paths": len(rows),
            "positives": positives,
            "auc": auc,
            "top10_recall": top10_recall,
            "cover_threshold": cover_threshold,
            "false_positive_rate_at_full_recall": fpr,
        },
        "gates": gates,
        "recorded_canonical_sha256": recorded_digest,
        "computed_canonical_sha256": computed_digest,
        "checks": checks,
        "audit_status": "PASS" if all(checks.values()) else "FAIL",
    }
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
