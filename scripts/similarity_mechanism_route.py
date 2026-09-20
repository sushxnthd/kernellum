#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BUILD = ROOT / "build" / "similarity_mechanism"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

DEVICE_ARGS = {
    "25k": ["--25k", "--package", "CABGA381", "--speed", "6"],
    "45k": ["--45k", "--package", "CABGA381", "--speed", "6"],
    "85k": ["--85k", "--package", "CABGA381", "--speed", "6"],
}

SIZES = {
    "25k": (3, 5),
    "45k": (3, 5, 7),
    "85k": (3, 5, 7, 9, 11),
}

TOPS = {
    "broadcast": ("rtl/similarity_broadcast_fabric.sv", "similarity_broadcast_fabric"),
    "local": ("rtl/similarity_local_fabric.sv", "similarity_local_fabric"),
}

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE = re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz", re.I)


def run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def parse_cells(text: str) -> dict[str, int]:
    cells: dict[str, int] = {}
    for line in text.splitlines():
        m = CELL_RE.match(line)
        if m:
            cells[m.group(1)] = int(m.group(2))
    return cells


def parse_fmax(text: str) -> float | None:
    vals = [float(m.group(1)) for m in FMAX_RE.finditer(text)]
    return min(vals) if vals else None


def route_one(device: str, topology: str, n: int, seed: int) -> dict:
    source, top = TOPS[topology]
    name = f"{topology}_{device}_{n}x{n}_s{seed}"
    work = BUILD / name
    work.mkdir(parents=True, exist_ok=True)
    design_json = work / "design.json"
    cfg = work / "design.config"

    ys = (
        f"read_verilog -sv {source}; "
        f"chparam -set ROWS {n} -set COLS {n} {top}; "
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design_json}; stat"
    )

    started = time.time()
    y = run(["yosys", "-p", ys])
    ytext = y.stdout + "\n" + y.stderr
    (work / "yosys.log").write_text(ytext)
    cells = parse_cells(ytext)

    row = {
        "device": device,
        "topology": topology,
        "seed": seed,
        "rows": n,
        "cols": n,
        "pe_count": n*n,
        "sqrt_pe": float(n),
        "synth_ok": False,
        "route_ok": False,
        "fmax_mhz": "",
        "period_ns": "",
        "synth_dsp": cells.get("MULT18X18D", 0),
        "synth_bram": cells.get("DP16KD", 0),
        "synth_lut4": cells.get("LUT4", 0),
        "synth_ff": cells.get("TRELLIS_FF", 0),
        "elapsed_sec": "",
        "error_stage": "",
        "returncode": "",
    }

    if y.returncode != 0 or not design_json.exists():
        row["elapsed_sec"] = time.time() - started
        row["error_stage"] = "yosys"
        row["returncode"] = y.returncode
        return row

    row["synth_ok"] = True
    p = run([
        "nextpnr-ecp5",
        *DEVICE_ARGS[device],
        "--json", str(design_json),
        "--textcfg", str(cfg),
        "--freq", "25",
        "--seed", str(seed),
        "--timing-allow-fail",
    ])
    ptext = p.stdout + "\n" + p.stderr
    (work / "nextpnr.log").write_text(ptext)
    fmax = parse_fmax(ptext)

    row["elapsed_sec"] = time.time() - started
    row["returncode"] = p.returncode
    if p.returncode == 0 and cfg.exists() and fmax is not None:
        row["route_ok"] = True
        row["fmax_mhz"] = fmax
        row["period_ns"] = 1000.0 / fmax
    else:
        row["error_stage"] = "nextpnr"
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", choices=sorted(DEVICE_ARGS), required=True)
    ap.add_argument("--topology", choices=sorted(TOPS), required=True)
    ap.add_argument("--seed", type=int, choices=(1,2,3), required=True)
    args = ap.parse_args()

    rows = []
    for n in SIZES[args.device]:
        print(f"[mechanism] {args.device} {args.topology} {n}x{n} seed={args.seed}", flush=True)
        r = route_one(args.device, args.topology, n, args.seed)
        rows.append(r)
        print(f"[mechanism] ok={r['route_ok']} fmax={r['fmax_mhz']} dsp={r['synth_dsp']}", flush=True)

    path = OUT / f"similarity_mechanism_{args.device}_{args.topology}_s{args.seed}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
