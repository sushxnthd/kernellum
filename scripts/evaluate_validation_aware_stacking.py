#!/usr/bin/env python3
"""Frozen prospective evaluation of conservative validation-aware stacking."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy

from evaluate_sign_anchor_shifted import (
    DOMAINS,
    canon,
    cfit,
    geomean_log,
    gfit,
    independent_fit,
    log_nmse,
    maximin,
    predict,
    shell,
)

FAMILIES = ("damped_chirp", "rotated_student", "asymmetric_ridge")
DIMS = (6, 10)
SEEDS = (12011, 12017)
NOISES = ("symmetric_t", "leverage_spikes")
METHODS = ("candidate", "globalized", "independent")
GRID_STEP = 0.1
CANDIDATE_FLOOR = 0.5
FOLDS = 4


def canonical(obj):
    return json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"


def dataset(family, dimension, seed, noise):
    family_offset = {
        "damped_chirp": 71000,
        "rotated_student": 97000,
        "asymmetric_ridge": 131000,
    }[family]
    offset = seed + 107 * dimension + family_offset + (0 if noise == NOISES[0] else 59000)
    rng = np.random.default_rng(offset)
    center = rng.uniform(-0.28, 0.28, dimension)
    q = np.linalg.qr(rng.normal(size=(dimension, dimension)))[0]
    curvature = (q * rng.uniform(0.35, 5.8, dimension)) @ q.T
    direction = rng.normal(size=dimension)
    direction /= max(float(np.linalg.norm(direction)), 1e-12)
    direction2 = rng.normal(size=dimension)
    direction2 -= direction * float(direction @ direction2)
    direction2 /= max(float(np.linalg.norm(direction2)), 1e-12)
    sign = 1.0 if seed == SEEDS[0] else -1.0

    def truth(z):
        u = z - center
        quad = np.einsum("ni,ij,nj->n", u, curvature, u)
        r1, r2 = z @ direction, z @ direction2
        if family == "damped_chirp":
            radius = np.sqrt(np.maximum(quad, 0.0) + 1e-10)
            base = np.exp(-0.62 * radius) * (1.0 + 0.20 * np.sin(2.2 * r1 + 0.85 * radius))
        elif family == "rotated_student":
            base = (1.0 + 0.48 * quad) ** -1.42
            base *= 1.0 + 0.17 * np.tanh(1.8 * r1) * np.cos(2.7 * r2)
        else:
            skew = np.maximum(r1, 0.0) ** 2 + 0.28 * np.maximum(-r1, 0.0)
            base = np.exp(-0.73 * np.sqrt(np.maximum(quad + 0.55 * skew, 0.0) + 1e-10))
            base *= 1.0 + 0.14 * np.sin(3.6 * r2)
        return sign * base

    pool = rng.uniform(-1, 1, (280, dimension))
    x = pool[maximin(pool, 32)]
    clean = truth(x)
    scale = max(float(np.std(clean)), 1e-12)
    if noise == NOISES[0]:
        y = clean + scale * 0.20 * rng.standard_t(6, size=len(x)) / math.sqrt(1.5)
    else:
        eps = 0.08 * rng.normal(size=len(x))
        idx = np.argsort(np.linalg.norm(x, axis=1))[-5:]
        eps[idx] += rng.normal(0.36, 0.09, size=5) * np.sign(x[idx, 0] + 0.01)
        y = clean + scale * eps
    requests = {
        "inside": rng.uniform(-1, 1, (256, dimension)),
        "near_shell": shell(rng, 256, dimension, 1, 1.6),
        "far_shell": shell(rng, 256, dimension, 1.6, 3.2),
    }
    return x, y, requests, truth, offset


def best_fit(x, y, name, fitter):
    bank, failures = [], []
    for sign in (1, -1):
        for family in ("exp_affine", "exp_concave"):
            try:
                model = fitter(x, y, sign, family)
                model["kind"] = name
                bank.append(model)
            except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                failures.append({"kind": name, "sign": sign, "family": family, "reason": str(exc)})
    if not bank:
        raise RuntimeError(f"empty {name} fit bank")
    return min(bank, key=lambda m: (m["cv"], m["sign"], m["family"])), failures


def fit_three(x, y):
    specs = (("candidate", cfit), ("globalized", gfit), ("independent", independent_fit))
    models, failures = {}, []
    for name, fitter in specs:
        models[name], ff = best_fit(x, y, name, fitter)
        failures.extend(ff)
    return models, failures


def simplex_grid():
    units = int(round(1 / GRID_STEP))
    floor = int(round(CANDIDATE_FLOOR / GRID_STEP))
    return [(a / units, b / units, (units - a - b) / units)
            for a in range(floor, units + 1)
            for b in range(units - a + 1)]


def validation_plan(x, y):
    oof = {name: np.empty(len(y), dtype=float) for name in METHODS}
    failures = []
    for fold in range(FOLDS):
        valid = np.arange(len(y)) % FOLDS == fold
        models, ff = fit_three(x[~valid], y[~valid])
        failures.extend(ff)
        for name in METHODS:
            oof[name][valid] = predict(models[name], x[valid])
    fold_den = []
    for fold in range(FOLDS):
        valid = np.arange(len(y)) % FOLDS == fold
        fold_den.append(max(float(np.mean((y[valid] - np.mean(y[valid])) ** 2)), 1e-12))

    def risks(weights):
        pred = sum(w * oof[name] for w, name in zip(weights, METHODS))
        values = []
        for fold in range(FOLDS):
            valid = np.arange(len(y)) % FOLDS == fold
            values.append(float(np.mean((pred[valid] - y[valid]) ** 2) / fold_den[fold]))
        return values

    scored = []
    for weights in simplex_grid():
        fold_risk = risks(weights)
        key = (max(fold_risk), float(np.mean(fold_risk)), 1 - weights[0], weights[1], weights[2])
        scored.append((key, weights, fold_risk))
    _, weights, fold_risk = min(scored, key=lambda row: row[0])
    hard = min(METHODS, key=lambda name: (
        max(risks(tuple(float(m == name) for m in METHODS))),
        float(np.mean(risks(tuple(float(m == name) for m in METHODS)))),
        METHODS.index(name),
    ))
    return {
        "weights": list(weights),
        "fold_nmse": fold_risk,
        "hard_method": hard,
        "hard_fold_nmse": risks(tuple(float(m == hard) for m in METHODS)),
        "oof_sha256": hashlib.sha256(np.column_stack([oof[n] for n in METHODS]).tobytes()).hexdigest(),
    }, failures


def rms_disagreement(predictions, scale):
    values = []
    for a, b in itertools.combinations(predictions, 2):
        values.append(float(np.sqrt(np.mean(((a - b) / scale) ** 2))))
    return max(values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rows = []
    for family in FAMILIES:
        for dim in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, requests, truth, _ = dataset(family, dim, seed, noise)
                    plan, failures = validation_plan(x, y)
                    models, ff = fit_three(x, y)
                    failures.extend(ff)
                    naive = min(models.values(), key=lambda m: (m["cv"], METHODS.index(m["kind"])))
                    all_z = np.concatenate([requests[d] for d in DOMAINS])
                    full_pred = {name: predict(models[name], all_z) for name in METHODS}
                    disagreement = rms_disagreement(list(full_pred.values()), max(float(np.std(y)), 1e-12))
                    noncandidate = 1.0 - plan["weights"][0]
                    active = noncandidate >= 0.2 - 1e-12 and disagreement > 0.10
                    rows.append({
                        "key": [family, dim, seed, noise],
                        "requests": requests,
                        "truth": truth,
                        "models": models,
                        "naive": naive,
                        "plan": plan,
                        "disagreement": disagreement,
                        "active": active,
                        "failures": failures,
                    })
                    print(family, dim, seed, noise, "weights", plan["weights"],
                          "disagreement", disagreement, "active", active, flush=True)

    decisions = {
        "schema": "kernellum.validation-aware-stacking-decisions.v1",
        "classification": "PROSPECTIVE_UNSEEN_SYNTHETIC_FAMILIES",
        "cohort": {"families": list(FAMILIES), "dimensions": list(DIMS), "seeds": list(SEEDS), "noises": list(NOISES)},
        "mechanism": {"folds": FOLDS, "grid_step": GRID_STEP, "candidate_weight_floor": CANDIDATE_FLOOR,
                      "active_non_candidate_weight": 0.2, "active_disagreement": 0.10},
        "rows": [{
            "key": r["key"], "weights": r["plan"]["weights"], "fold_nmse": r["plan"]["fold_nmse"],
            "hard_method": r["plan"]["hard_method"], "hard_fold_nmse": r["plan"]["hard_fold_nmse"],
            "oof_sha256": r["plan"]["oof_sha256"], "request_disagreement": r["disagreement"],
            "predicted_active": r["active"], "failed_attempts": r["failures"],
        } for r in rows],
    }
    args.decisions.write_text(canonical(decisions))
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    records = []
    for r in rows:
        scores = {}
        weights = r["plan"]["weights"]
        for domain, z in r["requests"].items():
            target = r["truth"](z)
            preds = {name: predict(r["models"][name], z) for name in METHODS}
            derived = {
                "naive": predict(r["naive"], z),
                "equal_average": sum(preds.values()) / 3,
                "hard_validation": preds[r["plan"]["hard_method"]],
                "stack": sum(w * preds[name] for w, name in zip(weights, METHODS)),
            }
            scores[domain] = {name: log_nmse(pred, target) for name, pred in {**preds, **derived}.items()}
        records.append({"key": r["key"], "predicted_active": r["active"], "scores": scores})

    methods = (*METHODS, "naive", "equal_average", "hard_validation", "stack")
    metrics = {}
    for domain in DOMAINS:
        metrics[domain] = {
            "geometric_nmse": {m: geomean_log([r["scores"][domain][m] for r in records]) for m in methods},
            "catastrophic": {m: sum(r["scores"][domain][m] > 5 for r in records) for m in methods},
        }
    ratios = {
        "inside_over_candidate": metrics["inside"]["geometric_nmse"]["stack"] / metrics["inside"]["geometric_nmse"]["candidate"],
        "far_over_candidate": metrics["far_shell"]["geometric_nmse"]["stack"] / metrics["far_shell"]["geometric_nmse"]["candidate"],
        "far_over_equal_average": metrics["far_shell"]["geometric_nmse"]["stack"] / metrics["far_shell"]["geometric_nmse"]["equal_average"],
        "far_over_hard_validation": metrics["far_shell"]["geometric_nmse"]["stack"] / metrics["far_shell"]["geometric_nmse"]["hard_validation"],
    }
    active = [r for r in records if r["predicted_active"]]
    active_families = len({r["key"][0] for r in active})
    active_precision = (sum(r["scores"]["far_shell"]["stack"] < r["scores"]["far_shell"]["candidate"] for r in active) / len(active)) if active else 0.0
    candidate_cats = {d: metrics[d]["catastrophic"]["candidate"] for d in DOMAINS}
    stack_cats = {d: metrics[d]["catastrophic"]["stack"] for d in DOMAINS}
    gates = {
        "complete": len(records) == 24,
        "far_improves": ratios["far_over_candidate"] <= 0.90,
        "inside_noninferior": ratios["inside_over_candidate"] <= 1.05,
        "no_excess_catastrophe": all(stack_cats[d] <= candidate_cats[d] for d in DOMAINS),
        "halves_far_catastrophes": candidate_cats["far_shell"] >= 2 and 2 * stack_cats["far_shell"] <= candidate_cats["far_shell"],
        "beats_equal_average": ratios["far_over_equal_average"] < 1.0,
        "beats_hard_validation": ratios["far_over_hard_validation"] < 1.0,
        "four_active": len(active) >= 4,
        "two_active_families": active_families >= 2,
        "active_precision": active_precision >= 0.75,
    }
    out = {
        "schema": "kernellum.validation-aware-stacking-result.v1",
        "classification": "PROSPECTIVE_UNSEEN_SYNTHETIC_FAMILIES",
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "decision_sha256": decision_sha,
        "paths": len(records),
        "predicted_active_paths": len(active),
        "active_families": active_families,
        "active_precision": active_precision,
        "metrics": metrics,
        "ratios": ratios,
        "gates": gates,
        "records": records,
        "status": "PASS_EXTERNAL_REPLICATION_REQUIRED" if all(gates.values()) else "FAIL_KILL_OR_REFORMULATE",
        "smallest_claim": "The frozen conservative OOF stack was evaluated prospectively on 24 unseen synthetic-family paths; external-data transfer is not established.",
    }
    out["canonical_sha256"] = canon(out)
    args.output.write_text(canonical(out))
    print(json.dumps({k: out[k] for k in ("status", "canonical_sha256", "predicted_active_paths", "active_families", "active_precision", "ratios", "gates")}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
