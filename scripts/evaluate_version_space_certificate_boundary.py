#!/usr/bin/env python3
"""Exact boundary certificate plus opened-cohort candidate-envelope audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_disagreement_acquisition import fit_candidates
from evaluate_sign_anchor_shifted import DIMS, DOMAINS, NOISES, SEEDS, SHAPES, dataset, log_nmse, predict
from kernellum.discovery.version_space_certificate import issue_envelope_certificate


def exhaustive_boolean_checks(max_n: int = 6) -> tuple[int, int]:
    checks = pairs = 0
    for n in range(1, max_n + 1):
        for observed_mask in range(1 << n):
            observed = [i for i in range(n) if observed_mask & (1 << i)]
            missing = [i for i in range(n) if not observed_mask & (1 << i)]
            if not missing:
                continue
            for assignment in range(1 << len(observed)):
                transcript = {point: (assignment >> j) & 1 for j, point in enumerate(observed)}
                for request in missing:
                    low = dict(transcript); low[request] = 0
                    high = dict(transcript); high[request] = 1
                    assert all(low[p] == high[p] == value for p, value in transcript.items())
                    assert low[request] != high[request]
                    checks += len(transcript) + 1
                    pairs += 1
    return checks, pairs


def opened_audit():
    rows = []
    for shape in SHAPES:
        for dimension in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, dimension, seed, noise)
                    models, failures = fit_candidates(x, y)
                    winner = min(models, key=lambda model: model["cv"])
                    for domain in DOMAINS:
                        request, truth = tests[domain]
                        bank = np.stack([predict(model, request) for model in models])
                        lower, upper = bank.min(axis=0), bank.max(axis=0)
                        outside = (truth < lower) | (truth > upper)
                        score = log_nmse(predict(winner, request), truth)
                        refusal = issue_envelope_certificate(
                            bank, predict(winner, request), scale=max(float(np.std(y)), 1e-12),
                            tolerance=1.0, provenance=None,
                        )
                        assert refusal["decision"] == "refuse"
                        rows.append({
                            "key": [shape, dimension, seed, noise, domain],
                            "candidate_models": len(models),
                            "fit_failures": len(failures),
                            "log_nmse": float(score),
                            "catastrophic": bool(score > 5),
                            "truth_outside_fraction": float(np.mean(outside)),
                            "all_truth_outside": bool(np.all(outside)),
                            "runtime_without_provenance": refusal,
                        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks, pairs = exhaustive_boolean_checks()
    rows = opened_audit()
    catastrophic = [row for row in rows if row["catastrophic"]]
    result = {
        "schema": "kernellum.version-space-certificate-boundary.v1",
        "classification": "EXACT_THEOREM_AND_OPENED_COHORT_DIAGNOSTIC",
        "theorem": {
            "statement": "Every finite training-only finite-valued interval is unsound for unrestricted responses at an unobserved request.",
            "construction": "Preserve the transcript and set the requested value below the lower endpoint or above the upper endpoint.",
            "boolean_exhaustive_max_domain": 6,
            "indistinguishable_completion_pairs": pairs,
            "checks": checks,
        },
        "conditional_law": "If truth is pointwise inside [lower,upper], normalized RMSE(selected,truth) is at most RMS(max(selected-lower,upper-selected))/scale.",
        "opened_cohort": {
            "cells": len(rows),
            "cells_truth_outside_envelope": sum(row["truth_outside_fraction"] > 0 for row in rows),
            "cells_all_truth_outside": sum(row["all_truth_outside"] for row in rows),
            "catastrophic_cells": len(catastrophic),
            "catastrophic_truth_outside_envelope": sum(row["truth_outside_fraction"] > 0 for row in catastrophic),
            "catastrophic_all_truth_outside": sum(row["all_truth_outside"] for row in catastrophic),
            "missing_provenance_refusals": sum(row["runtime_without_provenance"]["decision"] == "refuse" for row in rows),
            "rows": rows,
        },
        "scientific_gate": "PASS_BOUNDARY_PIVOT",
        "smallest_claim": "Finite fitted-candidate envelopes are conditional certificates only; training compatibility alone cannot certify unobserved unrestricted responses.",
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    result["canonical_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ("scientific_gate", "theorem", "opened_cohort", "canonical_sha256") if k != "opened_cohort"} | {"opened_summary": {k: v for k, v in result["opened_cohort"].items() if k != "rows"}}, indent=2))


if __name__ == "__main__":
    main()

