#!/usr/bin/env python3
"""Standard-library-only audit of sign-anchored dual-solver arbitration."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path


DOMAINS = ("inside", "near_shell", "far_shell")
FLOOR = math.log(1e-8)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.records.read_text())
    result = json.loads(args.result.read_text())

    choices = []
    for row in rows:
        candidate = row["candidate_winner"]
        independent = row["winner"]
        if int(candidate["sign"]) != int(independent["sign"]):
            choices.append("candidate")
        elif float(independent["cv"]) < float(candidate["cv"]):
            choices.append("independent")
        else:
            choices.append("candidate")

    checks = {}
    checks["choice_counts"] = result["choice_counts"] == {
        "candidate": choices.count("candidate"),
        "independent": choices.count("independent"),
    }
    for domain in DOMAINS:
        streams = {"candidate": [], "independent": [], "control": []}
        for row, choice in zip(rows, choices):
            scores = row["scores"][domain]
            candidate = max(float(scores["candidate_log_nmse"]), FLOOR)
            independent = max(float(scores["independent_log_nmse"]), FLOOR)
            streams["candidate"].append(candidate)
            streams["independent"].append(independent)
            streams["control"].append(independent if choice == "independent" else candidate)
        observed = result["metrics"][domain]
        checks[f"{domain}.geometric_nmse"] = all(
            math.isclose(
                math.exp(statistics.fmean(streams[name])),
                observed["geometric_nmse"][name],
                rel_tol=1e-13,
                abs_tol=1e-15,
            ) for name in streams
        )
        checks[f"{domain}.median_log_nmse"] = all(
            math.isclose(
                statistics.median(streams[name]),
                observed["median_log_nmse"][name],
                rel_tol=1e-13,
                abs_tol=1e-15,
            ) for name in streams
        )
        checks[f"{domain}.catastrophic_counts"] = all(
            sum(value > 5.0 for value in streams[name])
            == observed["catastrophic_log_nmse_gt_5"][name]
            for name in streams
        )
        checks[f"{domain}.paired_counts"] = (
            sum(a < b - 1e-12 for a, b in zip(streams["control"], streams["candidate"]))
            == observed["control_better_than_candidate"]
            and sum(a > b + 1e-12 for a, b in zip(streams["control"], streams["candidate"]))
            == observed["control_worse_than_candidate"]
        )

    audit = {
        "schema": "kernellum.sign-anchored-dual-solver-audit.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "paths": len(rows),
        "result_canonical_sha256": result["canonical_sha256"],
    }
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
