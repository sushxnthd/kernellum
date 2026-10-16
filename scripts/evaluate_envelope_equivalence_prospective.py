#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kernellum.discovery.solver_equivalence import certify_prediction_envelope
from evaluate_sign_anchor_shifted import (
    DOMAINS,
    cfit,
    geomean_log,
    independent_fit,
    log_nmse,
    maximin,
    predict,
    shell,
)

SHAPES = ("anisotropic_laplace", "rational_ridge")
DIMS = (2, 4)
SEEDS = (4101, 4103)
NOISES = ("contaminated_gaussian", "multiplicative_lognormal")


def canonical(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def dataset(shape, dimension, seed, noise):
    offset = (
        seed + 100 * dimension
        + (0 if shape == SHAPES[0] else 10000)
        + (0 if noise == NOISES[0] else 20000)
    )
    rng = np.random.default_rng(offset)
    center = rng.uniform(-0.35, 0.35, dimension)
    q = np.linalg.qr(rng.normal(size=(dimension, dimension)))[0]
    curvature = (q * rng.uniform(0.6, 5.0, dimension)) @ q.T
    direction = rng.normal(size=dimension)
    direction /= max(float(np.linalg.norm(direction)), 1e-12)
    sign = 1.0 if seed == SEEDS[0] else -1.0

    def truth(z):
        u = z - center
        quad = np.einsum("ni,ij,nj->n", u, curvature, u)
        ridge = z @ direction
        if shape == "anisotropic_laplace":
            base = np.exp(-np.sqrt(np.maximum(quad, 0.0) + 1e-6))
            base *= 1.0 + 0.18 * np.sin(2.2 * ridge)
        else:
            base = (1.0 + quad) ** -1.35
            base *= 1.0 + 0.22 * np.tanh(1.8 * ridge)
        return sign * base

    pool = rng.uniform(-1.0, 1.0, (160, dimension))
    ids = maximin(pool, 24)
    clean = truth(pool[ids])
    scale = max(float(np.std(clean)), 1e-12)
    if noise == "contaminated_gaussian":
        eps = rng.normal(size=24)
        contaminated = rng.random(24) < 0.125
        eps[contaminated] += rng.normal(0.0, 5.0, int(np.sum(contaminated)))
        observed = clean + 0.30 * scale * eps
    else:
        multiplier = np.exp(0.45 * rng.normal(size=24) - 0.5 * 0.45**2)
        observed = clean * (1.0 + 0.35 * (multiplier - 1.0))
        observed += 0.05 * scale * rng.normal(size=24)
    tests = {
        "inside": rng.uniform(-1.0, 1.0, (256, dimension)),
        "near_shell": shell(rng, 256, dimension, 1.0, 1.6),
        "far_shell": shell(rng, 256, dimension, 1.6, 3.2),
    }
    return pool[ids], observed, {key: (z, truth(z)) for key, z in tests.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    fitted = []
    for shape in SHAPES:
        for dimension in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, dimension, seed, noise)
                    candidate_bank, independent_bank, failures = [], [], []
                    for sign in (1, -1):
                        for family in ("exp_affine", "exp_concave"):
                            for bank, fn in (
                                ("candidate", lambda: cfit(x, y, sign, family)),
                                ("independent", lambda: independent_fit(x, y, sign, family)),
                            ):
                                try:
                                    model = fn()
                                    model["kind"] = bank
                                    (candidate_bank if bank == "candidate" else independent_bank).append(model)
                                except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                                    failures.append({
                                        "bank": bank, "sign": sign, "family": family,
                                        "reason": str(exc),
                                    })
                    if not candidate_bank or not independent_bank:
                        raise RuntimeError(f"empty bank for {shape} {dimension} {seed} {noise}: {failures}")
                    candidate = min(candidate_bank, key=lambda row: row["cv"])
                    independent = min(independent_bank, key=lambda row: row["cv"])
                    request_inputs = np.concatenate([tests[d][0] for d in DOMAINS], axis=0)
                    candidate_prediction = predict(candidate, request_inputs)
                    independent_prediction = predict(independent, request_inputs)
                    y_scale = max(float(np.std(y)), 1e-12)
                    receipt = certify_prediction_envelope(
                        candidate_prediction,
                        independent_prediction,
                        y_scale=y_scale,
                        candidate_cv=candidate["cv"],
                        independent_cv=independent["cv"],
                    )
                    selected = (
                        independent if receipt.selected_solver == "independent" else candidate
                    )
                    fitted.append({
                        "key": [shape, dimension, seed, noise],
                        "candidate": candidate,
                        "independent": independent,
                        "selected": selected,
                        "receipt": receipt,
                        "candidate_prediction": candidate_prediction,
                        "independent_prediction": independent_prediction,
                        "y_scale": y_scale,
                        "tests": tests,
                        "failures": failures,
                    })
                    print(shape, dimension, seed, noise, "accepted", receipt.accepted, flush=True)

    decisions = {
        "schema": "kernellum.envelope-equivalence-decisions.v1",
        "classification": "PROSPECTIVE_SHIFTED",
        "thresholds": {"rms": 0.5, "maximum": 4.0},
        "rows": [{
            "key": row["key"],
            "candidate": {k: row["candidate"][k] for k in ("sign", "family", "cv")},
            "independent": {k: row["independent"][k] for k in ("sign", "family", "cv")},
            "y_scale": row["y_scale"],
            "normalized_delta_count": int(row["candidate_prediction"].size),
            "normalized_delta_sum_squares": float(np.sum(
                ((row["candidate_prediction"] - row["independent_prediction"]) / row["y_scale"]) ** 2
            )),
            "normalized_delta_max": float(np.max(np.abs(
                (row["candidate_prediction"] - row["independent_prediction"]) / row["y_scale"]
            ))),
            "accepted": row["receipt"].accepted,
            "selected_solver": row["receipt"].selected_solver,
            "prediction_rms": row["receipt"].prediction_rms,
            "prediction_max": row["receipt"].prediction_max,
            "scope": row["receipt"].scope,
            "failed_model_attempts": row["failures"],
        } for row in fitted],
    }
    args.decisions.write_text(json.dumps(decisions, indent=2, sort_keys=True, allow_nan=False) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    records = []
    for row in fitted:
        scores = {}
        for domain, (z, truth) in row["tests"].items():
            scores[domain] = {
                "candidate": log_nmse(predict(row["candidate"], z), truth),
                "independent": log_nmse(predict(row["independent"], z), truth),
                "selected": log_nmse(predict(row["selected"], z), truth),
            }
        harmful = (
            row["receipt"].selected_solver == "independent"
            and any(scores[d]["independent"] - scores[d]["candidate"] > math.log(10.0) for d in DOMAINS)
        )
        records.append({
            "key": row["key"],
            "accepted": row["receipt"].accepted,
            "selected_solver": row["receipt"].selected_solver,
            "harmful_switch": harmful,
            "scores": scores,
        })

    accepted = [row for row in records if row["accepted"]]
    harmful = [row for row in records if row["harmful_switch"]]
    ratios = {}
    for domain in DOMAINS:
        ratios[domain] = (
            geomean_log([row["scores"][domain]["selected"] for row in accepted])
            / geomean_log([row["scores"][domain]["candidate"] for row in accepted])
            if accepted else None
        )
    gates = {
        "complete": len(records) == 16,
        "two_harmful_opportunities": len(harmful) >= 2,
        "all_harmful_switches_rejected": bool(harmful) and all(not row["accepted"] for row in harmful),
        "coverage": len(accepted) >= 8,
        "accepted_pointwise_noninferior": bool(accepted) and all(
            row["scores"][domain]["selected"] - row["scores"][domain]["candidate"] <= math.log(2.0)
            for row in accepted for domain in DOMAINS
        ),
        "accepted_aggregate_noninferior": bool(accepted) and all(value <= 1.10 for value in ratios.values()),
    }
    payload = {
        "schema": "kernellum.envelope-equivalence-result.v1",
        "classification": "PROSPECTIVE_SHIFTED",
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "decision_sha256": decision_sha,
        "paths": len(records),
        "accepted": len(accepted),
        "harmful_switches": len(harmful),
        "harmful_switches_rejected": sum(not row["accepted"] for row in harmful),
        "ratios": ratios,
        "gates": gates,
        "records": records,
        "status": "PASS" if all(gates.values()) else "FAIL",
    }
    payload["canonical_sha256"] = canonical(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in (
        "status", "canonical_sha256", "accepted", "harmful_switches",
        "harmful_switches_rejected", "ratios", "gates",
    )}, indent=2))


if __name__ == "__main__":
    main()
