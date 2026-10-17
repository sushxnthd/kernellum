#!/usr/bin/env python3
"""Independent audit of the exact completion count and preserved result."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def expected(max_n=6):
    pairs = checks = 0
    for n in range(1, max_n + 1):
        for observed_count in range(n):
            # C(n,k) transcripts masks, 2^k assignments, n-k requests.
            import math
            count = math.comb(n, observed_count) * (2**observed_count) * (n - observed_count)
            pairs += count
            checks += count * (observed_count + 1)
    return checks, pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    checks, pairs = expected()
    tests = {
        "schema": result["schema"] == "kernellum.version-space-certificate-boundary.v1",
        "completion_pairs": result["theorem"]["indistinguishable_completion_pairs"] == pairs,
        "enumeration_checks": result["theorem"]["checks"] == checks,
        "all_runtime_calls_refused_without_provenance": result["opened_cohort"]["missing_provenance_refusals"] == result["opened_cohort"]["cells"],
        "opened_cells_complete": result["opened_cohort"]["cells"] == 48,
        "misspecification_witness_present": result["opened_cohort"]["cells_truth_outside_envelope"] > 0,
        "catastrophic_witness_present": result["opened_cohort"]["catastrophic_truth_outside_envelope"] > 0,
        "terminal_gate": result["scientific_gate"] == "PASS_BOUNDARY_PIVOT",
    }
    audit = {"schema": "kernellum.version-space-certificate-boundary-audit.v1", "checks": tests, "passed": sum(tests.values()), "total": len(tests), "status": "PASS" if all(tests.values()) else "FAIL"}
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
