#!/usr/bin/env python3
"""Apply the predeclared continue/stop gate to the opened-data diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
import math
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


def predicted_replica_overhead(rows: int, cols: int) -> int:
    """Extra explicit data bits versus ordinary stride-two group registers."""
    col_groups = (cols + 1) // 2
    row_groups = (rows + 1) // 2
    return rows * (cols - col_groups) + 3 * cols * (rows - row_groups)


def load_csvs(root: Path, pattern: str) -> list[dict[str, str]]:
    rows = []
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
        r"(nangate45|sky130hd)/criticalbit/s(53|71|89)/"
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
            "platform": match.group(1), "seed": int(match.group(2)),
            "rows": int(match.group(3)), "cols": int(match.group(4)),
            "startpoint": start.group(1) if start else None,
            "endpoint": endpoint.group(1) if endpoint else None,
            "launch_q_fanout": int(launch.group(1)) if launch else None,
        })
    return sorted(evidence, key=lambda x: (
        x["platform"], x["rows"], x["cols"], x["seed"]
    ))


def summarize(candidate: list[dict[str, str]],
              baseline: list[dict[str, str]],
              functional: bool,
              paths: list[dict[str, object]]) -> dict[str, object]:
    expected = {
        (p, s, r, c) for p in PLATFORMS for s in SEEDS
        for r, c in GEOMETRIES
    }
    actual = [
        (row["platform"], int(row["seed"]), int(row["rows"]), int(row["cols"]))
        for row in candidate
    ]
    exact = len(candidate) == 12 and set(actual) == expected and len(set(actual)) == 12
    clean = exact and all(
        row["topology"] == "criticalbit"
        and row["attempted"].lower() == "true"
        and good_route(row)
        for row in candidate
    )
    c_lookup = {
        (row["platform"], int(row["seed"]), int(row["rows"]), int(row["cols"])): row
        for row in candidate if good_route(row)
    }
    b_lookup = {
        (row["platform"], row["topology"], int(row["seed"]),
         int(row["rows"]), int(row["cols"])): row
        for row in baseline
        if row["platform"] in PLATFORMS
        and row["topology"] in ("broadcast", "local", "stride2")
        and int(row["seed"]) in SEEDS
        and (int(row["rows"]), int(row["cols"])) in GEOMETRIES
        and good_route(row)
    }
    triples = []
    for platform, seed, rows, cols in sorted(expected):
        c_row = c_lookup.get((platform, seed, rows, cols))
        refs = [b_lookup.get((platform, topology, seed, rows, cols))
                for topology in ("broadcast", "local", "stride2")]
        if c_row is None or any(row is None for row in refs):
            continue
        broadcast, local, stride = refs
        B, L, S, C = [
            float(row["period_min_ns"])
            for row in (broadcast, local, stride, c_row)
        ]
        Ab, Al, As, Ac = [
            float(row["cell_area_um2"])
            for row in (broadcast, local, stride, c_row)
        ]
        Dl, Ds, Dc = [
            int(row["dff_cells"]) for row in (local, stride, c_row)
        ]
        triples.append({
            "platform": platform, "seed": seed, "rows": rows, "cols": cols,
            "broadcast_period_ns": B, "local_period_ns": L,
            "stride2_period_ns": S, "criticalbit_period_ns": C,
            "criticalbit_q": (B-C)/B,
            "criticalbit_retained_benefit": (B-C)/(B-L) if B > L else None,
            "criticalbit_vs_broadcast_density": B*Ab/(C*Ac),
            "criticalbit_vs_local_density": L*Al/(C*Ac),
            "criticalbit_vs_stride2_density": S*As/(C*Ac),
            "local_dffs": Dl, "stride2_dffs": Ds, "criticalbit_dffs": Dc,
            "local_area_um2": Al, "stride2_area_um2": As,
            "criticalbit_area_um2": Ac,
        })
    groups: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in triples:
        groups[(str(row["platform"]), int(row["rows"]), int(row["cols"]))].append(row)
    points = []
    metrics = (
        "criticalbit_q", "criticalbit_retained_benefit",
        "criticalbit_vs_broadcast_density", "criticalbit_vs_local_density",
        "criticalbit_vs_stride2_density", "broadcast_period_ns",
        "local_period_ns", "stride2_period_ns", "criticalbit_period_ns",
        "local_dffs", "stride2_dffs", "criticalbit_dffs",
        "local_area_um2", "stride2_area_um2", "criticalbit_area_um2",
    )
    for (platform, rows, cols), group in sorted(groups.items()):
        if len(group) != 3:
            continue
        points.append({
            "platform": platform, "rows": rows, "cols": cols,
            **{f"median_{field}": statistics.median(float(x[field]) for x in group)
               for field in metrics},
        })
    joint_density = [
        p for p in points
        if p["median_criticalbit_vs_broadcast_density"] > 1
        and p["median_criticalbit_vs_local_density"] > 1
    ]
    target = next((p for p in points
                   if p["platform"] == "nangate45"
                   and p["rows"] == 8 and p["cols"] == 5), None)
    gates = {
        "functional_equivalence_on_opened_shapes": functional,
        "exactly_12_unique_candidate_attempts": exact,
        "all_12_candidate_routes_clean": clean,
        "all_four_groups_have_three_matched_seeds": len(points) == 4,
        "candidate_dffs_between_stride2_and_90pct_local": len(triples) == 12
            and all(x["stride2_dffs"] < x["criticalbit_dffs"]
                    <= .90*x["local_dffs"] for x in triples),
        "candidate_area_below_full_local": len(triples) == 12
            and all(x["criticalbit_area_um2"] < x["local_area_um2"] for x in triples),
        "median_raw_timing_benefit_at_least_5pct": len(points) == 4
            and all(x["median_criticalbit_q"] >= .05 for x in points),
        "median_retention_at_least_70pct": len(points) == 4
            and all(x["median_criticalbit_retained_benefit"] >= .70 for x in points),
        "density_wins_at_least_three_of_four": len(joint_density) >= 3,
        "density_win_on_each_platform": all(
            any(x["platform"] == platform for x in joint_density)
            for platform in PLATFORMS
        ),
        "target_nangate45_8x5_improves_stride2_by_0p02ns": target is not None
            and target["median_criticalbit_period_ns"]
                <= target["median_stride2_period_ns"] - .02,
    }
    return {
        "schema_version": 1,
        "opened_data_only": True,
        "attempted": len(candidate),
        "clean": sum(good_route(row) for row in candidate),
        "complete_matched_sets": len(triples),
        "gates": gates,
        "prospective_study_warranted": all(gates.values()),
        "points": points,
        "triples": triples,
        "critical_paths": paths,
        "all_candidate_routes": candidate,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--baseline", type=Path,
        default=ROOT / "results" / "similarity_stride2_download",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "similarity_criticalbit_summary.json",
    )
    args = parser.parse_args()
    candidate = load_csvs(args.input, "similarity_criticalbit_*.csv")
    baseline = load_csvs(args.baseline, "similarity_stride2_*.csv")
    functional = any(args.input.rglob("similarity_criticalbit_functional_passed"))
    result = summarize(candidate, baseline, functional, critical_path_evidence(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("points", "triples", "critical_paths",
                                     "all_candidate_routes")}, indent=2))
    return 0 if result["prospective_study_warranted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
