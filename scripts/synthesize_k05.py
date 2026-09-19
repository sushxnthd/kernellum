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

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "rtl" / "kernellum_mac_array.sv"
OUT = ROOT / "results"
BUILD = ROOT / "build" / "k05"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    {"name": "a04x04_b064", "rows": 4,  "cols": 4,  "buffer_kb": 64},
    {"name": "a08x08_b064", "rows": 8,  "cols": 8,  "buffer_kb": 64},
    {"name": "a08x16_b064", "rows": 8,  "cols": 16, "buffer_kb": 64},
    {"name": "a16x08_b064", "rows": 16, "cols": 8,  "buffer_kb": 64},
    {"name": "a16x16_b064", "rows": 16, "cols": 16, "buffer_kb": 64},
    {"name": "a16x16_b128", "rows": 16, "cols": 16, "buffer_kb": 128},
    {"name": "a16x32_b128", "rows": 16, "cols": 32, "buffer_kb": 128},
    {"name": "a32x16_b128", "rows": 32, "cols": 16, "buffer_kb": 128},
    {"name": "a16x32_b256", "rows": 16, "cols": 32, "buffer_kb": 256},
]

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")

def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)

def parse_cells(text: str) -> dict[str, int]:
    cells: dict[str, int] = {}
    for line in text.splitlines():
        m = CELL_RE.match(line)
        if m:
            cells[m.group(1)] = int(m.group(2))
    return cells

def rank(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg = (i + j - 1) / 2.0 + 1.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg
        i = j
    return ranks

def pearson(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return float("nan")
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x-ma)**2 for x in a))
    db = math.sqrt(sum((y-mb)**2 for y in b))
    return num/(da*db) if da and db else 1.0

def spearman(a: list[float], b: list[float]) -> float:
    return pearson(rank(a), rank(b))

def synth_one(c: dict) -> dict:
    params = (
        f"chparam -set ROWS {c['rows']} -set COLS {c['cols']} "
        f"-set PRECISION 8 -set ACC_WIDTH 32 -set BUFFER_KB {c['buffer_kb']} kernellum_mac_array"
    )

    generic_cmd = (
        f"read_verilog -sv {RTL}; {params}; hierarchy -top kernellum_mac_array; "
        "proc; memory -nomap; opt; stat"
    )
    g = run(["yosys", "-p", generic_cmd])
    generic_cells = parse_cells(g.stdout + "\n" + g.stderr)

    xilinx_cmd = (
        f"read_verilog -sv {RTL}; {params}; "
        "synth_xilinx -family xc7 -top kernellum_mac_array -flatten -noiopad; stat -tech xilinx"
    )
    x = run(["yosys", "-p", xilinx_cmd])
    xilinx_text = x.stdout + "\n" + x.stderr
    (BUILD / f"{c['name']}.yosys.log").write_text(xilinx_text)
    cells = parse_cells(xilinx_text)

    dsp = cells.get("DSP48E1", 0) + cells.get("DSP48E2", 0)
    bram18 = cells.get("RAMB18E1", 0) + cells.get("RAMB18E2", 0)
    bram36 = cells.get("RAMB36E1", 0) + cells.get("RAMB36E2", 0)
    bram18eq = bram18 + 2 * bram36
    luts = sum(cells.get(f"LUT{i}", 0) for i in range(1, 7))
    ffs = sum(cells.get(n, 0) for n in ("FDRE", "FDSE", "FDCE", "FDPE"))

    pred_dsp = math.ceil(c["rows"] * c["cols"])
    pred_bram = math.ceil(c["buffer_kb"] * 1024 / 2304)

    return {
        **c,
        "pred_dsp": pred_dsp,
        "pred_bram18eq": pred_bram,
        "generic_mul_cells": generic_cells.get("$mul", 0),
        "generic_mem_cells": generic_cells.get("$mem_v2", 0),
        "synth_dsp": dsp,
        "synth_bram18": bram18,
        "synth_bram36": bram36,
        "synth_bram18eq": bram18eq,
        "synth_luts": luts,
        "synth_ffs": ffs,
        "dsp_abs_error": abs(dsp - pred_dsp),
        "bram_abs_error": abs(bram18eq - pred_bram),
        "bram_pct_error": 100.0 * abs(bram18eq - pred_bram) / pred_bram,
    }

def main() -> int:
    for tool in ("yosys", "iverilog", "vvp"):
        if not shutil.which(tool):
            print(f"missing required tool: {tool}", file=sys.stderr)
            return 2

    rows = []
    for c in CANDIDATES:
        print(f"[k0.5] synthesizing {c['name']}...", flush=True)
        rows.append(synth_one(c))

    csv_path = OUT / "k05_synthesis.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    dsp_rho = spearman([r["pred_dsp"] for r in rows], [r["synth_dsp"] for r in rows])
    bram_rho = spearman([r["pred_bram18eq"] for r in rows], [r["synth_bram18eq"] for r in rows])
    mean_bram_err = sum(r["bram_pct_error"] for r in rows) / len(rows)
    multiplier_preservation = sum(r["generic_mul_cells"] == r["rows"]*r["cols"] for r in rows) / len(rows)
    dsp_mapping_ratio = sum(min(1.0, r["synth_dsp"] / max(1, r["pred_dsp"])) for r in rows) / len(rows)

    yosys_version = run(["yosys", "-V"]).stdout.strip()
    iverilog_version = run(["iverilog", "-V"]).stdout.splitlines()[0].strip()

    gate = {
        "yosys_version": yosys_version,
        "iverilog_version": iverilog_version,
        "functional_simulation_required": True,
        "candidate_count": len(rows),
        "dsp_rank_spearman": dsp_rho,
        "bram_rank_spearman": bram_rho,
        "mean_bram_pct_error": mean_bram_err,
        "generic_multiplier_preservation_rate": multiplier_preservation,
        "mean_dsp_mapping_ratio": dsp_mapping_ratio,
    }
    gate["resource_model_gate_pass"] = bool(
        dsp_rho >= 0.90
        and bram_rho >= 0.90
        and mean_bram_err <= 20.0
        and multiplier_preservation >= 0.99
        and dsp_mapping_ratio >= 0.80
    )
    gate["interpretation"] = (
        "PASS means the coarse K0 resource ranking survives this Xilinx-7 synthesis sample. "
        "It does not validate latency, power, placement, routing, or measured FPGA performance."
    )

    json_path = OUT / "k05_validation.json"
    json_path.write_text(json.dumps(gate, indent=2) + "\n")

    print("\nKERNELLUM_K05_SYNTHESIS_CSV_BEGIN")
    print(csv_path.read_text().strip())
    print("KERNELLUM_K05_SYNTHESIS_CSV_END")
    print("KERNELLUM_K05_VALIDATION_JSON_BEGIN")
    print(json.dumps(gate, indent=2))
    print("KERNELLUM_K05_VALIDATION_JSON_END")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
