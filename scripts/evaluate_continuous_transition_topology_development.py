#!/usr/bin/env python3
"""Exact opened-cohort LOFO audit of transition topology versus a static matched ridge."""
from __future__ import annotations
import argparse, hashlib, json, math, platform
from pathlib import Path
import numpy as np

THRESHOLDS=(.10,.15,.20,.25,.30)
LAMBDA=10.0
FEATURES=("switch08","switch16","switch24","switch32","meanDist08","meanDist16","meanDist24","meanDist32","globalizedDistance","logResidualRatio")
TOPOLOGY=tuple(range(10))
STATIC=(8,9)

def canonical(obj):
    return json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_pairs(root):
    names=("basin_transition_continuation","basin_transition_confirmatory")
    pairs=[]
    for name in names:
        dp=root/"results"/f"{name}_decisions.json"
        rp=root/"results"/f"{name}_result.json"
        pairs.append((name,dp,rp,json.loads(dp.read_text()),json.loads(rp.read_text())))
    return pairs

def feature(row):
    alphas=(.08,.16,.24,.32)
    switch=[]; distances=[]
    for alpha in alphas:
        points=[next(p for p in trace if p["alpha"]==alpha) for trace in row["traces"]]
        switch.append(sum(bool(p["switched"]) for p in points)/len(points))
        distances.append(sum(float(p["distance"]) for p in points)/len(points))
    return switch+distances+[float(row["globalized_distance"]),math.log(max(float(row["residual_ratio"]),1e-12))]

def rows_from(pairs):
    rows=[]
    for archive,_,_,dec,res in pairs:
        records={tuple(r["key"]):r for r in res["records"]}
        for d in dec["rows"]:
            key=tuple(d["key"]); r=records[key]
            cand=float(r["scores"]["far_shell"]["candidate"])
            glob=float(r["scores"]["far_shell"]["globalized"])
            raw=cand-glob
            rows.append({"archive":archive,"key":list(key),"family":key[0],"x":feature(d),
                         "target":max(-2.0,min(2.0,raw)),"raw_gain":raw,
                         "candidate":cand,"globalized":glob})
    return rows

def fit(train,indices):
    x=np.asarray([[r["x"][j] for j in indices] for r in train],dtype=float)
    y=np.asarray([r["target"] for r in train],dtype=float)
    mean=x.mean(axis=0); sd=x.std(axis=0); sd=np.where(sd>0,sd,1.0)
    z=(x-mean)/sd; design=np.column_stack([np.ones(len(z)),z])
    penalty=np.eye(design.shape[1])*LAMBDA; penalty[0,0]=0.0
    beta=np.linalg.solve(design.T@design+penalty,design.T@y)
    return mean,sd,beta

def predict(model,row,indices):
    mean,sd,beta=model
    z=(np.asarray([row["x"][j] for j in indices])-mean)/sd
    return float(beta[0]+z@beta[1:])

def lofo(rows,indices):
    families=sorted({r["family"] for r in rows}); predictions=[]
    for held in families:
        train=[r for r in rows if r["family"]!=held]
        model=fit(train,indices)
        for r in rows:
            if r["family"]==held:
                predictions.append({**r,"score":predict(model,r,indices),"held_out_family":held})
    predictions.sort(key=lambda r:tuple(map(str,r["key"])))
    return predictions

def operating_points(predictions):
    baseline_cats=sum(math.exp(r["candidate"])>5 for r in predictions)
    baseline_geo=math.exp(sum(r["candidate"] for r in predictions)/len(predictions))
    out=[]
    for threshold in THRESHOLDS:
        routed=[r for r in predictions if r["score"]>threshold]
        wins=sum(r["raw_gain"]>0 for r in routed)
        selected=[r["globalized"] if r["score"]>threshold else r["candidate"] for r in predictions]
        cats=sum(math.exp(v)>5 for v in selected)
        geo=math.exp(sum(selected)/len(selected))
        out.append({"threshold":threshold,"routes":len(routed),"precision":wins/len(routed) if routed else None,
                    "far_geometric_ratio":geo/baseline_geo,"candidate_catastrophes":baseline_cats,
                    "selected_catastrophes":cats,"catastrophes_removed":baseline_cats-cats,
                    "family_routes":{f:sum(r["family"]==f for r in routed) for f in sorted({r["family"] for r in predictions})}})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    pairs=load_pairs(root); rows=rows_from(pairs)
    topo_pred=lofo(rows,TOPOLOGY); static_pred=lofo(rows,STATIC)
    topo=operating_points(topo_pred); static=operating_points(static_pred)
    for t in topo:
        nearby=[s for s in static if abs(s["routes"]-t["routes"])<=2]
        dominated=any(s["precision"] is not None and t["precision"] is not None and
                      s["precision"]>=t["precision"] and s["far_geometric_ratio"]<=t["far_geometric_ratio"]
                      for s in nearby)
        t["dominated_by_nearby_static"]=dominated
        t["gates"]={"eight_routes":t["routes"]>=8,"precision":t["precision"] is not None and t["precision"]>=.75,
                    "far_improves":t["far_geometric_ratio"]<=.90,
                    "no_excess_catastrophe":t["selected_catastrophes"]<=t["candidate_catastrophes"],
                    "removes_two_catastrophes":t["catastrophes_removed"]>=2,
                    "not_static_dominated":not dominated}
        t["passes"]=all(t["gates"].values())
    inputs={name:{"decisions_sha256":sha(dp),"result_sha256":sha(rp)} for name,dp,rp,_,_ in pairs}
    payload={"schema":"kernellum.continuous-transition-topology-development.v1",
             "classification":"OPENED_COHORT_LEAVE_ONE_FAMILY_OUT_DEVELOPMENT",
             "environment":{"python":platform.python_version(),"numpy":np.__version__},
             "inputs":inputs,"paths":len(rows),"families":sorted({r["family"] for r in rows}),
             "features":list(FEATURES),"ridge_lambda":LAMBDA,"target_clip":[-2.0,2.0],
             "thresholds":list(THRESHOLDS),"topology_operating_points":topo,
             "static_operating_points":static,
             "topology_predictions":[{"key":r["key"],"score":r["score"],"raw_gain":r["raw_gain"]} for r in topo_pred],
             "static_predictions":[{"key":r["key"],"score":r["score"],"raw_gain":r["raw_gain"]} for r in static_pred],
             "status":"PASS_FREEZE_PROSPECTIVE" if any(t["passes"] for t in topo) else "KILL_TOPOLOGY_NO_TRANSFER_GATE",
             "smallest_claim":"On the opened 40-path archive, no tested full transition-topology ridge operating point met the predeclared precision/tail/static-ablation gate under leave-one-family-out evaluation; no prospective claim is made."}
    without=canonical(payload).encode()
    payload["canonical_sha256"]=hashlib.sha256(without).hexdigest()
    args.output.write_text(canonical(payload))
    print(json.dumps({"status":payload["status"],"canonical_sha256":payload["canonical_sha256"],
                      "topology":topo,"static":static},indent=2,sort_keys=True))
    if payload["status"]!="KILL_TOPOLOGY_NO_TRANSFER_GATE":
        raise SystemExit(2)

if __name__=="__main__":
    main()
