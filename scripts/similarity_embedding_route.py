#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results";BUILD=ROOT/"build"/"similarity_embedding"
OUT.mkdir(exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
SIZES=(5,7,9,11)
TOPS={
    "local":("rtl/similarity_local_fabric.sv","similarity_local_fabric"),
    "shuffle":("rtl/similarity_shuffle_fabric.sv","similarity_shuffle_fabric"),
}
CELL_RE=re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE=re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz",re.I)

def run(cmd,timeout=2100):
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)

def cells(text):
    out={}
    for line in text.splitlines():
        m=CELL_RE.match(line)
        if m:out[m.group(1)]=int(m.group(2))
    return out

def route(topology,n,seed):
    src,top=TOPS[topology]
    d=BUILD/f"{topology}_n{n}_s{seed}";d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json";cfg=d/"design.config"
    param=(f"chparam -set N {n} {top}; " if topology=="shuffle"
           else f"chparam -set ROWS {n} -set COLS {n} {top}; ")
    ys=(f"read_verilog -sv {src}; {param}"
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat")
    started=time.time()
    y=run(["yosys","-p",ys]);yt=y.stdout+"\n"+y.stderr;cc=cells(yt)
    row={"topology":topology,"n":n,"pe_count":n*n,"seed":seed,
         "synth_dsp":cc.get("MULT18X18D",0),"synth_ff":cc.get("TRELLIS_FF",0),
         "synth_lut4":cc.get("LUT4",0),"route_ok":False,
         "fmax_mhz":"","period_ns":"","elapsed_sec":"","error_stage":""}
    if y.returncode!=0 or not design.exists():
        row["elapsed_sec"]=time.time()-started;row["error_stage"]="yosys";return row
    try:
        p=run(["nextpnr-ecp5","--85k","--package","CABGA381","--speed","6",
               "--json",str(design),"--textcfg",str(cfg),"--freq","25",
               "--seed",str(seed),"--timing-allow-fail"])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"]=time.time()-started;row["error_stage"]="nextpnr_timeout";return row
    text=p.stdout+"\n"+p.stderr;vals=[float(m.group(1)) for m in FMAX_RE.finditer(text)]
    row["elapsed_sec"]=time.time()-started
    if p.returncode==0 and cfg.exists() and vals:
        fm=min(vals);row["route_ok"]=True;row["fmax_mhz"]=fm;row["period_ns"]=1000.0/fm
    else:row["error_stage"]="nextpnr"
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--topology",choices=TOPS,required=True)
    ap.add_argument("--seed",type=int,choices=(13,14,15),required=True)
    a=ap.parse_args();rows=[]
    for n in SIZES:
        print(f"[embedding] {a.topology} N={n} seed={a.seed}",flush=True)
        q=route(a.topology,n,a.seed);rows.append(q)
        print(f"[embedding] ok={q['route_ok']} fmax={q['fmax_mhz']} dsp={q['synth_dsp']} ff={q['synth_ff']}",flush=True)
    p=OUT/f"similarity_embedding_{a.topology}_s{a.seed}.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
