#!/usr/bin/env python3
"""Independent audit of the frozen B-local prospective ASIC study.

This checker intentionally does not import the frozen evaluator.  It rebuilds
the expected cohort, electrical predicates, paired statistics and evidence
counts directly from the archived CSVs and reports.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path


PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEEDS = (101, 131, 157)
GEOMETRIES = (
    ("discovery", 6, 8),
    ("discovery", 8, 6),
    ("holdout", 6, 9),
    ("holdout", 9, 6),
)
FIELDS = (
    "platform", "split", "topology", "rows", "cols", "pe_count",
    "sqrt_pe", "seed", "attempted", "route_ok", "error_stage",
    "period_min_ns", "fmax_mhz", "critical_path_delay_ns",
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
    "total_cells", "dff_cells", "cell_area_um2", "wire_length_um",
    "gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256",
    "elapsed_sec",
)
EXPECTED_ZIP_DIGESTS = {
    "similarity-blocal-prospective-route-nangate45-blocal-s101.zip": "9db027fc10b9d6045d4c3f7aed5dedbea795c5d0d0baa5fc115d421b05778aa9",
    "similarity-blocal-prospective-route-nangate45-blocal-s131.zip": "78210d38f4fcd0855da7dc27316847d0f46dcc70ab13fb5536139876f4f7c68d",
    "similarity-blocal-prospective-route-nangate45-blocal-s157.zip": "f22d71a041667e8392fcfb7d3961b3053fcddf49df3e7b9718d33951bf616c1e",
    "similarity-blocal-prospective-route-nangate45-broadcast-s101.zip": "7ae0157a173d46078361fa0a7756d399b44314f018fc528c0647c720a95b87ce",
    "similarity-blocal-prospective-route-nangate45-broadcast-s131.zip": "71a0eada84bd7ff7b088a33b4e769e5300bb94985ef20842f01ba699d592d7c0",
    "similarity-blocal-prospective-route-nangate45-broadcast-s157.zip": "ce9dd61506a158521f3f2880b42d2dc1405d3edf265ccb18db63aecd028271dc",
    "similarity-blocal-prospective-route-nangate45-local-s101.zip": "5538743c92c4fd19a5dfcc6ba65e1651482944b43a84a7d49b05e4144f9f789c",
    "similarity-blocal-prospective-route-nangate45-local-s131.zip": "66ed1989a4b6c3fa7296959ab9965b15ea03cacb8f2a5c436d3c88029ba331f2",
    "similarity-blocal-prospective-route-nangate45-local-s157.zip": "052dc9bd760c176a769d65f8628ab844db78a596be29063eb77a95a4e353069f",
    "similarity-blocal-prospective-route-sky130hd-blocal-s101.zip": "326e6f206de634e563004667a722e28cb45ab5de50911cc6bf99d06da8fc6ee8",
    "similarity-blocal-prospective-route-sky130hd-blocal-s131.zip": "4c73c12891bd51f51c843e436aa015b3e1c2e12a72a30e9c39396cb3d7219133",
    "similarity-blocal-prospective-route-sky130hd-blocal-s157.zip": "87e15625d76601fd5566465a3aa873af289b5cb3c73b2594cd808e08e2bc29e2",
    "similarity-blocal-prospective-route-sky130hd-broadcast-s101.zip": "e4697bf64c2af6298c996aedb7fbc30fef3e0867b9c49e10db6e5672794ffce8",
    "similarity-blocal-prospective-route-sky130hd-broadcast-s131.zip": "6b6fc173c5d2aa6bcac4d7d19eda4939cab61dff27fcf9bfd171641eeea91f60",
    "similarity-blocal-prospective-route-sky130hd-broadcast-s157.zip": "cadb3927d19dd0286215f43367fc2c6535102f76da38408324e329b7dd6b0ebf",
    "similarity-blocal-prospective-route-sky130hd-local-s101.zip": "9fca823d486226298852a7fc7b0a1cdcfbf9fd1cd9b2458ea20d108d6bbef5c6",
    "similarity-blocal-prospective-route-sky130hd-local-s131.zip": "345f5edc9e11c1871c24a7fadc1186728e5edbf2c9a626db8ccb86b8bbf033dc",
    "similarity-blocal-prospective-route-sky130hd-local-s157.zip": "48ce64ad54ae130dfd5a659ad666f998d6aec11123119986214c3cbd086bdb53",
}
FUNCTIONAL_DIGEST = "b26d067f824a2f8fe5478fb8f0478c6264131f54af31ee3c61076150da79be91"
SUMMARY_ZIP_DIGEST = "37b56e371e747d26737a3ee4b98e4b6277858f1454489ae758486beb725b7c76"
FROZEN_SHA = "3a0d7f7364f55ad0757964f3d8cb2eb43717c635"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"], row["topology"], int(row["seed"]),
        int(row["rows"]), int(row["cols"]),
    )


def positive_number(value: str) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def clean_route(row: dict[str, str]) -> bool:
    if row["attempted"].lower() != "true" or row["route_ok"].lower() != "true":
        return False
    if row["error_stage"]:
        return False
    for field in ("period_min_ns", "fmax_mhz", "critical_path_delay_ns",
                  "total_cells", "dff_cells", "cell_area_um2", "wire_length_um"):
        if not positive_number(row[field]):
            return False
    for field in ("setup_violations", "hold_violations", "max_slew_violations",
                  "max_fanout_violations", "max_cap_violations", "drc_count"):
        try:
            if int(row[field]) != 0:
                return False
        except (TypeError, ValueError):
            return False
    return all(re.fullmatch(r"[0-9a-f]{64}", row[field]) is not None
               for field in ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256"))


def load_rows(routes: Path) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    csv_files = sorted(routes.rglob("similarity_blocal_prospective_*.csv"))
    for path in csv_files:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != FIELDS:
                raise ValueError(f"schema mismatch: {path}")
            rows.extend(reader)
    return rows, [str(path) for path in csv_files]


def parse_paths(routes: Path) -> list[dict[str, object]]:
    expected = {(p, t, s, r, c) for p in PLATFORMS for t in TOPOLOGIES
                for s in SEEDS for _, r, c in GEOMETRIES}
    pattern = re.compile(
        r"(nangate45|sky130hd)/(broadcast|local|blocal)/s(101|131|157)/"
        r"r(6|8|9)_c(6|8|9)/reports/6_finish\.rpt$"
    )
    parsed: list[dict[str, object]] = []
    for path in sorted(routes.rglob("6_finish.rpt")):
        match = pattern.search(path.as_posix())
        if not match:
            continue
        platform, topology, seed, rows, cols = match.groups()
        key = platform, topology, int(seed), int(rows), int(cols)
        if key not in expected:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        section = text.split("finish report_checks -path_delay max", 1)
        body = section[1] if len(section) == 2 else ""
        start = re.search(r"Startpoint: (.+)", body)
        end = re.search(r"Endpoint: (.+)", body)
        launch = re.search(
            r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[\^v]\s+.*?/Q\s+\(",
            body, re.MULTILINE,
        )
        parsed.append({
            "platform": platform, "topology": topology, "seed": int(seed),
            "rows": int(rows), "cols": int(cols),
            "startpoint": start.group(1) if start else None,
            "endpoint": end.group(1) if end else None,
            "launch_q_fanout": int(launch.group(1)) if launch else None,
        })
    return parsed


def median(values):
    return statistics.median(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--functional", type=Path, required=True)
    parser.add_argument("--zips", type=Path, required=True)
    parser.add_argument("--functional-zip", type=Path, required=True)
    parser.add_argument("--summary-zip", type=Path, required=True)
    parser.add_argument("--frozen-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows, csv_files = load_rows(args.routes)
    expected = {(p, t, s, r, c) for p in PLATFORMS for t in TOPOLOGIES
                for s in SEEDS for _, r, c in GEOMETRIES}
    ids = [identity(row) for row in rows]
    exact = len(rows) == 72 and len(set(ids)) == 72 and set(ids) == expected
    clean_rows = [row for row in rows if clean_route(row)]
    lookup = {identity(row): row for row in clean_rows}

    matched = []
    for platform in PLATFORMS:
        for split, r, c in GEOMETRIES:
            for seed in SEEDS:
                trio = [lookup.get((platform, topology, seed, r, c))
                        for topology in TOPOLOGIES]
                if any(row is None for row in trio):
                    continue
                broadcast, local, candidate = trio
                bp, lp, cp = [float(row["period_min_ns"]) for row in trio]
                ba, la, ca = [float(row["cell_area_um2"]) for row in trio]
                matched.append({
                    "platform": platform, "split": split, "rows": r, "cols": c,
                    "seed": seed, "broadcast_period_ns": bp, "local_period_ns": lp,
                    "blocal_period_ns": cp, "q_local": (bp - lp) / bp,
                    "q_candidate": (bp - cp) / bp,
                    "retention": (bp - cp) / (bp - lp) if bp > lp else None,
                    "density_vs_broadcast": bp * ba / (cp * ca),
                    "density_vs_local": lp * la / (cp * ca),
                    "broadcast_dffs": int(broadcast["dff_cells"]),
                    "local_dffs": int(local["dff_cells"]),
                    "blocal_dffs": int(candidate["dff_cells"]),
                    "local_area_um2": la, "blocal_area_um2": ca,
                })

    grouped = defaultdict(list)
    for row in matched:
        grouped[(row["platform"], row["split"], row["rows"], row["cols"])].append(row)
    points = []
    for (platform, split, r, c), group in sorted(grouped.items()):
        if len(group) != 3:
            continue
        points.append({
            "platform": platform, "split": split, "rows": r, "cols": c,
            "median_q_local": median([x["q_local"] for x in group]),
            "median_q_candidate": median([x["q_candidate"] for x in group]),
            "median_retention": median([x["retention"] for x in group]),
            "median_density_vs_broadcast": median([x["density_vs_broadcast"] for x in group]),
            "median_density_vs_local": median([x["density_vs_local"] for x in group]),
        })
    holdouts = [point for point in points if point["split"] == "holdout"]
    winners = [point for point in holdouts
               if point["median_density_vs_broadcast"] >= 1.01
               and point["median_density_vs_local"] >= 1.01]

    paths = parse_paths(args.routes)
    path_ids = {(x["platform"], x["topology"], x["seed"], x["rows"], x["cols"])
                for x in paths}
    reports_complete = (len(paths) == 72 and len(path_ids) == 72
                        and all(x["startpoint"] and x["endpoint"]
                                and x["launch_q_fanout"] is not None for x in paths))
    fanouts = defaultdict(list)
    for item in paths:
        if (item["platform"] == "nangate45" and item["topology"] == "blocal"
                and (item["rows"], item["cols"]) in ((6, 9), (9, 6))):
            fanouts[(item["rows"], item["cols"])].append(item["launch_q_fanout"])

    logs = sorted(args.functional.glob("tb_*.log"))
    expected_logs = {"tb_6x8.log", "tb_8x6.log", "tb_6x9.log", "tb_9x6.log"}
    functional = ({x.name for x in logs} == expected_logs
                  and all("KERNELLUM_BLOCAL_EQUIVALENCE_PASS" in x.read_text() for x in logs)
                  and (args.functional / "source_sha.txt").read_text().strip() == FROZEN_SHA)

    gates = {
        "signed_gemm_functional_on_all_four_shapes": functional,
        "exactly_72_unique_attempted_routes": exact and all(x["attempted"].lower() == "true" for x in rows),
        "all_72_final_routes_electrically_and_drc_clean": exact and len(clean_rows) == 72,
        "all_72_final_critical_path_reports_present": reports_complete,
        "all_eight_groups_three_complete_matched_seeds": len(points) == 8 and len(matched) == 24,
        "full_local_positive_each_group": len(points) == 8 and all(x["median_q_local"] > 0 for x in points),
        "all_24_candidate_dffs_at_most_90pct_local_and_above_broadcast": len(matched) == 24 and all(
            x["broadcast_dffs"] < x["blocal_dffs"] <= 0.9 * x["local_dffs"] for x in matched),
        "all_24_candidate_synthesis_areas_below_local": len(matched) == 24 and all(
            x["blocal_area_um2"] < x["local_area_um2"] for x in matched),
        "all_four_holdouts_raw_benefit_at_least_5pct": len(holdouts) == 4 and all(
            x["median_q_candidate"] >= 0.05 for x in holdouts),
        "all_four_holdouts_retention_at_least_70pct": len(holdouts) == 4 and all(
            x["median_retention"] is not None and x["median_retention"] >= 0.70 for x in holdouts),
        "holdout_joint_density_wins_at_least_3_of_4_at_1pct": len(winners) >= 3,
        "holdout_joint_density_wins_on_both_platforms": all(
            any(x["platform"] == platform for x in winners) for platform in PLATFORMS),
        "nangate45_holdout_launch_q_fanout_at_most_10": len(fanouts) == 2 and all(
            len(fanouts[shape]) == 3 and median(fanouts[shape]) <= 10 for shape in ((6, 9), (9, 6))),
    }

    route_zip_digests = {
        path.name: sha256(path)
        for path in sorted(args.zips.glob("similarity-blocal-prospective-route-*.zip"))
    }
    artifact_integrity = (
        route_zip_digests == EXPECTED_ZIP_DIGESTS
        and sha256(args.functional_zip) == FUNCTIONAL_DIGEST
        and sha256(args.summary_zip) == SUMMARY_ZIP_DIGEST
    )
    frozen = json.loads(args.frozen_summary.read_text(encoding="utf-8"))
    failed_rows = [row for row in rows if not clean_route(row)]
    result = {
        "schema_version": 1,
        "auditor": "independent implementation; frozen evaluator not imported",
        "source_sha": FROZEN_SHA,
        "counts": {
            "route_zip_files": len(route_zip_digests),
            "route_csv_files": len(csv_files),
            "route_rows": len(rows),
            "clean_rows": len(clean_rows),
            "critical_path_reports": len(paths),
            "matched_trios": len(matched),
            "complete_groups": len(points),
            "functional_logs": len(logs),
        },
        "artifact_integrity": artifact_integrity,
        "route_zip_sha256": route_zip_digests,
        "failed_rows": failed_rows,
        "gates": gates,
        "frozen_claim_supported": all(gates.values()),
        "frozen_summary_consistency": {
            "counts_match": (frozen["attempted"] == len(rows)
                             and frozen["clean"] == len(clean_rows)
                             and frozen["matched"] == len(matched)),
            "gates_match": frozen["gates"] == gates,
            "decision_matches": frozen["frozen_claim_supported"] == all(gates.values()),
        },
        "descriptive_complete_groups": points,
        "descriptive_complete_trio_cost_checks": {
            "all_23_dff_checks_pass": len(matched) == 23 and all(
                x["broadcast_dffs"] < x["blocal_dffs"] <= 0.9 * x["local_dffs"] for x in matched),
            "all_23_area_checks_pass": len(matched) == 23 and all(
                x["blocal_area_um2"] < x["local_area_um2"] for x in matched),
            "all_7_complete_groups_full_local_positive": len(points) == 7 and all(
                x["median_q_local"] > 0 for x in points),
        },
        "nangate45_holdout_launch_q_fanouts": {
            f"{r}x{c}": sorted(fanouts[(r, c)]) for r, c in ((6, 9), (9, 6))
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "counts": result["counts"], "artifact_integrity": artifact_integrity,
        "gates": gates, "frozen_claim_supported": result["frozen_claim_supported"],
        "frozen_summary_consistency": result["frozen_summary_consistency"],
    }, indent=2))
    return 0 if (artifact_integrity and all(result["frozen_summary_consistency"].values())) else 2


if __name__ == "__main__":
    raise SystemExit(main())
