#!/usr/bin/env python3
"""Frozen label-blind solver-invariance certificate on opened shifted paths."""
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
    NOISES,
    SEEDS,
    SHAPES,
    canon,
    cfit,
    dataset,
    geomean_log,
    independent_fit,
    log_nmse,
    predict,
)

CV_BAND = 1e-3
RMS_BAND = 0.5
MAX_BAND = 4.0


def certificate(c, i, tests, y_scale):
    deltas = []
    for domain in DOMAINS:
        z = tests[domain][0]
        deltas.extend(((predict(c, z) - predict(i, z)) / y_scale).tolist())
    d = np.asarray(deltas, dtype=float)
    rel_cv = abs(c["cv"] - i["cv"]) / (1.0 + min(c["cv"], i["cv"]))
    rms = float(np.sqrt(np.mean(d * d)))
    maximum = float(np.max(np.abs(d)))
    checks = {
        "identity_agreement": c["sign"] == i["sign"] and c["family"] == i["family"],
        "cv_separated": rel_cv >= CV_BAND,
        "rms_agreement": rms <= RMS_BAND,
        "max_agreement": maximum <= MAX_BAND,
    }
    return {
        "accepted": all(checks.values()),
        "checks": checks,
        "relative_cv_margin": rel_cv,
        "prediction_rms": rms,
        "prediction_max": maximum,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    fitted = []
    for shape in SHAPES:
        for d in (3, 5):
            for seed in SEEDS:
                for noise in NOISES:
                    x, y, tests = dataset(shape, d, seed, noise)
                    cm, im, failures = [], [], []
                    for sign in (1, -1):
                        for family in ("exp_affine", "exp_concave"):
                            for bank, fn in (
                                ("candidate", lambda: cfit(x, y, sign, family)),
                                ("independent", lambda: independent_fit(x, y, sign, family)),
                            ):
                                try:
                                    q = fn()
                                    q["kind"] = bank
                                    (cm if bank == "candidate" else im).append(q)
                                except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                                    failures.append({"bank": bank, "sign": sign, "family": family, "reason": str(exc)})
                    if not cm or not im:
                        raise RuntimeError(f"empty bank for {shape} {d} {seed} {noise}: {failures}")
                    c, i = min(cm, key=lambda z: z["cv"]), min(im, key=lambda z: z["cv"])
                    cert = certificate(c, i, tests, max(float(np.std(y)), 1e-12))
                    lower = i if i["cv"] < c["cv"] else c
                    fitted.append({
                        "key": [shape, d, seed, noise], "candidate": c, "independent": i,
                        "selected": lower, "certificate": cert, "tests": tests, "failures": failures,
                    })
                    print(shape, d, seed, noise, "accepted", cert["accepted"], flush=True)

    decisions = {
        "schema": "kernellum.stability-certified-abstention-decisions.v1",
        "thresholds": {"cv_band": CV_BAND, "rms_band": RMS_BAND, "max_band": MAX_BAND},
        "rows": [{
            "key": r["key"],
            "candidate": {k: r["candidate"][k] for k in ("sign", "family", "cv")},
            "independent": {k: r["independent"][k] for k in ("sign", "family", "cv")},
            "selected_kind": r["selected"]["kind"],
            "certificate": r["certificate"],
            "failed_model_attempts": r["failures"],
        } for r in fitted],
    }
    args.decisions.write_text(json.dumps(decisions, indent=2, sort_keys=True) + "\n")
    decision_sha = hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    records = []
    for r in fitted:
        scores = {}
        for domain, (z, truth) in r["tests"].items():
            scores[domain] = {
                "candidate": log_nmse(predict(r["candidate"], z), truth),
                "independent": log_nmse(predict(r["independent"], z), truth),
                "selected": log_nmse(predict(r["selected"], z), truth),
            }
        harmful = r["selected"]["kind"] == "independent" and any(
            scores[d]["independent"] - scores[d]["candidate"] > math.log(10) for d in DOMAINS
        )
        records.append({"key": r["key"], "accepted": r["certificate"]["accepted"], "harmful_switch": harmful, "scores": scores})

    accepted = [r for r in records if r["accepted"]]
    harmful = [r for r in records if r["harmful_switch"]]
    harmful_rejected = sum(not r["accepted"] for r in harmful)
    accepted_safe = all(
        r["scores"][d]["selected"] - r["scores"][d]["candidate"] <= math.log(2)
        for r in accepted for d in DOMAINS
    )
    ratios = {}
    for domain in DOMAINS:
        if accepted:
            selected_g = geomean_log([r["scores"][domain]["selected"] for r in accepted])
            candidate_g = geomean_log([r["scores"][domain]["candidate"] for r in accepted])
            ratios[domain] = selected_g / candidate_g
        else:
            ratios[domain] = None
    gates = {
        "complete": len(records) == 16,
        "all_harmful_switches_rejected": bool(harmful) and harmful_rejected == len(harmful),
        "accepted_pointwise_noninferior": bool(accepted) and accepted_safe,
        "nonvacuous_coverage": len(accepted) >= 4,
        "accepted_aggregate_noninferior": bool(accepted) and all(v <= 1.10 for v in ratios.values()),
    }
    payload = {
        "schema": "kernellum.stability-certified-abstention-result.v1",
        "classification": "OPENED_DEVELOPMENT",
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "decision_sha256": decision_sha,
        "paths": len(records), "accepted": len(accepted), "harmful_switches": len(harmful),
        "harmful_switches_rejected": harmful_rejected, "ratios": ratios, "gates": gates,
        "records": records,
        "status": "PASS" if all(gates.values()) else "FAIL",
    }
    payload["canonical_sha256"] = canon(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({k: payload[k] for k in ("status", "canonical_sha256", "accepted", "harmful_switches", "harmful_switches_rejected", "ratios", "gates")}, indent=2))


if __name__ == "__main__":
    main()
