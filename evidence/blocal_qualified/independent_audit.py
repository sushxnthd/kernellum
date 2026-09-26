#!/usr/bin/env python3
"""Independent read-only audit of the qualified prospective B-local study.

This checker intentionally does not import the frozen route or validation code.
It reconstructs identities, raw-evidence completeness, cleanliness and every
preregistered gate from the preserved GitHub Actions artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_SHA = "a8f24cb1825f249c43ef43457d74bbabaac31625"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
PLATFORMS = ("nangate45", "sky130hd")
TOPOLOGIES = ("broadcast", "local", "blocal")
SEEDS = (293, 317, 347)
GEOMETRIES = (
    ("discovery", 6, 10),
    ("discovery", 10, 6),
    ("holdout", 7, 10),
    ("holdout", 10, 7),
)
HOLDOUTS = {(7, 10), (10, 7)}
FIELDS = [
    "platform", "split", "topology", "rows", "cols", "pe_count",
    "sqrt_pe", "seed", "attempted", "route_ok", "error_stage",
    "period_min_ns", "fmax_mhz", "critical_path_delay_ns",
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
    "total_cells", "dff_cells", "cell_area_um2", "wire_length_um",
    "gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256",
    "elapsed_sec", "routed_cell_area_um2", "vectorless_power_w",
    "cap_slack_fraction", "slew_slack_fraction",
    "final_antenna_net_violations", "final_antenna_pin_violations",
]
VIOLATIONS = (
    "setup_violations", "hold_violations", "max_slew_violations",
    "max_fanout_violations", "max_cap_violations", "drc_count",
    "final_antenna_net_violations", "final_antenna_pin_violations",
)
POSITIVE = (
    "period_min_ns", "fmax_mhz", "critical_path_delay_ns", "total_cells",
    "dff_cells", "cell_area_um2", "wire_length_um", "routed_cell_area_um2",
    "vectorless_power_w",
)
HASHES = ("gds_sha256", "odb_sha256", "spef_sha256", "netlist_sha256")

FINAL_REMOVED = """# Save a final image if openroad is compiled with the gui
if { [ord::openroad_gui_compiled] } {
  gui::show \"source $::env(SCRIPTS_DIR)/save_images.tcl\" false
}
"""
FINAL_REPLACEMENT = """# Optional GUI images intentionally disabled for deterministic headless evidence.
"""
ANTENNA_REMOVED = "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT)\n"
ANTENNA_REPLACEMENT = (
    "    repair_antennas -iterations $::env(MAX_REPAIR_ANTENNAS_ITER_GRT) "
    "-ratio_margin 20\n"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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
            and all(row[field] and int(row[field]) == 0 for field in VIOLATIONS)
            and all(positive(row[field]) for field in POSITIVE)
            and float(row["cap_slack_fraction"]) >= 0.02
            and float(row["slew_slack_fraction"]) >= 0.02
            and all(re.fullmatch(r"[0-9a-f]{64}", row[field]) for field in HASHES)
        )
    except (KeyError, TypeError, ValueError):
        return False


def route_complete(row: dict[str, str]) -> bool:
    return row["attempted"].lower() == "true" and row["route_ok"].lower() == "true"


def report_metric(text: str, name: str) -> float | None:
    found = re.search(
        rf"finish {re.escape(name)}\s*\n-+\s*\n([-+0-9.eE]+)", text
    )
    return float(found.group(1)) if found else None


def path_identity(path: Path, leaf: str) -> tuple[str, str, int, int, int] | None:
    match = re.search(
        rf"/(nangate45|sky130hd)/(broadcast|local|blocal)/s(293|317|347)/"
        rf"r(6|7|10)_c(6|7|10)/(?:reports/|logs/)?{re.escape(leaf)}$",
        path.as_posix(),
    )
    if not match:
        return None
    platform, topology, seed, rows, cols = match.groups()
    key = platform, topology, int(seed), int(rows), int(cols)
    return key if key in expected_identities() else None


def load_rows(data: Path) -> tuple[list[dict[str, str]], list[Path]]:
    paths = sorted(data.rglob("similarity_blocal_qualified_*.csv"))
    rows: list[dict[str, str]] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != FIELDS:
                raise AssertionError(f"schema mismatch: {path}")
            rows.extend(reader)
    return rows, paths


def verify_artifacts(manifest: dict[str, object]) -> list[dict[str, object]]:
    records = []
    artifacts = manifest["github_artifacts"]
    assert isinstance(artifacts, list) and len(artifacts) == 20
    for item in artifacts:
        assert isinstance(item, dict)
        path = ROOT / "original_zips" / f"{item['name']}.zip"
        actual = sha256(path)
        expected = str(item["digest"]).removeprefix("sha256:")
        records.append({
            "name": item["name"], "id": item["id"],
            "size": path.stat().st_size, "digest": actual,
            "size_match": path.stat().st_size == item["size_in_bytes"],
            "digest_match": actual == expected,
        })
    assert all(x["size_match"] and x["digest_match"] for x in records)
    bundle = manifest["extracted_bundle"]
    assert isinstance(bundle, dict)
    bundle_path = ROOT / str(bundle["name"])
    assert sha256(bundle_path) == str(bundle["digest"]).removeprefix("sha256:")
    with zipfile.ZipFile(bundle_path) as archive:
        assert len([x for x in archive.infolist() if not x.is_dir()]) == bundle["file_count"]
    return records


def verify_function(data: Path) -> tuple[bool, str]:
    logs = sorted(data.rglob("tb_*.log"))
    expected = {f"tb_{rows}x{cols}.log" for _, rows, cols in GEOMETRIES}
    sources = list(data.rglob("source_sha.txt"))
    hashes = list(data.rglob("source_hashes.txt"))
    markers = list(data.rglob("similarity_blocal_qualified_functional_passed"))
    source = sources[0].read_text().strip() if len(sources) == 1 else ""
    passed = (
        len(logs) == 4 and {x.name for x in logs} == expected
        and len(sources) == len(hashes) == len(markers) == 1
        and source == SOURCE_SHA
        and all(
            f"KERNELLUM_BLOCAL_EQUIVALENCE_PASS rows={rows} cols={cols}"
            in next(x for x in logs if x.name == f"tb_{rows}x{cols}.log")
            .read_text(errors="replace")
            for _, rows, cols in GEOMETRIES
        )
    )
    return passed, source


def verify_patches(data: Path) -> tuple[bool, list[dict[str, object]]]:
    paths = sorted(data.rglob("flow_patch_*.json"))
    expected_names = {
        f"flow_patch_{platform}_{topology}_s{seed}.json"
        for platform in PLATFORMS for topology in TOPOLOGIES for seed in SEEDS
    }
    expected = (
        ("flow/scripts/final_outputs.tcl", FINAL_REMOVED, FINAL_REPLACEMENT),
        ("flow/scripts/global_route.tcl", ANTENNA_REMOVED, ANTENNA_REPLACEMENT),
    )
    records = []
    for path in paths:
        item = json.loads(path.read_text())
        valid = (
            item.get("schema_version") == 1
            and item.get("orfs_image") == IMAGE
            and item.get("workflow_source_sha") == SOURCE_SHA
            and item.get("antenna_ratio_margin") == 20
            and len(item.get("patches", [])) == 2
        )
        for patch, (target, removed, replacement) in zip(item.get("patches", []), expected):
            valid &= (
                patch.get("target") == target
                and patch.get("replacement_count") == 1
                and patch.get("removed_text") == removed
                and patch.get("replacement_text") == replacement
                and bool(re.fullmatch(r"[0-9a-f]{64}", patch.get("before_sha256", "")))
                and bool(re.fullmatch(r"[0-9a-f]{64}", patch.get("after_sha256", "")))
                and patch.get("before_sha256") != patch.get("after_sha256")
            )
        records.append({"file": path.name, "valid": bool(valid)})
    return (
        len(paths) == 18 and {x.name for x in paths} == expected_names
        and all(x["valid"] for x in records),
        records,
    )


def collect_raw_evidence(
    data: Path, rows: list[dict[str, str]],
) -> tuple[bool, list[dict[str, object]], dict[str, int]]:
    expected = expected_identities()
    by_row = {identity(row): row for row in rows}
    mappings: dict[str, dict[tuple[str, str, int, int, int], Path]] = {}
    counts: dict[str, int] = {}
    for leaf in ("driver.log", "6_finish.rpt", "5_2_route.log", "5_route_drc.rpt"):
        paths = [x for x in data.rglob(leaf) if path_identity(x, leaf)]
        mapping = {path_identity(x, leaf): x for x in paths}
        mappings[leaf] = mapping
        counts[leaf] = len(paths)

    records = []
    for key in sorted(expected):
        row = by_row[key]
        driver_path = mappings["driver.log"].get(key)
        finish_path = mappings["6_finish.rpt"].get(key)
        route_path = mappings["5_2_route.log"].get(key)
        drc_path = mappings["5_route_drc.rpt"].get(key)
        driver = driver_path.read_text(errors="replace") if driver_path else ""
        timed_out = "TIMEOUT" in driver
        complete = all(x is not None for x in (driver_path, finish_path, route_path, drc_path))
        cap = slew = routed_area = power = antenna_nets = antenna_pins = launch = None
        raw_match = False
        if complete:
            finish = finish_path.read_text(errors="replace")
            route = route_path.read_text(errors="replace")
            cap = report_metric(finish, "max_capacitance_check_slack_limit")
            slew = report_metric(finish, "max_slew_check_slack_limit")
            areas = [float(x) for x in re.findall(r"Design area\s+([0-9.eE+-]+)\s+um\^2", route)]
            powers = [float(x) for x in re.findall(
                r"^Total\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+"
                r"([0-9.eE+-]+)\s+100\.0%\s*$", finish, re.MULTILINE,
            )]
            nets = [int(x) for x in re.findall(r"Found (\d+) net violations\.", route)]
            pins = [int(x) for x in re.findall(r"Found (\d+) pin violations\.", route)]
            routed_area = areas[-1] if areas else None
            power = powers[-1] if powers else None
            antenna_nets = nets[-1] if nets else None
            antenna_pins = pins[-1] if pins else None
            section = finish.split("finish report_checks -path_delay max", 1)
            body = section[1] if len(section) == 2 else ""
            launch_match = re.search(
                r"^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+[0-9.]+\s+"
                r"[\^v]\s+.*?/Q\s+\(", body, re.MULTILINE,
            )
            launch = int(launch_match.group(1)) if launch_match else None
            drt = [int(x) for x in re.findall(r"Number of violations = (\d+)\.", route)]
            raw_match = bool(
                cap is not None and slew is not None and routed_area is not None
                and power is not None and antenna_nets is not None and antenna_pins is not None
                and math.isclose(float(row["cap_slack_fraction"]), cap, abs_tol=1e-12)
                and math.isclose(float(row["slew_slack_fraction"]), slew, abs_tol=1e-12)
                and math.isclose(float(row["routed_cell_area_um2"]), routed_area, abs_tol=1e-6)
                and math.isclose(float(row["vectorless_power_w"]), power, abs_tol=1e-12)
                and int(row["final_antenna_net_violations"]) == antenna_nets
                and int(row["final_antenna_pin_violations"]) == antenna_pins
                and drt and drt[-1] == 0
                and not drc_path.read_text().strip()
                and "===== native finish" in driver
                and not timed_out and "make: ***" not in driver and "Signal 11 received" not in driver
            )
        records.append({
            "identity": list(key), "complete": complete, "raw_matches_csv": raw_match,
            "timed_out": timed_out, "cap_slack_fraction": cap,
            "slew_slack_fraction": slew, "routed_cell_area_um2": routed_area,
            "vectorless_power_w": power, "antenna_nets": antenna_nets,
            "antenna_pins": antenna_pins, "launch_q_fanout": launch,
        })
    exact = (
        counts == {"driver.log": 72, "6_finish.rpt": 72, "5_2_route.log": 72, "5_route_drc.rpt": 72}
        and all(x["complete"] and x["raw_matches_csv"] for x in records)
    )
    return exact, records, counts


def summarize_matches(rows: list[dict[str, str]], eligible_only: bool) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    selected = [row for row in rows if clean_route(row)] if eligible_only else [row for row in rows if route_complete(row)]
    lookup = {identity(row): row for row in selected}
    matched = []
    for platform in PLATFORMS:
        for split, row_count, col_count in GEOMETRIES:
            for seed in SEEDS:
                trio = [lookup.get((platform, topology, seed, row_count, col_count)) for topology in TOPOLOGIES]
                if any(item is None for item in trio):
                    continue
                broadcast, local, candidate = trio
                bp, lp, cp = (float(x["period_min_ns"]) for x in trio)
                ba, la, ca = (float(x["cell_area_um2"]) for x in trio)
                bra, lra, cra = (float(x["routed_cell_area_um2"]) for x in trio)
                matched.append({
                    "platform": platform, "split": split, "rows": row_count,
                    "cols": col_count, "seed": seed,
                    "broadcast_period_ns": bp, "local_period_ns": lp,
                    "blocal_period_ns": cp, "q_local": (bp - lp) / bp,
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
                    "local_vectorless_power_w": float(local["vectorless_power_w"]),
                    "blocal_vectorless_power_w": float(candidate["vectorless_power_w"]),
                })
    grouped: dict[tuple[str, str, int, int], list[dict[str, object]]] = defaultdict(list)
    for item in matched:
        grouped[(item["platform"], item["split"], item["rows"], item["cols"])].append(item)
    points = []
    for (platform, split, row_count, col_count), group in sorted(grouped.items()):
        if len(group) != 3:
            continue
        points.append({
            "platform": platform, "split": split, "rows": row_count, "cols": col_count,
            "median_q_local": statistics.median(x["q_local"] for x in group),
            "median_q_candidate": statistics.median(x["q_candidate"] for x in group),
            "median_retention": statistics.median(x["retention"] for x in group) if all(x["retention"] is not None for x in group) else None,
            "median_synth_density_vs_broadcast": statistics.median(x["synth_density_vs_broadcast"] for x in group),
            "median_synth_density_vs_local": statistics.median(x["synth_density_vs_local"] for x in group),
            "median_routed_density_vs_broadcast": statistics.median(x["routed_density_vs_broadcast"] for x in group),
            "median_routed_density_vs_local": statistics.median(x["routed_density_vs_local"] for x in group),
            "median_wire_ratio_vs_local": statistics.median(x["blocal_wire_um"] / x["local_wire_um"] for x in group),
            "median_vectorless_power_ratio_vs_local": statistics.median(x["blocal_vectorless_power_w"] / x["local_vectorless_power_w"] for x in group),
        })
    return matched, points


def audit(data: Path, artifact_records: list[dict[str, object]]) -> dict[str, object]:
    rows, csvs = load_rows(data)
    expected = expected_identities()
    identities = [identity(row) for row in rows]
    exact_rows = len(csvs) == 18 and len(rows) == 72 and len(set(identities)) == 72 and set(identities) == expected
    function_ok, source = verify_function(data)
    patch_ok, patch_records = verify_patches(data)
    raw_ok, raw_records, raw_counts = collect_raw_evidence(data, rows)
    eligible = [row for row in rows if clean_route(row)]
    route_complete_rows = [row for row in rows if route_complete(row)]
    matched, points = summarize_matches(rows, eligible_only=True)
    diagnostic_matched, diagnostic_points = summarize_matches(rows, eligible_only=False)
    all_groups = len(points) == 8 and len(matched) == 24
    holdouts = [point for point in points if point["split"] == "holdout"]
    synth_winners = [point for point in holdouts if point["median_synth_density_vs_broadcast"] >= 1.01 and point["median_synth_density_vs_local"] >= 1.01]
    routed_winners = [point for point in holdouts if point["median_routed_density_vs_broadcast"] >= 1.01 and point["median_routed_density_vs_local"] >= 1.01]
    fanouts: dict[tuple[int, int], list[int]] = defaultdict(list)
    for item in raw_records:
        platform, topology, seed, rows_count, cols_count = item["identity"]
        if platform == "nangate45" and topology == "blocal" and (rows_count, cols_count) in HOLDOUTS and item["launch_q_fanout"] is not None:
            fanouts[(rows_count, cols_count)].append(item["launch_q_fanout"])
    fanout_gate = len(fanouts) == 2 and all(len(values) == 3 and statistics.median(values) <= 10 for values in fanouts.values())
    gates = {
        "signed_gemm_functional_on_all_four_unopened_shapes": function_ok,
        "exactly_18_shards_and_72_unique_attempted_rows": exact_rows and all(row["attempted"].lower() == "true" for row in rows),
        "all_18_exact_headless_and_antenna_patch_manifests": patch_ok,
        "all_72_raw_reports_drivers_drc_and_route_logs_complete": raw_ok,
        "all_72_routes_clean_hashed_with_2pct_headroom_and_zero_antenna": exact_rows and len(eligible) == 72,
        "all_eight_groups_three_complete_matched_seeds": all_groups,
        "full_local_positive_each_group": all_groups and all(point["median_q_local"] > 0 for point in points),
        "all_24_candidate_dffs_above_broadcast_and_at_most_90pct_local": len(matched) == 24 and all(row["broadcast_dffs"] < row["blocal_dffs"] <= 0.90 * row["local_dffs"] for row in matched),
        "all_24_candidate_synthesis_and_routed_cell_areas_below_local": len(matched) == 24 and all(row["blocal_synth_area_um2"] < row["local_synth_area_um2"] and row["blocal_routed_area_um2"] < row["local_routed_area_um2"] for row in matched),
        "all_12_holdout_seed_pairs_candidate_faster_than_broadcast": len([row for row in matched if row["split"] == "holdout"]) == 12 and all(row["blocal_period_ns"] < row["broadcast_period_ns"] for row in matched if row["split"] == "holdout"),
        "all_four_holdouts_raw_benefit_at_least_5pct": len(holdouts) == 4 and all(point["median_q_candidate"] >= 0.05 for point in holdouts),
        "all_four_holdouts_retention_at_least_70pct": len(holdouts) == 4 and all(point["median_retention"] is not None and point["median_retention"] >= 0.70 for point in holdouts),
        "synthesis_area_normalized_wins_at_least_3_of_4_and_both_platforms": len(synth_winners) >= 3 and all(any(point["platform"] == platform for point in synth_winners) for platform in PLATFORMS),
        "routed_area_normalized_wins_at_least_3_of_4_and_both_platforms": len(routed_winners) >= 3 and all(any(point["platform"] == platform for point in routed_winners) for platform in PLATFORMS),
        "all_four_holdouts_median_wirelength_not_above_local": len(holdouts) == 4 and all(point["median_wire_ratio_vs_local"] <= 1.0 for point in holdouts),
        "nangate45_holdout_launch_q_fanout_at_most_10": fanout_gate,
    }
    failures = []
    for row in rows:
        if clean_route(row):
            continue
        key = list(identity(row))
        record = next(x for x in raw_records if x["identity"] == key)
        if record["timed_out"]:
            reason = "native_route_timeout_3600s"
        elif route_complete(row) and float(row.get("cap_slack_fraction") or -1) < 0.02:
            reason = "capacitance_headroom_below_2pct"
        else:
            reason = row.get("error_stage") or "electrical_or_evidence_failure"
        failures.append({
            "identity": key, "reason": reason, "error_stage": row["error_stage"],
            "cap_slack_fraction": float(row["cap_slack_fraction"]) if row["cap_slack_fraction"] else None,
            "slew_slack_fraction": float(row["slew_slack_fraction"]) if row["slew_slack_fraction"] else None,
        })
    exact_summary = ROOT / "exact_summary.json"
    extracted_summary = next(data.rglob("similarity_blocal_qualified_summary.json"))
    return {
        "schema_version": 1, "run_id": 36262319975, "source_sha": source,
        "artifact_digests_verified": all(x["digest_match"] and x["size_match"] for x in artifact_records),
        "artifact_count": len(artifact_records), "extracted_file_count": 468,
        "exact_summary_byte_match": exact_summary.read_bytes() == extracted_summary.read_bytes(),
        "attempted": len(rows), "route_complete": len(route_complete_rows),
        "eligible_clean": len(eligible), "matched_seed_trios": len(matched),
        "complete_groups": len(points), "raw_file_counts": raw_counts,
        "failures": failures, "gates": gates,
        "frozen_claim_supported": all(gates.values()),
        "eligible_points": points, "eligible_matched_rows": matched,
        "diagnostic_only_points_from_route_complete_rows": diagnostic_points,
        "diagnostic_only_matched_rows": diagnostic_matched,
        "nangate45_holdout_launch_q_fanouts": {f"{r}x{c}": sorted(v) for (r, c), v in sorted(fanouts.items())},
        "patch_manifests": patch_records,
        "power_boundary": "Vectorless OpenROAD total power has no activity file and is descriptive only; it is not measured energy, silicon power, or deployed throughput.",
    }


def main() -> int:
    manifest = json.loads((ROOT / "artifact_digests.json").read_text())
    artifact_records = verify_artifacts(manifest)
    bundle = ROOT / str(manifest["extracted_bundle"]["name"])
    with tempfile.TemporaryDirectory(prefix="blocal-qualified-audit-") as tmp:
        data = Path(tmp) / "extracted"
        data.mkdir()
        with zipfile.ZipFile(bundle) as archive:
            archive.extractall(data)
        result = audit(data, artifact_records)
    output = ROOT / "independent_audit.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["frozen_claim_supported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
