#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"results"/"similarity_backend_invariance_download"
OUT=ROOT/"results"
INTERCEPT=-1.7762324290813414
SLOPE=0.8022441162585179

def main():
    raw=[]
    for p in sorted(IN.glob("similarity_backend_invariance_*.csv")):
        with p.open() as f:raw.extend(csv.DictReader(f))
    if not raw:raise RuntimeError("no backend invariance rows")
    rows=[]
    for r in raw:
        q=dict(r)
        for k in ("n","pe_count","seed","synth_dsp","synth_lut4","synth_ff"):q[k]=int(q[k])
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        if q["route_ok"]:
            q["period_ns"]=float(q["period_ns"]);q["fmax_mhz"]=float(q["fmax_mhz"])
        rows.append(q)
    ok=[r for r in rows if r["route_ok"]]
    groups=defaultdict(list)
    for r in ok:groups[(r["backend"],r["topology"],r["n"])].append(r)
    pts={}
    cvs=defaultdict(list)
    for k,rs in groups.items():
        vals=np.asarray([r["period_ns"] for r in rs],float)
        cv=float(np.std(vals,ddof=1)/np.mean(vals)*100.0) if len(vals)>1 else 0.0
        pts[k]=(float(np.median(vals)),cv)
        cvs[(k[0],k[1])].append(cv)
    pairs=[]
    for backend in ("dsp","lut"):
        for n in (3,5,7,9):
            bk=(backend,"broadcast",n);lk=(backend,"local",n)
            if bk not in pts or lk not in pts:continue
            b=pts[bk][0];l=pts[lk][0];pred=INTERCEPT+SLOPE*n;obs=b-l
            pairs.append({"backend":backend,"n":n,"pe_count":n*n,
                          "broadcast_period_ns":b,"local_period_ns":l,
                          "observed_tax_ns":obs,"predicted_tax_ns":pred,
                          "abs_error_ns":abs(obs-pred),
                          "local_improvement_pct":(b-l)/b*100.0})
    lut=[p for p in pairs if p["backend"]=="lut"]
    def metrics(ps):
        pred=np.asarray([p["predicted_tax_ns"] for p in ps],float)
        obs=np.asarray([p["observed_tax_ns"] for p in ps],float)
        return {
            "mae_ns":float(np.mean(np.abs(obs-pred))),
            "rmse_ns":float(np.sqrt(np.mean((obs-pred)**2))),
            "correlation":float(np.corrcoef(pred,obs)[0,1]) if len(ps)>1 and np.std(obs)>0 else 0.0
        }
    lutm=metrics(lut)
    exact_dsp=all(r["synth_dsp"]==r["pe_count"] for r in ok if r["backend"]=="dsp")
    zero_lut=all(r["synth_dsp"]==0 for r in ok if r["backend"]=="lut")
    medcv={f"{b}_{t}":float(np.median(v)) if v else None for (b,t),v in cvs.items()}
    p9=next((p for p in lut if p["n"]==9),None)
    within=sum(p["abs_error_ns"]<=2.25 for p in lut)
    flags={
        "route_success":len(ok)>=46,
        "dsp_mapping_exact":exact_dsp,
        "lut_mapping_zero_dsp":zero_lut,
        "seed_stability":all(v is not None and v<=7.0 for v in medcv.values()),
        "positive_tax_all_pairs":len(pairs)==8 and all(p["observed_tax_ns"]>0 for p in pairs),
        "lut_frozen_mae":lutm["mae_ns"]<=1.75,
        "lut_frozen_rmse":lutm["rmse_ns"]<=2.25,
        "lut_tax_correlation":lutm["correlation"]>=0.70,
        "lut_9x9_improvement":p9 is not None and p9["local_improvement_pct"]>=15.0,
        "lut_three_of_four_within_2p25ns":within>=3,
    }
    fits={}
    for backend in ("dsp","lut"):
        ps=[p for p in pairs if p["backend"]==backend]
        x=np.asarray([p["n"] for p in ps],float);y=np.asarray([p["observed_tax_ns"] for p in ps],float)
        X=np.column_stack([np.ones(len(x)),x]);coef,*_=np.linalg.lstsq(X,y,rcond=None)
        fits[backend]={"intercept_ns":float(coef[0]),"slope_ns_per_sqrt_pe":float(coef[1])}
    result={"attempted_routes":len(rows),"successful_routes":len(ok),
            "frozen_equation":{"intercept_ns":INTERCEPT,"slope_ns_per_sqrt_pe":SLOPE},
            "pairs":pairs,"median_seed_cv_pct":medcv,"lut_frozen_metrics":lutm,
            "lut_pairs_within_2p25ns":within,"descriptive_backend_fits":fits,
            "flags":flags,"backend_invariance_gate_pass":all(flags.values())}
    (OUT/"similarity_backend_invariance_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"similarity_backend_invariance_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
