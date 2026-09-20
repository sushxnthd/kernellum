#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"results"/"similarity_mechanism_confirm_download"
OUT=ROOT/"results"

INTERCEPT=-1.7762324290813414
SLOPE=0.8022441162585179

def main():
    raw=[]
    for p in sorted(IN.glob("similarity_mechanism_confirm_*.csv")):
        with p.open() as f: raw.extend(csv.DictReader(f))
    if not raw: raise RuntimeError("no confirmation rows")

    rows=[]
    for r in raw:
        q=dict(r)
        for k in ("rows","cols","pe_count","seed","synth_dsp"): q[k]=int(q[k])
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        if q["route_ok"]:
            q["period_ns"]=float(q["period_ns"]); q["fmax_mhz"]=float(q["fmax_mhz"])
        rows.append(q)
    ok=[r for r in rows if r["route_ok"]]

    groups=defaultdict(list)
    for r in ok:
        groups[(r["device"],r["rows"],r["cols"],r["topology"])].append(r)

    points={}
    cvs={"broadcast":[],"local":[]}
    for key,rs in groups.items():
        vals=np.asarray([r["period_ns"] for r in rs],dtype=float)
        med=float(np.median(vals))
        cv=float(np.std(vals,ddof=1)/np.mean(vals)*100.0) if len(vals)>1 else 0.0
        points[key]=(med,cv,len(rs))
        cvs[key[3]].append(cv)

    pairs=[]
    for device,rs,cs in [
        ("25k",3,7),("45k",3,7),("45k",5,9),
        ("85k",3,7),("85k",5,9),("85k",7,11)
    ]:
        bk=(device,rs,cs,"broadcast"); lk=(device,rs,cs,"local")
        if bk not in points or lk not in points: continue
        b=points[bk][0]; l=points[lk][0]
        pred=INTERCEPT+SLOPE*math.sqrt(rs*cs)
        obs=b-l
        pairs.append({
            "device":device,"rows":rs,"cols":cs,"pe_count":rs*cs,
            "broadcast_period_ns":b,"local_period_ns":l,
            "observed_tax_ns":obs,"predicted_tax_ns":pred,
            "abs_error_ns":abs(obs-pred),
            "local_period_improvement_pct":(b-l)/b*100.0,
        })

    pred=np.asarray([p["predicted_tax_ns"] for p in pairs],dtype=float)
    obs=np.asarray([p["observed_tax_ns"] for p in pairs],dtype=float)
    mae=float(np.mean(np.abs(obs-pred))) if len(pairs) else float("inf")
    rmse=float(np.sqrt(np.mean((obs-pred)**2))) if len(pairs) else float("inf")
    corr=float(np.corrcoef(pred,obs)[0,1]) if len(pairs)>1 and np.std(obs)>0 else 0.0
    exact=all(r["synth_dsp"]==r["pe_count"] for r in ok)
    largest=next((p for p in pairs if p["device"]=="85k" and p["rows"]==7 and p["cols"]==11),None)
    within=sum(p["abs_error_ns"]<=1.75 for p in pairs)

    flags={
        "route_success":len(ok)>=34,
        "dsp_exact":exact,
        "seed_stability_broadcast":bool(cvs["broadcast"]) and float(np.median(cvs["broadcast"]))<=6.0,
        "seed_stability_local":bool(cvs["local"]) and float(np.median(cvs["local"]))<=6.0,
        "positive_tax_all_pairs":len(pairs)==6 and all(p["observed_tax_ns"]>0 for p in pairs),
        "frozen_tax_mae":mae<=1.25,
        "frozen_tax_rmse":rmse<=1.50,
        "tax_correlation":corr>=0.75,
        "largest_local_improvement":largest is not None and largest["local_period_improvement_pct"]>=20.0,
        "five_of_six_within_1p75ns":within>=5,
    }
    result={
        "attempted_routes":len(rows),"successful_routes":len(ok),
        "frozen_tax_intercept_ns":INTERCEPT,
        "frozen_tax_slope_ns_per_sqrt_pe":SLOPE,
        "pairs":pairs,
        "median_seed_cv_pct":{
            "broadcast":float(np.median(cvs["broadcast"])) if cvs["broadcast"] else None,
            "local":float(np.median(cvs["local"])) if cvs["local"] else None,
        },
        "tax_mae_ns":mae,"tax_rmse_ns":rmse,"tax_correlation":corr,
        "pairs_within_1p75ns":within,
        "flags":flags,
        "confirmation_gate_pass":all(flags.values()),
    }
    (OUT/"similarity_mechanism_confirmation_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"similarity_mechanism_confirmation_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
