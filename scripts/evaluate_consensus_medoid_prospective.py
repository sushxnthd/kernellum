#!/usr/bin/env python3
"""Frozen prospective evaluation of a three-solver consensus-medoid selector."""
from __future__ import annotations

import argparse
import hashlib
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

FAMILIES = ("oscillatory_cauchy", "tilted_matern")
DIMS = (2, 6)
SEEDS = (5201, 5207)
NOISES = ("asymmetric_contamination", "variance_ramp")
RMS_BAND = 0.5
MAX_BAND = 4.0


def dataset(family, dimension, seed, noise):
    offset = seed + 101 * dimension + (0 if family == FAMILIES[0] else 17000) + (0 if noise == NOISES[0] else 29000)
    rng = np.random.default_rng(offset)
    center = rng.uniform(-0.3, 0.3, dimension)
    q = np.linalg.qr(rng.normal(size=(dimension, dimension)))[0]
    curvature = (q * rng.uniform(0.5, 4.5, dimension)) @ q.T
    direction = rng.normal(size=dimension)
    direction /= max(float(np.linalg.norm(direction)), 1e-12)
    sign = 1.0 if seed == SEEDS[0] else -1.0

    def truth(z):
        u = z - center
        quad = np.einsum("ni,ij,nj->n", u, curvature, u)
        ridge = z @ direction
        if family == "oscillatory_cauchy":
            base = (1.0 + quad) ** -1.15
            base *= 1.0 + 0.28 * np.sin(2.7 * ridge)
        else:
            radius = np.sqrt(np.maximum(quad, 0.0) + 1e-8)
            base = (1.0 + 1.7 * radius) * np.exp(-1.7 * radius)
            base *= 1.0 + 0.20 * np.tanh(2.0 * ridge)
        return sign * base

    pool = rng.uniform(-1.0, 1.0, (192, dimension))
    ids = maximin(pool, 24)
    x = pool[ids]
    clean = truth(x)
    scale = max(float(np.std(clean)), 1e-12)
    if noise == "asymmetric_contamination":
        eps = rng.normal(0.0, 0.18, 24)
        mask = rng.random(24) < 0.17
        eps[mask] += rng.lognormal(mean=0.0, sigma=0.8, size=int(np.sum(mask)))
        y = clean + scale * eps
    else:
        ramp = 0.08 + 0.28 * (x[:, 0] + 1.0) / 2.0
        y = clean + scale * ramp * rng.standard_t(4, size=24) / math.sqrt(2.0)
    requests = {
        "inside": rng.uniform(-1.0, 1.0, (256, dimension)),
        "near_shell": shell(rng, 256, dimension, 1.0, 1.6),
        "far_shell": shell(rng, 256, dimension, 1.6, 3.2),
    }
    return x, y, requests, truth


def edge(a, b, requests, y_scale):
    z = np.concatenate([requests[d] for d in DOMAINS], axis=0)
    delta = (predict(a, z) - predict(b, z)) / y_scale
    rms = float(np.sqrt(np.mean(delta * delta)))
    maximum = float(np.max(np.abs(delta)))
    return {"rms": rms, "maximum": maximum, "admissible": rms <= RMS_BAND and maximum <= MAX_BAND}


def choose(candidate, independent, globalized, requests, y_scale):
    edges = {
        "candidate_independent": edge(candidate, independent, requests, y_scale),
        "candidate_globalized": edge(candidate, globalized, requests, y_scale),
        "independent_globalized": edge(independent, globalized, requests, y_scale),
    }
    order = sorted(edges, key=lambda key: (edges[key]["rms"], key))
    unique_ig_min = order[0] == "independent_globalized" and edges[order[0]]["rms"] + 1e-12 < edges[order[1]]["rms"]
    override = (
        unique_ig_min
        and edges["independent_globalized"]["admissible"]
        and not edges["candidate_independent"]["admissible"]
        and not edges["candidate_globalized"]["admissible"]
    )
    if override:
        selected = independent if independent["cv"] <= globalized["cv"] else globalized
    else:
        selected = candidate
    margin = min(edges["candidate_independent"]["rms"], edges["candidate_globalized"]["rms"]) - edges["independent_globalized"]["rms"]
    return selected, override, margin, edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    fitted = []
    for family in FAMILIES:
        for dimension in DIMS:
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, requests, truth = dataset(family, dimension, seed, noise)
                    banks = {"candidate": [], "independent": [], "globalized": []}
                    failures = []
                    for sign in (1, -1):
                        for model_family in ("exp_affine", "exp_concave"):
                            attempts = (
                                ("candidate", lambda: cfit(x, y, sign, model_family)),
                                ("independent", lambda: independent_fit(x, y, sign, model_family)),
                                ("globalized", lambda: gfit(x, y, sign, model_family)),
                            )
                            for bank, fn in attempts:
                                try:
                                    model = fn()
                                    model["kind"] = bank
                                    banks[bank].append(model)
                                except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                                    failures.append({"bank": bank, "sign": sign, "family": model_family, "reason": str(exc)})
                    if any(not banks[name] for name in banks):
                        raise RuntimeError(f"empty bank for {family} {dimension} {seed} {noise}: {failures}")
                    c = min(banks["candidate"], key=lambda row: row["cv"])
                    i = min(banks["independent"], key=lambda row: row["cv"])
                    g = min(banks["globalized"], key=lambda row: row["cv"])
                    selected, override, margin, edges = choose(c, i, g, requests, max(float(np.std(y)), 1e-12))
                    naive = min((c, i, g), key=lambda row: row["cv"])
                    fitted.append({
                        "key": [family, dimension, seed, noise],
                        "candidate": c, "independent": i, "globalized": g,
                        "selected": selected, "naive": naive, "override": override,
                        "margin": margin, "edges": edges, "requests": requests,
                        "truth": truth, "failures": failures,
                    })
                    print(family, dimension, seed, noise, "override", override, "margin", margin, flush=True)

    decisions = {
        "schema": "kernellum.consensus-medoid-decisions.v1",
        "classification": "PROSPECTIVE_UNSEEN",
        "thresholds": {"rms": RMS_BAND, "maximum": MAX_BAND},
        "rows": [{
            "key": row["key"],
            "models": {
                name: {k: row[name][k] for k in ("sign", "family", "cv")}
                for name in ("candidate", "independent", "globalized")
            },
            "edges": row["edges"],
            "consensus_margin": row["margin"],
            "override": row["override"],
            "selected_solver": row["selected"]["kind"],
            "naive_solver": row["naive"]["kind"],
            "failed_model_attempts": row["failures"],
        } for row in fitted],
    }
    args.decisions.write_text(json.dumps(decisions, indent=2, sort_keys=True, allow_nan=False) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    records = []
    for row in fitted:
        models = {name: row[name] for name in ("candidate", "independent", "globalized", "selected", "naive")}
        scores = {}
        for domain, z in row["requests"].items():
            target = row["truth"](z)
            scores[domain] = {name: log_nmse(predict(model, z), target) for name, model in models.items()}
        records.append({
            "key": row["key"], "override": row["override"], "consensus_margin": row["margin"],
            "selected_solver": row["selected"]["kind"], "scores": scores,
        })

    methods = ("candidate", "independent", "globalized", "naive", "selected")
    metrics = {}
    for domain in DOMAINS:
        metrics[domain] = {
            "geometric_nmse": {m: geomean_log([r["scores"][domain][m] for r in records]) for m in methods},
            "catastrophic": {m: sum(r["scores"][domain][m] > 5.0 for r in records) for m in methods},
        }
    overrides = [r for r in records if r["override"]]
    candidate_cat = {d: metrics[d]["catastrophic"]["candidate"] for d in DOMAINS}
    selected_cat = {d: metrics[d]["catastrophic"]["selected"] for d in DOMAINS}
    ratios = {
        "inside_over_candidate": metrics["inside"]["geometric_nmse"]["selected"] / metrics["inside"]["geometric_nmse"]["candidate"],
        "far_over_candidate": metrics["far_shell"]["geometric_nmse"]["selected"] / metrics["far_shell"]["geometric_nmse"]["candidate"],
    }
    gates = {
        "complete": len(records) == 16,
        "two_overrides": len(overrides) >= 2,
        "no_excess_catastrophe": all(selected_cat[d] <= candidate_cat[d] for d in DOMAINS),
        "halves_one_domain_catastrophes": any(candidate_cat[d] >= 2 and selected_cat[d] * 2 <= candidate_cat[d] for d in DOMAINS),
        "inside_noninferior": ratios["inside_over_candidate"] <= 1.05,
        "far_improves": ratios["far_over_candidate"] <= 0.90,
    }
    payload = {
        "schema": "kernellum.consensus-medoid-result.v1",
        "classification": "PROSPECTIVE_UNSEEN",
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "decision_sha256": decision_sha,
        "paths": len(records), "overrides": len(overrides),
        "metrics": metrics, "ratios": ratios, "gates": gates, "records": records,
        "status": "PASS" if all(gates.values()) else "FAIL",
    }
    payload["canonical_sha256"] = canon(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in ("status", "canonical_sha256", "overrides", "ratios", "gates")}, indent=2))


if __name__ == "__main__":
    main()
