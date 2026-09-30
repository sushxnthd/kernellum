#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results"
BUILD=ROOT/"build"/"similarity_span_pilot"
OUT.mkdir(exist_ok=True)
BUILD.mkdir(parents=True,exist_ok=True)

TOPS={
    "broadcast":("rtl/similarity_broadcast_fabric.sv","similarity_broadcast_fabric"),
    "local":("rtl/similarity_local_fabric.sv","similarity_local_fabric"),
}
FMAX_RE=re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz",re.I)
CELL_RE=re.compile(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$")
XY_RE=re.compile(r"X(\d+)[/ ]Y(\d+)",re.I)


def run(cmd,env=None,timeout=1800):
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env,timeout=timeout)


def parse_cells(text):
    out={}
    for line in text.splitlines():
        m=CELL_RE.match(line)
        if m: out[m.group(1)]=int(m.group(2))
    return out


def placed_dsp_coords(path:Path):
    data=json.loads(path.read_text())
    coords=[]
    def walk(x):
        if isinstance(x,dict):
            typ=x.get("type")
            attrs=x.get("attributes") or {}
            if typ=="MULT18X18D":
                bel=attrs.get("NEXTPNR_BEL") or attrs.get("BEL")
                if bel:
                    m=XY_RE.search(str(bel))
                    if m: coords.append((int(m.group(1)),int(m.group(2)),str(bel)))
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(data)
    return coords


def route(topology,mode):
    source,top=TOPS[topology]
    work=BUILD/f"{topology}_{mode}"
    work.mkdir(parents=True,exist_ok=True)
    design=work/"design.json"
    placed=work/"routed.json"
    cfg=work/"design.config"
    ys=(
        f"read_verilog -sv {source}; "
        f"chparam -set ROWS 7 -set COLS 7 {top}; "
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat"
    )
    y=run(["yosys","-p",ys])
    ytext=y.stdout+"\n"+y.stderr
    (work/"yosys.log").write_text(ytext)
    cells=parse_cells(ytext)
    row={
        "topology":topology,"mode":mode,"seed":1,"pe_count":49,
        "synth_dsp":cells.get("MULT18X18D",0),"route_ok":False,
        "fmax_mhz":"","period_ns":"","placed_dsp_count":0,
        "bbox_x_span":"","bbox_y_span":"","bbox_manhattan_span":"",
        "hook_summary":"","error_stage":""
    }
    if y.returncode!=0:
        row["error_stage"]="yosys"; return row
    env=os.environ.copy()
    env["KERNELLUM_SPAN_MODE"]=mode
    env["KERNELLUM_DSP_COUNT"]="49"
    p=run([
        "nextpnr-ecp5","--85k","--package","CABGA381","--speed","6",
        "--json",str(design),"--write",str(placed),"--textcfg",str(cfg),
        "--freq","25","--seed","1","--timing-allow-fail",
        "--pre-place","scripts/similarity_span_constraints.py"
    ],env=env)
    ptext=p.stdout+"\n"+p.stderr
    (work/"nextpnr.log").write_text(ptext)
    row["hook_summary"]=" | ".join(
        line.strip() for line in ptext.splitlines() if "[span-hook]" in line
    )
    fvals=[float(m.group(1)) for m in FMAX_RE.finditer(ptext)]
    if p.returncode==0 and fvals and placed.exists():
        coords=placed_dsp_coords(placed)
        row["placed_dsp_count"]=len(coords)
        if coords:
            xs=[x for x,_,_ in coords]; ys=[y for _,y,_ in coords]
            row["bbox_x_span"]=max(xs)-min(xs)
            row["bbox_y_span"]=max(ys)-min(ys)
            row["bbox_manhattan_span"]=row["bbox_x_span"]+row["bbox_y_span"]
        fmax=min(fvals)
        row["route_ok"]=True
        row["fmax_mhz"]=fmax
        row["period_ns"]=1000.0/fmax
    else:
        row["error_stage"]="nextpnr"
    print("[span-pilot]",json.dumps(row,sort_keys=True),flush=True)
    return row


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--topology",choices=TOPS,required=True)
    args=ap.parse_args()
    rows=[route(args.topology,m) for m in ("compact","elongated")]
    path=OUT/f"similarity_span_pilot_{args.topology}.csv"
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
