#!/usr/bin/env python3
"""Run one frozen platform/topology/seed shard of the ASIC transfer study."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
BUILD = ROOT / "build" / "similarity_asic_transfer"
IMAGE = "openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6"
SEEDS = (11, 29, 47)
DISCOVERY_GEOMETRIES = ((2, 4), (4, 2), (3, 6), (6, 3), (5, 5), (7, 7))
HOLDOUT_GEOMETRIES = ((3, 8), (8, 3), (5, 9), (9, 5))

FIELDS = (
    "platform",
    "split",
    "topology",
    "rows",
    "cols",
    "pe_count",
    "sqrt_pe",
    "seed",
    "attempted",
    "route_ok",
    "error_stage",
    "period_min_ns",
    "fmax_mhz",
    "critical_path_delay_ns",
    "setup_violations",
    "hold_violations",
    "max_slew_violations",
    "max_fanout_violations",
    "max_cap_violations",
    "drc_count",
    "total_cells",
    "dff_cells",
    "cell_area_um2",
    "wire_length_um",
    "gds_sha256",
    "odb_sha256",
    "spef_sha256",
    "netlist_sha256",
    "elapsed_sec",
)


def geometries(platform: str) -> tuple[tuple[str, int, int], ...]:
    bridge = tuple(("discovery" if platform == "nangate45" else "bridge", r, c)
                   for r, c in DISCOVERY_GEOMETRIES)
    if platform == "nangate45":
        return bridge
    return bridge + tuple(("holdout", r, c) for r, c in HOLDOUT_GEOMETRIES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(pattern: str, text: str, label: str, flags: int = 0) -> re.Match[str]:
    match = re.search(pattern, text, flags)
    if match is None:
        raise ValueError(f"missing {label}")
    return match


def parse_synthesis(path: Path) -> dict[str, int | float]:
    text = path.read_text(encoding="utf-8")
    total_cells = int(require(
        r"^\s*(\d+)\s+\S+\s+\d+\s+\S+\s+cells\s*$",
        text,
        "total cell count",
        re.MULTILINE,
    ).group(1))
    area = float(require(
        r"Chip area for module '[^']+':\s*([0-9.eE+-]+)",
        text,
        "cell area",
    ).group(1))
    cell_rows = re.finditer(
        r"^\s*(\d+)\s+\S+\s+\d+\s+\S+\s+(\S+)\s*$",
        text,
        re.MULTILINE,
    )
    dff_cells = sum(
        int(match.group(1))
        for match in cell_rows
        if re.search(r"(?:^|__)(?:s?dff|df|dl)", match.group(2), re.IGNORECASE)
    )
    if total_cells <= 0 or dff_cells <= 0 or area <= 0:
        raise ValueError("nonpositive structural metric")
    return {"total_cells": total_cells, "dff_cells": dff_cells, "cell_area_um2": area}


def parse_finish(path: Path) -> dict[str, int | float]:
    text = path.read_text(encoding="utf-8")
    clock = require(
        r"^clk period_min =\s*([0-9.eE+-]+)\s+fmax =\s*([0-9.eE+-]+)\s*$",
        text,
        "minimum clock period",
        re.MULTILINE,
    )
    result: dict[str, int | float] = {
        "period_min_ns": float(clock.group(1)),
        "fmax_mhz": float(clock.group(2)),
        "critical_path_delay_ns": float(require(
            r"finish critical path delay\s*\n-+\s*\n([0-9.eE+-]+)",
            text,
            "critical path delay",
        ).group(1)),
    }
    for report_name, field_name in (
        ("setup", "setup_violations"),
        ("hold", "hold_violations"),
        ("max slew", "max_slew_violations"),
        ("max fanout", "max_fanout_violations"),
        ("max cap", "max_cap_violations"),
    ):
        result[field_name] = int(require(
            rf"^{re.escape(report_name)} violation count\s+(\d+)\s*$",
            text,
            f"{report_name} violation count",
            re.MULTILINE,
        ).group(1))
    return result


def parse_wire_length(path: Path) -> float:
    text = path.read_text(encoding="utf-8")
    values = re.findall(r"^Total wire length =\s*([0-9.eE+-]+)\s+um\.", text, re.MULTILINE)
    if not values:
        raise ValueError("missing final routed wire length")
    return float(values[-1])


def docker_command(
    repo_root: Path,
    flow_root: Path,
    shell_command: str,
    qemu: Path | None = None,
) -> list[str]:
    command = [
        "docker", "run", "--rm",
        "-v", f"{repo_root}:/work:ro",
        "-v", f"{flow_root}:/OpenROAD-flow-scripts/flow",
    ]
    if qemu is not None:
        command.extend(["-v", f"{qemu}:/usr/local/bin/qemu-x86_64-static:ro"])
    command.extend([
        IMAGE,
        "bash", "-lc",
        "source /OpenROAD-flow-scripts/env.sh && "
        "cd /OpenROAD-flow-scripts/flow && " + shell_command,
    ])
    return command


def run_stage(command: list[str], log: Path, label: str) -> int:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=3600,
            check=False,
        )
        output = completed.stdout
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        # TimeoutExpired may retain captured output as bytes even when the
        # subprocess requested text mode.  Preserve it instead of losing the
        # route's null record to a secondary TypeError.
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        output += "\nTIMEOUT\n"
        returncode = 124
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"\n===== {label} ({time.time() - started:.2f}s) =====\n")
        handle.write(output)
    return returncode


def copy_evidence(flow_root: Path, platform: str, design: str, target: Path) -> None:
    result = flow_root / "results" / platform / design / "base"
    report = flow_root / "reports" / platform / design / "base"
    log = flow_root / "logs" / platform / design / "base"
    (target / "results").mkdir(parents=True, exist_ok=True)
    (target / "reports").mkdir(parents=True, exist_ok=True)
    (target / "logs").mkdir(parents=True, exist_ok=True)
    for name in ("6_final.gds", "6_final.odb", "6_final.spef", "6_final.v", "6_final.sdc"):
        source = result / name
        if source.exists():
            shutil.copy2(source, target / "results" / name)
    for name in ("synth_stat.txt", "5_route_drc.rpt", "6_finish.rpt"):
        source = report / name
        if source.exists():
            shutil.copy2(source, target / "reports" / name)
    for name in ("5_2_route.log", "6_report.log"):
        source = log / name
        if source.exists():
            shutil.copy2(source, target / "logs" / name)


def route_one(
    platform: str,
    split: str,
    topology: str,
    seed: int,
    rows: int,
    cols: int,
    flow_root: Path,
    qemu: Path,
) -> dict[str, object]:
    started = time.time()
    design = f"similarity_asic_transfer_{topology}"
    config = f"/work/asic/transfer/config_{platform}.mk"
    shard = BUILD / platform / topology / f"s{seed}" / f"r{rows}_c{cols}"
    shard.mkdir(parents=True, exist_ok=True)
    run_log = shard / "driver.log"
    common = (
        f"DESIGN_CONFIG={config} DESIGN_NAME={design} "
        f"VERILOG_DEFINES='-D ASIC_ROWS={rows} -D ASIC_COLS={cols}' "
        f"GPL_RANDOM_SEED={seed} GRT_SEED={seed}"
    )
    row: dict[str, object] = {field: "" for field in FIELDS}
    row.update({
        "platform": platform,
        "split": split,
        "topology": topology,
        "rows": rows,
        "cols": cols,
        "pe_count": rows * cols,
        "sqrt_pe": math.sqrt(rows * cols),
        "seed": seed,
        "attempted": True,
        "route_ok": False,
    })

    result_dir = f"results/{platform}/{design}/base"
    native = (
        f"make {common} clean_all && make {common} route && make {common} do-6_1_fill && "
        f"cp {result_dir}/5_route.sdc {result_dir}/6_1_fill.sdc"
    )
    if run_stage(docker_command(ROOT, flow_root, native), run_log, "native route and fill") != 0:
        row["error_stage"] = "native_route"
        copy_evidence(flow_root, platform, design, shard)
        row["elapsed_sec"] = time.time() - started
        return row

    emulated = (
        "/work/scripts/openroad_qemu_wrapper.sh -version && "
        f"make {common} OPENROAD_EXE=/work/scripts/openroad_qemu_wrapper.sh do-6_report"
    )
    if run_stage(docker_command(ROOT, flow_root, emulated, qemu), run_log, "emulated final report") != 0:
        row["error_stage"] = "final_report"
        copy_evidence(flow_root, platform, design, shard)
        row["elapsed_sec"] = time.time() - started
        return row

    if run_stage(docker_command(ROOT, flow_root, f"make {common} finish"), run_log, "native finish") != 0:
        row["error_stage"] = "native_finish"
        copy_evidence(flow_root, platform, design, shard)
        row["elapsed_sec"] = time.time() - started
        return row

    copy_evidence(flow_root, platform, design, shard)
    try:
        report_dir = shard / "reports"
        result_dir = shard / "results"
        row.update(parse_finish(report_dir / "6_finish.rpt"))
        row.update(parse_synthesis(report_dir / "synth_stat.txt"))
        row["wire_length_um"] = parse_wire_length(shard / "logs" / "5_2_route.log")
        drc_text = (report_dir / "5_route_drc.rpt").read_text(encoding="utf-8").strip()
        row["drc_count"] = len(drc_text.splitlines()) if drc_text else 0
        for name, field in (
            ("6_final.gds", "gds_sha256"),
            ("6_final.odb", "odb_sha256"),
            ("6_final.spef", "spef_sha256"),
            ("6_final.v", "netlist_sha256"),
        ):
            path = result_dir / name
            if path.stat().st_size <= 0:
                raise ValueError(f"empty {name}")
            row[field] = sha256(path)
        row["route_ok"] = True
    except (OSError, ValueError) as exc:
        row["error_stage"] = f"audit:{exc}"
    row["elapsed_sec"] = time.time() - started
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("nangate45", "sky130hd"), required=True)
    parser.add_argument("--topology", choices=("broadcast", "local"), required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--flow-root", type=Path, required=True)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-x86_64-static"))
    args = parser.parse_args()

    RESULTS.mkdir(exist_ok=True)
    rows = []
    for split, row_count, col_count in geometries(args.platform):
        print(
            f"[asic-transfer] {args.platform} {args.topology} s{args.seed} "
            f"{split} {row_count}x{col_count}",
            flush=True,
        )
        result = route_one(
            args.platform,
            split,
            args.topology,
            args.seed,
            row_count,
            col_count,
            args.flow_root.resolve(),
            args.qemu.resolve(),
        )
        rows.append(result)
        print(
            f"[asic-transfer] ok={result['route_ok']} "
            f"period={result['period_min_ns']} error={result['error_stage']}",
            flush=True,
        )

    output = RESULTS / f"similarity_asic_transfer_{args.platform}_{args.topology}_s{args.seed}.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
