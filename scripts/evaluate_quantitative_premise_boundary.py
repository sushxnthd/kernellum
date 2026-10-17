#!/usr/bin/env python3
"""Fixed empirical-Lipschitz screen on the already-opened shifted cohort."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from evaluate_disagreement_acquisition import fit_candidates
from evaluate_sign_anchor_shifted import DIMS, DOMAINS, NOISES, SEEDS, SHAPES, dataset, log_nmse, predict
from kernellum.discovery.quantitative_premise import (
    empirical_lipschitz_lower_bound,
    issue_lipschitz_envelope,
    lipschitz_interval,
)

MULTIPLIERS = (1, 2, 5, 10)


def exhaustive_grid_sharpness(max_n: int = 5, bound: int = 2, constant: int = 1) -> dict:
    checks = transcripts = 0
    values = range(-bound, bound + 1)
    for n in range(2, max_n + 1):
        points = np.arange(n, dtype=float)[:, None]
        functions = [v for v in itertools.product(values, repeat=n)
                     if all(abs(v[i] - v[j]) <= constant * abs(i - j)
                            for i in range(n) for j in range(n))]
        for mask_bits in range(1, (1 << n) - 1):
            observed = [i for i in range(n) if mask_bits & (1 << i)]
            missing = [i for i in range(n) if i not in observed]
            grouped: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
            for f in functions:
                grouped.setdefault(tuple(f[i] for i in observed), []).append(f)
            for observed_y, completions in grouped.items():
                for request in missing:
                    lower, upper = lipschitz_interval(
                        points[observed], np.asarray(observed_y), points[[request]], constant
                    )
                    feasible = [f[request] for f in completions]
                    expected_low = max(-bound, int(round(lower[0])))
                    expected_high = min(bound, int(round(upper[0])))
                    assert min(feasible) == expected_low and max(feasible) == expected_high
                    checks += len(completions) + 2
                    transcripts += 1
    return {"max_domain": max_n, "bounded_values": [-bound, bound],
            "constant": constant, "transcript_requests": transcripts, "checks": checks}


def opened_audit() -> list[dict]:
    rows = []
    for shape in SHAPES:
        for dimension in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, dimension, seed, noise)
                    empirical = empirical_lipschitz_lower_bound(x, y)
                    models, _ = fit_candidates(x, y)
                    winner = min(models, key=lambda model: model["cv"])
                    scale = max(float(np.std(y)), 1e-12)
                    for domain in DOMAINS:
                        request, truth = tests[domain]
                        score = log_nmse(predict(winner, request), truth)
                        metrics = {}
                        for multiplier in MULTIPLIERS:
                            lower, upper = lipschitz_interval(x, y, request, multiplier * empirical)
                            outside = (truth < lower) | (truth > upper)
                            metrics[str(multiplier)] = {
                                "outside_fraction": float(np.mean(outside)),
                                "any_outside": bool(np.any(outside)),
                                "all_outside": bool(np.all(outside)),
                                "mean_normalized_width": float(np.mean(upper - lower) / scale),
                            }
                        refusal = issue_lipschitz_envelope(
                            x, y, request,
                            {"hypothesis_class": "global_lipschitz", "request_scope": domain,
                             "constant": empirical, "source": "estimated_from_same_transcript"},
                            verifier=lambda _premise: True,
                        )
                        assert refusal["decision"] == "refuse"
                        rows.append({"key": [shape, dimension, seed, noise, domain],
                                     "empirical_constant": empirical,
                                     "catastrophic": bool(score > 5),
                                     "metrics": metrics, "runtime": refusal})
    return rows


def summarize(rows: list[dict]) -> dict:
    out = {}
    for multiplier in MULTIPLIERS:
        key = str(multiplier)
        subset_summary = {}
        for label, subset in [("all", rows), ("catastrophic", [r for r in rows if r["catastrophic"]])]:
            subset_summary[label] = {
                "cells": len(subset),
                "cells_any_outside": sum(r["metrics"][key]["any_outside"] for r in subset),
                "cells_all_outside": sum(r["metrics"][key]["all_outside"] for r in subset),
                "mean_outside_fraction": float(np.mean([r["metrics"][key]["outside_fraction"] for r in subset])),
                "mean_normalized_width": float(np.mean([r["metrics"][key]["mean_normalized_width"] for r in subset])),
            }
        subset_summary["by_domain"] = {
            domain: {
                "cells_any_outside": sum(r["metrics"][key]["any_outside"] for r in rows if r["key"][-1] == domain),
                "mean_outside_fraction": float(np.mean([r["metrics"][key]["outside_fraction"] for r in rows if r["key"][-1] == domain])),
                "mean_normalized_width": float(np.mean([r["metrics"][key]["mean_normalized_width"] for r in rows if r["key"][-1] == domain])),
            } for domain in DOMAINS
        }
        out[key] = subset_summary
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = opened_audit()
    payload = {
        "schema": "kernellum.quantitative-premise-boundary.v1",
        "classification": "EXACT_BOUNDARY_AND_OPENED_COHORT_DIAGNOSTIC",
        "protocol_commit": "08cd22be8d5da22cd7faf91298ebd6a263372d62",
        "theorem": {
            "statement": "For every finite multiplier of the transcript's empirical Lipschitz lower bound, an unrestricted completion can agree on the transcript and leave the resulting interval at an unobserved request.",
            "construction": "Keep every observed value and assign the request above the finite upper endpoint; the completion then has a larger finite Lipschitz constant on the augmented finite domain.",
        },
        "conditional_law": "Given an independently verified global L, the McShane--Whitney interval is pointwise sharp.",
        "finite_sharpness": exhaustive_grid_sharpness(),
        "opened_summary": summarize(rows),
        "runtime_empirical_refusals": sum(r["runtime"]["decision"] == "refuse" for r in rows),
        "rows": rows,
        "scientific_gate": "PASS_PIVOT_TO_EXTERNAL_QUANTITATIVE_PREMISES",
        "smallest_claim": "A transcript-derived Lipschitz constant, including any fixed inflation, is not a certificate; only an independently justified constant makes the sharp interval conditional guarantee valid.",
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload["canonical_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in ("scientific_gate", "finite_sharpness", "opened_summary", "runtime_empirical_refusals", "canonical_sha256")}, indent=2))


if __name__ == "__main__":
    main()
