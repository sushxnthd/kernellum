#!/usr/bin/env python3
"""All-required frozen gates for the prospective B-local replication."""

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
from scripts.similarity_blocal_replication_route import (
    GEOMETRIES,
    PLATFORMS,
    SEEDS,
    TOPOLOGIES,
)
from scripts.similarity_final_report_canary import IMAGE, REMOVED, REPLACEMENT


ROOT = Path(__file__).resolve().parents[1]
VIOLATIONS = (
    "setup_violations",
    "hold_violations",
    "max_slew_violations",
    "max_fanout_violations",
    "max_cap_violations",
    "drc_count",
)
POSITIVE = (
    "period_min_ns",
    "fmax_mhz",
    "critical_path_delay_ns",
    "total_cells",
    "dff_cells",
    "cell_area_um2",
    "wire_length_um",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")
HOLDOUT_SHAPES = ((7, 8), (8, 7))


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"],
        row["topology"],
        int(row["seed"]),
        int(row["rows"]),
        int(row["cols"]),
    )


def expected_identities() -> set[tuple[str, str, int, int, int]]:
    return {
        (platform, topology, seed, rows, cols)
        for platform in PLATFORMS
        for topology in TOPOLOGIES
        for seed in SEEDS
        for _, rows, cols in GEOMETRIES
    }


def positive(value: str) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def clean_route(row: dict[str, str]) -> bool:
    try:
        return (
            row["attempted"].lower() == "true"
            and row["route_ok"].lower() == "true"
            and not row["error_stage"]
            and all(row[field] != "" and int(row[field]) == 0 for field in VIOLATIONS)
            and all(positive(row[field]) for field in POSITIVE)
            and all(re.fullmatch(r"[0-9a-f]{64}", row[field]) is not None
                    for field in HASHES)
        )
    except (KeyError, TypeError, ValueError):
        return False


def load_rows(root: Path) -> tuple[list[dict[str, str]], list[Path]]:
    paths = sorted(root.rglob("similarity_blocal_replication_*.csv"))
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != list(FIELDS):
                raise ValueError(f"route schema mismatch: {path}")
            rows.extend(reader)
    return rows, paths


def functional_evidence(root: Path) -> tuple[bool, str]:
    logs = sorted(root.rglob("tb_*.log"))
    expected = {f"tb_{rows}x{cols}.log" for _, rows, cols in GEOMETRIES}
    source_paths = list(root.rglob("source_sha.txt"))
    hash_paths = list(root.rglob("source_hashes.txt"))
    markers = list(root.rglob("similarity_blocal_replication_functional_passed"))
    source_sha = (
        source_paths[0].read_text(encoding="utf-8").strip()
        if len(source_paths) == 1
        else ""
    )
    functional = (
        {path.name for path in logs} == expected
        and len(logs) == 4
        and len(source_paths) == 1
        and len(hash_paths) == 1
        and len(markers) == 1
        and re.fullmatch(r"[0-9a-f]{40}", source_sha) is not None
        and all(
            f"KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows={rows} cols={cols}"
            in next(path for path in logs if path.name == f"tb_{rows}x{cols}.log")
            .read_text(encoding="utf-8", errors="replace")
            for _, rows, cols in GEOMETRIES
        )
    )
    return functional, source_sha


def patch_evidence(root: Path, source_sha: str) -> tuple[bool, list[dict[str, object]]]:
    paths = sorted(root.rglob("flow_patch_*.json"))
    expected_names = {
        f"flow_patch_{platform}_{topology}_s{seed}.json"
        for platform in PLATFORMS
        for topology in TOPOLOGIES
        for seed in SEEDS
    }
    records = []
    for path in paths:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        valid = (
            manifest.get("schema_version") == 1
            and manifest.get("orfs_image") == IMAGE
            and manifest.get("workflow_source_sha") == source_sha
            and manifest.get("target") == "flow/scripts/final_outputs.tcl"
            and manifest.get("replacement_count") == 1
            and manifest.get("removed_text") == REMOVED
            and manifest.get("replacement_text") == REPLACEMENT
            and re.fullmatch(r"[0-9a-f]{64}", manifest.get("before_sha256", ""))
            is not None
            and re.fullmatch(r"[0-9a-f]{64}", manifest.get("after_sha256", ""))
            is not None
            and manifest.get("before_sha256") != manifest.get("after_sha256")
        )
        records.append({"file": path.name, "valid": valid, **manifest})
    valid = (
        len(paths) == 18
        and {path.name for path in paths} == expected_names
        and all(record["valid"] for record in records)
    )
    return valid, records


def report_evidence(root: Path) -> list[dict[str, object]]:
    seed_pattern = "|".join(str(seed) for seed in SEEDS)
    dimension_pattern = "|".join(
        str(value) for value in sorted({v for _, rows, cols in GEOMETRIES for v in (rows, cols)})
    )
    pattern = re.compile(
        rf"(nangate45|sky130hd)/(broadcast|local|blocal)/"
        rf"s({seed_pattern})/r({dimension_pattern})_c({dimension_pattern})/"
        r"reports/6_finish\.rpt$"
    )
    expected = expected_identities()
    paths = []
    for path in sorted(root.rglob("6_finish.rpt")):
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
        startpoint = re.search(r"Startpoint: (.+)", body)
        endpoint = re.search(r"Endpoint: (.+)", body)
        launch = re.search(
            r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+"
            r"[\^v]\s+.*?/Q\s+\(",
            body,
            re.MULTILINE,
        )
        paths.append({
            "platform": platform,
            "topology": topology,
            "seed": int(seed),
            "rows": int(rows),
            "cols": int(cols),
            "startpoint": startpoint.group(1) if startpoint else None,
            "endpoint": endpoint.group(1) if endpoint else None,
            "launch_q_fanout": int(launch.group(1)) if launch else None,
        })
    return paths


def driver_evidence(root: Path) -> list[dict[str, object]]:
    seed_pattern = "|".join(str(seed) for seed in SEEDS)
    dimension_pattern = "|".join(
        str(value) for value in sorted({v for _, rows, cols in GEOMETRIES for v in (rows, cols)})
    )
    pattern = re.compile(
        rf"(nangate45|sky130hd)/(broadcast|local|blocal)/"
        rf"s({seed_pattern})/r({dimension_pattern})_c({dimension_pattern})/driver\.log$"
    )
    expected = expected_identities()
    records = []
    for path in sorted(root.rglob("driver.log")):
        match = pattern.search(path.as_posix())
        if not match:
            continue
        platform, topology, seed, rows, cols = match.groups()
        key = platform, topology, int(seed), int(rows), int(cols)
        if key not in expected:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        records.append({
            "platform": platform,
            "topology": topology,
            "seed": int(seed),
            "rows": int(rows),
            "cols": int(cols),
            "native_finish": "===== native finish" in text,
            "signal_11": "Signal 11 received" in text,
            "make_failure": "make: ***" in text,
        })
    return records


def summarize(root: Path) -> dict[str, object]:
    rows, csv_paths = load_rows(root)
    functional, source_sha = functional_evidence(root)
    patches_valid, patches = patch_evidence(root, source_sha)
    paths = report_evidence(root)
    drivers = driver_evidence(root)

    expected = expected_identities()
    identities = [identity(row) for row in rows]
    exact_rows = (
        len(rows) == 72
        and len(set(identities)) == 72
        and set(identities) == expected
    )
    clean_rows = [row for row in rows if clean_route(row)]
    lookup = {identity(row): row for row in clean_rows}

    matched = []
    for platform in PLATFORMS:
        for split, rows_count, cols_count in GEOMETRIES:
            for seed in SEEDS:
                trio = [
                    lookup.get((platform, topology, seed, rows_count, cols_count))
                    for topology in TOPOLOGIES
                ]
                if any(item is None for item in trio):
                    continue
                broadcast, local, candidate = trio
                broadcast_period, local_period, candidate_period = [
                    float(item["period_min_ns"]) for item in trio
                ]
                broadcast_area, local_area, candidate_area = [
                    float(item["cell_area_um2"]) for item in trio
                ]
                matched.append({
                    "platform": platform,
                    "split": split,
                    "rows": rows_count,
                    "cols": cols_count,
                    "seed": seed,
                    "broadcast_period_ns": broadcast_period,
                    "local_period_ns": local_period,
                    "blocal_period_ns": candidate_period,
                    "q_local": (broadcast_period - local_period) / broadcast_period,
                    "q_candidate": (broadcast_period - candidate_period) / broadcast_period,
                    "retention": (
                        (broadcast_period - candidate_period)
                        / (broadcast_period - local_period)
                        if broadcast_period > local_period
                        else None
                    ),
                    "density_vs_broadcast": (
                        broadcast_period * broadcast_area
                        / (candidate_period * candidate_area)
                    ),
                    "density_vs_local": (
                        local_period * local_area
                        / (candidate_period * candidate_area)
                    ),
                    "broadcast_dffs": int(broadcast["dff_cells"]),
                    "local_dffs": int(local["dff_cells"]),
                    "blocal_dffs": int(candidate["dff_cells"]),
                    "local_area_um2": local_area,
                    "blocal_area_um2": candidate_area,
                })

    groups: dict[tuple[str, str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in matched:
        groups[(row["platform"], row["split"], row["rows"], row["cols"])].append(row)
    points = []
    for (platform, split, rows_count, cols_count), group in sorted(groups.items()):
        if len(group) != 3:
            continue
        points.append({
            "platform": platform,
            "split": split,
            "rows": rows_count,
            "cols": cols_count,
            "median_q_local": statistics.median(x["q_local"] for x in group),
            "median_q_candidate": statistics.median(x["q_candidate"] for x in group),
            "median_retention": (
                statistics.median(x["retention"] for x in group)
                if all(x["retention"] is not None for x in group)
                else None
            ),
            "median_density_vs_broadcast": statistics.median(
                x["density_vs_broadcast"] for x in group
            ),
            "median_density_vs_local": statistics.median(
                x["density_vs_local"] for x in group
            ),
        })

    holdouts = [point for point in points if point["split"] == "holdout"]
    winners = [
        point for point in holdouts
        if point["median_density_vs_broadcast"] >= 1.01
        and point["median_density_vs_local"] >= 1.01
    ]
    path_ids = {
        (x["platform"], x["topology"], x["seed"], x["rows"], x["cols"])
        for x in paths
    }
    driver_ids = {
        (x["platform"], x["topology"], x["seed"], x["rows"], x["cols"])
        for x in drivers
    }
    fanouts: dict[tuple[int, int], list[int]] = defaultdict(list)
    for path in paths:
        if (
            path["platform"] == "nangate45"
            and path["topology"] == "blocal"
            and (path["rows"], path["cols"]) in HOLDOUT_SHAPES
            and path["launch_q_fanout"] is not None
        ):
            fanouts[(path["rows"], path["cols"])].append(path["launch_q_fanout"])

    evidence_complete = (
        len(csv_paths) == 18
        and len(paths) == 72
        and path_ids == expected
        and all(path["startpoint"] and path["endpoint"]
                and path["launch_q_fanout"] is not None for path in paths)
        and len(drivers) == 72
        and driver_ids == expected
    )
    driver_clean = evidence_complete and all(
        driver["native_finish"]
        and not driver["signal_11"]
        and not driver["make_failure"]
        for driver in drivers
    )
    gates = {
        "signed_gemm_functional_on_all_four_shapes": functional,
        "exactly_18_shards_72_rows_reports_and_drivers": evidence_complete,
        "all_18_headless_patch_manifests_exact": patches_valid,
        "all_72_drivers_native_finish_without_signal_or_make_failure": driver_clean,
        "exactly_72_unique_attempted_routes": (
            exact_rows and all(row["attempted"].lower() == "true" for row in rows)
        ),
        "all_72_final_routes_electrically_and_drc_clean": (
            exact_rows and len(clean_rows) == 72
        ),
        "all_eight_groups_three_complete_matched_seeds": (
            len(points) == 8 and len(matched) == 24
        ),
        "full_local_positive_each_group": (
            len(points) == 8 and all(point["median_q_local"] > 0 for point in points)
        ),
        "all_24_candidate_dffs_at_most_90pct_local_and_above_broadcast": (
            len(matched) == 24
            and all(
                row["broadcast_dffs"] < row["blocal_dffs"]
                <= 0.90 * row["local_dffs"]
                for row in matched
            )
        ),
        "all_24_candidate_synthesis_areas_below_local": (
            len(matched) == 24
            and all(row["blocal_area_um2"] < row["local_area_um2"] for row in matched)
        ),
        "all_four_holdouts_raw_benefit_at_least_5pct": (
            len(holdouts) == 4
            and all(point["median_q_candidate"] >= 0.05 for point in holdouts)
        ),
        "all_four_holdouts_retention_at_least_70pct": (
            len(holdouts) == 4
            and all(point["median_retention"] is not None
                    and point["median_retention"] >= 0.70 for point in holdouts)
        ),
        "holdout_joint_density_wins_at_least_3_of_4_at_1pct": len(winners) >= 3,
        "holdout_joint_density_wins_on_both_platforms": all(
            any(point["platform"] == platform for point in winners)
            for platform in PLATFORMS
        ),
        "nangate45_holdout_launch_q_fanout_at_most_10": (
            len(fanouts) == 2
            and all(
                len(fanouts[shape]) == 3
                and statistics.median(fanouts[shape]) <= 10
                for shape in HOLDOUT_SHAPES
            )
        ),
    }
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "planned": 72,
        "attempted": len(rows),
        "clean": len(clean_rows),
        "matched": len(matched),
        "gates": gates,
        "frozen_claim_supported": all(gates.values()),
        "points": points,
        "matched_rows": matched,
        "critical_paths": paths,
        "drivers": drivers,
        "patch_manifests": patches,
        "raw_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "similarity_blocal_replication_summary.json",
    )
    args = parser.parse_args()
    data = summarize(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        key: data[key]
        for key in (
            "source_sha", "planned", "attempted", "clean", "matched",
            "gates", "frozen_claim_supported",
        )
    }, indent=2))
    return 0 if data["frozen_claim_supported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
