#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path

from kernellum.k1.routed_timing import post_route_fmax_mhz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BUILD = ROOT / "build" / "similarity_functional"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

ARCHITECTURES = (
    ("r04_c04_k16", 4, 4, 16),
    ("r04_c08_k32", 4, 8, 32),
    ("r08_c04_k32", 8, 4, 32),
    ("r08_c08_k16", 8, 8, 16),
    ("r08_c08_k64", 8, 8, 64),
    ("r08_c12_k32", 8, 12, 32),
    ("r12_c08_k32", 12, 8, 32),
    ("r10_c12_k64", 10, 12, 64),
    ("r12_c10_k64", 12, 10, 64),
)


def run(cmd: list[str], timeout: int = 2100) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def utilization(report: Path, cell: str) -> int:
    data = json.loads(report.read_text())
    item = data.get("utilization", {}).get(cell)
    return int(item["used"]) if item else 0


def route_one(name: str, rows: int, cols: int, k_tile: int, topology: str, seed: int) -> dict:
    transport = 0 if topology == "broadcast" else 1
    d = BUILD / f"{name}_{topology}_s{seed}"
    d.mkdir(parents=True, exist_ok=True)
    design = d / "design.json"
    config = d / "design.config"
    report = d / "report.json"
    yosys_log = d / "yosys.log"
    nextpnr_log = d / "nextpnr.log"

    ys = (
        "read_verilog -sv rtl/kernellum_mac_array.sv "
        "rtl/kernellum_local_mac_array.sv rtl/kernellum_gemm_engine.sv "
        "rtl/kernellum_k1_pnr_top.sv; "
        f"chparam -set ROWS {rows} -set COLS {cols} -set K_TILE {k_tile} "
        f"-set TRANSPORT {transport} kernellum_k1_pnr_top; "
        "hierarchy -check -top kernellum_k1_pnr_top; "
        f"synth_ecp5 -top kernellum_k1_pnr_top -json {design}; stat"
    )

    started = time.time()
    y = run(["yosys", "-p", ys])
    yosys_log.write_text(y.stdout + "\n" + y.stderr)
    row = {
        "name": name,
        "topology": topology,
        "rows": rows,
        "cols": cols,
        "k_tile": k_tile,
        "pe_count": rows * cols,
        "seed": seed,
        "route_ok": False,
        "routed_fmax_mhz": "",
        "routed_period_ns": "",
        "synth_dsp": "",
        "synth_bram": "",
        "synth_lut4": "",
        "synth_ff": "",
        "elapsed_sec": "",
        "error_stage": "",
        "timing_metric": "post_route_report_json",
    }
    if y.returncode != 0 or not design.exists():
        row["elapsed_sec"] = time.time() - started
        row["error_stage"] = "yosys"
        return row

    try:
        p = run([
            "nextpnr-ecp5", "--85k", "--package", "CABGA381", "--speed", "6",
            "--json", str(design), "--textcfg", str(config), "--report", str(report),
            "--freq", "25", "--seed", str(seed), "--timing-allow-fail",
        ])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"] = time.time() - started
        row["error_stage"] = "nextpnr_timeout"
        return row

    nextpnr_log.write_text(p.stdout + "\n" + p.stderr)
    row["elapsed_sec"] = time.time() - started
    if p.returncode == 0 and config.exists() and report.exists():
        try:
            fmax = post_route_fmax_mhz(report)
            row["route_ok"] = True
            row["routed_fmax_mhz"] = fmax
            row["routed_period_ns"] = 1000.0 / fmax
            row["synth_dsp"] = utilization(report, "MULT18X18D")
            row["synth_bram"] = utilization(report, "DP16KD")
            row["synth_lut4"] = utilization(report, "LUT4")
            row["synth_ff"] = utilization(report, "TRELLIS_FF")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            row["error_stage"] = f"report_parse:{exc}"
    else:
        row["error_stage"] = "nextpnr"
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topology", choices=("broadcast", "local"), required=True)
    parser.add_argument("--seed", type=int, choices=(23, 24, 25), required=True)
    args = parser.parse_args()

    rows = []
    for name, nr, nc, kt in ARCHITECTURES:
        print(f"[functional-transfer] {name} {args.topology} seed={args.seed}", flush=True)
        row = route_one(name, nr, nc, kt, args.topology, args.seed)
        rows.append(row)
        print(
            f"[functional-transfer] ok={row['route_ok']} "
            f"fmax={row['routed_fmax_mhz']} dsp={row['synth_dsp']}",
            flush=True,
        )

    path = OUT / f"similarity_functional_{args.topology}_s{args.seed}.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
