#!/usr/bin/env python3
"""Independent artifact-level audit of the frozen selector evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.primary.read_text())
    payload = data.pop("payload_sha256")
    canonical = json.dumps(data, indent=2, sort_keys=True) + "\n"
    checks = {}
    checks["payload_digest"] = hashlib.sha256(canonical.encode()).hexdigest() == payload
    checks["protocol"] = data["protocol"] == "certificate-conditioned-selector-v1"
    checks["trial_count"] = len(data["records"]) == 36
    checks["transform_count"] = len(data["transforms"]) == 12
    expected_routes = {"freudenstein_roth": True, "himmelblau": True, "ftrig": False}
    checks["routes"] = all(data["certificates"][name]["passed"] is expected
                            for name, expected in expected_routes.items())
    selector_nfev = sum(row["selector"]["nfev"] for row in data["records"])
    baseline_nfev = sum(row["baseline"]["nfev"] for row in data["records"])
    checks["evaluation_totals"] = (
        selector_nfev == data["summary"]["selector_nfev"]
        and baseline_nfev == data["summary"]["baseline_nfev"]
    )
    checks["reduction"] = abs(
        (1-selector_nfev/baseline_nfev)-data["summary"]["evaluation_reduction"]
    ) < 1e-15
    coverage_losses = 0
    objective_losses = 0
    for row in data["records"]:
        coverage_key = "coverage" if "coverage" in row["selector"] else "distinct_minima"
        coverage_losses += row["selector"][coverage_key] < row["baseline"][coverage_key]
        objective_losses += row["selector"]["best_objective"] > row["baseline"]["best_objective"] + 1e-12
    checks["no_coverage_loss"] = coverage_losses == data["summary"]["coverage_losses"] == 0
    checks["no_objective_loss"] = objective_losses == data["summary"]["objective_losses"] == 0
    checks["gate"] = (
        data["summary"]["evaluation_reduction"] < 0.25
        and data["scientific_gate"] == "KILL_AGGREGATE_SAVINGS"
    )
    checks["family_counts"] = all(
        data["summary"]["by_family"][name]["trials"] == 12 for name in expected_routes
    )
    audit = {"schema": "certificate-conditioned-selector-audit-v1",
             "checks": checks, "passed": sum(checks.values()), "total": len(checks),
             "status": "pass" if all(checks.values()) else "fail"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
