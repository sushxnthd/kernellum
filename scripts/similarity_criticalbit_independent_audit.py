#!/usr/bin/env python3
"""Independent report-level audit of the opened critical-bit diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

PLATFORMS = ("nangate45", "sky130hd")
SEEDS = (53, 71, 89)
SHAPES = ((5, 8), (8, 5))
VIOLATIONS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
)


def require(test: bool, message: str) -> None:
    if not test:
        raise AssertionError(message)


def rows_under(root: Path, pattern: str) -> list[dict[str, str]]:
    result = []
    for path in sorted(root.rglob(pattern)):
        with path.open(newline="", encoding="utf-8") as handle:
            result.extend(csv.DictReader(handle))
    return result


def key(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"], row["topology"], int(row["seed"]),
        int(row["rows"]), int(row["cols"]),
    )


def clean(row: dict[str, str]) -> bool:
    try:
        return (
            row["attempted"].lower() == row["route_ok"].lower() == "true"
            and all(int(row[field]) == 0 for field in VIOLATIONS)
            and all(math.isfinite(float(row[field])) and float(row[field]) > 0
                    for field in ("period_min_ns", "cell_area_um2",
                                  "wire_length_um", "dff_cells", "total_cells"))
            and all(re.fullmatch(r"[0-9a-f]{64}", row[field])
                    for field in ("gds_sha256", "odb_sha256",
                                  "spef_sha256", "netlist_sha256"))
        )
    except (KeyError, ValueError):
        return False


def report_number(pattern: str, text: str, name: str) -> float:
    match = re.search(pattern, text, re.MULTILINE)
    require(match is not None, f"missing {name}")
    return float(match.group(1))


def audit_reports(root: Path, candidate: list[dict[str, str]]) -> None:
    reports = {path.as_posix(): path for path in root.rglob("6_finish.rpt")}
    for row in candidate:
        p, _, seed, rows, cols = key(row)
        suffix = (
            f"/{p}/criticalbit/s{seed}/r{rows}_c{cols}/reports/6_finish.rpt"
        )
        matches = [path for name, path in reports.items() if name.endswith(suffix)]
        require(len(matches) == 1, f"missing/duplicate finish report {suffix}")
        report_dir = matches[0].parent
        finish = matches[0].read_text(encoding="utf-8", errors="replace")
        synth = (report_dir / "synth_stat.txt").read_text(
            encoding="utf-8", errors="replace"
        )
        drc = (report_dir / "5_route_drc.rpt").read_text(
            encoding="utf-8", errors="replace"
        ).strip()
        logs = list(report_dir.parent.glob("logs/5_2_route.log"))
        require(len(logs) == 1, f"missing route log {suffix}")
        route_log = logs[0].read_text(encoding="utf-8", errors="replace")
        wires = re.findall(
            r"^Total wire length =\s*([0-9.eE+-]+)\s+um\.",
            route_log, re.MULTILINE,
        )
        require(wires, f"missing wire length {suffix}")
        require(float(row["period_min_ns"]) == report_number(
            r"^clk period_min =\s*([0-9.eE+-]+)", finish, "period"
        ), f"period mismatch {suffix}")
        require(float(row["cell_area_um2"]) == report_number(
            r"Chip area for module '[^']+':\s*([0-9.eE+-]+)",
            synth, "cell area",
        ), f"area mismatch {suffix}")
        require(float(row["wire_length_um"]) == float(wires[-1]),
                f"wire mismatch {suffix}")
        require(int(row["drc_count"]) == (len(drc.splitlines()) if drc else 0),
                f"DRC mismatch {suffix}")
        for label, field in (
            ("setup", "setup_violations"), ("hold", "hold_violations"),
            ("max slew", "max_slew_violations"),
            ("max fanout", "max_fanout_violations"),
            ("max cap", "max_cap_violations"),
        ):
            require(int(row[field]) == report_number(
                rf"^{label} violation count\s+(\d+)\s*$", finish, field
            ), f"{field} mismatch {suffix}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    candidate = rows_under(args.input, "similarity_criticalbit_*.csv")
    baseline = rows_under(args.baseline, "similarity_stride2_*.csv")
    expected = {
        (p, "criticalbit", seed, rows, cols)
        for p in PLATFORMS for seed in SEEDS for rows, cols in SHAPES
    }
    require(len(candidate) == 12 and {key(row) for row in candidate} == expected,
            "candidate matrix mismatch")
    require(all(clean(row) for row in candidate), "candidate route not clean")
    audit_reports(args.input, candidate)
    functional = any(args.input.rglob("similarity_criticalbit_functional_passed"))
    require(functional, "functional marker missing")
    source = next(args.input.rglob("source_sha.txt")).read_text().strip()
    require(source == "7b243236694885fc69affff10fcb6fa83b13c7f1",
            "wrong source commit")

    lookup = {key(row): row for row in baseline}
    c_lookup = {key(row): row for row in candidate}
    triples = []
    for p in PLATFORMS:
        for rows, cols in SHAPES:
            for seed in SEEDS:
                b, l, s = [
                    lookup[p, topology, seed, rows, cols]
                    for topology in ("broadcast", "local", "stride2")
                ]
                c = c_lookup[p, "criticalbit", seed, rows, cols]
                B, L, S, C = [float(x["period_min_ns"]) for x in (b, l, s, c)]
                Ab, Al, As, Ac = [float(x["cell_area_um2"]) for x in (b, l, s, c)]
                triples.append({
                    "platform": p, "rows": rows, "cols": cols, "seed": seed,
                    "q": (B-C)/B, "retained": (B-C)/(B-L),
                    "db": B*Ab/(C*Ac), "dl": L*Al/(C*Ac),
                    "ds": S*As/(C*Ac), "B": B, "L": L, "S": S, "C": C,
                    "Dl": int(l["dff_cells"]), "Ds": int(s["dff_cells"]),
                    "Dc": int(c["dff_cells"]), "Al": Al, "Ac": Ac,
                })
    grouped: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in triples:
        grouped[row["platform"], row["rows"], row["cols"]].append(row)
    points = []
    for (p, rows, cols), group in sorted(grouped.items()):
        points.append({
            "platform": p, "rows": rows, "cols": cols,
            **{name: statistics.median(float(x[name]) for x in group)
               for name in ("q", "retained", "db", "dl", "ds",
                            "B", "L", "S", "C")},
        })
    wins = [point for point in points if point["db"] > 1 and point["dl"] > 1]
    target = next(point for point in points
                  if point["platform"] == "nangate45"
                  and (point["rows"], point["cols"]) == (8, 5))
    gates = {
        "functional_equivalence_on_opened_shapes": functional,
        "exactly_12_unique_candidate_attempts": len(candidate) == 12,
        "all_12_candidate_routes_clean": all(clean(row) for row in candidate),
        "all_four_groups_have_three_matched_seeds": all(
            len(group) == 3 for group in grouped.values()
        ) and len(grouped) == 4,
        "candidate_dffs_between_stride2_and_90pct_local": all(
            x["Ds"] < x["Dc"] <= .90*x["Dl"] for x in triples
        ),
        "candidate_area_below_full_local": all(x["Ac"] < x["Al"] for x in triples),
        "median_raw_timing_benefit_at_least_5pct": all(x["q"] >= .05 for x in points),
        "median_retention_at_least_70pct": all(x["retained"] >= .70 for x in points),
        "density_wins_at_least_three_of_four": len(wins) >= 3,
        "density_win_on_each_platform": all(
            any(x["platform"] == p for x in wins) for p in PLATFORMS
        ),
        "target_nangate45_8x5_improves_stride2_by_0p02ns":
            target["C"] <= target["S"] - .02,
    }
    summary = json.loads(args.summary.read_text())
    require(gates == summary["gates"], "independent gate vector mismatch")
    require(all(gates.values()) == summary["prospective_study_warranted"],
            "independent decision mismatch")
    print(json.dumps({
        "rows_checked": len(candidate), "reports_checked": len(candidate),
        "gates": gates, "prospective_study_warranted": all(gates.values()),
        "points": points,
    }, indent=2))


if __name__ == "__main__":
    main()
