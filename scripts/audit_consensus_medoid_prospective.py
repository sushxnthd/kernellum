#!/usr/bin/env python3
"""Independent standard-library audit of consensus-medoid aggregation and gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

DOMAINS = ("inside", "near_shell", "far_shell")
METHODS = ("candidate", "independent", "globalized", "naive", "selected")
FLOOR = math.log(1e-8)


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def geomean(rows, domain, method):
    return math.exp(sum(max(row["scores"][domain][method], FLOOR) for row in rows) / len(rows))


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
    checks.append(decisions["classification"] == result["classification"] == "PROSPECTIVE_UNSEEN")
    checks.append(len(decisions["rows"]) == len(result["records"]) == result["paths"] == 16)
    drows = {tuple(row["key"]): row for row in decisions["rows"]}
    rrows = {tuple(row["key"]): row for row in result["records"]}
    checks.append(drows.keys() == rrows.keys())

    for key, row in drows.items():
        edges = row["edges"]
        order = sorted(edges, key=lambda name: (edges[name]["rms"], name))
        unique_ig = order[0] == "independent_globalized" and edges[order[0]]["rms"] + 1e-12 < edges[order[1]]["rms"]
        override = (
            unique_ig and edges["independent_globalized"]["admissible"]
            and not edges["candidate_independent"]["admissible"]
            and not edges["candidate_globalized"]["admissible"]
        )
        margin = min(edges["candidate_independent"]["rms"], edges["candidate_globalized"]["rms"]) - edges["independent_globalized"]["rms"]
        checks.extend([
            override == row["override"] == rrows[key]["override"],
            abs(margin - row["consensus_margin"]) <= 1e-12,
            abs(margin - rrows[key]["consensus_margin"]) <= 1e-12,
            (row["selected_solver"] != "candidate") == override,
        ])

    metrics = {}
    for domain in DOMAINS:
        metrics[domain] = {
            "geometric_nmse": {m: geomean(result["records"], domain, m) for m in METHODS},
            "catastrophic": {m: sum(row["scores"][domain][m] > 5.0 for row in result["records"]) for m in METHODS},
        }
        for method in METHODS:
            checks.append(abs(metrics[domain]["geometric_nmse"][method] - result["metrics"][domain]["geometric_nmse"][method]) <= 1e-9 * max(1.0, metrics[domain]["geometric_nmse"][method]))
            checks.append(metrics[domain]["catastrophic"][method] == result["metrics"][domain]["catastrophic"][method])

    overrides = sum(row["override"] for row in result["records"])
    ratios = {
        "inside_over_candidate": metrics["inside"]["geometric_nmse"]["selected"] / metrics["inside"]["geometric_nmse"]["candidate"],
        "far_over_candidate": metrics["far_shell"]["geometric_nmse"]["selected"] / metrics["far_shell"]["geometric_nmse"]["candidate"],
    }
    ccat = {d: metrics[d]["catastrophic"]["candidate"] for d in DOMAINS}
    scat = {d: metrics[d]["catastrophic"]["selected"] for d in DOMAINS}
    gates = {
        "complete": len(result["records"]) == 16,
        "two_overrides": overrides >= 2,
        "no_excess_catastrophe": all(scat[d] <= ccat[d] for d in DOMAINS),
        "halves_one_domain_catastrophes": any(ccat[d] >= 2 and scat[d] * 2 <= ccat[d] for d in DOMAINS),
        "inside_noninferior": ratios["inside_over_candidate"] <= 1.05,
        "far_improves": ratios["far_over_candidate"] <= 0.90,
    }
    checks.extend([
        overrides == result["overrides"],
        all(abs(ratios[k] - result["ratios"][k]) <= 1e-12 * max(1.0, ratios[k]) for k in ratios),
        gates == result["gates"],
        ("PASS" if all(gates.values()) else "FAIL") == result["status"],
    ])
    raw = dict(result)
    claimed = raw.pop("canonical_sha256")
    checks.append(digest(raw) == claimed)
    failures = sum(not item for item in checks)
    payload = {
        "schema": "kernellum.consensus-medoid-audit.v1",
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
