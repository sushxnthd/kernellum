#!/usr/bin/env python3
"""All-required gates for the flow-qualified prospective B-local study."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

from scripts.similarity_antenna_margin_canary import (
    ANTENNA_REMOVED,
    ANTENNA_REPLACEMENT,
    ANTENNA_TARGET,
    FINAL_REMOVED,
    FINAL_REPLACEMENT,
    FINAL_TARGET,
)
from scripts.similarity_blocal_qualified_route import (
    FIELDS,
    GEOMETRIES,
    PLATFORMS,
    RATIO_MARGIN,
    SEEDS,
    TOPOLOGIES,
)
from scripts.similarity_final_report_canary import IMAGE


ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_SHAPES = ((7, 10), (10, 7))
VIOLATIONS = (
    "setup_violations",
    "hold_violations",
    "max_slew_violations",
    "max_fanout_violations",
    "max_cap_violations",
    "drc_count",
    "final_antenna_net_violations",
    "final_antenna_pin_violations",
)
POSITIVE = (
    "period_min_ns",
    "fmax_mhz",
    "critical_path_delay_ns",
    "total_cells",
    "dff_cells",
    "cell_area_um2",
    "wire_length_um",
    "routed_cell_area_um2",
    "vectorless_power_w",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")


def identity(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"], row["topology"], int(row["seed"]),
        int(row["rows"]), int(row["cols"]),
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
            and float(row["cap_slack_fraction"]) >= 0.02
            and float(row["slew_slack_fraction"]) >= 0.02
            and all(re.fullmatch(r"[0-9a-f]{64}", row[field]) for field in HASHES)
        )
    except (KeyError, TypeError, ValueError):
        return False


def load_rows(root: Path) -> tuple[list[dict[str, str]], list[Path]]:
    paths = sorted(root.rglob("similarity_blocal_qualified_*.csv"))
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
    expected_logs = {f"tb_{rows}x{cols}.log" for _, rows, cols in GEOMETRIES}
    source_paths = list(root.rglob("source_sha.txt"))
    hash_paths = list(root.rglob("source_hashes.txt"))
    markers = list(root.rglob("similarity_blocal_qualified_functional_passed"))
    source_sha = (
        source_paths[0].read_text(encoding="utf-8").strip()
        if len(source_paths) == 1 else ""
    )
    functional = (
        len(logs) == 4
        and {path.name for path in logs} == expected_logs
        and len(source_paths) == len(hash_paths) == len(markers) == 1
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
        for platform in PLATFORMS for topology in TOPOLOGIES for seed in SEEDS
    }
    expected_patches = (
        (FINAL_TARGET, FINAL_REMOVED, FINAL_REPLACEMENT),
        (ANTENNA_TARGET, ANTENNA_REMOVED, ANTENNA_REPLACEMENT),
    )
    records = []
    for path in paths:
        item = json.loads(path.read_text(encoding="utf-8"))
        valid = (
            item.get("schema_version") == 1
            and item.get("orfs_image") == IMAGE
            and item.get("workflow_source_sha") == source_sha
            and item.get("antenna_ratio_margin") == RATIO_MARGIN
            and len(item.get("patches", [])) == 2
        )
        for patch, (target, removed, replacement) in zip(
            item.get("patches", []), expected_patches
        ):
            valid &= (
                patch.get("target") == f"flow/{target}"
                and patch.get("replacement_count") == 1
                and patch.get("removed_text") == removed
                and patch.get("replacement_text") == replacement
                and re.fullmatch(r"[0-9a-f]{64}", patch.get("before_sha256", ""))
                is not None
                and re.fullmatch(r"[0-9a-f]{64}", patch.get("after_sha256", ""))
                is not None
                and patch.get("before_sha256") != patch.get("after_sha256")
            )
        records.append({"file": path.name, "valid": bool(valid), **item})
    return (
        len(paths) == 18
        and {path.name for path in paths} == expected_names
        and all(record["valid"] for record in records),
        records,
    )


def evidence_key(path: Path, leaf: str) -> tuple[str, str, int, int, int] | None:
    seeds = "|".join(str(seed) for seed in SEEDS)
    dimensions = "|".join(
        str(value)
        for value in sorted({v for _, rows, cols in GEOMETRIES for v in (rows, cols)})
    )
    match = re.search(
        rf"(nangate45|sky130hd)/(broadcast|local|blocal)/s({seeds})/"
        rf"r({dimensions})_c({dimensions})/(?:reports|logs)?/?{re.escape(leaf)}$",
        path.as_posix(),
    )
    if match is None:
        return None
    platform, topology, seed, rows, cols = match.groups()
    key = platform, topology, int(seed), int(rows), int(cols)
    return key if key in expected_identities() else None


def report_metric(text: str, name: str) -> float | None:
    match = re.search(
        rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text
    )
    return float(match.group(1)) if match else None


def raw_evidence(root: Path) -> tuple[bool, list[dict[str, object]]]:
    expected = expected_identities()
    csv_rows, _ = load_rows(root)
    lookup = {identity(row): row for row in csv_rows}
    finish_paths = [path for path in root.rglob("6_finish.rpt")
                    if evidence_key(path, "6_finish.rpt") is not None]
    route_paths = [path for path in root.rglob("5_2_route.log")
                   if evidence_key(path, "5_2_route.log") is not None]
    drc_paths = [path for path in root.rglob("5_route_drc.rpt")
                 if evidence_key(path, "5_route_drc.rpt") is not None]
    driver_paths = [path for path in root.rglob("driver.log")
                    if evidence_key(path, "driver.log") is not None]
    finishes = {evidence_key(path, "6_finish.rpt"): path for path in finish_paths}
    routes = {evidence_key(path, "5_2_route.log"): path for path in route_paths}
    drcs = {evidence_key(path, "5_route_drc.rpt"): path for path in drc_paths}
    drivers = {evidence_key(path, "driver.log"): path for path in driver_paths}
    exact_files = all(
        len(paths) == len(mapping) == 72 and set(mapping) == expected
        for paths, mapping in (
            (finish_paths, finishes), (route_paths, routes),
            (drc_paths, drcs), (driver_paths, drivers),
        )
    )
    records = []
    for key in sorted(expected):
        row = lookup.get(key)
        finish_path, route_path = finishes.get(key), routes.get(key)
        drc_path, driver_path = drcs.get(key), drivers.get(key)
        if row is None or None in (finish_path, route_path, drc_path, driver_path):
            records.append({"identity": key, "complete": False})
            continue
        finish = finish_path.read_text(encoding="utf-8", errors="replace")
        route = route_path.read_text(encoding="utf-8", errors="replace")
        driver = driver_path.read_text(encoding="utf-8", errors="replace")
        cap = report_metric(finish, "max_capacitance_check_slack_limit")
        slew = report_metric(finish, "max_slew_check_slack_limit")
        areas = [float(x) for x in re.findall(
            r"Design area\s+([0-9.eE+-]+)\s+um\^2", route
        )]
        powers = [float(x) for x in re.findall(
            r"^Total\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+"
            r"([0-9.eE+-]+)\s+100\.0%\s*$", finish, re.MULTILINE
        )]
        nets = [int(x) for x in re.findall(r"Found (\d+) net violations\.", route)]
        pins = [int(x) for x in re.findall(r"Found (\d+) pin violations\.", route)]
        drt = [int(x) for x in re.findall(r"Number of violations = (\d+)\.", route)]
        section = finish.split("finish report_checks -path_delay max", 1)
        body = section[1] if len(section) == 2 else ""
        startpoint = re.search(r"Startpoint: (.+)", body)
        endpoint = re.search(r"Endpoint: (.+)", body)
        launch = re.search(
            r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+"
            r"[\^v]\s+.*?/Q\s+\(", body, re.MULTILINE,
        )
        values = (
            cap, slew, areas[-1] if areas else None, powers[-1] if powers else None,
            nets[-1] if nets else None, pins[-1] if pins else None,
        )
        same = all(value is not None for value in values)
        if same:
            same &= (
                math.isclose(float(row["cap_slack_fraction"]), cap, abs_tol=1e-12)
                and math.isclose(float(row["slew_slack_fraction"]), slew, abs_tol=1e-12)
                and math.isclose(float(row["routed_cell_area_um2"]), areas[-1], abs_tol=1e-6)
                and math.isclose(float(row["vectorless_power_w"]), powers[-1], abs_tol=1e-12)
                and int(row["final_antenna_net_violations"]) == nets[-1]
                and int(row["final_antenna_pin_violations"]) == pins[-1]
            )
        complete = bool(
            same and cap >= 0.02 and slew >= 0.02
            and nets[-1] == pins[-1] == 0 and drt and drt[-1] == 0
            and not drc_path.read_text(encoding="utf-8").strip()
            and "===== native finish" in driver
            and "Signal 11 received" not in driver and "make: ***" not in driver
            and startpoint and endpoint and launch
        )
        records.append({
            "identity": key, "complete": complete,
            "cap_slack_fraction": cap, "slew_slack_fraction": slew,
            "routed_cell_area_um2": areas[-1] if areas else None,
            "vectorless_power_w": powers[-1] if powers else None,
            "antenna_nets": nets[-1] if nets else None,
            "antenna_pins": pins[-1] if pins else None,
            "launch_q_fanout": int(launch.group(1)) if launch else None,
            "startpoint": startpoint.group(1) if startpoint else None,
            "endpoint": endpoint.group(1) if endpoint else None,
        })
    return (
        exact_files and len(records) == 72
        and all(item["complete"] for item in records),
        records,
    )


def summarize(root: Path) -> dict[str, object]:
    rows, csv_paths = load_rows(root)
    functional, source_sha = functional_evidence(root)
    patches_valid, patches = patch_evidence(root, source_sha)
    raw_valid, raw = raw_evidence(root)
    expected = expected_identities()
    identities = [identity(row) for row in rows]
    exact_rows = (
        len(csv_paths) == 18 and len(rows) == 72
        and len(set(identities)) == 72 and set(identities) == expected
    )
    clean_rows = [row for row in rows if clean_route(row)]
    lookup = {identity(row): row for row in clean_rows}

    matched = []
    for platform in PLATFORMS:
        for split, rows_count, cols_count in GEOMETRIES:
            for seed in SEEDS:
                trio = [lookup.get((platform, topology, seed, rows_count, cols_count))
                        for topology in TOPOLOGIES]
                if any(item is None for item in trio):
                    continue
                broadcast, local, candidate = trio
                bp, lp, cp = [float(item["period_min_ns"]) for item in trio]
                ba, la, ca = [float(item["cell_area_um2"]) for item in trio]
                bra, lra, cra = [float(item["routed_cell_area_um2"]) for item in trio]
                matched.append({
                    "platform": platform, "split": split,
                    "rows": rows_count, "cols": cols_count, "seed": seed,
                    "broadcast_period_ns": bp, "local_period_ns": lp,
                    "blocal_period_ns": cp,
                    "q_local": (bp - lp) / bp,
                    "q_candidate": (bp - cp) / bp,
                    "retention": (bp - cp) / (bp - lp) if bp > lp else None,
                    "synth_density_vs_broadcast": bp * ba / (cp * ca),
                    "synth_density_vs_local": lp * la / (cp * ca),
                    "routed_density_vs_broadcast": bp * bra / (cp * cra),
                    "routed_density_vs_local": lp * lra / (cp * cra),
                    "broadcast_dffs": int(broadcast["dff_cells"]),
                    "local_dffs": int(local["dff_cells"]),
                    "blocal_dffs": int(candidate["dff_cells"]),
                    "local_synth_area_um2": la, "blocal_synth_area_um2": ca,
                    "local_routed_area_um2": lra, "blocal_routed_area_um2": cra,
                    "local_wire_um": float(local["wire_length_um"]),
                    "blocal_wire_um": float(candidate["wire_length_um"]),
                    "broadcast_vectorless_power_w": float(broadcast["vectorless_power_w"]),
                    "local_vectorless_power_w": float(local["vectorless_power_w"]),
                    "blocal_vectorless_power_w": float(candidate["vectorless_power_w"]),
                })

    grouped: dict[tuple[str, str, int, int], list[dict[str, object]]] = defaultdict(list)
    for item in matched:
        grouped[(item["platform"], item["split"], item["rows"], item["cols"])].append(item)
    points = []
    for (platform, split, rows_count, cols_count), group in sorted(grouped.items()):
        if len(group) != 3:
            continue
        points.append({
            "platform": platform, "split": split,
            "rows": rows_count, "cols": cols_count,
            "median_q_local": statistics.median(x["q_local"] for x in group),
            "median_q_candidate": statistics.median(x["q_candidate"] for x in group),
            "median_retention": (
                statistics.median(x["retention"] for x in group)
                if all(x["retention"] is not None for x in group) else None
            ),
            "median_synth_density_vs_broadcast": statistics.median(
                x["synth_density_vs_broadcast"] for x in group
            ),
            "median_synth_density_vs_local": statistics.median(
                x["synth_density_vs_local"] for x in group
            ),
            "median_routed_density_vs_broadcast": statistics.median(
                x["routed_density_vs_broadcast"] for x in group
            ),
            "median_routed_density_vs_local": statistics.median(
                x["routed_density_vs_local"] for x in group
            ),
            "median_wire_ratio_vs_local": statistics.median(
                x["blocal_wire_um"] / x["local_wire_um"] for x in group
            ),
            "median_vectorless_power_ratio_vs_local": statistics.median(
                x["blocal_vectorless_power_w"] / x["local_vectorless_power_w"]
                for x in group
            ),
        })

    holdouts = [point for point in points if point["split"] == "holdout"]
    synth_winners = [point for point in holdouts
                     if point["median_synth_density_vs_broadcast"] >= 1.01
                     and point["median_synth_density_vs_local"] >= 1.01]
    routed_winners = [point for point in holdouts
                      if point["median_routed_density_vs_broadcast"] >= 1.01
                      and point["median_routed_density_vs_local"] >= 1.01]
    raw_lookup = {tuple(item["identity"]): item for item in raw if item.get("complete")}
    fanouts: dict[tuple[int, int], list[int]] = defaultdict(list)
    for rows_count, cols_count in HOLDOUT_SHAPES:
        for seed in SEEDS:
            item = raw_lookup.get(("nangate45", "blocal", seed, rows_count, cols_count))
            if item and item["launch_q_fanout"] is not None:
                fanouts[(rows_count, cols_count)].append(item["launch_q_fanout"])

    all_groups = len(points) == 8 and len(matched) == 24
    gates = {
        "signed_gemm_functional_on_all_four_unopened_shapes": functional,
        "exactly_18_shards_and_72_unique_attempted_rows": (
            exact_rows and all(row["attempted"].lower() == "true" for row in rows)
        ),
        "all_18_exact_headless_and_antenna_patch_manifests": patches_valid,
        "all_72_raw_reports_drivers_drc_and_route_logs_complete": raw_valid,
        "all_72_routes_clean_hashed_with_2pct_headroom_and_zero_antenna": (
            exact_rows and len(clean_rows) == 72
        ),
        "all_eight_groups_three_complete_matched_seeds": all_groups,
        "full_local_positive_each_group": (
            all_groups and all(point["median_q_local"] > 0 for point in points)
        ),
        "all_24_candidate_dffs_above_broadcast_and_at_most_90pct_local": (
            len(matched) == 24 and all(
                row["broadcast_dffs"] < row["blocal_dffs"]
                <= 0.90 * row["local_dffs"] for row in matched
            )
        ),
        "all_24_candidate_synthesis_and_routed_cell_areas_below_local": (
            len(matched) == 24 and all(
                row["blocal_synth_area_um2"] < row["local_synth_area_um2"]
                and row["blocal_routed_area_um2"] < row["local_routed_area_um2"]
                for row in matched
            )
        ),
        "all_12_holdout_seed_pairs_candidate_faster_than_broadcast": (
            len([row for row in matched if row["split"] == "holdout"]) == 12
            and all(row["blocal_period_ns"] < row["broadcast_period_ns"]
                    for row in matched if row["split"] == "holdout")
        ),
        "all_four_holdouts_raw_benefit_at_least_5pct": (
            len(holdouts) == 4
            and all(point["median_q_candidate"] >= 0.05 for point in holdouts)
        ),
        "all_four_holdouts_retention_at_least_70pct": (
            len(holdouts) == 4 and all(
                point["median_retention"] is not None
                and point["median_retention"] >= 0.70 for point in holdouts
            )
        ),
        "synthesis_area_normalized_wins_at_least_3_of_4_and_both_platforms": (
            len(synth_winners) >= 3 and all(
                any(point["platform"] == platform for point in synth_winners)
                for platform in PLATFORMS
            )
        ),
        "routed_area_normalized_wins_at_least_3_of_4_and_both_platforms": (
            len(routed_winners) >= 3 and all(
                any(point["platform"] == platform for point in routed_winners)
                for platform in PLATFORMS
            )
        ),
        "all_four_holdouts_median_wirelength_not_above_local": (
            len(holdouts) == 4
            and all(point["median_wire_ratio_vs_local"] <= 1.0 for point in holdouts)
        ),
        "nangate45_holdout_launch_q_fanout_at_most_10": (
            len(fanouts) == 2 and all(
                len(fanouts[shape]) == 3
                and statistics.median(fanouts[shape]) <= 10
                for shape in HOLDOUT_SHAPES
            )
        ),
    }
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "planned": 72, "attempted": len(rows), "clean": len(clean_rows),
        "matched": len(matched), "gates": gates,
        "frozen_claim_supported": all(gates.values()),
        "power_boundary": (
            "Vectorless OpenROAD total power is preserved descriptively only; "
            "no activity-file, workload-energy, or silicon-power claim is made."
        ),
        "points": points, "matched_rows": matched,
        "raw_evidence": raw, "patch_manifests": patches, "raw_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "similarity_blocal_qualified_summary.json",
    )
    args = parser.parse_args()
    data = summarize(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: data[key] for key in (
        "source_sha", "planned", "attempted", "clean", "matched",
        "gates", "frozen_claim_supported",
    )}, indent=2))
    return 0 if data["frozen_claim_supported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
