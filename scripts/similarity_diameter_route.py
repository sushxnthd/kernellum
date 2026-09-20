#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BUILD = ROOT / "build" / "similarity_diameter"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

GEOMETRIES = {
    64: ((2,32),(4,16),(8,8),(16,4),(32,2)),
    96: ((4,24),(6,16),(8,12),(12,8),(16,6),(24,4)),
}

TOPS = {
    "broadcast": ("rtl/similarity_diameter_broadcast.sv", "similarity_diameter_broadcast"),
    "local": ("rtl/similarity_diameter_local.sv", "similarity_diameter_local"),
}

CELL_RE = re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE = re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz", re.I)


def run(cmd: list[str], timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def parse_cells(text: str) -> dict[str,int]:
    cells={}
    for line in text.splitlines():
        m=CELL_RE.match(line)
        if m:
            cells[m.group(1)]=int(m.group(2))
    return cells


def parse_fmax(text: str) -> float | None:
    vals=[float(m.group(1)) for m in FMAX_RE.finditer(text)]
    return min(vals) if vals else None


def route_one(group: int, topology: str, rows: int, cols: int, seed: int) -> dict:
    source, top = TOPS[topology]
    name=f"p{group}_{topology}_r{rows:02d}_c{cols:02d}_s{seed}"
    d=BUILD/name
    d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json"
    cfg=d/"design.config"

    ys=(
        f"read_verilog -sv {source}; "
        f"chparam -set ROWS {rows} -set COLS {cols} {top}; "
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat"
    )
    started=time.time()
    try:
        y=run(["yosys","-p",ys])
    except subprocess.TimeoutExpired:
        return {
            "pe_group":group,"topology":topology,"seed":seed,"rows":rows,"cols":cols,
            "pe_count":rows*cols,"diameter":max(rows,cols),"synth_ok":False,"route_ok":False,
            "fmax_mhz":"","period_ns":"","synth_dsp":0,"synth_lut4":0,"synth_ff":0,
            "elapsed_sec":time.time()-started,"error_stage":"yosys_timeout","returncode":""
        }
    ytext=y.stdout+"\n"+y.stderr
    (d/"yosys.log").write_text(ytext)
    cells=parse_cells(ytext)

    row={
        "pe_group":group,"topology":topology,"seed":seed,"rows":rows,"cols":cols,
        "pe_count":rows*cols,"diameter":max(rows,cols),
        "synth_ok":False,"route_ok":False,"fmax_mhz":"","period_ns":"",
        "synth_dsp":cells.get("MULT18X18D",0),"synth_lut4":cells.get("LUT4",0),
        "synth_ff":cells.get("TRELLIS_FF",0),"elapsed_sec":"","error_stage":"","returncode":""
    }
    if y.returncode != 0 or not design.exists():
        row["elapsed_sec"]=time.time()-started
        row["error_stage"]="yosys"
        row["returncode"]=y.returncode
        return row
    row["synth_ok"]=True

    try:
        p=run([
            "nextpnr-ecp5","--85k","--package","CABGA381","--speed","6",
            "--json",str(design),"--textcfg",str(cfg),"--freq","25",
            "--seed",str(seed),"--timing-allow-fail"
        ])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"]=time.time()-started
        row["error_stage"]="nextpnr_timeout"
        return row
    ptext=p.stdout+"\n"+p.stderr
    (d/"nextpnr.log").write_text(ptext)
    fmax=parse_fmax(ptext)
    row["elapsed_sec"]=time.time()-started
    row["returncode"]=p.returncode
    if p.returncode==0 and cfg.exists() and fmax is not None:
        row["route_ok"]=True
        row["fmax_mhz"]=fmax
        row["period_ns"]=1000.0/fmax
    else:
        row["error_stage"]="nextpnr"
    return row


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--group",type=int,choices=(64,96),required=True)
    ap.add_argument("--topology",choices=("broadcast","local"),required=True)
    ap.add_argument("--seed",type=int,choices=(1,2,3),required=True)
    args=ap.parse_args()

    rows=[]
    for r,c in GEOMETRIES[args.group]:
        print(f"[diameter] P={args.group} {args.topology} {r}x{c} D={max(r,c)} seed={args.seed}",flush=True)
        item=route_one(args.group,args.topology,r,c,args.seed)
        rows.append(item)
        print(f"[diameter] ok={item['route_ok']} fmax={item['fmax_mhz']} dsp={item['synth_dsp']}",flush=True)

    path=OUT/f"similarity_diameter_p{args.group}_{args.topology}_s{args.seed}.csv"
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
