#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

from kernellum.k1 import candidate_set, predicted_cycles, spearman
from kernellum.k1.routed_timing import post_route_fmax_mhz
from kernellum.workload import tiny_transformer_suite

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "k1"
OUT = ROOT / "results"
BUILD.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")

def run(cmd: list[str], *, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

def parse_cells(text: str) -> dict[str, int]:
    cells: dict[str, int] = {}
    for line in text.splitlines():
        m = CELL_RE.match(line)
        if m:
            cells[m.group(1)] = int(m.group(2))
    return cells

def synth_and_route(arch) -> dict:
    d = BUILD / arch.name
    d.mkdir(parents=True, exist_ok=True)
    json_path = d / "design.json"
    cfg_path = d / "design.config"
    report_path = d / "report.json"

    params = (
        f"chparam -set ROWS {arch.rows} -set COLS {arch.cols} "
        f"-set K_TILE {arch.k_tile} kernellum_k1_pnr_top"
    )
    yosys_script = (
        "read_verilog -sv rtl/kernellum_mac_array.sv "
        "rtl/kernellum_gemm_engine.sv rtl/kernellum_k1_pnr_top.sv; "
        f"{params}; "
        "hierarchy -check -top kernellum_k1_pnr_top; "
        f"synth_ecp5 -top kernellum_k1_pnr_top -json {json_path}; "
        "stat"
    )
    y = run(["yosys", "-p", yosys_script])
    yosys_text = y.stdout + "\n" + y.stderr
    (d / "yosys.log").write_text(yosys_text)
    cells = parse_cells(yosys_text)

    synth_ok = y.returncode == 0 and json_path.exists()
    if not synth_ok:
        return {
            "name": arch.name,
            "rows": arch.rows,
            "cols": arch.cols,
            "k_tile": arch.k_tile,
            "pred_dsp": arch.pe_count,
            "pred_buffer_bits": arch.ideal_buffer_bits,
            "synth_ok": False,
            "route_ok": False,
            "fmax_mhz": "",
            "timing_metric": "post_route_report_json",
            "synth_dsp": 0,
            "synth_bram": 0,
            "synth_lut4": 0,
            "synth_ff": 0,
            "nextpnr_returncode": "",
        }

    p = run([
        "nextpnr-ecp5",
        "--85k",
        "--package", "CABGA381",
        "--json", str(json_path),
        "--textcfg", str(cfg_path),
        "--report", str(report_path),
        "--freq", "25",
        "--seed", "1",
        "--timing-allow-fail",
    ])
    pnr_text = p.stdout + "\n" + p.stderr
    (d / "nextpnr.log").write_text(pnr_text)
    fmax = None
    if p.returncode == 0 and cfg_path.exists() and report_path.exists():
        try:
            fmax = post_route_fmax_mhz(report_path)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            fmax = None
    route_ok = fmax is not None

    return {
        "name": arch.name,
        "rows": arch.rows,
        "cols": arch.cols,
        "k_tile": arch.k_tile,
        "pred_dsp": arch.pe_count,
        "pred_buffer_bits": arch.ideal_buffer_bits,
        "synth_ok": True,
        "route_ok": route_ok,
        "fmax_mhz": fmax if fmax is not None else "",
        "timing_metric": "post_route_report_json",
        "synth_dsp": cells.get("MULT18X18D", 0),
        "synth_bram": cells.get("DP16KD", 0),
        "synth_lut4": cells.get("LUT4", 0),
        "synth_ff": cells.get("TRELLIS_FF", 0),
        "nextpnr_returncode": p.returncode,
    }

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")

def main() -> int:
    missing = [tool for tool in ("yosys", "iverilog", "vvp", "nextpnr-ecp5") if not shutil.which(tool)]
    if missing:
        print("missing required tools: " + ", ".join(missing), file=sys.stderr)
        return 2

    routes: list[dict] = []
    for arch in candidate_set():
        print(f"[k1] route {arch.name}: {arch.rows}x{arch.cols}, K_TILE={arch.k_tile}", flush=True)
        row = synth_and_route(arch)
        routes.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    routes_path = OUT / "k1_routes.csv"
    write_csv(routes_path, routes)

    successful = [r for r in routes if r["route_ok"]]
    route_by_name = {r["name"]: r for r in successful}
    arch_by_name = {a.name: a for a in candidate_set()}

    dsp_rho = 0.0
    if len([r for r in routes if r["synth_ok"]]) >= 2:
        synth_rows = [r for r in routes if r["synth_ok"]]
        dsp_rho = spearman(
            [float(r["pred_dsp"]) for r in synth_rows],
            [float(r["synth_dsp"]) for r in synth_rows],
        )

    ranking_rows: list[dict] = []
    workload_rhos: list[float] = []
    winner_regrets: list[float] = []
    all_predicted_winners_routed = True

    for w in tiny_transformer_suite():
        per_workload: list[dict] = []
        for arch in candidate_set():
            cycles = predicted_cycles(w.m, w.n, w.k, arch)
            fixed_latency_ms = cycles / (100.0 * 1e3)
            route = route_by_name.get(arch.name)
            routed_latency_ms = ""
            fmax = ""
            if route is not None:
                fmax = float(route["fmax_mhz"])
                routed_latency_ms = cycles / (fmax * 1e3)
            per_workload.append({
                "workload": w.name,
                "architecture": arch.name,
                "m": w.m,
                "n": w.n,
                "k": w.k,
                "predicted_cycles": cycles,
                "fixed_100mhz_ms": fixed_latency_ms,
                "fmax_mhz": fmax,
                "routed_latency_ms": routed_latency_ms,
                "route_ok": route is not None,
            })
        ranking_rows.extend(per_workload)

        routed_rows = [r for r in per_workload if r["route_ok"]]
        if len(routed_rows) >= 2:
            rho = spearman(
                [float(r["fixed_100mhz_ms"]) for r in routed_rows],
                [float(r["routed_latency_ms"]) for r in routed_rows],
            )
            workload_rhos.append(rho)

        predicted_winner = min(per_workload, key=lambda r: float(r["fixed_100mhz_ms"]))
        if not predicted_winner["route_ok"]:
            all_predicted_winners_routed = False
        else:
            routed_winner = min(routed_rows, key=lambda r: float(r["routed_latency_ms"]))
            regret = 100.0 * (
                float(predicted_winner["routed_latency_ms"]) / float(routed_winner["routed_latency_ms"]) - 1.0
            )
            winner_regrets.append(regret)

    rankings_path = OUT / "k1_workload_rankings.csv"
    write_csv(rankings_path, ranking_rows)

    route_success_count = len(successful)
    mean_rho = mean(workload_rhos)
    mean_regret = mean(winner_regrets) if all_predicted_winners_routed else float("inf")

    gate = {
        "target": "Lattice ECP5-85K / CABGA381",
        "candidate_count": len(routes),
        "route_success_count": route_success_count,
        "route_success_required": 8,
        "dsp_rank_spearman": dsp_rho,
        "dsp_rank_required": 0.95,
        "mean_workload_rank_spearman": mean_rho,
        "workload_rank_required": 0.80,
        "mean_predicted_winner_routed_regret_pct": mean_regret if math.isfinite(mean_regret) else None,
        "winner_regret_required_pct": 15.0,
        "all_predicted_winners_routed": all_predicted_winners_routed,
    }
    gate["k1_gate_pass"] = bool(
        route_success_count >= 8
        and dsp_rho >= 0.95
        and mean_rho >= 0.80
        and all_predicted_winners_routed
        and mean_regret <= 15.0
    )
    gate["interpretation"] = (
        "PASS means fixed-frequency analytical architecture ranking remains useful after "
        "ECP5 synthesis and place-and-route for the frozen K1 candidate family. "
        "It is not a physical-board latency, power, or energy result."
    )

    validation_path = OUT / "k1_validation.json"
    validation_path.write_text(json.dumps(gate, indent=2) + "\n")

    print("KERNELLUM_K1_VALIDATION_BEGIN")
    print(json.dumps(gate, indent=2))
    print("KERNELLUM_K1_VALIDATION_END")
    print("KERNELLUM_K1_ROUTES_BEGIN")
    print(routes_path.read_text().strip())
    print("KERNELLUM_K1_ROUTES_END")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
