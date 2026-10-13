#!/usr/bin/env python3
"""Label-blind factorized stability matrix on the opened PR #99 cohort."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        value = ((i + 1 + j) / 2 - 1) / max(len(values) - 1, 1)
        for k in range(i, j):
            out[order[k]] = value
        i = j
    return out


def auc(values: list[float], labels: list[bool]) -> float:
    order_ranks = ranks(values)
    # ranks() is zero based and normalized; pairwise definition avoids conversion mistakes.
    pos = [values[i] for i, y in enumerate(labels) if y]
    neg = [values[i] for i, y in enumerate(labels) if not y]
    return sum((a > b) + 0.5 * (a == b) for a in pos for b in neg) / (len(pos) * len(neg))


def load_candidate_models() -> dict[tuple, list[dict]]:
    path = ROOT / "results/additive_response/confirmation/traces.jsonl.gz"
    result = {}
    with gzip.open(path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if (row["method"] == "exponential_only" and row["domain"] == "inside"
                    and row["function"] in {"gaussian_4d", "negative_gaussian_4d"}):
                result[(row["function"], row["seed"], float(row["noise"]))] = row["models"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unlabeled", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    scalar_path = ROOT / "results/fold_basin_scores_unlabeled.json"
    records_path = ROOT / "results/additive_response/independent_replication_full/records.json"
    trace_path = ROOT / "results/additive_response/confirmation/traces.jsonl.gz"
    scalar = json.loads(scalar_path.read_text())["scores"]
    candidate_models = load_candidate_models()
    scalar.sort(key=lambda r: (r["function"], r["seed"], r["noise"]))

    by_pair = {}
    for row in scalar:
        by_pair.setdefault((row["seed"], row["noise"]), []).append(row)

    matrix = []
    for row in scalar:
        key = (row["function"], row["seed"], float(row["noise"]))
        # The immutable trace schema retains the selected model only. Use its
        # normalized exact-LOO burden; do not silently reconstruct unavailable
        # runner-up margins after labels are known.
        if len(candidate_models[key]) != 1:
            raise ValueError(f"expected one retained selected model for {key}")
        selected_cv = float(candidate_models[key][0]["original_cv"])
        pair = by_pair[(row["seed"], row["noise"])]
        if len(pair) != 2:
            raise ValueError(f"expected signed pair for {key}")
        pair_scores = [math.log10(1.0 + float(item["score"])) for item in pair]
        matrix.append({
            "function": row["function"], "seed": row["seed"], "noise": row["noise"],
            "within_prediction_dispersion": float(row["score"]),
            "within_objective_dispersion": float(row["max_objective_spread"]),
            "signed_pair_asymmetry": abs(pair_scores[0] - pair_scores[1]),
            "selected_model_cv_burden": math.log10(1.0 + max(selected_cv, 0.0)),
        })

    names = ["within_prediction_dispersion", "within_objective_dispersion",
             "signed_pair_asymmetry", "selected_model_cv_burden"]
    percentiles = {name: ranks([row[name] for row in matrix]) for name in names}
    for index, row in enumerate(matrix):
        row["component_percentiles"] = {name: percentiles[name][index] for name in names}
        # Frozen equal-weight L4 upper-tail norm: no learned weights and no labels.
        row["score"] = (sum(percentiles[name][index] ** 4 for name in names) / len(names)) ** 0.25

    unlabeled = {"schema": "kernellum.selection-stability-matrix.v1", "rows": matrix}
    raw = json.dumps(unlabeled, sort_keys=True, indent=2, allow_nan=False) + "\n"
    args.unlabeled.write_text(raw)
    unlabeled_sha = hashlib.sha256(raw.encode()).hexdigest()

    independent = json.loads(records_path.read_text())
    labels = {(r["function"], r["seed"], float(r["noise"])): not r["winner_agrees"] for r in independent}
    y = [labels[(r["function"], r["seed"], float(r["noise"]))] for r in matrix]
    scores = [r["score"] for r in matrix]
    top = sorted(range(len(matrix)), key=lambda i: scores[i], reverse=True)[:10]
    positive_scores = [score for score, label in zip(scores, y) if label]
    cover_threshold = min(positive_scores)
    false_positive_rate = sum(score >= cover_threshold and not label for score, label in zip(scores, y)) / sum(not z for z in y)
    ablations = {}
    for omitted in names:
        values = [(sum(percentiles[name][i] ** 4 for name in names if name != omitted) / 3) ** 0.25
                  for i in range(len(matrix))]
        ablations[omitted] = {"auc": auc(values, y),
                              "top10_recall": sum(y[i] for i in sorted(range(len(matrix)), key=lambda j: values[j], reverse=True)[:10]) / sum(y)}
    metrics = {"paths": len(matrix), "positives": sum(y), "auc": auc(scores, y),
               "top10_recall": sum(y[i] for i in top) / sum(y),
               "false_positive_rate_at_full_recall": false_positive_rate,
               "cover_threshold": cover_threshold, "ablations": ablations}
    gates = {"auc_090": metrics["auc"] >= 0.90, "top10_all": metrics["top10_recall"] == 1.0,
             "fpr_le_025": false_positive_rate <= 0.25}
    for row, label in zip(matrix, y):
        row["solver_dependent_label"] = label
    payload = {"schema": "kernellum.selection-stability-matrix-result.v1",
               "classification": "OPENED_DEVELOPMENT", "status": "PASS" if all(gates.values()) else "FAIL",
               "metrics": metrics, "gates": gates, "rows": matrix,
               "unlabeled_matrix_sha256": unlabeled_sha,
               "inputs": {"scalar_sha256": hashlib.sha256(scalar_path.read_bytes()).hexdigest(),
                          "records_sha256": hashlib.sha256(records_path.read_bytes()).hexdigest(),
                          "traces_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest()}}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload["canonical_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": payload["status"], "metrics": metrics, "gates": gates,
                      "canonical_sha256": payload["canonical_sha256"],
                      "unlabeled_matrix_sha256": unlabeled_sha}, indent=2))


if __name__ == "__main__":
    main()
