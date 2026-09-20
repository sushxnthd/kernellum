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

from kernellum.k1.closed_loop import (
    RoutedObservation,
    active_proposals,
    expanded_pool,
    load_observations,
    predict_fmax,
    random_controls,
)
from kernellum.k1.model import predicted_cycles
from kernellum.k1.routed_timing import post_route_fmax_mhz
from kernellum.workload import tiny_transformer_suite

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "k1_closed_loop"
OUT = ROOT / "results"
BUILD.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

BASE_ROUTES = OUT / "k1_routes.csv"
CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")


def run(cmd: list[str], *, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def parse_cells(text: str) -> dict[str, int]:
    cells: dict[str, int] = {}
    for line in text.splitlines():
        m = CELL_RE.match(line)
        if m:
            cells[m.group(1)] = int(m.group(2))
    return cells


def synth_and_route(arch, arm: str, predicted_fmax: float | None, uncertainty: float | None) -> dict:
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
    ytext = y.stdout + "\n" + y.stderr
    (d / "yosys.log").write_text(ytext)
    cells = parse_cells(ytext)
    synth_ok = y.returncode == 0 and json_path.exists()

    pnr_returncode: int | str = ""
    fmax: float | str = ""
    route_ok = False
    if synth_ok:
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
        pnr_returncode = p.returncode
        ptext = p.stdout + "\n" + p.stderr
        (d / "nextpnr.log").write_text(ptext)
        if p.returncode == 0 and cfg_path.exists() and report_path.exists():
            try:
                fmax = post_route_fmax_mhz(report_path)
                route_ok = True
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                fmax = ""

    return {
        "arm": arm,
        "name": arch.name,
        "rows": arch.rows,
        "cols": arch.cols,
        "k_tile": arch.k_tile,
        "predicted_fmax_mhz": predicted_fmax if predicted_fmax is not None else "",
        "uncertainty": uncertainty if uncertainty is not None else "",
        "synth_ok": synth_ok,
        "route_ok": route_ok,
        "fmax_mhz": fmax,
        "timing_metric": "post_route_report_json",
        "synth_dsp": cells.get("MULT18X18D", 0),
        "synth_bram": cells.get("DP16KD", 0),
        "synth_lut4": cells.get("LUT4", 0),
        "synth_ff": cells.get("TRELLIS_FF", 0),
        "nextpnr_returncode": pnr_returncode,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def routed_latency_ms(w, arch, fmax: float) -> float:
    return predicted_cycles(w.m, w.n, w.k, arch) / (fmax * 1e3)


def main() -> int:
    required = ("yosys", "nextpnr-ecp5", "iverilog", "vvp")
    missing = [x for x in required if not shutil.which(x)]
    if missing:
        print("missing required tools: " + ", ".join(missing), file=sys.stderr)
        return 2
    if not BASE_ROUTES.exists():
        print(f"missing initial K1 evidence: {BASE_ROUTES}", file=sys.stderr)
        return 2

    observations = load_observations(BASE_ROUTES)
    workloads = tiny_transformer_suite()
    active = active_proposals(observations, workloads, n=4)
    controls = random_controls(observations, active, n=4, seed=20260919)

    proposal_doc = {
        "pool_size": len(expanded_pool()),
        "initial_observations": len(observations),
        "active": [
            {
                "name": x["arch"].name,
                "rows": x["arch"].rows,
                "cols": x["arch"].cols,
                "k_tile": x["arch"].k_tile,
                "predicted_fmax_mhz": x["predicted_fmax_mhz"],
                "uncertainty": x["uncertainty"],
                "acquisition_score": x["acquisition_score"],
            }
            for x in active
        ],
        "random_seed": 20260919,
        "random": [
            {"name": a.name, "rows": a.rows, "cols": a.cols, "k_tile": a.k_tile}
            for a in controls
        ],
    }
    (OUT / "k1_closed_loop_proposals.json").write_text(json.dumps(proposal_doc, indent=2) + "\n")
    print(json.dumps(proposal_doc, indent=2), flush=True)

    routed_rows: list[dict] = []
    for x in active:
        arch = x["arch"]
        print(f"[closed-loop active] routing {arch.name}", flush=True)
        routed_rows.append(synth_and_route(
            arch,
            "active",
            float(x["predicted_fmax_mhz"]),
            float(x["uncertainty"]),
        ))

    for arch in controls:
        pred, uncertainty = predict_fmax(arch, observations)
        print(f"[closed-loop random] routing {arch.name}", flush=True)
        routed_rows.append(synth_and_route(arch, "random", pred, uncertainty))

    write_csv(OUT / "k1_closed_loop_routes.csv", routed_rows)

    successful = [r for r in routed_rows if r["route_ok"]]
    mape_values = [
        abs(float(r["fmax_mhz"]) - float(r["predicted_fmax_mhz"])) / float(r["fmax_mhz"]) * 100.0
        for r in successful
    ]
    surrogate_mape = sum(mape_values) / len(mape_values) if mape_values else float("inf")

    initial_by_name = {o.arch.name: o for o in observations}
    active_success = [
        RoutedObservation(
            next(x["arch"] for x in active if x["arch"].name == r["name"]),
            float(r["fmax_mhz"]),
        )
        for r in routed_rows if r["route_ok"] and r["arm"] == "active"
    ]
    control_arch_by_name = {a.name: a for a in controls}
    random_success = [
        RoutedObservation(control_arch_by_name[r["name"]], float(r["fmax_mhz"]))
        for r in routed_rows if r["route_ok"] and r["arm"] == "random"
    ]

    active_final_values: list[float] = []
    random_final_values: list[float] = []
    active_improvements = 0
    random_improvements = 0
    per_workload = []

    for w in workloads:
        initial_best = min(routed_latency_ms(w, o.arch, o.fmax_mhz) for o in observations)
        active_best = min(
            [initial_best] + [routed_latency_ms(w, o.arch, o.fmax_mhz) for o in active_success]
        )
        random_best = min(
            [initial_best] + [routed_latency_ms(w, o.arch, o.fmax_mhz) for o in random_success]
        )
        active_final_values.append(active_best)
        random_final_values.append(random_best)
        if active_best < initial_best - 1e-12:
            active_improvements += 1
        if random_best < initial_best - 1e-12:
            random_improvements += 1
        per_workload.append({
            "workload": w.name,
            "initial_best_ms": initial_best,
            "active_final_best_ms": active_best,
            "random_final_best_ms": random_best,
        })

    active_mean = sum(active_final_values) / len(active_final_values)
    random_mean = sum(random_final_values) / len(random_final_values)
    attempted_total = len(observations) + len(routed_rows)
    observed_fraction = attempted_total / len(expanded_pool())

    validation = {
        "pool_size": len(expanded_pool()),
        "initial_observations": len(observations),
        "new_routes_attempted": len(routed_rows),
        "new_route_success_count": len(successful),
        "route_success_required": 7,
        "total_architectures_physically_attempted": attempted_total,
        "observed_fraction": observed_fraction,
        "observed_fraction_limit": 0.10,
        "surrogate_fmax_mape_pct": surrogate_mape,
        "surrogate_fmax_mape_limit_pct": 20.0,
        "active_mean_final_best_ms": active_mean,
        "random_mean_final_best_ms": random_mean,
        "active_no_worse_than_random": active_mean <= random_mean + 1e-12,
        "active_improved_workloads": active_improvements,
        "random_improved_workloads": random_improvements,
        "active_improvement_count_no_worse": active_improvements >= random_improvements,
        "per_workload": per_workload,
    }
    validation["closed_loop_gate_pass"] = bool(
        len(successful) >= 7
        and observed_fraction <= 0.10
        and surrogate_mape <= 20.0
        and validation["active_no_worse_than_random"]
        and validation["active_improvement_count_no_worse"]
    )
    validation["interpretation"] = (
        "PASS means the routed-observation-driven selector used its equal physical-design budget "
        "at least as effectively as the frozen random control in this ECP5 candidate space."
    )
    (OUT / "k1_closed_loop_validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print("KERNELLUM_K1_CLOSED_LOOP_VALIDATION_BEGIN")
    print(json.dumps(validation, indent=2))
    print("KERNELLUM_K1_CLOSED_LOOP_VALIDATION_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
