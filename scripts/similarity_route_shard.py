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
BUILD = ROOT / "build" / "similarity"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

ROWS_COLS = (2, 4, 6, 8, 10, 12, 14)
K_TILES = (8, 16, 32, 64)

DEVICE_ARGS = {
    "25k": ["--25k", "--package", "CABGA381", "--speed", "6"],
    "45k": ["--45k", "--package", "CABGA381", "--speed", "6"],
    "85k": ["--85k", "--package", "CABGA381", "--speed", "6"],
}

DEVICE_CAPS = {
    "25k": {"dsp": 28, "bram": 56},
    "45k": {"dsp": 72, "bram": 108},
    "85k": {"dsp": 156, "bram": 208},
}

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE = re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz", re.I)


def architecture_pool(device: str) -> list[tuple[int, int, int]]:
    pool = [
        (r, c, t)
        for r in ROWS_COLS
        for c in ROWS_COLS
        for t in K_TILES
        if r * c <= 120
    ]
    if device == "25k":
        pool = [x for x in pool if x[0] * x[1] <= 48]
    return pool


def run(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
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


def parse_fmax(text: str) -> float | None:
    values = [float(m.group(1)) for m in FMAX_RE.finditer(text)]
    return min(values) if values else None


def route_one(device: str, r: int, c: int, t: int) -> dict:
    name = f"r{r:02d}_c{c:02d}_k{t:02d}"
    work = BUILD / device / name
    work.mkdir(parents=True, exist_ok=True)
    design_json = work / "design.json"
    cfg = work / "design.config"

    params = (
        f"chparam -set ROWS {r} -set COLS {c} "
        f"-set K_TILE {t} kernellum_k1_pnr_top"
    )
    ys = (
        "read_verilog -sv rtl/kernellum_mac_array.sv "
        "rtl/kernellum_gemm_engine.sv rtl/kernellum_k1_pnr_top.sv; "
        f"{params}; "
        "hierarchy -check -top kernellum_k1_pnr_top; "
        f"synth_ecp5 -top kernellum_k1_pnr_top -json {design_json}; "
        "stat"
    )

    started = time.time()
    y = run(["yosys", "-p", ys])
    ytext = y.stdout + "\n" + y.stderr
    (work / "yosys.log").write_text(ytext)
    cells = parse_cells(ytext)

    base = {
        "device": device,
        "name": name,
        "rows": r,
        "cols": c,
        "k_tile": t,
        "pe_count": r * c,
        "perimeter": r + c,
        "anisotropy": abs(math.log(r / c)),
        "log2_k_tile": math.log2(t),
        "dsp_capacity": DEVICE_CAPS[device]["dsp"],
        "bram_capacity": DEVICE_CAPS[device]["bram"],
        "synth_ok": False,
        "route_ok": False,
        "fmax_mhz": "",
        "synth_dsp": cells.get("MULT18X18D", 0),
        "synth_bram": cells.get("DP16KD", 0),
        "synth_lut4": cells.get("LUT4", 0),
        "synth_ff": cells.get("TRELLIS_FF", 0),
        "elapsed_sec": "",
        "error_stage": "",
        "returncode": "",
    }

    if y.returncode != 0 or not design_json.exists():
        base["elapsed_sec"] = time.time() - started
        base["error_stage"] = "yosys"
        base["returncode"] = y.returncode
        return base

    base["synth_ok"] = True

    p = run([
        "nextpnr-ecp5",
        *DEVICE_ARGS[device],
        "--json", str(design_json),
        "--textcfg", str(cfg),
        "--freq", "25",
        "--seed", "1",
        "--timing-allow-fail",
    ])
    ptext = p.stdout + "\n" + p.stderr
    (work / "nextpnr.log").write_text(ptext)
    fmax = parse_fmax(ptext)

    base["elapsed_sec"] = time.time() - started
    base["returncode"] = p.returncode
    if p.returncode == 0 and cfg.exists() and fmax is not None:
        base["route_ok"] = True
        base["fmax_mhz"] = fmax
    else:
        base["error_stage"] = "nextpnr"
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", choices=sorted(DEVICE_ARGS), required=True)
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--shards", type=int, required=True)
    args = ap.parse_args()

    pool = architecture_pool(args.device)
    selected = [x for i, x in enumerate(pool) if i % args.shards == args.shard]
    rows: list[dict] = []

    print(
        f"[similarity] device={args.device} shard={args.shard}/{args.shards} "
        f"points={len(selected)} total_pool={len(pool)}",
        flush=True,
    )

    for i, (r, c, t) in enumerate(selected, start=1):
        print(
            f"[similarity] {args.device} {i}/{len(selected)} "
            f"r={r} c={c} k_tile={t}",
            flush=True,
        )
        row = route_one(args.device, r, c, t)
        rows.append(row)
        print(
            f"[similarity] result route_ok={row['route_ok']} "
            f"fmax={row['fmax_mhz']} dsp={row['synth_dsp']}",
            flush=True,
        )

    out = OUT / f"similarity_{args.device}_shard_{args.shard}.csv"
    if rows:
        with out.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        out.write_text("")
    print(f"[similarity] wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
