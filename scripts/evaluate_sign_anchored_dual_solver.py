#!/usr/bin/env python3
"""Evaluate an opened-development dual-solver arbitration rule.

The decision table is materialized and hashed before persisted test metrics are
read. This does not convert opened evidence into confirmation; it only makes
the mechanism probe auditable and prevents accidental truth-conditioned
selection inside this execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


FLOOR = math.log(1e-8)
DOMAINS = ("inside", "near_shell", "far_shell")


def canonical_sha(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def geometric(values: list[float]) -> float:
    return math.exp(sum(values) / len(values))


def median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def choose(row: dict) -> tuple[str, str]:
    candidate = row["candidate_winner"]
    independent = row["winner"]
    if int(candidate["sign"]) != int(independent["sign"]):
        return "candidate", "sign_disagreement_anchor"
    if float(independent["cv"]) < float(candidate["cv"]):
        return "independent", "same_sign_lower_cv"
    return "candidate", "same_sign_lower_cv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = json.loads(args.records.read_text())
    keys = [(row["function"], row["seed"], float(row["noise"])) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate path keys")
    if any("winner" not in row for row in rows):
        raise ValueError("incomplete independent replication")

    decisions = []
    for row in rows:
        selected, reason = choose(row)
        decisions.append({
            "function": row["function"],
            "seed": row["seed"],
            "noise": float(row["noise"]),
            "candidate_family": row["candidate_winner"]["family"],
            "candidate_sign": int(row["candidate_winner"]["sign"]),
            "candidate_cv": float(row["candidate_winner"]["cv"]),
            "independent_family": row["winner"]["family"],
            "independent_sign": int(row["winner"]["sign"]),
            "independent_cv": float(row["winner"]["cv"]),
            "selected": selected,
            "reason": reason,
            "model_agreement": bool(row["winner_agrees"]),
        })
    decision_payload = {
        "schema": "kernellum.sign-anchored-dual-solver-decisions.v1",
        "classification": "OPENED_DEVELOPMENT_POST_HOC",
        "rule": "candidate_on_sign_disagreement_else_lower_exact_loo_cv",
        "decisions": decisions,
    }
    args.decisions.write_text(json.dumps(decision_payload, indent=2, sort_keys=True) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    by_key = {key: row for key, row in zip(keys, rows)}
    metrics = {}
    for domain in DOMAINS:
        values = {"candidate": [], "independent": [], "control": []}
        for decision in decisions:
            key = (decision["function"], decision["seed"], decision["noise"])
            scores = by_key[key]["scores"][domain]
            candidate = max(float(scores["candidate_log_nmse"]), FLOOR)
            independent = max(float(scores["independent_log_nmse"]), FLOOR)
            control = independent if decision["selected"] == "independent" else candidate
            values["candidate"].append(candidate)
            values["independent"].append(independent)
            values["control"].append(control)
        metrics[domain] = {
            "geometric_nmse": {name: geometric(series) for name, series in values.items()},
            "median_log_nmse": {name: median(series) for name, series in values.items()},
            "catastrophic_log_nmse_gt_5": {
                name: sum(value > 5.0 for value in series) for name, series in values.items()
            },
            "control_better_than_candidate": sum(
                control < candidate - 1e-12
                for control, candidate in zip(values["control"], values["candidate"])
            ),
            "control_worse_than_candidate": sum(
                control > candidate + 1e-12
                for control, candidate in zip(values["control"], values["candidate"])
            ),
        }

    disagreement_rows = []
    for decision in decisions:
        if decision["model_agreement"]:
            continue
        key = (decision["function"], decision["seed"], decision["noise"])
        row = by_key[key]
        comparison = {}
        for domain in DOMAINS:
            scores = row["scores"][domain]
            comparison[domain] = {
                "candidate_log_nmse": float(scores["candidate_log_nmse"]),
                "independent_log_nmse": float(scores["independent_log_nmse"]),
            }
        disagreement_rows.append({**decision, "test_metrics": comparison})

    payload = {
        "schema": "kernellum.sign-anchored-dual-solver-result.v1",
        "classification": "OPENED_DEVELOPMENT_POST_HOC",
        "claim_status": "FOOTHOLD_NOT_CONFIRMATION",
        "records_sha256": hashlib.sha256(args.records.read_bytes()).hexdigest(),
        "decision_table_sha256": decision_sha,
        "paths": len(rows),
        "choice_counts": {
            "candidate": sum(row["selected"] == "candidate" for row in decisions),
            "independent": sum(row["selected"] == "independent" for row in decisions),
        },
        "known_model_disagreements": disagreement_rows,
        "metrics": metrics,
    }
    payload["canonical_sha256"] = canonical_sha(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
