#!/usr/bin/env python3
from __future__ import annotations

import csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"results"/"similarity_embedding_download";OUT=ROOT/"results"

def main():
    raw=[]
    for p in sorted(IN.glob("similarity_embedding_*.csv")):
        with p.open() as f:raw.extend(csv.DictReader(f))
    if not raw:raise RuntimeError("no embedding rows")
    rows=[]
    for r in raw:
        q=dict(r)
        for k in ("n","pe_count","seed","synth_dsp","synth_ff","synth_lut4"):q[k]=int(q[k])
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        if q["route_ok"]:q["period_ns"]=float(q["period_ns"]);q["fmax_mhz"]=float(q["fmax_mhz"])
        rows.append(q)
    ok=[r for r in rows if r["route_ok"]]
    groups=defaultdict(list)
    for r in ok:groups[(r["topology"],r["n"])].append(r)
    pts={}
    for k,rs in groups.items():
        vals=np.asarray([r["period_ns"] for r in rs],float)
        pts[k]={"median_period_ns":float(np.median(vals)),
                "seed_cv_pct":float(np.std(vals,ddof=1)/np.mean(vals)*100.0) if len(vals)>1 else 0.0,
                "dsp_counts":sorted(set(r["synth_dsp"] for r in rs)),
                "ff_counts":sorted(set(r["synth_ff"] for r in rs))}
    pairs=[]
    for n in (5,7,9,11):
        if ("local",n) not in pts or ("shuffle",n) not in pts:continue
        l=pts[("local",n)]["median_period_ns"];s=pts[("shuffle",n)]["median_period_ns"]
        pairs.append({"n":n,"local_period_ns":l,"shuffle_period_ns":s,
                      "embedding_tax_ns":s-l,"shuffle_penalty_pct":(s/l-1.0)*100.0})
    disc=[p for p in pairs if p["n"] in (5,7,9)]
    x=np.asarray([p["n"] for p in disc],float);y=np.asarray([p["embedding_tax_ns"] for p in disc],float)
    X=np.column_stack([np.ones(len(x)),x]);coef,*_=np.linalg.lstsq(X,y,rcond=None)
    held=next((p for p in pairs if p["n"]==11),None)
    pred11=float(coef[0]+coef[1]*11)
    err11=abs(pred11-held["embedding_tax_ns"]) if held else float("inf")
    counts_equal=True
    for n in (5,7,9,11):
        lr=[r for r in ok if r["topology"]=="local" and r["n"]==n]
        sr=[r for r in ok if r["topology"]=="shuffle" and r["n"]==n]
        if not lr or not sr:counts_equal=False;continue
        lcounts={(r["synth_dsp"],r["synth_ff"]) for r in lr}
        scounts={(r["synth_dsp"],r["synth_ff"]) for r in sr}
        if lcounts!=scounts:counts_equal=False
    cv_local=float(np.median([v["seed_cv_pct"] for (t,n),v in pts.items() if t=="local"])) if pts else 999
    cv_shuffle=float(np.median([v["seed_cv_pct"] for (t,n),v in pts.items() if t=="shuffle"])) if pts else 999
    p5=next((p for p in pairs if p["n"]==5),None)
    flags={"route_success":len(ok)>=23,
           "dsp_exact":all(r["synth_dsp"]==r["pe_count"] for r in ok),
           "matched_dsp_ff_counts":counts_equal,
           "seed_stability":cv_local<=6.0 and cv_shuffle<=6.0,
           "shuffle_slower_all_sizes":len(pairs)==4 and all(p["embedding_tax_ns"]>0 for p in pairs),
           "n11_penalty":held is not None and held["shuffle_penalty_pct"]>=12.0,
           "positive_tax_slope":float(coef[1])>0,
           "heldout_n11_error":err11<=1.50,
           "tax_growth_1p5x":held is not None and p5 is not None and held["embedding_tax_ns"]>=1.5*p5["embedding_tax_ns"],
           "local_n11_bounded":held is not None and held["local_period_ns"]<=13.0}
    result={"attempted_routes":len(rows),"successful_routes":len(ok),
            "pairs":pairs,"median_seed_cv_pct":{"local":cv_local,"shuffle":cv_shuffle},
            "discovery_tax_fit":{"intercept_ns":float(coef[0]),"slope_ns_per_N":float(coef[1])},
            "heldout_n11":{"predicted_tax_ns":pred11,"absolute_error_ns":err11},
            "flags":flags,"embedding_tax_gate_pass":all(flags.values())}
    (OUT/"similarity_embedding_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    with (OUT/"similarity_embedding_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(result,indent=2));return 0

if __name__=="__main__":
    raise SystemExit(main())
