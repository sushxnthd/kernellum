#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"results"/"similarity_path_diagnostic_download"
OUT=ROOT/"results"

def main()->int:
    rows=[]
    for p in sorted(IN.glob("similarity_path_diagnostic_*.csv")):
        with p.open() as f: rows.extend(csv.DictReader(f))
    if not rows: raise RuntimeError("no path diagnostic rows")

    clean=[]
    for r in rows:
        q=dict(r)
        q["n"]=int(q["n"]); q["seed"]=int(q["seed"]); q["pe_count"]=int(q["pe_count"])
        q["synth_dsp"]=int(q["synth_dsp"])
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        for k in ("fmax_mhz","period_ns","logic_ns","routing_ns","routing_fraction",
                  "max_manhattan_span","sum_manhattan_span","max_reported_net_delay_ns"):
            q[k]=float(q[k]) if q[k] not in ("",None) else float("nan")
        for k in ("has_operand","has_accumulator","has_counter"):
            q[k]=str(q[k]).lower()=="true"
        clean.append(q)

    ok=[r for r in clean if r["route_ok"]]
    by_n={}
    for n in sorted({r["n"] for r in ok}):
        rs=[r for r in ok if r["n"]==n]
        by_n[str(n)]={
            "routes":len(rs),
            "median_period_ns":float(np.median([r["period_ns"] for r in rs])),
            "median_logic_ns":float(np.median([r["logic_ns"] for r in rs])),
            "median_routing_ns":float(np.median([r["routing_ns"] for r in rs])),
            "median_routing_fraction":float(np.median([r["routing_fraction"] for r in rs])),
            "median_max_manhattan_span":float(np.median([r["max_manhattan_span"] for r in rs])),
            "median_max_reported_net_delay_ns":float(np.median([r["max_reported_net_delay_ns"] for r in rs])),
            "operand_path_fraction":float(np.mean([r["has_operand"] for r in rs])),
            "accumulator_path_fraction":float(np.mean([r["has_accumulator"] for r in rs])),
            "counter_path_fraction":float(np.mean([r["has_counter"] for r in rs])),
            "path_classes":dict(Counter(r["critical_path_class"] for r in rs)),
            "period_seed_cv_pct":float(np.std([r["period_ns"] for r in rs],ddof=1)/np.mean([r["period_ns"] for r in rs])*100.0) if len(rs)>1 else 0.0,
        }

    ns=np.asarray([r["n"] for r in ok],dtype=float)
    period=np.asarray([r["period_ns"] for r in ok],dtype=float)
    routing=np.asarray([r["routing_ns"] for r in ok],dtype=float)
    logic=np.asarray([r["logic_ns"] for r in ok],dtype=float)

    def corr(a,b):
        return float(np.corrcoef(a,b)[0,1]) if len(a)>1 and np.std(a)>0 and np.std(b)>0 else 0.0

    result={
        "attempted_routes":len(clean),
        "successful_routes":len(ok),
        "all_successful_dsp_exact":all(r["synth_dsp"]==r["pe_count"] for r in ok),
        "by_n":by_n,
        "correlation_n_period":corr(ns,period),
        "correlation_n_routing_delay":corr(ns,routing),
        "correlation_n_logic_delay":corr(ns,logic),
        "overall_operand_path_fraction":float(np.mean([r["has_operand"] for r in ok])) if ok else 0.0,
        "overall_accumulator_path_fraction":float(np.mean([r["has_accumulator"] for r in ok])) if ok else 0.0,
        "interpretation_boundary":"Diagnostic only. Use the observed path identity and delay decomposition to preregister the next causal experiment."
    }

    with (OUT/"similarity_path_diagnostic_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(clean[0])); w.writeheader(); w.writerows(clean)
    (OUT/"similarity_path_diagnostic_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
