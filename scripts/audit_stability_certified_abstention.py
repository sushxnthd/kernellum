#!/usr/bin/env python3
"""Independent standard-library audit of the frozen abstention result."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

DOMAINS = ("inside", "near_shell", "far_shell")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decisions", type=Path, required=True)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    decisions = json.loads(args.decisions.read_text())
    result = json.loads(args.result.read_text())
    checks = []
    checks.append(hashlib.sha256(args.decisions.read_bytes()).hexdigest() == result["decision_sha256"])
    checks.append(len(decisions["rows"]) == result["paths"] == len(result["records"]) == 16)
    drows = {tuple(row["key"]): row for row in decisions["rows"]}
    rrows = {tuple(row["key"]): row for row in result["records"]}
    checks.append(drows.keys() == rrows.keys())
    for key in drows:
        checks.append(drows[key]["certificate"]["accepted"] == rrows[key]["accepted"])

    accepted = [row for row in result["records"] if row["accepted"]]
    harmful = [row for row in result["records"] if row["harmful_switch"]]
    rejected = sum(not row["accepted"] for row in harmful)
    pointwise = all(
        row["scores"][domain]["selected"] - row["scores"][domain]["candidate"] <= math.log(2)
        for row in accepted for domain in DOMAINS
    )
    ratios = {}
    for domain in DOMAINS:
        selected = math.exp(sum(max(row["scores"][domain]["selected"], math.log(1e-8)) for row in accepted) / len(accepted))
        candidate = math.exp(sum(max(row["scores"][domain]["candidate"], math.log(1e-8)) for row in accepted) / len(accepted))
        ratios[domain] = selected / candidate
        checks.append(abs(ratios[domain] - result["ratios"][domain]) <= 1e-12)
    gates = {
        "complete": len(result["records"]) == 16,
        "all_harmful_switches_rejected": bool(harmful) and rejected == len(harmful),
        "accepted_pointwise_noninferior": bool(accepted) and pointwise,
        "nonvacuous_coverage": len(accepted) >= 4,
        "accepted_aggregate_noninferior": bool(accepted) and all(value <= 1.10 for value in ratios.values()),
    }
    checks.extend([
        len(accepted) == result["accepted"], len(harmful) == result["harmful_switches"],
        rejected == result["harmful_switches_rejected"], gates == result["gates"],
        ("PASS" if all(gates.values()) else "FAIL") == result["status"],
    ])
    raw = dict(result)
    claimed = raw.pop("canonical_sha256")
    checks.append(digest(raw) == claimed)
    failures = sum(not item for item in checks)
    payload = {
        "schema": "kernellum.stability-certified-abstention-audit.v1",
        "status": "PASS" if failures == 0 else "FAIL",
        "checks": len(checks), "failures": failures,
        "source_canonical_sha256": claimed,
    }
    payload["canonical_sha256"] = digest(payload)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))
    raise SystemExit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()

