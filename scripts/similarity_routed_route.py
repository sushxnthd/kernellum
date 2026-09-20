#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,json,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results";BUILD=ROOT/"build"/"similarity_routed_law"
OUT.mkdir(exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)

DEVICE_ARGS={
 "25k":["--25k","--package","CABGA381","--speed","6"],
 "45k":["--45k","--package","CABGA381","--speed","6"],
 "85k":["--85k","--package","CABGA381","--speed","6"],
}
DISC={"25k":((3,3),(5,5)),"45k":((3,3),(5,5),(7,7)),"85k":((3,3),(5,5),(7,7),(9,9),(11,11))}
HOLD={"25k":((3,7),),"45k":((3,7),(5,9)),"85k":((3,7),(5,9),(7,11))}
TOPS={
 "broadcast":("rtl/similarity_broadcast_fabric.sv","similarity_broadcast_fabric"),
 "local":("rtl/similarity_local_fabric.sv","similarity_local_fabric"),
}

def run(cmd,timeout=2100):
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)

def routed_fmax(report:Path)->float:
    data=json.loads(report.read_text())
    vals=[float(v["achieved"]) for v in data.get("fmax",{}).values() if v.get("achieved") is not None]
    if not vals: raise RuntimeError("post-route report contains no fmax")
    return min(vals)

def dsp_count_from_report(report:Path)->int:
    data=json.loads(report.read_text())
    item=data.get("utilization",{}).get("MULT18X18D")
    return int(item["used"]) if item else 0

def route_one(device,topology,rows,cols,seed,split):
    src,top=TOPS[topology]
    d=BUILD/f"{split}_{device}_{topology}_{rows}x{cols}_s{seed}";d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json";cfg=d/"design.config";report=d/"report.json"
    ys=(f"read_verilog -sv {src}; "
        f"chparam -set ROWS {rows} -set COLS {cols} {top}; "
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat")
    started=time.time()
    y=run(["yosys","-p",ys])
    row={"split":split,"device":device,"topology":topology,"rows":rows,"cols":cols,
         "pe_count":rows*cols,"sqrt_pe":(rows*cols)**0.5,"seed":seed,
         "route_ok":False,"synth_dsp":"","routed_fmax_mhz":"","routed_period_ns":"",
         "elapsed_sec":"","error_stage":""}
    if y.returncode!=0 or not design.exists():
        row["elapsed_sec"]=time.time()-started;row["error_stage"]="yosys";return row
    try:
        p=run(["nextpnr-ecp5",*DEVICE_ARGS[device],
               "--json",str(design),"--textcfg",str(cfg),"--report",str(report),
               "--freq","25","--seed",str(seed),"--timing-allow-fail"])
    except subprocess.TimeoutExpired:
        row["elapsed_sec"]=time.time()-started;row["error_stage"]="nextpnr_timeout";return row
    row["elapsed_sec"]=time.time()-started
    if p.returncode==0 and cfg.exists() and report.exists():
        try:
            fm=routed_fmax(report);dsp=dsp_count_from_report(report)
            row["route_ok"]=True;row["synth_dsp"]=dsp
            row["routed_fmax_mhz"]=fm;row["routed_period_ns"]=1000.0/fm
        except Exception as e:
            row["error_stage"]="report_parse:"+str(e)
    else:row["error_stage"]="nextpnr"
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--device",choices=DEVICE_ARGS,required=True)
    ap.add_argument("--topology",choices=TOPS,required=True)
    ap.add_argument("--split",choices=("discovery","holdout"),required=True)
    ap.add_argument("--seed",type=int,required=True)
    a=ap.parse_args()
    allowed=(17,18,19) if a.split=="discovery" else (20,21,22)
    if a.seed not in allowed:raise SystemExit("seed not allowed for split")
    geoms=DISC[a.device] if a.split=="discovery" else HOLD[a.device]
    rows=[]
    for r,c in geoms:
        print(f"[routed-law] {a.split} {a.device} {a.topology} {r}x{c} seed={a.seed}",flush=True)
        q=route_one(a.device,a.topology,r,c,a.seed,a.split);rows.append(q)
        print(f"[routed-law] ok={q['route_ok']} fmax={q['routed_fmax_mhz']} dsp={q['synth_dsp']}",flush=True)
    p=OUT/f"similarity_routed_{a.split}_{a.device}_{a.topology}_s{a.seed}.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
