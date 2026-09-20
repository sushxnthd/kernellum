#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results"
BUILD=ROOT/"build"/"similarity_mechanism_confirmation"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True,exist_ok=True)

DEVICE_ARGS={
    "25k":["--25k","--package","CABGA381","--speed","6"],
    "45k":["--45k","--package","CABGA381","--speed","6"],
    "85k":["--85k","--package","CABGA381","--speed","6"],
}
GEOMS={
    "25k":((3,7),),
    "45k":((3,7),(5,9)),
    "85k":((3,7),(5,9),(7,11)),
}
TOPS={
    "broadcast":("rtl/similarity_broadcast_fabric.sv","similarity_broadcast_fabric"),
    "local":("rtl/similarity_local_fabric.sv","similarity_local_fabric"),
}
CELL_RE=re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE=re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz",re.I)

def run(cmd,timeout=1800):
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)

def cells(text):
    out={}
    for line in text.splitlines():
        m=CELL_RE.match(line)
        if m: out[m.group(1)]=int(m.group(2))
    return out

def route_one(device,topology,rows,cols,seed):
    src,top=TOPS[topology]
    name=f"{device}_{topology}_{rows}x{cols}_s{seed}"
    d=BUILD/name; d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json"; cfg=d/"design.config"
    ys=(
        f"read_verilog -sv {src}; "
        f"chparam -set ROWS {rows} -set COLS {cols} {top}; "
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat"
    )
    started=time.time()
    y=run(["yosys","-p",ys])
    ytext=y.stdout+"\n"+y.stderr
    cc=cells(ytext)
    row={
        "device":device,"topology":topology,"rows":rows,"cols":cols,
        "pe_count":rows*cols,"seed":seed,"synth_dsp":cc.get("MULT18X18D",0),
        "route_ok":False,"fmax_mhz":"","period_ns":"",
        "elapsed_sec":"","error_stage":""
    }
    if y.returncode!=0 or not design.exists():
        row["elapsed_sec"]=time.time()-started; row["error_stage"]="yosys"; return row
    try:
        p=run([
            "nextpnr-ecp5",*DEVICE_ARGS[device],
            "--json",str(design),"--textcfg",str(cfg),
            "--freq","25","--seed",str(seed),"--timing-allow-fail"
        ])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"]=time.time()-started; row["error_stage"]="nextpnr_timeout"; return row
    text=p.stdout+"\n"+p.stderr
    f=[float(m.group(1)) for m in FMAX_RE.finditer(text)]
    row["elapsed_sec"]=time.time()-started
    if p.returncode==0 and cfg.exists() and f:
        fm=min(f)
        row["route_ok"]=True; row["fmax_mhz"]=fm; row["period_ns"]=1000.0/fm
    else:
        row["error_stage"]="nextpnr"
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--device",choices=DEVICE_ARGS,required=True)
    ap.add_argument("--topology",choices=TOPS,required=True)
    ap.add_argument("--seed",type=int,choices=(4,5,6),required=True)
    a=ap.parse_args()
    rows=[]
    for r,c in GEOMS[a.device]:
        print(f"[mech-confirm] {a.device} {a.topology} {r}x{c} seed={a.seed}",flush=True)
        q=route_one(a.device,a.topology,r,c,a.seed); rows.append(q)
        print(f"[mech-confirm] ok={q['route_ok']} fmax={q['fmax_mhz']} dsp={q['synth_dsp']}",flush=True)
    p=OUT/f"similarity_mechanism_confirm_{a.device}_{a.topology}_s{a.seed}.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
