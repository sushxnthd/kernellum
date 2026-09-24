#!/usr/bin/env python3
"""Apply the frozen gates to the preserved-replica physical diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from scripts.similarity_asic_transfer_route import FIELDS
from scripts.similarity_stride2_validate import good_route

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("nangate45", "sky130hd")
SEEDS = (53, 71, 89)
GEOMETRIES = ((5, 8), (8, 5))
EXPECTED_DFFS = {(5, 8): 1899, (8, 5): 1872}


def load_csvs(root: Path, pattern: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(root.rglob(pattern)):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(FIELDS):
                raise ValueError(f"unexpected route schema: {path}")
            rows.extend(reader)
    return rows


def critical_path_evidence(root: Path) -> list[dict[str, object]]:
    evidence = []
    pattern = re.compile(
        r"(nangate45|sky130hd)/preserved/s(53|71|89)/"
        r"r(5|8)_c(8|5)/reports/6_finish\.rpt$"
    )
    for path in root.rglob("6_finish.rpt"):
        match = pattern.search(path.as_posix())
        if not match:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        section = text.split("finish report_checks -path_delay max", 1)
        if len(section) != 2:
            raise ValueError(f"missing maximum-delay section: {path}")
        start = re.search(r"Startpoint: (.+)", section[1])
        endpoint = re.search(r"Endpoint: (.+)", section[1])
        launch = re.search(
            r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+"
            r"[0-9.]+\s+[\^v]\s+.*?/Q\s+\(",
            section[1], re.MULTILINE,
        )
        evidence.append({
            "platform": match.group(1),
            "seed": int(match.group(2)),
            "rows": int(match.group(3)),
            "cols": int(match.group(4)),
            "startpoint": start.group(1) if start else None,
            "endpoint": endpoint.group(1) if endpoint else None,
            "launch_q_fanout": int(launch.group(1)) if launch else None,
        })
    return sorted(evidence, key=lambda x: (
        x["platform"], x["rows"], x["cols"], x["seed"]
    ))


def summarize(candidate: list[dict[str, str]], baseline: list[dict[str, str]],
              prior_candidate: list[dict[str, str]], functional: bool,
              paths: list[dict[str, object]]) -> dict[str, object]:
    expected = {
        (p, s, r, c) for p in PLATFORMS for s in SEEDS
        for r, c in GEOMETRIES
    }
    actual = [
        (x["platform"], int(x["seed"]), int(x["rows"]), int(x["cols"]))
        for x in candidate
    ]
    exact = len(candidate) == 12 and set(actual) == expected and len(set(actual)) == 12
    clean = exact and all(
        x["topology"] == "preserved"
        and x["attempted"].lower() == "true"
        and good_route(x) for x in candidate
    )
    c_lookup = {
        (x["platform"], int(x["seed"]), int(x["rows"]), int(x["cols"])): x
        for x in candidate if good_route(x)
    }
    b_lookup = {
        (x["platform"], x["topology"], int(x["seed"]),
         int(x["rows"]), int(x["cols"])): x
        for x in baseline
        if x["platform"] in PLATFORMS
        and x["topology"] in ("broadcast", "local", "stride2")
        and int(x["seed"]) in SEEDS
        and (int(x["rows"]), int(x["cols"])) in GEOMETRIES
        and good_route(x)
    }
    n_lookup = {
        (x["platform"], int(x["seed"]), int(x["rows"]), int(x["cols"])): x
        for x in prior_candidate
        if x["topology"] == "criticalbit" and good_route(x)
    }
    matched = []
    for platform, seed, rows, cols in sorted(expected):
        c_row = c_lookup.get((platform, seed, rows, cols))
        refs = [b_lookup.get((platform, t, seed, rows, cols))
                for t in ("broadcast", "local", "stride2")]
        no_op = n_lookup.get((platform, seed, rows, cols))
        if c_row is None or any(x is None for x in refs) or no_op is None:
            continue
        broadcast, local, stride = refs
        B, L, S, N, C = [float(x["period_min_ns"]) for x in
                          (broadcast, local, stride, no_op, c_row)]
        Ab, Al, Ac = [float(x["cell_area_um2"]) for x in
                      (broadcast, local, c_row)]
        matched.append({
            "platform": platform, "seed": seed, "rows": rows, "cols": cols,
            "broadcast_period_ns": B, "local_period_ns": L,
            "stride2_period_ns": S, "noop_period_ns": N,
            "preserved_period_ns": C,
            "preserved_q": (B-C)/B,
            "preserved_retained_benefit": (B-C)/(B-L) if B > L else None,
            "preserved_vs_broadcast_density": B*Ab/(C*Ac),
            "preserved_vs_local_density": L*Al/(C*Ac),
            "local_dffs": int(local["dff_cells"]),
            "preserved_dffs": int(c_row["dff_cells"]),
            "local_area_um2": Al, "preserved_area_um2": Ac,
        })

    grouped: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in matched:
        grouped[(str(row["platform"]), int(row["rows"]), int(row["cols"]))].append(row)
    metrics = (
        "broadcast_period_ns", "local_period_ns", "stride2_period_ns",
        "noop_period_ns", "preserved_period_ns", "preserved_q",
        "preserved_retained_benefit", "preserved_vs_broadcast_density",
        "preserved_vs_local_density", "local_dffs", "preserved_dffs",
        "local_area_um2", "preserved_area_um2",
    )
    points = []
    for (platform, rows, cols), group in sorted(grouped.items()):
        if len(group) == 3:
            points.append({
                "platform": platform, "rows": rows, "cols": cols,
                **{f"median_{m}": statistics.median(float(x[m]) for x in group)
                   for m in metrics},
            })
    density_wins = [
        x for x in points
        if x["median_preserved_vs_broadcast_density"] > 1
        and x["median_preserved_vs_local_density"] > 1
    ]
    target = next((x for x in points if x["platform"] == "nangate45"
                   and x["rows"] == 8 and x["cols"] == 5), None)
    target_paths = [x for x in paths if x["platform"] == "nangate45"
                    and x["rows"] == 8 and x["cols"] == 5]
    path_fanouts = [int(x["launch_q_fanout"]) for x in target_paths
                    if x["launch_q_fanout"] is not None]

    gates = {
        "functional_equivalence_on_opened_shapes": functional,
        "exactly_12_unique_candidate_attempts": exact,
        "all_12_candidate_routes_clean": clean,
        "all_four_groups_have_three_matched_seeds": len(points) == 4,
        "exact_preserved_dff_counts": len(matched) == 12 and all(
            x["preserved_dffs"] == EXPECTED_DFFS[(x["rows"], x["cols"])]
            for x in matched
        ),
        "candidate_dffs_at_most_90pct_local": len(matched) == 12 and all(
            x["preserved_dffs"] <= .90*x["local_dffs"] for x in matched
        ),
        "candidate_area_below_full_local": len(matched) == 12 and all(
            x["preserved_area_um2"] < x["local_area_um2"] for x in matched
        ),
        "median_raw_timing_benefit_at_least_5pct": len(points) == 4 and all(
            x["median_preserved_q"] >= .05 for x in points
        ),
        "median_retention_at_least_70pct": len(points) == 4 and all(
            x["median_preserved_retained_benefit"] >= .70 for x in points
        ),
        "density_wins_at_least_three_of_four": len(density_wins) >= 3,
        "density_win_on_each_platform": all(
            any(x["platform"] == p for x in density_wins) for p in PLATFORMS
        ),
        "target_improves_stride2_by_0p04ns": target is not None and
            target["median_preserved_period_ns"] <=
            target["median_stride2_period_ns"] - .04,
        "target_improves_noop_by_0p02ns": target is not None and
            target["median_preserved_period_ns"] <=
            target["median_noop_period_ns"] - .02,
        "target_median_launch_q_fanout_at_most_10": len(path_fanouts) == 3
            and statistics.median(path_fanouts) <= 10,
    }
    return {
        "schema_version": 1,
        "opened_data_only": True,
        "attempted": len(candidate),
        "clean": sum(good_route(x) for x in candidate),
        "complete_matched_sets": len(matched),
        "gates": gates,
        "prospective_study_warranted": all(gates.values()),
        "points": points,
        "matched_rows": matched,
        "critical_paths": paths,
        "all_candidate_routes": candidate,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--baseline", type=Path,
                        default=ROOT / "results" / "similarity_stride2_download")
    parser.add_argument("--prior-candidate", type=Path,
                        default=ROOT / "results" / "similarity_criticalbit_download")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results" / "similarity_preserved_summary.json")
    args = parser.parse_args()
    result = summarize(
        load_csvs(args.input, "similarity_preserved_*.csv"),
        load_csvs(args.baseline, "similarity_stride2_*.csv"),
        load_csvs(args.prior_candidate, "similarity_criticalbit_*.csv"),
        any(args.input.rglob("similarity_preserved_functional_passed")),
        critical_path_evidence(args.input),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ("points", "matched_rows", "critical_paths",
                       "all_candidate_routes")}, indent=2))
    return 0 if result["prospective_study_warranted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
