#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"results"/"similarity_relay_download"
OUT=ROOT/"results"
OPT={6:{2,3},8:{2,4},10:{2,5}}

def main():
    raw=[]
    for p in sorted(IN.glob("similarity_relay_*.csv")):
        with p.open() as f:raw.extend(csv.DictReader(f))
    if not raw:raise RuntimeError("no relay rows")
    rows=[]
    for r in raw:
        q=dict(r)
        for k in ("n","pe_count","seed","synth_dsp","synth_ff"):q[k]=int(q[k])
        q["relay_fanout"]=int(q["relay_fanout"]) if q["relay_fanout"] else None
        q["stage_max_fanout"]=int(q["stage_max_fanout"]) if q["stage_max_fanout"] else None
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        if q["route_ok"]:q["period_ns"]=float(q["period_ns"]);q["fmax_mhz"]=float(q["fmax_mhz"])
        rows.append(q)
    ok=[r for r in rows if r["route_ok"]]
    groups=defaultdict(list)
    for r in ok:groups[(r["topology"],r["n"],r["relay_fanout"])].append(r)
    pts=[]
    for (top,n,f),rs in groups.items():
        vals=np.asarray([r["period_ns"] for r in rs],float)
        pts.append({"topology":top,"n":n,"relay_fanout":f,
                    "stage_max_fanout":max(f,n//f) if f is not None else None,
                    "median_period_ns":float(np.median(vals)),
                    "seed_cv_pct":float(np.std(vals,ddof=1)/np.mean(vals)*100.0) if len(vals)>1 else 0.0,
                    "seeds":len(rs)})
    relay=[p for p in pts if p["topology"]=="relay"]
    X=[];y=[]
    for p in relay:
        X.append([1.0 if p["n"]==6 else 0.0,1.0 if p["n"]==8 else 0.0,
                  1.0 if p["n"]==10 else 0.0,float(p["stage_max_fanout"])])
        y.append(p["median_period_ns"])
    X=np.asarray(X,float);y=np.asarray(y,float)
    coef,*_=np.linalg.lstsq(X,y,rcond=None);pred=X@coef
    rmse=float(np.sqrt(np.mean((pred-y)**2)))
    beta=float(coef[3])
    lookup={(p["topology"],p["n"],p["relay_fanout"]):p for p in pts}
    details={}
    opt_min_ok=[]
    extreme_slow=[]
    remove40=[]
    direct_positive=[]
    for n in (6,8,10):
        rp=[p for p in relay if p["n"]==n]
        best=min(p["median_period_ns"] for p in rp)
        near=[p for p in rp if p["median_period_ns"]<=best+0.25]
        opt_min_ok.append(any(p["relay_fanout"] in OPT[n] for p in near))
        bestopt=min(p["median_period_ns"] for p in rp if p["relay_fanout"] in OPT[n])
        f1=lookup[("relay",n,1)]["median_period_ns"]
        fn=lookup[("relay",n,n)]["median_period_ns"]
        extreme_slow.append((f1/bestopt-1.0)*100.0>=2.0 and (fn/bestopt-1.0)*100.0>=2.0)
        direct=lookup[("direct",n,None)]["median_period_ns"]
        local=lookup[("local",n,None)]["median_period_ns"]
        dt=direct-local
        bt=bestopt-local
        direct_positive.append(dt>0)
        frac=(dt-bt)/dt*100.0 if dt>0 else -999.0
        remove40.append(frac>=40.0)
        details[str(n)]={"direct_period_ns":direct,"local_period_ns":local,
                         "direct_tax_ns":dt,"best_optimal_relay_period_ns":bestopt,
                         "best_optimal_relay_tax_ns":bt,
                         "direct_tax_removed_pct":frac,
                         "f1_period_ns":f1,"fN_period_ns":fn,
                         "optimal_fanouts":sorted(OPT[n])}
    medcv=float(np.median([p["seed_cv_pct"] for p in pts]))
    d10=details["10"]
    flags={"route_success":len(ok)>=52,
           "dsp_exact":all(r["synth_dsp"]==r["pe_count"] for r in ok),
           "seed_stability":medcv<=6.0,
           "positive_minimax_coefficient":beta>0,
           "relay_model_rmse":rmse<=1.25,
           "minima_in_optimal_sets":all(opt_min_ok),
           "extremes_slower_two_of_three":sum(extreme_slow)>=2,
           "direct_tax_positive":all(direct_positive),
           "relay_removes_40pct_two_of_three":sum(remove40)>=2,
           "n10_best_relay_vs_direct":d10["best_optimal_relay_period_ns"]<=0.85*d10["direct_period_ns"]}
    result={"attempted_routes":len(rows),"successful_routes":len(ok),
            "relay_model":{"alpha6":float(coef[0]),"alpha8":float(coef[1]),
                           "alpha10":float(coef[2]),"beta_ns_per_stage_max_fanout":beta,
                           "rmse_ns":rmse},
            "median_seed_cv_pct":medcv,"by_size":details,
            "minima_in_optimal_sets":opt_min_ok,
            "extreme_slow_flags":extreme_slow,
            "tax_removal_40pct_flags":remove40,
            "flags":flags,"relay_hierarchy_gate_pass":all(flags.values())}
    (OUT/"similarity_relay_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"similarity_relay_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
