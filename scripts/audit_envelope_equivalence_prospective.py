#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

DOMAINS = ("inside", "near_shell", "far_shell")
FLOOR = math.log(1e-8)


def geometric(scores):
    return math.exp(sum(max(value, FLOOR) for value in scores) / len(scores))


def canonical(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    decisions = json.loads(args.decisions.read_text())
    result = json.loads(args.result.read_text())
    checks = []

    decision_by_key = {tuple(row["key"]): row for row in decisions["rows"]}
    result_by_key = {tuple(row["key"]): row for row in result["records"]}
    checks.append(set(decision_by_key) == set(result_by_key))
    for key, row in decision_by_key.items():
        count = int(row["normalized_delta_count"])
        rms = math.sqrt(float(row["normalized_delta_sum_squares"]) / count)
        maximum = float(row["normalized_delta_max"])
        accepted = rms <= 0.5 and maximum <= 4.0
        selected = None
        if accepted:
            selected = (
                "independent"
                if row["independent"]["cv"] < row["candidate"]["cv"]
                else "candidate"
            )
        checks.extend([
            abs(rms - row["prediction_rms"]) <= 1e-12,
            abs(maximum - row["prediction_max"]) <= 1e-12,
            accepted == row["accepted"],
            selected == row["selected_solver"],
            accepted == result_by_key[key]["accepted"],
            selected == result_by_key[key]["selected_solver"],
        ])

    records = list(result_by_key.values())
    accepted_rows = [row for row in records if row["accepted"]]
    harmful_rows = [row for row in records if row["harmful_switch"]]
    ratios = {}
    for domain in DOMAINS:
        ratios[domain] = (
            geometric([row["scores"][domain]["selected"] for row in accepted_rows])
            / geometric([row["scores"][domain]["candidate"] for row in accepted_rows])
            if accepted_rows else None
        )
    gates = {
        "complete": len(records) == 16,
        "two_harmful_opportunities": len(harmful_rows) >= 2,
        "all_harmful_switches_rejected": bool(harmful_rows) and all(not row["accepted"] for row in harmful_rows),
        "coverage": len(accepted_rows) >= 8,
        "accepted_pointwise_noninferior": bool(accepted_rows) and all(
            row["scores"][domain]["selected"] - row["scores"][domain]["candidate"] <= math.log(2.0)
            for row in accepted_rows for domain in DOMAINS
        ),
        "accepted_aggregate_noninferior": bool(accepted_rows) and all(value <= 1.10 for value in ratios.values()),
    }
    checks.extend([
        len(accepted_rows) == result["accepted"],
        len(harmful_rows) == result["harmful_switches"],
        ratios == result["ratios"],
        gates == result["gates"],
        canonical({k: v for k, v in result.items() if k != "canonical_sha256"}) == result["canonical_sha256"],
    ])
    payload = {
        "schema": "kernellum.envelope-equivalence-audit.v1",
        "checks": len(checks),
        "failures": sum(not check for check in checks),
        "source_canonical_sha256": result["canonical_sha256"],
        "status": "PASS" if all(checks) else "FAIL",
    }
    payload["canonical_sha256"] = canonical(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()
