#!/usr/bin/env python3
"""Audit the published B-local synthesis canary evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SOURCE_SHA = "7bfe4521a2b3034abc10e412398a0028a4dc8e95"
EXPECTED = {
    ("nangate45", 5, 8): (1979, 2284),
    ("nangate45", 8, 5): (1972, 2232),
    ("sky130hd", 5, 8): (1979, 2284),
    ("sky130hd", 8, 5): (1972, 2232),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results", type=Path,
        default=Path("results/similarity_blocal_preservation_download"),
    )
    args = parser.parse_args()
    found = {}
    for path in sorted(args.results.glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        key = (row["platform"], row["rows"], row["cols"])
        if key in found:
            raise SystemExit(f"duplicate row: {key}")
        found[key] = row
    if set(found) != set(EXPECTED):
        raise SystemExit("four-row set mismatch")
    gates = {}
    for key, (expected, local) in EXPECTED.items():
        row = found[key]
        label = f"{key[0]}_{key[1]}x{key[2]}"
        gates[f"{label}_source"] = row["source_sha"] == SOURCE_SHA
        gates[f"{label}_synth_exit"] = row["synth_exit_code"] == 0
        gates[f"{label}_exact_dffs"] = (
            row["expected_dffs"] == expected and row["dff_cells"] == expected
        )
        gates[f"{label}_local_reference"] = row["local_dffs"] == local
        gates[f"{label}_dff_budget"] = row["dff_cells"] <= .90*local
        gates[f"{label}_reported_pass"] = row["replicas_preserved"] is True
    gates["functional_source"] = (
        (args.results / "source_sha.txt").read_text().strip() == SOURCE_SHA
    )
    for geometry in ("5x8", "8x5"):
        log = (args.results / f"tb_{geometry}.log").read_text()
        gates[f"functional_{geometry}"] = (
            f"KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows={geometry[0]} "
            f"cols={geometry[2]}" in log
        )
    result = {
        "source_sha": SOURCE_SHA,
        "row_count": len(found),
        "gates": gates,
        "canary_pass": all(gates.values()),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["canary_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
