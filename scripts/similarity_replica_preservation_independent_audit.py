#!/usr/bin/env python3
"""Independently audit the published replica-preservation canary evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SOURCE_SHA = "8935555a38fc3892810f7b33d00f9ed07a6bebed"
EXPECTED = {
    ("nangate45", 5, 8): (1899, 2284),
    ("nangate45", 8, 5): (1872, 2232),
    ("sky130hd", 5, 8): (1899, 2284),
    ("sky130hd", 8, 5): (1872, 2232),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("results/similarity_replica_preservation_download"),
    )
    args = parser.parse_args()

    found: dict[tuple[str, int, int], dict] = {}
    for path in sorted(args.results.glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        key = (row["platform"], row["rows"], row["cols"])
        if key in found:
            raise SystemExit(f"duplicate row: {key}")
        found[key] = row
    if set(found) != set(EXPECTED):
        raise SystemExit(
            f"row set mismatch: missing={set(EXPECTED)-set(found)}, "
            f"extra={set(found)-set(EXPECTED)}"
        )

    gates: dict[str, bool] = {}
    for key, (expected_dffs, local_dffs) in EXPECTED.items():
        row = found[key]
        label = f"{key[0]}_{key[1]}x{key[2]}"
        gates[f"{label}_source"] = row["source_sha"] == SOURCE_SHA
        gates[f"{label}_synth_exit"] = row["synth_exit_code"] == 0
        gates[f"{label}_exact_dffs"] = (
            row["expected_dffs"] == expected_dffs
            and row["dff_cells"] == expected_dffs
        )
        gates[f"{label}_local_reference"] = row["local_dffs"] == local_dffs
        gates[f"{label}_dff_budget"] = row["dff_cells"] <= 0.90 * local_dffs
        gates[f"{label}_reported_pass"] = row["replicas_preserved"] is True

    functional_sha = (args.results / "source_sha.txt").read_text(
        encoding="utf-8"
    ).strip()
    gates["functional_source"] = functional_sha == SOURCE_SHA
    for geometry in ("5x8", "8x5"):
        text = (args.results / f"tb_{geometry}.log").read_text(encoding="utf-8")
        gates[f"functional_{geometry}"] = (
            f"KERNELLUM_PRESERVED_EQUIVALENCE_PASS rows={geometry[0]} "
            f"cols={geometry[2]}" in text
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
