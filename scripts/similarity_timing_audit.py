#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results"
BUILD=ROOT/"build"/"similarity_timing_audit"
OUT.mkdir(exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)

TOPS={
    "broadcast":("rtl/similarity_broadcast_fabric.sv","similarity_broadcast_fabric"),
    "local":("rtl/similarity_local_fabric.sv","similarity_local_fabric"),
}
CLOCK_RE=re.compile(r"Max frequency for clock\s+[^:]*:\s*([0-9.]+)\s*MHz",re.I)
XCLK_RE=re.compile(r"Max frequency for\s+(?!clock\b)[^:]*->[^:]*:\s*([0-9.]+)\s*MHz",re.I)
HIST_RE=re.compile(r"Max frequency[^:]*:\s*([0-9.]+)\s*MHz",re.I)

def run(cmd,timeout=1800):
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout)

def route(topology,n):
    src,top=TOPS[topology]
    d=BUILD/f"{topology}_{n}";d.mkdir(parents=True,exist_ok=True)
    design=d/"design.json";cfg=d/"design.config"
    ys=(f"read_verilog -sv {src}; "
        f"chparam -set ROWS {n} -set COLS {n} {top}; "
        f"hierarchy -check -top {top}; "
        f"synth_ecp5 -top {top} -json {design}; stat")
    y=run(["yosys","-p",ys])
    if y.returncode!=0: raise RuntimeError(f"yosys failed {topology} N={n}")
    p=run(["nextpnr-ecp5","--85k","--package","CABGA381","--speed","6",
           "--json",str(design),"--textcfg",str(cfg),"--freq","25",
           "--seed","16","--timing-allow-fail"])
    text=p.stdout+"\n"+p.stderr
    (d/"nextpnr.log").write_text(text)
    lines=[ln.strip() for ln in text.splitlines() if "Max frequency" in ln]
    clocks=[float(x) for x in CLOCK_RE.findall(text)]
    xclks=[float(x) for x in XCLK_RE.findall(text)]
    hist=[float(x) for x in HIST_RE.findall(text)]
    summaries=[ln.strip() for ln in text.splitlines() if re.search(r"ns logic,.*ns routing",ln)]
    row={
      "topology":topology,"n":n,"route_ok":p.returncode==0 and cfg.exists(),
      "clock_fmax_min_mhz":min(clocks) if clocks else "",
      "xclock_fmax_min_mhz":min(xclks) if xclks else "",
      "historical_fmax_min_mhz":min(hist) if hist else "",
      "historical_period_ns":1000.0/min(hist) if hist else "",
      "primary_clock_period_ns":1000.0/min(clocks) if clocks else "",
      "historical_limiter":(
         "primary_clock" if clocks and hist and abs(min(hist)-min(clocks))<1e-9
         else "cross_domain_or_other"
      ),
      "max_frequency_lines_json":json.dumps(lines),
      "critical_summaries_json":json.dumps(summaries),
    }
    print("[timing-audit] "+json.dumps(row,sort_keys=True),flush=True)
    return row

def main():
    rows=[route(t,n) for t in ("broadcast","local") for n in (5,9)]
    p=OUT/"similarity_timing_audit.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/"similarity_timing_audit.json").write_text(json.dumps(rows,indent=2)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
