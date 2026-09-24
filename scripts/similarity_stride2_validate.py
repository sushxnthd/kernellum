#!/usr/bin/env python3
"""Evaluate every preregistered stride-two physical route and preserve nulls."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from scripts.similarity_stride2_route import GEOMETRIES, PLATFORMS, SEEDS, TOPOLOGIES
from scripts.similarity_asic_transfer_route import FIELDS

ROOT = Path(__file__).resolve().parents[1]
VIOLATIONS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
)
COSTS = ("total_cells", "dff_cells", "cell_area_um2", "wire_length_um")
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")


def expected_keys() -> set[tuple[str, str, int, int, int]]:
    return {
        (p, t, s, r, c)
        for p in PLATFORMS for t in TOPOLOGIES for s in SEEDS
        for _, r, c in GEOMETRIES
    }


def key(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"], row["topology"], int(row["seed"]),
        int(row["rows"]), int(row["cols"]),
    )


def good_route(row: dict[str, str]) -> bool:
    if row["route_ok"].lower() != "true":
        return False
    try:
        return (
            all(row[field] != "" and int(row[field]) == 0 for field in VIOLATIONS)
            and all(row[field] != "" and float(row[field]) > 0
                    for field in COSTS + ("period_min_ns",))
            and all(len(row[field]) == 64 for field in HASHES)
        )
    except (KeyError, ValueError):
        return False


def summarize(rows: list[dict[str, str]], functional_passed: bool) -> dict[str, object]:
    expected = expected_keys()
    actual = [key(row) for row in rows]
    unique_complete = (
        len(rows) == len(expected)
        and set(actual) == expected
        and len(set(actual)) == len(actual)
    )
    all_clean = unique_complete and all(good_route(row) for row in rows)
    lookup = {key(row): row for row in rows if good_route(row)}
    pairs = []
    for platform in PLATFORMS:
        for split, r, c in GEOMETRIES:
            for seed in SEEDS:
                trio = [lookup.get((platform, topology, seed, r, c))
                        for topology in TOPOLOGIES]
                if any(item is None for item in trio):
                    continue
                broadcast, local, stride = trio
                tb, tl, ts = [float(x["period_min_ns"]) for x in trio]
                ab, al, a_s = [float(x["cell_area_um2"]) for x in trio]
                db, dl, ds = [int(x["dff_cells"]) for x in trio]
                pairs.append({
                    "platform": platform, "split": split, "rows": r, "cols": c,
                    "seed": seed, "broadcast_period_ns": tb, "local_period_ns": tl,
                    "stride2_period_ns": ts,
                    "local_q": (tb-tl)/tb, "stride2_q": (tb-ts)/tb,
                    "retained_benefit": (tb-ts)/(tb-tl) if tb > tl else None,
                    "stride2_vs_broadcast_density": tb*ab/(ts*a_s),
                    "stride2_vs_local_density": tl*al/(ts*a_s),
                    "broadcast_area_um2": ab, "local_area_um2": al,
                    "stride2_area_um2": a_s,
                    "broadcast_dffs": db, "local_dffs": dl, "stride2_dffs": ds,
                    "stride2_wire_length_um": float(stride["wire_length_um"]),
                })
    groups: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for pair in pairs:
        groups[(str(pair["platform"]), int(pair["rows"]), int(pair["cols"]))].append(pair)
    points = []
    for (platform, r, c), group in sorted(groups.items()):
        if len(group) < 2:
            continue
        points.append({
            "platform": platform, "rows": r, "cols": c,
            "split": group[0]["split"], "complete_seeds": len(group),
            **{f"median_{field}": statistics.median(float(p[field]) for p in group)
               for field in (
                   "local_q", "stride2_q", "stride2_vs_broadcast_density",
                   "stride2_vs_local_density", "broadcast_area_um2",
                   "local_area_um2", "stride2_area_um2", "broadcast_dffs",
                   "local_dffs", "stride2_dffs",
               )},
            "median_retained_benefit": (
                statistics.median(float(p["retained_benefit"]) for p in group
                                  if p["retained_benefit"] is not None)
                if any(p["retained_benefit"] is not None for p in group) else None
            ),
        })
    holdout = [p for p in points if p["split"] == "holdout"]
    density_wins = [
        p for p in holdout
        if p["median_stride2_vs_broadcast_density"] > 1.0
        and p["median_stride2_vs_local_density"] > 1.0
    ]
    gates = {
        "functional_equivalence": functional_passed,
        "exactly_72_unique_attempts": unique_complete
            and all(row["attempted"].lower() == "true" for row in rows),
        "all_72_final_routes_clean": all_clean,
        "all_eight_geometries_have_two_complete_seeds": len(points) == 8,
        "full_local_positive_on_all_eight": len(points) == 8
            and all(p["median_local_q"] > 0 for p in points),
        "stride2_transport_register_reduction": len(pairs) == 24
            and all(p["broadcast_dffs"] < p["stride2_dffs"]
                    <= 0.90*p["local_dffs"] for p in pairs),
        "stride2_area_below_full_local": len(pairs) == 24
            and all(p["stride2_area_um2"] < p["local_area_um2"] for p in pairs),
        "holdout_stride2_raw_benefit_at_least_5pct": len(holdout) == 4
            and all(p["median_stride2_q"] >= 0.05 for p in holdout),
        "holdout_retains_at_least_60pct_full_local_benefit": len(holdout) == 4
            and all(p["median_retained_benefit"] is not None
                    and p["median_retained_benefit"] >= 0.60 for p in holdout),
        "holdout_density_wins_at_least_three_of_four": len(density_wins) >= 3,
        "holdout_density_win_on_each_platform": all(
            any(p["platform"] == platform for p in density_wins)
            for platform in PLATFORMS
        ),
    }
    return {
        "schema_version": 1, "attempted": len(rows),
        "successful": sum(row["route_ok"].lower() == "true" for row in rows),
        "clean": sum(good_route(row) for row in rows),
        "complete_triples": len(pairs),
        "gates": gates, "claim_supported": all(gates.values()),
        "points": points, "pairs": pairs,
        "all_raw_routes": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "similarity_stride2_summary.json")
    args = parser.parse_args()
    rows: list[dict[str, str]] = []
    for path in sorted(args.input.rglob("similarity_stride2_*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(FIELDS):
                raise ValueError(f"unexpected route schema: {path}")
            rows.extend(reader)
    marker = any(args.input.rglob("similarity_stride2_functional_passed"))
    result = summarize(rows, marker)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items()
                      if k not in ("points","pairs","all_raw_routes")}, indent=2))
    return 0 if result["claim_supported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
