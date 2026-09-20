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
BUILD=ROOT/"build"/"similarity_relay"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True,exist_ok=True)

FANOUTS={6:(1,2,3,6),8:(1,2,4,8),10:(1,2,5,10)}
CELL_RE=re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE=re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz",re.I)

def run(cmd,timeout=2100):
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)

def parse_cells(text):
    out={}
    for line in text.splitlines():
        m=CELL_RE.match(line)
        if m:out[m.group(1)]=int(m.group(2))
    return out

def route(source,top,n,seed,fanout=None):
    tag=f"{top}_n{n}_s{seed}" + (f"_f{fanout}" if fanout is not None else "")
    d=BUILD/tag;d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json";cfg=d/"design.config"
    params=(f"chparam -set N {n} -set RELAY_FANOUT {fanout} {top}; "
            if fanout is not None else
            f"chparam -set ROWS {n} -set COLS {n} {top}; ")
    ys=(f"read_verilog -sv {source}; {params}"
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat")
    started=time.time()
    y=run(["yosys","-p",ys]);yt=y.stdout+"\n"+y.stderr;cc=parse_cells(yt)
    row={"topology":"relay" if fanout is not None else ("direct" if "broadcast" in top else "local"),
         "n":n,"pe_count":n*n,"relay_fanout":fanout if fanout is not None else "",
         "stage_max_fanout":max(fanout,n//fanout) if fanout is not None else "",
         "seed":seed,"synth_dsp":cc.get("MULT18X18D",0),"synth_ff":cc.get("TRELLIS_FF",0),
         "route_ok":False,"fmax_mhz":"","period_ns":"","elapsed_sec":"","error_stage":""}
    if y.returncode!=0 or not design.exists():
        row["elapsed_sec"]=time.time()-started;row["error_stage"]="yosys";return row
    try:
        p=run(["nextpnr-ecp5","--85k","--package","CABGA381","--speed","6",
               "--json",str(design),"--textcfg",str(cfg),"--freq","25",
               "--seed",str(seed),"--timing-allow-fail"])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"]=time.time()-started;row["error_stage"]="nextpnr_timeout";return row
    text=p.stdout+"\n"+p.stderr
    vals=[float(m.group(1)) for m in FMAX_RE.finditer(text)]
    row["elapsed_sec"]=time.time()-started
    if p.returncode==0 and cfg.exists() and vals:
        fm=min(vals);row["route_ok"]=True;row["fmax_mhz"]=fm;row["period_ns"]=1000.0/fm
    else:row["error_stage"]="nextpnr"
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,choices=FANOUTS,required=True)
    ap.add_argument("--seed",type=int,choices=(10,11,12),required=True)
    a=ap.parse_args();rows=[]
    for f in FANOUTS[a.n]:
        print(f"[relay] N={a.n} F={f} M={max(f,a.n//f)} seed={a.seed}",flush=True)
        q=route("rtl/similarity_relay_fabric.sv","similarity_relay_fabric",a.n,a.seed,f);rows.append(q)
        print(f"[relay] ok={q['route_ok']} fmax={q['fmax_mhz']} dsp={q['synth_dsp']}",flush=True)
    for source,top in [
        ("rtl/similarity_broadcast_fabric.sv","similarity_broadcast_fabric"),
        ("rtl/similarity_local_fabric.sv","similarity_local_fabric")
    ]:
        print(f"[relay] baseline {top} N={a.n} seed={a.seed}",flush=True)
        q=route(source,top,a.n,a.seed,None);rows.append(q)
        print(f"[relay] ok={q['route_ok']} fmax={q['fmax_mhz']} dsp={q['synth_dsp']}",flush=True)
    p=OUT/f"similarity_relay_n{a.n}_s{a.seed}.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
