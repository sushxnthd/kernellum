#!/usr/bin/env python3
"""Independently reproduce every preserved-physical diagnostic gate."""

from __future__ import annotations

import csv
import argparse
import io
import json
import re
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path

from scripts.similarity_asic_transfer_route import FIELDS
from scripts.similarity_stride2_validate import good_route

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "results" / "similarity_preserved_artifacts"
DOWNLOAD = ROOT / "results" / "similarity_preserved_download"
SOURCE_SHA = "9678983c99e4cf282b47a50e2deaea67397926a9"
PLATFORMS = ("nangate45", "sky130hd")
GEOMETRIES = ((5, 8), (8, 5))
SEEDS = (53, 71, 89)
EXPECTED_DFFS = {(5, 8): 1899, (8, 5): 1872}


def load_repo_csvs(root: Path, pattern: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(root.rglob(pattern)):
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(FIELDS):
                raise ValueError(f"unexpected route schema: {path}")
            rows.extend(reader)
    return rows


def load_candidate_artifacts(
    root: Path,
) -> tuple[list[dict[str, str]], bool, str, list[dict[str, object]]]:
    rows: list[dict[str, str]] = []
    paths: list[dict[str, object]] = []
    functional = False
    functional_sha = ""
    route_pattern = re.compile(
        r"(nangate45|sky130hd)/preserved/s(53|71|89)/"
        r"r(5|8)_c(8|5)/reports/6_finish\.rpt$"
    )
    launch_pattern = re.compile(
        r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+"
        r"[0-9.]+\s+[\^v]\s+.*?/Q\s+\(", re.MULTILINE,
    )
    for archive in sorted(root.rglob("similarity-preserved-*.zip")):
        with zipfile.ZipFile(archive) as zipped:
            for name in zipped.namelist():
                if name.endswith("similarity_preserved_functional_passed"):
                    functional = True
                elif name.endswith("source_sha.txt") and "functional" in archive.name:
                    functional_sha = zipped.read(name).decode().strip()
                elif name.endswith(".csv"):
                    reader = csv.DictReader(io.StringIO(zipped.read(name).decode()))
                    if reader.fieldnames != list(FIELDS):
                        raise ValueError(f"unexpected route schema: {archive}:{name}")
                    rows.extend(reader)
                elif name.endswith("6_finish.rpt"):
                    match = route_pattern.search(name)
                    if not match:
                        continue
                    text = zipped.read(name).decode(errors="replace")
                    section = text.split("finish report_checks -path_delay max", 1)
                    if len(section) != 2:
                        raise ValueError(f"missing maximum path: {archive}:{name}")
                    launch = launch_pattern.search(section[1])
                    paths.append({
                        "platform": match.group(1),
                        "seed": int(match.group(2)),
                        "rows": int(match.group(3)),
                        "cols": int(match.group(4)),
                        "launch_q_fanout": int(launch.group(1)) if launch else None,
                    })
    return rows, functional, functional_sha, paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=ARTIFACTS)
    parser.add_argument("--download", type=Path, default=DOWNLOAD)
    parser.add_argument(
        "--baseline", type=Path,
        default=ROOT / "results" / "similarity_stride2_download",
    )
    parser.add_argument(
        "--prior", type=Path,
        default=ROOT / "results" / "similarity_criticalbit_download",
    )
    args = parser.parse_args()
    candidate, functional, functional_sha, paths = load_candidate_artifacts(
        args.artifacts
    )
    baseline = load_repo_csvs(
        args.baseline,
        "similarity_stride2_*.csv",
    )
    prior = load_repo_csvs(
        args.prior,
        "similarity_criticalbit_*.csv",
    )
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
        x["topology"] == "preserved" and x["attempted"].lower() == "true"
        and good_route(x) for x in candidate
    )
    c_lookup = {
        (x["platform"], int(x["seed"]), int(x["rows"]), int(x["cols"])): x
        for x in candidate if good_route(x)
    }
    b_lookup = {
        (x["platform"], x["topology"], int(x["seed"]),
         int(x["rows"]), int(x["cols"])): x
        for x in baseline if x["platform"] in PLATFORMS
        and x["topology"] in ("broadcast", "local", "stride2")
        and int(x["seed"]) in SEEDS
        and (int(x["rows"]), int(x["cols"])) in GEOMETRIES and good_route(x)
    }
    n_lookup = {
        (x["platform"], int(x["seed"]), int(x["rows"]), int(x["cols"])): x
        for x in prior if x["topology"] == "criticalbit" and good_route(x)
    }
    matched = []
    for platform, seed, rows, cols in sorted(expected):
        cand = c_lookup.get((platform, seed, rows, cols))
        refs = [b_lookup.get((platform, t, seed, rows, cols))
                for t in ("broadcast", "local", "stride2")]
        noop = n_lookup.get((platform, seed, rows, cols))
        if cand is None or any(x is None for x in refs) or noop is None:
            continue
        broadcast, local, stride = refs
        b, l, s, n, c = [float(x["period_min_ns"]) for x in
                          (broadcast, local, stride, noop, cand)]
        ab, al, ac = [float(x["cell_area_um2"]) for x in
                      (broadcast, local, cand)]
        matched.append({
            "platform": platform, "rows": rows, "cols": cols,
            "broadcast_period": b, "local_period": l, "stride_period": s,
            "noop_period": n, "candidate_period": c,
            "q": (b-c)/b, "retention": (b-c)/(b-l),
            "density_b": b*ab/(c*ac), "density_l": l*al/(c*ac),
            "candidate_dffs": int(cand["dff_cells"]),
            "local_dffs": int(local["dff_cells"]),
            "candidate_area": ac, "local_area": al,
        })
    groups: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in matched:
        groups[(str(row["platform"]), int(row["rows"]), int(row["cols"]))].append(row)
    metrics = (
        "broadcast_period", "local_period", "stride_period", "noop_period",
        "candidate_period", "q", "retention", "density_b", "density_l",
    )
    points = []
    for (platform, rows, cols), group in sorted(groups.items()):
        if len(group) == 3:
            points.append({
                "platform": platform, "rows": rows, "cols": cols,
                **{m: statistics.median(float(x[m]) for x in group)
                   for m in metrics},
            })
    density = [x for x in points if x["density_b"] > 1 and x["density_l"] > 1]
    target = next((x for x in points if x["platform"] == "nangate45"
                   and x["rows"] == 8 and x["cols"] == 5), None)
    target_fanouts = [int(x["launch_q_fanout"]) for x in paths
                      if x["platform"] == "nangate45" and x["rows"] == 8
                      and x["cols"] == 5 and x["launch_q_fanout"] is not None]
    gates = {
        "functional_equivalence_on_opened_shapes": functional
            and functional_sha == SOURCE_SHA,
        "exactly_12_unique_candidate_attempts": exact,
        "all_12_candidate_routes_clean": clean,
        "all_four_groups_have_three_matched_seeds": len(points) == 4,
        "exact_preserved_dff_counts": len(matched) == 12 and all(
            x["candidate_dffs"] == EXPECTED_DFFS[(x["rows"], x["cols"])]
            for x in matched
        ),
        "candidate_dffs_at_most_90pct_local": len(matched) == 12 and all(
            x["candidate_dffs"] <= .90*x["local_dffs"] for x in matched
        ),
        "candidate_area_below_full_local": len(matched) == 12 and all(
            x["candidate_area"] < x["local_area"] for x in matched
        ),
        "median_raw_timing_benefit_at_least_5pct": len(points) == 4 and all(
            x["q"] >= .05 for x in points
        ),
        "median_retention_at_least_70pct": len(points) == 4 and all(
            x["retention"] >= .70 for x in points
        ),
        "density_wins_at_least_three_of_four": len(density) >= 3,
        "density_win_on_each_platform": all(
            any(x["platform"] == p for x in density) for p in PLATFORMS
        ),
        "target_improves_stride2_by_0p04ns": target is not None and
            target["candidate_period"] <= target["stride_period"] - .04,
        "target_improves_noop_by_0p02ns": target is not None and
            target["candidate_period"] <= target["noop_period"] - .02,
        "target_median_launch_q_fanout_at_most_10": len(target_fanouts) == 3
            and statistics.median(target_fanouts) <= 10,
    }
    frozen = json.loads((args.download / "similarity_preserved_summary.json").read_text())
    result = {
        "source_sha": SOURCE_SHA,
        "attempted": len(candidate),
        "clean": sum(good_route(x) for x in candidate),
        "complete_matched_sets": len(matched),
        "gates": gates,
        "prospective_study_warranted": all(gates.values()),
        "matches_frozen_gates": gates == frozen["gates"],
        "matches_frozen_decision": all(gates.values()) ==
            frozen["prospective_study_warranted"],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["matches_frozen_gates"] and result["matches_frozen_decision"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
