#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
IN_DIR=ROOT/"results"/"similarity_diameter_download"
OUT=ROOT/"results"


def load_rows() -> list[dict]:
    rows=[]
    for p in sorted(IN_DIR.glob("similarity_diameter_*.csv")):
        with p.open() as f:
            rows.extend(csv.DictReader(f))
    if not rows:
        raise RuntimeError("no diameter rows")
    return rows


def clean(rows: list[dict]) -> list[dict]:
    out=[]
    for r in rows:
        q=dict(r)
        for k in ("pe_group","seed","rows","cols","pe_count","diameter","synth_dsp"):
            q[k]=int(q[k])
        q["route_ok"]=str(q["route_ok"]).lower()=="true"
        if q["route_ok"]:
            q["fmax_mhz"]=float(q["fmax_mhz"])
            q["period_ns"]=float(q["period_ns"])
        out.append(q)
    return out


def median_points(success: list[dict]) -> list[dict]:
    groups=defaultdict(list)
    for r in success:
        groups[(r["pe_group"],r["topology"],r["rows"],r["cols"],r["diameter"])].append(r)
    points=[]
    for (p,top,r,c,d),rs in sorted(groups.items()):
        vals=np.asarray([x["period_ns"] for x in rs],dtype=float)
        points.append({
            "pe_group":p,"topology":top,"rows":r,"cols":c,"diameter":d,
            "seeds":len(rs),"median_period_ns":float(np.median(vals)),
            "mean_period_ns":float(np.mean(vals)),
            "seed_cv_pct":float(np.std(vals,ddof=1)/np.mean(vals)*100.0) if len(vals)>1 else 0.0
        })
    return points


def rank(v: list[float]) -> np.ndarray:
    order=np.argsort(v,kind="mergesort")
    ranks=np.empty(len(v),dtype=float)
    i=0
    while i<len(v):
        j=i+1
        while j<len(v) and v[order[j]]==v[order[i]]:
            j+=1
        avg=(i+j-1)/2+1
        ranks[order[i:j]]=avg
        i=j
    return ranks


def spearman(a:list[float],b:list[float]) -> float:
    ra,rb=rank(a),rank(b)
    return float(np.corrcoef(ra,rb)[0,1])


def fit(points:list[dict]) -> dict:
    y=np.asarray([p["median_period_ns"] for p in points],dtype=float)
    X=[]
    for p in points:
        local=1.0 if p["topology"]=="local" else 0.0
        X.append([
            1.0 if p["pe_group"]==64 else 0.0,
            1.0 if p["pe_group"]==96 else 0.0,
            float(p["diameter"]),
            local,
            local*float(p["diameter"])
        ])
    X=np.asarray(X,dtype=float)
    coef,*_=np.linalg.lstsq(X,y,rcond=None)
    pred=X@coef
    return {
        "alpha_64":float(coef[0]),"alpha_96":float(coef[1]),
        "broadcast_span_slope_ns_per_D":float(coef[2]),
        "local_intercept_shift_ns":float(coef[3]),
        "interaction_delta_slope_ns_per_D":float(coef[4]),
        "local_span_slope_ns_per_D":float(coef[2]+coef[4]),
        "rmse_ns":float(np.sqrt(np.mean((pred-y)**2)))
    }


def main() -> int:
    raw=clean(load_rows())
    success=[r for r in raw if r["route_ok"]]
    points=median_points(success)
    model=fit(points)

    dsp_exact=all(r["synth_dsp"]==r["pe_count"] for r in success)
    rho={}
    penalty={}
    for group in (64,96):
        rho[group]={}
        penalty[group]={}
        for top in ("broadcast","local"):
            ps=[p for p in points if p["pe_group"]==group and p["topology"]==top]
            rho[group][top]=spearman([p["diameter"] for p in ps],[p["median_period_ns"] for p in ps])
            compact=min(ps,key=lambda p:p["diameter"])
            elongated=max(ps,key=lambda p:p["diameter"])
            pct=(elongated["median_period_ns"]/compact["median_period_ns"]-1.0)*100.0
            penalty[group][top]={
                "compact_geometry":f"{compact['rows']}x{compact['cols']}",
                "elongated_geometry":f"{elongated['rows']}x{elongated['cols']}",
                "compact_period_ns":compact["median_period_ns"],
                "elongated_period_ns":elongated["median_period_ns"],
                "penalty_pct":pct
            }

    median_cv={
        top:float(np.median([p["seed_cv_pct"] for p in points if p["topology"]==top]))
        for top in ("broadcast","local")
    }
    bs=model["broadcast_span_slope_ns_per_D"]
    ls=model["local_span_slope_ns_per_D"]

    flags={
        "route_success":len(success)>=63,
        "dsp_exact":dsp_exact,
        "broadcast_span_slope":bs>=0.15,
        "local_slope_halved":ls<=0.50*bs,
        "negative_interaction":model["interaction_delta_slope_ns_per_D"]<0,
        "broadcast_rank":all(rho[g]["broadcast"]>=0.75 for g in (64,96)),
        "elongated_broadcast_penalty":all(penalty[g]["broadcast"]["penalty_pct"]>=15.0 for g in (64,96)),
        "local_penalty_suppressed":all(
            penalty[g]["local"]["penalty_pct"]<=0.50*penalty[g]["broadcast"]["penalty_pct"]
            for g in (64,96)
        ),
        "seed_stability":median_cv["broadcast"]<=5.0 and median_cv["local"]<=5.0,
    }
    result={
        "attempted_routes":len(raw),"successful_routes":len(success),
        "all_successful_dsp_exact":dsp_exact,
        "model":model,"spearman_period_vs_diameter":rho,
        "elongation_penalties":penalty,"median_seed_cv_pct":median_cv,
        "flags":flags,"diameter_gate_pass":all(flags.values()),
        "claim_boundary":(
            "A pass shows that at fixed PE count, critical-period variation tracks "
            "communication span and that registered local propagation suppresses this dependence "
            "in the tested ECP5 fabrics."
        )
    }
    with (OUT/"similarity_diameter_combined.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(raw[0]));w.writeheader();w.writerows(raw)
    with (OUT/"similarity_diameter_points.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(points[0]));w.writeheader();w.writerows(points)
    (OUT/"similarity_diameter_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
