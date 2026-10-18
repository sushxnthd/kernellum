#!/usr/bin/env python3
"""Independent invariants and digest audit for quantitative-premise result."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    claimed = result.pop("canonical_sha256")
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    summary = result["opened_summary"]
    tests = {
        "canonical_digest": hashlib.sha256(raw.encode()).hexdigest() == claimed,
        "schema": result["schema"] == "kernellum.quantitative-premise-boundary.v1",
        "frozen_protocol": result["protocol_commit"] == "08cd22be8d5da22cd7faf91298ebd6a263372d62",
        "finite_sharpness_nontrivial": result["finite_sharpness"]["transcript_requests"] >= 2000,
        "all_empirical_calls_refused": result["runtime_empirical_refusals"] == 48,
        "empirical_shortcut_collides": summary["1"]["all"]["cells_any_outside"] > 0,
        "twofold_inflation_still_collides": summary["2"]["all"]["cells_any_outside"] > 0,
        "fivefold_coverage_is_wide": summary["5"]["all"]["cells_any_outside"] == 0
            and summary["5"]["all"]["mean_normalized_width"] > 40,
        "catastrophic_subset_complete": summary["1"]["catastrophic"]["cells"] == 11,
        "terminal_gate": result["scientific_gate"] == "PASS_PIVOT_TO_EXTERNAL_QUANTITATIVE_PREMISES",
    }
    audit = {"schema": "kernellum.quantitative-premise-boundary-audit.v1",
             "checks": tests, "passed": sum(tests.values()), "total": len(tests),
             "status": "PASS" if all(tests.values()) else "FAIL",
             "source_canonical_sha256": claimed}
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
