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
BUILD = ROOT / "build" / "similarity_fanout"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

FANOUTS = {
    6: (1, 2, 3, 6),
    8: (1, 2, 4, 8),
    10: (1, 2, 5, 10),
}

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE = re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz", re.I)


def run(cmd: list[str], timeout: int = 1800) -> subprocess.CompletedProcess[str]:
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


def route_one(n: int, a_fanout: int, b_fanout: int, seed: int) -> dict:
    name = f"n{n}_fa{a_fanout}_fb{b_fanout}_s{seed}"
    work = BUILD / name
    work.mkdir(parents=True, exist_ok=True)
    design_json = work / "design.json"
    cfg = work / "design.config"

    ys = (
        "read_verilog -sv rtl/similarity_segmented_broadcast.sv; "
        f"chparam -set N {n} -set A_FANOUT {a_fanout} -set B_FANOUT {b_fanout} "
        "similarity_segmented_broadcast; "
        "hierarchy -check -top similarity_segmented_broadcast; "
        f"synth_ecp5 -top similarity_segmented_broadcast -json {design_json}; stat"
    )

    started = time.time()
    try:
        y = run(["yosys", "-p", ys])
    except subprocess.TimeoutExpired:
        return {
            "n": n, "seed": seed, "a_fanout": a_fanout, "b_fanout": b_fanout,
            "pe_count": n*n, "fanout_product": a_fanout*b_fanout,
            "fanout_geomean": math.sqrt(a_fanout*b_fanout),
            "fanout_arithmean": 0.5*(a_fanout+b_fanout),
            "fanout_max": max(a_fanout,b_fanout),
            "synth_ok": False, "route_ok": False, "fmax_mhz": "", "period_ns": "",
            "synth_dsp": 0, "synth_lut4": 0, "synth_ff": 0,
            "elapsed_sec": time.time()-started, "error_stage": "yosys_timeout",
            "returncode": "",
        }

    ytext = y.stdout + "\n" + y.stderr
    (work / "yosys.log").write_text(ytext)
    cells = parse_cells(ytext)

    row = {
        "n": n,
        "seed": seed,
        "a_fanout": a_fanout,
        "b_fanout": b_fanout,
        "pe_count": n*n,
        "fanout_product": a_fanout*b_fanout,
        "fanout_geomean": math.sqrt(a_fanout*b_fanout),
        "fanout_arithmean": 0.5*(a_fanout+b_fanout),
        "fanout_max": max(a_fanout,b_fanout),
        "synth_ok": False,
        "route_ok": False,
        "fmax_mhz": "",
        "period_ns": "",
        "synth_dsp": cells.get("MULT18X18D", 0),
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
    try:
        p = run([
            "nextpnr-ecp5",
            "--85k", "--package", "CABGA381", "--speed", "6",
            "--json", str(design_json),
            "--textcfg", str(cfg),
            "--freq", "25",
            "--seed", str(seed),
            "--timing-allow-fail",
        ])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"] = time.time() - started
        row["error_stage"] = "nextpnr_timeout"
        return row

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
    ap.add_argument("--n", type=int, choices=sorted(FANOUTS), required=True)
    ap.add_argument("--seed", type=int, choices=(1, 2, 3), required=True)
    args = ap.parse_args()

    rows = []
    for fa in FANOUTS[args.n]:
        for fb in FANOUTS[args.n]:
            print(
                f"[fanout] N={args.n} FA={fa} FB={fb} "
                f"G={math.sqrt(fa*fb):.3f} seed={args.seed}",
                flush=True,
            )
            r = route_one(args.n, fa, fb, args.seed)
            rows.append(r)
            print(
                f"[fanout] ok={r['route_ok']} fmax={r['fmax_mhz']} "
                f"dsp={r['synth_dsp']} ff={r['synth_ff']}",
                flush=True,
            )

    path = OUT / f"similarity_fanout_n{args.n}_s{args.seed}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
