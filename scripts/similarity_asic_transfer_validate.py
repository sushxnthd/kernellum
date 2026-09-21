#!/usr/bin/env python3
"""Evaluate the frozen cross-technology ASIC transport gate."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from scripts.similarity_asic_transfer_route import (
    DISCOVERY_GEOMETRIES,
    FIELDS,
    HOLDOUT_GEOMETRIES,
    SEEDS,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "similarity_asic_transfer_download"
OUTPUT = ROOT / "results"
VIOLATION_FIELDS = (
    "setup_violations",
    "hold_violations",
    "max_slew_violations",
    "max_fanout_violations",
    "max_cap_violations",
    "drc_count",
)
COST_FIELDS = ("total_cells", "dff_cells", "cell_area_um2", "wire_length_um")


def expected_keys() -> set[tuple[str, str, int, int, int]]:
    keys: set[tuple[str, str, int, int, int]] = set()
    for topology in ("broadcast", "local"):
        for seed in SEEDS:
            for rows, cols in DISCOVERY_GEOMETRIES:
                keys.add(("nangate45", topology, seed, rows, cols))
            for rows, cols in DISCOVERY_GEOMETRIES + HOLDOUT_GEOMETRIES:
                keys.add(("sky130hd", topology, seed, rows, cols))
    return keys


def rankdata(values: Iterable[float]) -> list[float]:
    array = [float(value) for value in values]
    order = sorted(range(len(array)), key=array.__getitem__)
    ranks = [0.0] * len(array)
    index = 0
    while index < len(array):
        end = index + 1
        while end < len(array) and array[order[end]] == array[order[index]]:
            end += 1
        rank = (index + end - 1) / 2.0 + 1.0
        for position in order[index:end]:
            ranks[position] = rank
        index = end
    return ranks


def spearman(left: Iterable[float], right: Iterable[float]) -> float:
    left_rank = rankdata(left)
    right_rank = rankdata(right)
    if len(left_rank) < 2 or len(left_rank) != len(right_rank):
        return float("nan")
    left_mean = statistics.mean(left_rank)
    right_mean = statistics.mean(right_rank)
    left_centered = [value - left_mean for value in left_rank]
    right_centered = [value - right_mean for value in right_rank]
    denominator = math.sqrt(
        sum(value * value for value in left_centered) *
        sum(value * value for value in right_centered)
    )
    if denominator == 0:
        return float("nan")
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left_centered, right_centered)
    ) / denominator


def linear_fit(x_values: Iterable[float], y_values: Iterable[float]) -> tuple[float, float]:
    x = [float(value) for value in x_values]
    y = [float(value) for value in y_values]
    if len(x) < 2 or len(x) != len(y):
        return float("nan"), float("nan")
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    if denominator == 0:
        return float("nan"), float("nan")
    slope = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x, y)
    ) / denominator
    return y_mean - slope * x_mean, slope


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def normalize(row: dict[str, object]) -> dict[str, object]:
    normalized = dict(row)
    for field in ("rows", "cols", "pe_count", "seed"):
        normalized[field] = int(normalized[field])
    for field in ("attempted", "route_ok"):
        normalized[field] = as_bool(normalized[field])
    for field in ("sqrt_pe", "elapsed_sec"):
        normalized[field] = float(normalized[field]) if normalized[field] != "" else float("nan")
    if normalized["route_ok"]:
        for field in (
            "period_min_ns",
            "fmax_mhz",
            "critical_path_delay_ns",
            "cell_area_um2",
            "wire_length_um",
        ):
            normalized[field] = float(normalized[field])
        for field in VIOLATION_FIELDS + ("total_cells", "dff_cells"):
            normalized[field] = int(normalized[field])
    return normalized


def median(values: Iterable[float]) -> float:
    return float(statistics.median(values))


def cv_pct(values: Iterable[float]) -> float:
    array = [float(value) for value in values]
    if len(array) < 2:
        return float("nan")
    mean = statistics.mean(array)
    if mean == 0:
        return float("nan")
    return statistics.stdev(array) / mean * 100.0


def evaluate(raw_rows: list[dict[str, object]], functional_passed: bool) -> dict[str, object]:
    rows = [normalize(row) for row in raw_rows]
    actual_keys = {
        (str(row["platform"]), str(row["topology"]), int(row["seed"]),
         int(row["rows"]), int(row["cols"]))
        for row in rows
    }
    expected = expected_keys()
    successful = [row for row in rows if row["route_ok"]]
    success_lookup = {
        (str(row["platform"]), str(row["topology"]), int(row["seed"]),
         int(row["rows"]), int(row["cols"])): row
        for row in successful
    }

    groups: dict[tuple[str, str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in successful:
        groups[(str(row["platform"]), str(row["topology"]),
                int(row["rows"]), int(row["cols"]))].append(row)
    cvs = {
        key: cv_pct(float(row["period_min_ns"]) for row in values)
        for key, values in groups.items()
        if len(values) >= 2
    }

    paired_seed_rows: list[dict[str, object]] = []
    for platform, geometry_list in (
        ("nangate45", DISCOVERY_GEOMETRIES),
        ("sky130hd", DISCOVERY_GEOMETRIES + HOLDOUT_GEOMETRIES),
    ):
        for rows_count, cols_count in geometry_list:
            for seed in SEEDS:
                broadcast = success_lookup.get((platform, "broadcast", seed, rows_count, cols_count))
                local = success_lookup.get((platform, "local", seed, rows_count, cols_count))
                if broadcast is None or local is None:
                    continue
                broadcast_period = float(broadcast["period_min_ns"])
                local_period = float(local["period_min_ns"])
                paired_seed_rows.append({
                    "platform": platform,
                    "split": "discovery" if platform == "nangate45" else (
                        "bridge" if (rows_count, cols_count) in DISCOVERY_GEOMETRIES else "holdout"
                    ),
                    "rows": rows_count,
                    "cols": cols_count,
                    "pe_count": rows_count * cols_count,
                    "sqrt_pe": math.sqrt(rows_count * cols_count),
                    "seed": seed,
                    "broadcast_period_ns": broadcast_period,
                    "local_period_ns": local_period,
                    "q": (broadcast_period - local_period) / broadcast_period,
                    "broadcast_total_cells": int(broadcast["total_cells"]),
                    "local_total_cells": int(local["total_cells"]),
                    "broadcast_dff_cells": int(broadcast["dff_cells"]),
                    "local_dff_cells": int(local["dff_cells"]),
                    "broadcast_area_um2": float(broadcast["cell_area_um2"]),
                    "local_area_um2": float(local["cell_area_um2"]),
                    "broadcast_wire_length_um": float(broadcast["wire_length_um"]),
                    "local_wire_length_um": float(local["wire_length_um"]),
                })

    paired_groups: dict[tuple[str, int, int], list[dict[str, object]]] = defaultdict(list)
    for row in paired_seed_rows:
        paired_groups[(str(row["platform"]), int(row["rows"]), int(row["cols"]))].append(row)
    points: list[dict[str, object]] = []
    for (platform, rows_count, cols_count), group in sorted(paired_groups.items()):
        if len(group) < 2:
            continue
        first = group[0]
        points.append({
            "platform": platform,
            "split": first["split"],
            "rows": rows_count,
            "cols": cols_count,
            "pe_count": rows_count * cols_count,
            "sqrt_pe": math.sqrt(rows_count * cols_count),
            "complete_seeds": len(group),
            "median_q": median(float(row["q"]) for row in group),
            "median_broadcast_period_ns": median(float(row["broadcast_period_ns"]) for row in group),
            "median_local_period_ns": median(float(row["local_period_ns"]) for row in group),
            "median_broadcast_area_um2": median(float(row["broadcast_area_um2"]) for row in group),
            "median_local_area_um2": median(float(row["local_area_um2"]) for row in group),
            "median_broadcast_dff_cells": median(float(row["broadcast_dff_cells"]) for row in group),
            "median_local_dff_cells": median(float(row["local_dff_cells"]) for row in group),
            "median_broadcast_wire_length_um": median(float(row["broadcast_wire_length_um"]) for row in group),
            "median_local_wire_length_um": median(float(row["local_wire_length_um"]) for row in group),
        })

    point_lookup = {
        (str(point["platform"]), int(point["rows"]), int(point["cols"])): point
        for point in points
    }
    discovery = [point_lookup.get(("nangate45", r, c)) for r, c in DISCOVERY_GEOMETRIES]
    discovery_complete = all(point is not None for point in discovery)
    alpha = beta = float("nan")
    if discovery_complete:
        alpha, beta = linear_fit(
            (float(point["sqrt_pe"]) for point in discovery),
            (float(point["median_q"]) for point in discovery),
        )

    bridge = [point_lookup.get(("sky130hd", r, c)) for r, c in DISCOVERY_GEOMETRIES]
    bridge_complete = all(point is not None for point in bridge)
    bridge_predictions: list[float] = []
    bridge_observations: list[float] = []
    bridge_spearman = calibration_intercept = calibration_slope = float("nan")
    if discovery_complete and bridge_complete:
        bridge_predictions = [alpha + beta * float(point["sqrt_pe"]) for point in bridge]
        bridge_observations = [float(point["median_q"]) for point in bridge]
        bridge_spearman = spearman(bridge_predictions, bridge_observations)
        calibration_intercept, calibration_slope = linear_fit(
            bridge_predictions,
            bridge_observations,
        )

    holdout_results: list[dict[str, object]] = []
    if math.isfinite(calibration_slope):
        for rows_count, cols_count in HOLDOUT_GEOMETRIES:
            point = point_lookup.get(("sky130hd", rows_count, cols_count))
            if point is None:
                continue
            nan_pred = alpha + beta * float(point["sqrt_pe"])
            prediction = calibration_intercept + calibration_slope * nan_pred
            observed = float(point["median_q"])
            holdout_results.append({
                "rows": rows_count,
                "cols": cols_count,
                "pe_count": rows_count * cols_count,
                "observed_q": observed,
                "predicted_q": prediction,
                "absolute_error": abs(observed - prediction),
            })

    holdout_errors = [float(row["absolute_error"]) for row in holdout_results]
    holdout_mae = statistics.mean(holdout_errors) if holdout_errors else float("inf")
    median_cv = median(value for value in cvs.values() if math.isfinite(value)) if cvs else float("inf")
    structural_pairs_ok = bool(paired_seed_rows) and all(
        int(row["local_dff_cells"]) > int(row["broadcast_dff_cells"])
        for row in paired_seed_rows
    )
    final_checks_ok = bool(successful) and all(
        all(int(row[field]) == 0 for field in VIOLATION_FIELDS)
        for row in successful
    )
    costs_complete = bool(successful) and all(
        all(float(row[field]) > 0 for field in COST_FIELDS)
        for row in successful
    )
    q_7x7 = point_lookup.get(("nangate45", 7, 7))
    forty_five = [
        row for row in holdout_results
        if int(row["pe_count"]) == 45
    ]

    gates = {
        "functional_equivalence": functional_passed,
        "attempted_96_unique_routes": (
            len(rows) == 96 and actual_keys == expected and all(row["attempted"] for row in rows)
        ),
        "at_least_92_routes_succeed": len(successful) >= 92,
        "successful_routes_zero_final_violations": final_checks_ok,
        "all_16_geometry_pairs_have_two_complete_seeds": len(points) == 16,
        "local_sequential_structure_retained": structural_pairs_ok,
        "median_route_seed_cv_at_most_6pct": median_cv <= 6.0,
        "nangate_positive_at_least_5_of_6": (
            discovery_complete and sum(float(point["median_q"]) > 0 for point in discovery) >= 5
        ),
        "nangate_size_slope_positive": beta > 0,
        "nangate_7x7_q_at_least_5pct": (
            q_7x7 is not None and float(q_7x7["median_q"]) >= 0.05
        ),
        "sky_bridge_positive_at_least_5_of_6": (
            bridge_complete and sum(float(point["median_q"]) > 0 for point in bridge) >= 5
        ),
        "bridge_spearman_at_least_0p60": bridge_spearman >= 0.60,
        "calibration_slope_positive": calibration_slope > 0,
        "holdout_positive_at_least_3_of_4": (
            len(holdout_results) == 4 and
            sum(float(row["observed_q"]) > 0 for row in holdout_results) >= 3
        ),
        "both_45pe_holdouts_q_at_least_5pct": (
            len(forty_five) == 2 and all(float(row["observed_q"]) >= 0.05 for row in forty_five)
        ),
        "holdout_mae_at_most_0p08": holdout_mae <= 0.08,
        "every_holdout_abs_error_at_most_0p15": (
            len(holdout_results) == 4 and all(error <= 0.15 for error in holdout_errors)
        ),
        "cost_metrics_complete": costs_complete,
    }

    return {
        "schema_version": 1,
        "study": "SIMILARITY cross-technology ASIC transport transfer",
        "attempted_routes": len(rows),
        "successful_routes": len(successful),
        "complete_seed_pairs": len(paired_seed_rows),
        "median_route_seed_cv_pct": median_cv,
        "nangate_model": {"alpha": alpha, "beta_per_sqrt_pe": beta},
        "sky_bridge": {
            "spearman": bridge_spearman,
            "calibration_intercept": calibration_intercept,
            "calibration_slope": calibration_slope,
        },
        "holdouts": holdout_results,
        "holdout_mae": holdout_mae,
        "gates": gates,
        "claim_supported": all(gates.values()),
        "points": points,
        "paired_seed_rows": paired_seed_rows,
        "null_routes": [
            {field: row[field] for field in ("platform", "topology", "seed", "rows", "cols", "error_stage")}
            for row in rows if not row["route_ok"]
        ],
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def json_safe(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def main() -> int:
    raw_rows: list[dict[str, object]] = []
    for path in sorted(INPUT.glob("similarity_asic_transfer_*.csv")):
        with path.open(encoding="utf-8") as handle:
            raw_rows.extend(csv.DictReader(handle))
    if not raw_rows:
        raise RuntimeError("no ASIC transfer route rows")
    functional_passed = (INPUT / "similarity_asic_transfer_functional_passed").exists()
    result = evaluate(raw_rows, functional_passed)
    safe_result = json_safe(result)
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / "similarity_asic_transfer_summary.json").write_text(
        json.dumps(safe_result, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    normalized_rows = [normalize(row) for row in raw_rows]
    write_csv(OUTPUT / "similarity_asic_transfer_combined.csv", normalized_rows)
    write_csv(OUTPUT / "similarity_asic_transfer_pairs.csv", result["paired_seed_rows"])
    write_csv(OUTPUT / "similarity_asic_transfer_points.csv", result["points"])
    print(json.dumps({
        key: value
        for key, value in safe_result.items()
        if key not in ("points", "paired_seed_rows")
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
