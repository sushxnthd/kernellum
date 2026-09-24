#!/usr/bin/env python3
"""Re-route a previously opened 7x7 geometry to qualify electrical repair."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts import similarity_asic_transfer_route as prior


ROOT = Path(__file__).resolve().parents[1]
SEEDS = prior.SEEDS
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local")
VIOLATION_FIELDS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
)


def evaluate(rows: list[dict[str, str]]) -> dict[str, object]:
    expected = {(p, t, s) for p in PLATFORMS for t in TOPOLOGIES for s in SEEDS}
    actual = [(r["platform"], r["topology"], int(r["seed"])) for r in rows]
    complete = (
        len(rows) == len(expected)
        and len(set(actual)) == len(actual)
        and set(actual) == expected
        and all((int(r["rows"]), int(r["cols"])) == (7, 7) for r in rows)
    )
    clean = complete and all(
        r["route_ok"].lower() == "true"
        and all(r[field] != "" and int(r[field]) == 0 for field in VIOLATION_FIELDS)
        and all(r[field] for field in
                ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256"))
        for r in rows
    )
    return {
        "schema_version": 1,
        "role": "plumbing qualification only; previously opened 7x7 excluded from future claims",
        "expected": len(expected),
        "received": len(rows),
        "complete": complete,
        "all_final_routes_electrically_clean": clean,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=PLATFORMS)
    parser.add_argument("--topology", choices=TOPOLOGIES)
    parser.add_argument("--seed", type=int, choices=SEEDS)
    parser.add_argument("--flow-root", type=Path)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    parser.add_argument("--evaluate", type=Path)
    args = parser.parse_args()
    if args.evaluate:
        rows: list[dict[str, str]] = []
        for path in sorted(args.evaluate.rglob("similarity_asic_repair_*.csv")):
            with path.open(newline="", encoding="utf-8") as handle:
                rows.extend(csv.DictReader(handle))
        result = evaluate(rows)
        output = ROOT / "results" / "similarity_asic_repair_canary.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
        return 0 if result["all_final_routes_electrically_clean"] else 1
    if args.platform is None or args.topology is None or args.seed is None or args.flow_root is None:
        parser.error("routing requires platform, topology, seed and flow-root")
    # The old frozen route logic is reused with a separate config, evidence root,
    # and result name. The historical 96-route data and evaluator are untouched.
    prior.BUILD = ROOT / "build" / "similarity_asic_repair_canary"
    row = prior.route_one(
        args.platform, "excluded_canary", args.topology, args.seed, 7, 7,
        args.flow_root.resolve(), args.qemu.resolve(),
        f"/work/asic/repair_canary/config_{args.platform}.mk",
    )
    output = ROOT / "results" / (
        f"similarity_asic_repair_{args.platform}_{args.topology}_s{args.seed}.csv"
    )
    output.parent.mkdir(exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=prior.FIELDS)
        writer.writeheader()
        writer.writerow(row)
    print(output, "route_ok=", row["route_ok"], "error_stage=", row["error_stage"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
