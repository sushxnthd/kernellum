#!/usr/bin/env python3
from __future__ import annotations

import csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"results"/"similarity_routed_download";OUT=ROOT/"results"

def main():
    raw=[]
    for p in sorted(IN.glob("similarity_routed_*.csv")):
        with p.open() as f:raw.extend(csv.DictReader(f))
    if not raw:raise RuntimeError("no routed-law rows")
    rows=[]
    for r in raw:
        q=dict(r)
        for k in ("rows","cols","pe_count","seed"):q[k]=int(q[k])
        q["sqrt_pe"]=float(q["sqrt_pe"])
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        q["synth_dsp"]=int(q["synth_dsp"]) if q["synth_dsp"] else 0
        if q["route_ok"]:
            q["routed_fmax_mhz"]=float(q["routed_fmax_mhz"])
            q["routed_period_ns"]=float(q["routed_period_ns"])
        rows.append(q)
    ok=[r for r in rows if r["route_ok"]]
    groups=defaultdict(list)
    for r in ok:groups[(r["split"],r["device"],r["topology"],r["rows"],r["cols"])].append(r)
    pts=[]
    for (split,dev,top,rs,cs),gs in groups.items():
        vals=np.asarray([g["routed_period_ns"] for g in gs],float)
        pts.append({"split":split,"device":dev,"topology":top,"rows":rs,"cols":cs,
                    "pe_count":rs*cs,"sqrt_pe":float(np.sqrt(rs*cs)),
                    "median_period_ns":float(np.median(vals)),
                    "seed_cv_pct":float(np.std(vals,ddof=1)/np.mean(vals)*100.0) if len(vals)>1 else 0.0,
                    "seeds":len(gs)})
    disc=[p for p in pts if p["split"]=="discovery"]
    hold=[p for p in pts if p["split"]=="holdout"]
    X=[];y=[]
    for p in disc:
        X.append([
          1.0 if p["device"]=="25k" else 0.0,
          1.0 if p["device"]=="45k" else 0.0,
          1.0 if p["device"]=="85k" else 0.0,
          p["sqrt_pe"],
          1.0 if p["topology"]=="local" else 0.0,
          p["sqrt_pe"] if p["topology"]=="local" else 0.0,
        ])
        y.append(p["median_period_ns"])
    X=np.asarray(X,float);y=np.asarray(y,float)
    coef,*_=np.linalg.lstsq(X,y,rcond=None);pred=X@coef
    model={"alpha25":float(coef[0]),"alpha45":float(coef[1]),"alpha85":float(coef[2]),
           "broadcast_slope":float(coef[3]),"local_intercept_shift":float(coef[4]),
           "interaction_delta_slope":float(coef[5]),
           "local_slope":float(coef[3]+coef[5]),
           "discovery_rmse_ns":float(np.sqrt(np.mean((pred-y)**2)))}
    lookup={(p["split"],p["device"],p["topology"],p["rows"],p["cols"]):p for p in pts}
    hpairs=[]
    for dev,rs,cs in [("25k",3,7),("45k",3,7),("45k",5,9),("85k",3,7),("85k",5,9),("85k",7,11)]:
        b=lookup.get(("holdout",dev,"broadcast",rs,cs));l=lookup.get(("holdout",dev,"local",rs,cs))
        if not b or not l:continue
        obs=b["median_period_ns"]-l["median_period_ns"]
        x=float(np.sqrt(rs*cs))
        predtax=-model["local_intercept_shift"]-model["interaction_delta_slope"]*x
        hpairs.append({"device":dev,"rows":rs,"cols":cs,"sqrt_pe":x,
                       "broadcast_period_ns":b["median_period_ns"],"local_period_ns":l["median_period_ns"],
                       "observed_tax_ns":obs,"predicted_tax_ns":predtax,
                       "abs_error_ns":abs(obs-predtax),
                       "local_improvement_pct":obs/b["median_period_ns"]*100.0})
    obs=np.asarray([p["observed_tax_ns"] for p in hpairs],float)
    pr=np.asarray([p["predicted_tax_ns"] for p in hpairs],float)
    mae=float(np.mean(np.abs(obs-pr))) if len(hpairs) else float("inf")
    rmse=float(np.sqrt(np.mean((obs-pr)**2))) if len(hpairs) else float("inf")
    corr=float(np.corrcoef(obs,pr)[0,1]) if len(hpairs)>1 and np.std(obs)>0 and np.std(pr)>0 else 0.0
    cvsets={}
    for split in ("discovery","holdout"):
        for top in ("broadcast","local"):
            vals=[p["seed_cv_pct"] for p in pts if p["split"]==split and p["topology"]==top]
            cvsets[f"{split}_{top}"]=float(np.median(vals)) if vals else None
    d11=lookup.get(("discovery","85k","broadcast",11,11));l11=lookup.get(("discovery","85k","local",11,11))
    h711=next((p for p in hpairs if p["device"]=="85k" and p["rows"]==7 and p["cols"]==11),None)
    within=sum(p["abs_error_ns"]<=1.75 for p in hpairs)
    flags={
      "route_success":len(ok)>=92,
      "dsp_exact":all(r["synth_dsp"]==r["pe_count"] for r in ok),
      "seed_stability":all(v is not None and v<=6.0 for v in cvsets.values()),
      "broadcast_slope":model["broadcast_slope"]>=0.15,
      "local_slope_suppressed":model["local_slope"]<=0.60*model["broadcast_slope"],
      "negative_interaction":model["interaction_delta_slope"]<0.0,
      "discovery_85k_11_improvement":d11 is not None and l11 is not None and (d11["median_period_ns"]-l11["median_period_ns"])/d11["median_period_ns"]*100.0>=12.0,
      "heldout_positive_all":len(hpairs)==6 and all(p["observed_tax_ns"]>0 for p in hpairs),
      "heldout_mae":mae<=1.25,
      "heldout_rmse":rmse<=1.50,
      "heldout_correlation":corr>=0.70,
      "heldout_five_within":within>=5,
      "heldout_85k_7x11_improvement":h711 is not None and h711["local_improvement_pct"]>=15.0,
    }
    result={"attempted_routes":len(rows),"successful_routes":len(ok),"model":model,
            "median_seed_cv_pct":cvsets,"heldout_pairs":hpairs,
            "heldout_tax_mae_ns":mae,"heldout_tax_rmse_ns":rmse,
            "heldout_tax_correlation":corr,"heldout_within_1p75ns":within,
            "flags":flags,"corrected_routed_law_gate_pass":all(flags.values())}
    (OUT/"similarity_routed_law_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"similarity_routed_law_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(result,indent=2));return 0

if __name__=="__main__":
    raise SystemExit(main())
