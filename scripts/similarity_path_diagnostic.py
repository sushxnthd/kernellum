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
BUILD=ROOT/"build"/"similarity_path_diagnostic"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True,exist_ok=True)

SIZES=(3,5,7,9,11)
CELL_RE=re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
FMAX_RE=re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz",re.I)
SUMMARY_RE=re.compile(r"([-+0-9.]+)\s*ns logic,\s*([-+0-9.]+)\s*ns routing",re.I)
COORD_RE=re.compile(r"\((-?\d+),\s*(-?\d+)\)\s*->\s*\((-?\d+),\s*(-?\d+)\)")
OLD_NET_RE=re.compile(r"Info:\s+([-+0-9.]+)\s+[-+0-9.]+\s+Net\s+",re.I)
NEW_NET_RE=re.compile(r"Info:\s+routing\s+([-+0-9.]+)\s+[-+0-9.]+\s+Net\s+",re.I)

def run(cmd:list[str],timeout:int=1800)->subprocess.CompletedProcess[str]:
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)

def parse_cells(text:str)->dict[str,int]:
    out={}
    for line in text.splitlines():
        m=CELL_RE.match(line)
        if m:
            out[m.group(1)]=int(m.group(2))
    return out

def critical_block(text:str)->str:
    # Select an interior same-clock critical-path report, not the later
    # cross-domain/asynchronous digest report. The selected block must end
    # at its associated Max frequency line.
    starts=[m.start() for m in re.finditer(r"Critical path report for clock",text,re.I)]
    if not starts:
        starts=[m.start() for m in re.finditer(r"Critical path report",text,re.I)]
    candidates=[]
    for start in starts:
        end_m=re.search(r"Max frequency[^\n]*",text[start:],re.I)
        if end_m is None:
            continue
        end=start+end_m.end()
        block=text[start:end]
        summaries=list(SUMMARY_RE.finditer(block))
        fvals=[float(m.group(1)) for m in FMAX_RE.finditer(block)]
        if summaries and fvals:
            candidates.append((min(fvals),block))
    if not candidates:
        return ""
    # If multiple clocks ever appear, use the block with the lowest achieved
    # frequency, which is the global Fmax limiter.
    return min(candidates,key=lambda x:x[0])[1]

def classify(block:str)->str:
    low=block.lower()
    has_operand=("a_source" in low or "b_source" in low)
    has_acc=("accumulator" in low or "acc_flat" in low)
    has_counter=("counter" in low)
    labels=[]
    if has_operand: labels.append("operand")
    if has_acc: labels.append("accumulator")
    if has_counter: labels.append("counter")
    return "+".join(labels) if labels else "other"

def route_one(n:int,seed:int)->dict:
    name=f"n{n}_s{seed}"
    d=BUILD/name
    d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json"
    cfg=d/"design.config"

    ys=(
        "read_verilog -sv rtl/similarity_arithmetic_broadcast.sv; "
        f"chparam -set ROWS {n} -set COLS {n} similarity_arithmetic_broadcast; "
        "hierarchy -check -top similarity_arithmetic_broadcast; "
        f"synth_ecp5 -top similarity_arithmetic_broadcast -json {design}; stat"
    )
    started=time.time()
    y=run(["yosys","-p",ys])
    ytext=y.stdout+"\n"+y.stderr
    (d/"yosys.log").write_text(ytext)
    cells=parse_cells(ytext)

    base={
        "n":n,"seed":seed,"pe_count":n*n,"synth_dsp":cells.get("MULT18X18D",0),
        "synth_lut4":cells.get("LUT4",0),"synth_ff":cells.get("TRELLIS_FF",0),
        "route_ok":False,"fmax_mhz":"","period_ns":"","logic_ns":"","routing_ns":"",
        "routing_fraction":"","timing_sum_error_ns":"","critical_net_arcs":"","max_manhattan_span":"",
        "sum_manhattan_span":"","max_reported_net_delay_ns":"",
        "critical_path_class":"","has_operand":False,"has_accumulator":False,
        "has_counter":False,"elapsed_sec":"","error_stage":""
    }
    if y.returncode!=0 or not design.exists():
        base["elapsed_sec"]=time.time()-started; base["error_stage"]="yosys"; return base

    try:
        p=run([
            "nextpnr-ecp5","--85k","--package","CABGA381","--speed","6",
            "--json",str(design),"--textcfg",str(cfg),"--freq","25",
            "--seed",str(seed),"--timing-allow-fail"
        ])
    except subprocess.TimeoutExpired:
        base["elapsed_sec"]=time.time()-started; base["error_stage"]="nextpnr_timeout"; return base

    ptext=p.stdout+"\n"+p.stderr
    (d/"nextpnr.log").write_text(ptext)
    fvals=[float(m.group(1)) for m in FMAX_RE.finditer(ptext)]
    block=critical_block(ptext)
    summaries=list(SUMMARY_RE.finditer(block))
    coords=[tuple(map(int,m.groups())) for m in COORD_RE.finditer(block)]
    net_delays=[float(m.group(1)) for m in OLD_NET_RE.finditer(block)]
    net_delays += [float(m.group(1)) for m in NEW_NET_RE.finditer(block)]

    if p.returncode==0 and cfg.exists() and fvals and summaries:
        fmax=min(fvals)
        logic=float(summaries[-1].group(1))
        routing=float(summaries[-1].group(2))
        spans=[abs(x1-x0)+abs(y1-y0) for x0,y0,x1,y1 in coords]
        low=block.lower()
        base.update({
            "route_ok":True,"fmax_mhz":fmax,"period_ns":1000.0/fmax,
            "logic_ns":logic,"routing_ns":routing,
            "routing_fraction":routing/(logic+routing) if logic+routing else 0.0,
            "timing_sum_error_ns":abs((logic+routing)-(1000.0/fmax)),
            "critical_net_arcs":len(coords),
            "max_manhattan_span":max(spans) if spans else 0,
            "sum_manhattan_span":sum(spans),
            "max_reported_net_delay_ns":max(net_delays) if net_delays else 0.0,
            "critical_path_class":classify(block),
            "has_operand":("a_source" in low or "b_source" in low),
            "has_accumulator":("accumulator" in low or "acc_flat" in low),
            "has_counter":("counter" in low),
        })
    else:
        base["error_stage"]="nextpnr_or_parse"

    base["elapsed_sec"]=time.time()-started
    return base

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,choices=(1,2,3,4,5),required=True)
    args=ap.parse_args()
    rows=[]
    for n in SIZES:
        print(f"[pathdiag] N={n} seed={args.seed}",flush=True)
        r=route_one(n,args.seed)
        rows.append(r)
        print(
            f"[pathdiag] ok={r['route_ok']} fmax={r['fmax_mhz']} "
            f"logic={r['logic_ns']} routing={r['routing_ns']} "
            f"sumerr={r['timing_sum_error_ns']} class={r['critical_path_class']} "
            f"span={r['max_manhattan_span']}",
            flush=True,
        )
    path=OUT/f"similarity_path_diagnostic_s{args.seed}.csv"
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
