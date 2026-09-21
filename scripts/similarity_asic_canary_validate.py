#!/usr/bin/env python3
"""Validate the non-scientific SIMILARITY ASIC flow canary artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


TOPOLOGIES = ("broadcast", "local")
FINAL_ARTIFACTS = ("6_final.gds", "6_final.odb", "6_final.spef", "6_final.v")
VIOLATION_NAMES = (
    "max slew",
    "max fanout",
    "max cap",
    "setup",
    "hold",
)


def require_match(pattern: str, text: str, label: str, flags: int = 0) -> re.Match[str]:
    match = re.search(pattern, text, flags)
    if match is None:
        raise ValueError(f"missing {label}")
    return match


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_synthesis(path: Path, expected_top: str) -> dict[str, int | float | str]:
    text = path.read_text(encoding="utf-8")
    top = require_match(r"^===\s+([^=\s]+)\s+===$", text, "synthesis top", re.MULTILINE).group(1)
    if top != expected_top:
        raise ValueError(f"unexpected synthesis top {top!r}; expected {expected_top!r}")

    total_cells = int(
        require_match(
            r"^\s*(\d+)\s+\S+\s+\d+\s+\S+\s+cells\s*$",
            text,
            "total cell count",
            re.MULTILINE,
        ).group(1)
    )
    chip_area_um2 = float(
        require_match(
            r"Chip area for module '[^']+':\s*([0-9.eE+-]+)",
            text,
            "synthesized chip area",
        ).group(1)
    )
    dff_cells = sum(
        int(match.group(1))
        for match in re.finditer(
            r"^\s*(\d+)\s+\S+\s+\d+\s+\S+\s+(?:S?DFF\S*)\s*$",
            text,
            re.MULTILINE,
        )
    )
    if total_cells <= 0 or chip_area_um2 <= 0 or dff_cells <= 0:
        raise ValueError("synthesis did not retain nonzero logic, area, and sequential cells")
    return {
        "top": top,
        "total_cells": total_cells,
        "dff_cells": dff_cells,
        "chip_area_um2": chip_area_um2,
    }


def parse_finish(path: Path) -> dict[str, float | dict[str, int]]:
    text = path.read_text(encoding="utf-8")
    clock_match = require_match(
        r"^clk period_min =\s*([0-9.eE+-]+)\s+fmax =\s*([0-9.eE+-]+)\s*$",
        text,
        "post-route minimum clock period",
        re.MULTILINE,
    )
    violation_counts: dict[str, int] = {}
    for name in VIOLATION_NAMES:
        value = int(
            require_match(
                rf"^{re.escape(name)} violation count\s+(\d+)\s*$",
                text,
                f"{name} violation count",
                re.MULTILINE,
            ).group(1)
        )
        violation_counts[name.replace(" ", "_")] = value
    if any(violation_counts.values()):
        raise ValueError(f"post-route violations present: {violation_counts}")

    critical_path_delay_ns = float(
        require_match(
            r"finish critical path delay\s*\n-+\s*\n([0-9.eE+-]+)",
            text,
            "post-route critical path delay",
        ).group(1)
    )
    return {
        "period_min_ns": float(clock_match.group(1)),
        "fmax_mhz": float(clock_match.group(2)),
        "critical_path_delay_ns": critical_path_delay_ns,
        "violations": violation_counts,
    }


def validate_topology(root: Path, topology: str) -> dict[str, object]:
    design = f"similarity_asic_{topology}_canary"
    result_dir = root / design / "base"
    report_dir = root / f"{topology}-reports" / "base"
    synthesis = parse_synthesis(report_dir / "synth_stat.txt", design)
    finish = parse_finish(report_dir / "6_finish.rpt")

    route_drc = report_dir / "5_route_drc.rpt"
    if route_drc.read_text(encoding="utf-8").strip():
        raise ValueError(f"{topology}: detailed-route DRC report is not empty")

    artifacts: dict[str, dict[str, int | str]] = {}
    for name in FINAL_ARTIFACTS:
        path = result_dir / name
        size = path.stat().st_size
        if size <= 0:
            raise ValueError(f"{topology}: final artifact is empty: {name}")
        artifacts[name] = {"bytes": size, "sha256": sha256(path)}

    return {
        "design": design,
        "geometry": {"rows": 3, "cols": 3},
        "synthesis": synthesis,
        "post_route": finish,
        "detailed_route_drc_count": 0,
        "artifacts": artifacts,
    }


def validate(root: Path) -> dict[str, object]:
    designs = {topology: validate_topology(root, topology) for topology in TOPOLOGIES}
    broadcast_dffs = int(designs["broadcast"]["synthesis"]["dff_cells"])
    local_dffs = int(designs["local"]["synthesis"]["dff_cells"])
    if local_dffs <= broadcast_dffs:
        raise ValueError(
            "registered-local topology was not structurally retained: "
            f"local DFFs={local_dffs}, broadcast DFFs={broadcast_dffs}"
        )
    broadcast_gds = designs["broadcast"]["artifacts"]["6_final.gds"]["sha256"]
    local_gds = designs["local"]["artifacts"]["6_final.gds"]["sha256"]
    if broadcast_gds == local_gds:
        raise ValueError("broadcast and local final GDS hashes unexpectedly match")

    return {
        "schema_version": 1,
        "study": "SIMILARITY ASIC transfer",
        "stage": "non-scientific canary",
        "status": "passed",
        "scientific_result": False,
        "excluded_from_discovery_and_confirmation": True,
        "exclusion_reason": "3x3 canary opened before the ASIC hypothesis and thresholds were frozen",
        "platform": "nangate45",
        "checks": {
            "complete_rtl_to_gds": True,
            "post_route_reports_parseable": True,
            "final_timing_violations_zero": True,
            "detailed_route_drc_zero": True,
            "topology_distinction_structurally_retained": True,
        },
        "designs": designs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = validate(args.artifact_root)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
