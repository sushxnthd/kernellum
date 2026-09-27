#!/usr/bin/env python3
"""Independent raw-artifact audit for Actions run 36298460695.

This checker deliberately imports no Kernellum evaluator or route module.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path


SOURCE_SHA = "8aba1ab82c9cfec0388c4ff3bfd6999c8f36cddf"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEEDS = (397, 421, 449)
GEOMETRIES = (
    ("discovery", 6, 11),
    ("discovery", 11, 6),
    ("holdout", 8, 9),
    ("holdout", 9, 8),
)
HOLDOUTS = ((8, 9), (9, 8))
CAP_MARGIN = 31
SLEW_MARGIN = 25
RATIO_MARGIN = 20
STAGE_TIMEOUT_SECONDS = 7200
EXPECTED_MISSING = ("sky130hd", "blocal", 421, 11, 6)
FIELDS = [
    "platform", "split", "topology", "rows", "cols", "pe_count", "sqrt_pe",
    "seed", "attempted", "route_ok", "error_stage", "period_min_ns",
    "fmax_mhz", "critical_path_delay_ns", "setup_violations",
    "hold_violations", "max_slew_violations", "max_fanout_violations",
    "max_cap_violations", "drc_count", "total_cells", "dff_cells",
    "cell_area_um2", "wire_length_um", "gds_sha256", "odb_sha256",
    "spef_sha256", "netlist_sha256", "elapsed_sec", "routed_cell_area_um2",
    "vectorless_power_w", "cap_slack_fraction", "slew_slack_fraction",
    "final_antenna_net_violations", "final_antenna_pin_violations",
]
VIOLATIONS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
    "final_antenna_net_violations", "final_antenna_pin_violations",
)
POSITIVE = (
    "period_min_ns", "fmax_mhz", "critical_path_delay_ns", "total_cells",
    "dff_cells", "cell_area_um2", "wire_length_um", "elapsed_sec",
    "routed_cell_area_um2", "vectorless_power_w",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")


def expected_ids() -> set[tuple[str, str, int, int, int]]:
    return {
        (platform, topology, seed, rows, cols)
        for platform in PLATFORMS for topology in TOPOLOGIES for seed in SEEDS
        for _, rows, cols in GEOMETRIES
    }


def ident(row: dict[str, str]) -> tuple[str, str, int, int, int]:
    return (
        row["platform"], row["topology"], int(row["seed"]),
        int(row["rows"]), int(row["cols"]),
    )


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def final_metric(text: str, name: str) -> float | None:
    match = re.search(rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text)
    return float(match.group(1)) if match else None


def final_count(text: str, name: str, label: str) -> int | None:
    match = re.search(
        rf"finish {re.escape(name)}\s*\n-+\s*\n{re.escape(label)} (\d+)", text
    )
    return int(match.group(1)) if match else None


def finite_positive(value: str) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--official-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    zips = sorted(args.artifacts.glob("*.zip"))
    metadata = json.loads(args.official_metadata.read_text(encoding="utf-8"))
    official = {item["name"]: item for item in metadata["artifacts"]}
    downloaded = {path.stem: path for path in zips}
    digest_checks = {
        name: (
            name in downloaded
            and digest(downloaded[name]) == item["digest"].removeprefix("sha256:")
        )
        for name, item in official.items()
    }

    expected_artifacts = {
        f"similarity-blocal-flowqualified-route-{p}-{t}-s{s}-r{r}c{c}"
        for p in PLATFORMS for t in TOPOLOGIES for s in SEEDS
        for _, r, c in GEOMETRIES
    }
    route_artifacts = {name for name in downloaded if "-route-" in name}
    missing_artifacts = sorted(expected_artifacts - route_artifacts)
    unexpected_artifacts = sorted(route_artifacts - expected_artifacts)

    rows: list[dict[str, str]] = []
    manifests: dict[tuple[str, str, int, int, int], dict[str, object]] = {}
    raw_records: list[dict[str, object]] = []
    functional_logs: dict[str, str] = {}
    extracted_files = 0
    for name, archive in downloaded.items():
        if name.endswith("final-summary"):
            continue
        with zipfile.ZipFile(archive) as zf:
            members = [member for member in zf.namelist() if not member.endswith("/")]
            extracted_files += len(members)
            if name.endswith("functional"):
                for member in members:
                    if re.fullmatch(r"tb_(6x11|11x6|8x9|9x8)\.log", Path(member).name):
                        functional_logs[Path(member).name] = zf.read(member).decode(
                            "utf-8", errors="replace"
                        )
                source_files = [m for m in members if Path(m).name == "source_sha.txt"]
                source_sha = (
                    zf.read(source_files[0]).decode().strip()
                    if len(source_files) == 1 else ""
                )
                continue

            csv_names = [m for m in members if Path(m).name.startswith(
                "similarity_blocal_flowqualified_") and m.endswith(".csv")]
            manifest_names = [m for m in members if Path(m).name.startswith(
                "flow_patch_") and m.endswith(".json")]
            drivers = [m for m in members if Path(m).name == "driver.log"]
            finishes = [m for m in members if Path(m).name == "6_finish.rpt"]
            routes = [m for m in members if Path(m).name == "5_2_route.log"]
            drcs = [m for m in members if Path(m).name == "5_route_drc.rpt"]
            if not all(len(group) == 1 for group in (
                csv_names, manifest_names, drivers, finishes, routes, drcs
            )):
                raw_records.append({"artifact": name, "complete": False,
                                    "reason": "non-exact raw-file multiplicity"})
                continue

            reader = csv.DictReader(
                zf.read(csv_names[0]).decode("utf-8").splitlines()
            )
            artifact_rows = list(reader)
            if reader.fieldnames != FIELDS or len(artifact_rows) != 1:
                raw_records.append({"artifact": name, "complete": False,
                                    "reason": "CSV schema/row count"})
                continue
            row = artifact_rows[0]
            key = ident(row)
            rows.append(row)
            manifest = json.loads(zf.read(manifest_names[0]))
            manifests[key] = manifest
            driver = zf.read(drivers[0]).decode("utf-8", errors="replace")
            finish = zf.read(finishes[0]).decode("utf-8", errors="replace")
            route = zf.read(routes[0]).decode("utf-8", errors="replace")
            drc = zf.read(drcs[0]).decode("utf-8", errors="replace")

            cap = final_metric(finish, "max_capacitance_check_slack_limit")
            slew = final_metric(finish, "max_slew_check_slack_limit")
            counts = {
                "max_slew": final_count(finish, "max_slew_violation_count",
                                        "max slew violation count"),
                "max_fanout": final_count(finish, "max_fanout_violation_count",
                                          "max fanout violation count"),
                "max_cap": final_count(finish, "max_cap_violation_count",
                                       "max cap violation count"),
                "setup": final_count(finish, "setup_violation_count",
                                     "setup violation count"),
                "hold": final_count(finish, "hold_violation_count",
                                    "hold violation count"),
            }
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
            launch = re.search(
                r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+"
                r"[\^v]\s+.*?/Q\s+\(", finish.split(
                    "finish report_checks -path_delay max", 1
                )[-1], re.MULTILINE,
            )
            manifest_ok = (
                manifest.get("schema_version") == 1
                and manifest.get("orfs_image") == IMAGE
                and manifest.get("workflow_source_sha") == SOURCE_SHA
                and manifest.get("antenna_ratio_margin") == RATIO_MARGIN
                and manifest.get("native_stage_timeout_seconds") == STAGE_TIMEOUT_SECONDS
                and manifest.get("cap_margin") == CAP_MARGIN
                and manifest.get("slew_margin") == SLEW_MARGIN
                and manifest.get("seeds") == list(SEEDS)
                and manifest.get("geometries")
                == [[split, r, c] for split, r, c in GEOMETRIES]
                and len(manifest.get("patches", [])) == 2
                and all(patch.get("replacement_count") == 1
                        for patch in manifest.get("patches", []))
            )
            csv_clean = (
                row["attempted"].lower() == "true"
                and row["route_ok"].lower() == "true"
                and not row["error_stage"]
                and all(row[field] and int(row[field]) == 0 for field in VIOLATIONS)
                and all(finite_positive(row[field]) for field in POSITIVE)
                and float(row["cap_slack_fraction"]) >= 0.02
                and float(row["slew_slack_fraction"]) >= 0.02
                and all(re.fullmatch(r"[0-9a-f]{64}", row[field]) for field in HASHES)
            )
            raw_same = (
                cap is not None and slew is not None and areas and powers and nets and pins
                and math.isclose(float(row["cap_slack_fraction"]), cap, abs_tol=1e-12)
                and math.isclose(float(row["slew_slack_fraction"]), slew, abs_tol=1e-12)
                and math.isclose(float(row["routed_cell_area_um2"]), areas[-1], abs_tol=1e-6)
                and math.isclose(float(row["vectorless_power_w"]), powers[-1], abs_tol=1e-12)
                and int(row["final_antenna_net_violations"]) == nets[-1]
                and int(row["final_antenna_pin_violations"]) == pins[-1]
            )
            raw_clean = bool(
                raw_same and cap >= 0.02 and slew >= 0.02
                and all(value == 0 for value in counts.values())
                and nets[-1] == pins[-1] == 0 and drt and drt[-1] == 0
                and not drc.strip() and "===== native finish" in driver
                and not any(token in driver for token in (
                    "TIMEOUT", "Signal 11 received", "make: ***"
                ))
            )
            raw_records.append({
                "artifact": name, "identity": key,
                "complete": bool(manifest_ok and csv_clean and raw_clean),
                "manifest_ok": manifest_ok, "csv_clean": csv_clean,
                "raw_clean": raw_clean, "cap_slack_fraction": cap,
                "slew_slack_fraction": slew,
                "launch_q_fanout": int(launch.group(1)) if launch else None,
                "finish_counts": counts,
            })

    expected = expected_ids()
    row_ids = [ident(row) for row in rows]
    present = set(row_ids)
    missing_ids = sorted(expected - present)
    clean_records = {tuple(item["identity"]): item for item in raw_records
                     if item.get("complete") and "identity" in item}
    lookup = {ident(row): row for row in rows if ident(row) in clean_records}

    matched: list[dict[str, object]] = []
    for platform in PLATFORMS:
        for split, rr, cc in GEOMETRIES:
            for seed in SEEDS:
                trio = [lookup.get((platform, topology, seed, rr, cc))
                        for topology in TOPOLOGIES]
                if any(row is None for row in trio):
                    continue
                broadcast, local, candidate = trio
                bp, lp, cp = (float(row["period_min_ns"]) for row in trio)
                ba, la, ca = (float(row["cell_area_um2"]) for row in trio)
                bra, lra, cra = (float(row["routed_cell_area_um2"]) for row in trio)
                matched.append({
                    "platform": platform, "split": split, "rows": rr, "cols": cc,
                    "seed": seed, "broadcast_period_ns": bp, "local_period_ns": lp,
                    "blocal_period_ns": cp, "q_local": (bp-lp)/bp,
                    "q_candidate": (bp-cp)/bp,
                    "retention": (bp-cp)/(bp-lp) if bp > lp else None,
                    "synth_vs_broadcast": bp*ba/(cp*ca),
                    "synth_vs_local": lp*la/(cp*ca),
                    "routed_vs_broadcast": bp*bra/(cp*cra),
                    "routed_vs_local": lp*lra/(cp*cra),
                    "broadcast_dffs": int(broadcast["dff_cells"]),
                    "local_dffs": int(local["dff_cells"]),
                    "blocal_dffs": int(candidate["dff_cells"]),
                    "local_synth_area": la, "blocal_synth_area": ca,
                    "local_routed_area": lra, "blocal_routed_area": cra,
                    "local_wire": float(local["wire_length_um"]),
                    "blocal_wire": float(candidate["wire_length_um"]),
                    "local_power": float(local["vectorless_power_w"]),
                    "blocal_power": float(candidate["vectorless_power_w"]),
                })

    grouped: dict[tuple[str, str, int, int], list[dict[str, object]]] = defaultdict(list)
    for item in matched:
        grouped[(item["platform"], item["split"], item["rows"], item["cols"])].append(item)
    points = []
    for (platform, split, rr, cc), group in sorted(grouped.items()):
        if len(group) != 3:
            continue
        points.append({
            "platform": platform, "split": split, "rows": rr, "cols": cc,
            "median_q_local": statistics.median(x["q_local"] for x in group),
            "median_q_candidate": statistics.median(x["q_candidate"] for x in group),
            "median_retention": statistics.median(x["retention"] for x in group),
            "median_synth_vs_broadcast": statistics.median(x["synth_vs_broadcast"] for x in group),
            "median_synth_vs_local": statistics.median(x["synth_vs_local"] for x in group),
            "median_routed_vs_broadcast": statistics.median(x["routed_vs_broadcast"] for x in group),
            "median_routed_vs_local": statistics.median(x["routed_vs_local"] for x in group),
            "median_wire_ratio_vs_local": statistics.median(x["blocal_wire"]/x["local_wire"] for x in group),
            "median_vectorless_power_ratio_vs_local": statistics.median(x["blocal_power"]/x["local_power"] for x in group),
        })
    holdouts = [point for point in points if point["split"] == "holdout"]
    synth_winners = [point for point in holdouts if
                     point["median_synth_vs_broadcast"] >= 1.01 and
                     point["median_synth_vs_local"] >= 1.01]
    routed_winners = [point for point in holdouts if
                      point["median_routed_vs_broadcast"] >= 1.01 and
                      point["median_routed_vs_local"] >= 1.01]
    fanouts = defaultdict(list)
    for rr, cc in HOLDOUTS:
        for seed in SEEDS:
            record = clean_records.get(("nangate45", "blocal", seed, rr, cc))
            if record and record["launch_q_fanout"] is not None:
                fanouts[(rr, cc)].append(record["launch_q_fanout"])

    functional = (
        source_sha == SOURCE_SHA and len(functional_logs) == 4
        and all(
            f"KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows={rr} cols={cc}"
            in functional_logs.get(f"tb_{rr}x{cc}.log", "")
            for _, rr, cc in GEOMETRIES
        )
    )
    exact_72 = len(rows) == 72 and len(set(row_ids)) == 72 and present == expected
    all_raw = len(raw_records) == 72 and all(x.get("complete") for x in raw_records)
    all_groups = len(points) == 8 and len(matched) == 24
    gates = {
        "signed_gemm_functional_on_all_four_unopened_shapes": functional,
        "exactly_72_shards_and_72_unique_attempted_rows": exact_72,
        "all_72_exact_flow_patch_and_runtime_manifests": (
            len(manifests) == 72 and all(x.get("manifest_ok") for x in raw_records)
        ),
        "all_72_raw_reports_drivers_drc_and_route_logs_complete": all_raw,
        "all_72_routes_clean_hashed_with_2pct_headroom_and_zero_antenna": all_raw,
        "all_eight_groups_three_complete_matched_seeds": all_groups,
        "full_local_positive_each_group": (
            all_groups and all(point["median_q_local"] > 0 for point in points)
        ),
        "all_24_candidate_dffs_above_broadcast_and_at_most_90pct_local": (
            len(matched) == 24 and all(
                x["broadcast_dffs"] < x["blocal_dffs"] <= 0.9*x["local_dffs"]
                for x in matched
            )
        ),
        "all_24_candidate_synthesis_and_routed_cell_areas_below_local": (
            len(matched) == 24 and all(
                x["blocal_synth_area"] < x["local_synth_area"] and
                x["blocal_routed_area"] < x["local_routed_area"]
                for x in matched
            )
        ),
        "all_12_holdout_seed_pairs_candidate_faster_than_broadcast": (
            len([x for x in matched if x["split"] == "holdout"]) == 12 and
            all(x["blocal_period_ns"] < x["broadcast_period_ns"]
                for x in matched if x["split"] == "holdout")
        ),
        "all_four_holdouts_raw_benefit_at_least_5pct": (
            len(holdouts) == 4 and all(x["median_q_candidate"] >= 0.05 for x in holdouts)
        ),
        "all_four_holdouts_retention_at_least_70pct": (
            len(holdouts) == 4 and all(x["median_retention"] >= 0.70 for x in holdouts)
        ),
        "synthesis_area_normalized_wins_at_least_3_of_4_and_both_platforms": (
            len(synth_winners) >= 3 and all(
                any(x["platform"] == platform for x in synth_winners)
                for platform in PLATFORMS
            )
        ),
        "routed_area_normalized_wins_at_least_3_of_4_and_both_platforms": (
            len(routed_winners) >= 3 and all(
                any(x["platform"] == platform for x in routed_winners)
                for platform in PLATFORMS
            )
        ),
        "all_four_holdouts_median_wirelength_not_above_local": (
            len(holdouts) == 4 and all(x["median_wire_ratio_vs_local"] <= 1.0 for x in holdouts)
        ),
        "nangate45_holdout_launch_q_fanout_at_most_10": (
            len(fanouts) == 2 and all(
                len(values) == 3 and statistics.median(values) <= 10
                for values in fanouts.values()
            )
        ),
    }
    conditional_present = {
        "all_71_present_rows_clean": len(clean_records) == 71,
        "all_23_present_matched_trios_dff_gate": len(matched) == 23 and all(
            x["broadcast_dffs"] < x["blocal_dffs"] <= 0.9*x["local_dffs"]
            for x in matched
        ),
        "all_23_present_matched_trios_area_gate": len(matched) == 23 and all(
            x["blocal_synth_area"] < x["local_synth_area"] and
            x["blocal_routed_area"] < x["local_routed_area"] for x in matched
        ),
    }
    result = {
        "schema_version": 1,
        "run_id": 36298460695,
        "source_sha": source_sha,
        "official_artifacts": len(official),
        "downloaded_artifacts": len(downloaded),
        "all_official_digests_match": all(digest_checks.values()),
        "digest_checks": digest_checks,
        "route_artifacts": len(route_artifacts),
        "missing_artifacts": missing_artifacts,
        "unexpected_artifacts": unexpected_artifacts,
        "extracted_files_excluding_final_summary": extracted_files,
        "planned_rows": 72, "attempted_rows": len(rows),
        "clean_rows": len(clean_records), "matched_trios": len(matched),
        "missing_identities": missing_ids,
        "expected_missing_identity": list(EXPECTED_MISSING),
        "gates": gates,
        "conditional_present_evidence": conditional_present,
        "frozen_claim_supported": all(gates.values()),
        "holdout_points": holdouts,
        "synthesis_area_normalized_winners": len(synth_winners),
        "routed_area_normalized_winners": len(routed_winners),
        "matched_rows": matched,
        "raw_records": raw_records,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        key: result[key] for key in (
            "official_artifacts", "downloaded_artifacts",
            "all_official_digests_match", "route_artifacts",
            "missing_artifacts", "planned_rows", "attempted_rows",
            "clean_rows", "matched_trios", "missing_identities", "gates",
            "conditional_present_evidence", "frozen_claim_supported",
            "synthesis_area_normalized_winners", "routed_area_normalized_winners",
            "holdout_points",
        )
    }, indent=2))
    return 0 if not result["frozen_claim_supported"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
