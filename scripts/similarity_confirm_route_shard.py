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
BUILD = ROOT / "build" / "similarity_confirmation"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

K_TILES = (12, 24, 48)

SHARED = (
    (3, 3), (3, 5), (5, 3), (3, 7), (7, 3), (5, 5),
)
MID = (
    (5, 7), (7, 5), (5, 9), (9, 5), (7, 7),
    (5, 11), (11, 5), (7, 9), (9, 7),
)
LARGE = (
    (7, 11), (11, 7), (9, 9), (7, 13), (13, 7),
    (9, 11), (11, 9), (9, 13), (13, 9),
)

DEVICE_ARGS = {
    "25k": ["--25k", "--package", "CABGA381", "--speed", "6"],
    "45k": ["--45k", "--package", "CABGA381", "--speed", "6"],
    "85k": ["--85k", "--package", "CABGA381", "--speed", "6"],
}

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE = re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz", re.I)


def architecture_pool(device: str) -> list[tuple[int, int, int]]:
    geoms = list(SHARED)
    if device in ("45k", "85k"):
        geoms.extend(MID)
    if device == "85k":
        geoms.extend(LARGE)
    return [(r, c, t) for r, c in geoms for t in K_TILES]


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
        f"{params}; hierarchy -check -top kernellum_k1_pnr_top; "
        f"synth_ecp5 -top kernellum_k1_pnr_top -json {design_json}; stat"
    )

    started = time.time()
    y = run(["yosys", "-p", ys])
    ytext = y.stdout + "\n" + y.stderr
    (work / "yosys.log").write_text(ytext)
    cells = parse_cells(ytext)

    row = {
        "device": device,
        "name": name,
        "rows": r,
        "cols": c,
        "k_tile": t,
        "pe_count": r * c,
        "sqrt_pe": math.sqrt(r * c),
        "perimeter": r + c,
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
        "--seed", "1",
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
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--shards", type=int, default=6)
    args = ap.parse_args()

    pool = architecture_pool(args.device)
    selected = [x for i, x in enumerate(pool) if i % args.shards == args.shard]
    rows = []
    print(f"[confirm] {args.device} shard {args.shard}/{args.shards}: {len(selected)} points", flush=True)
    for i, (r, c, t) in enumerate(selected, 1):
        print(f"[confirm] {args.device} {i}/{len(selected)} {r}x{c} k={t}", flush=True)
        result = route_one(args.device, r, c, t)
        rows.append(result)
        print(f"[confirm] route_ok={result['route_ok']} fmax={result['fmax_mhz']}", flush=True)

    path = OUT / f"similarity_confirm_{args.device}_shard_{args.shard}.csv"
    if rows:
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        path.write_text("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
