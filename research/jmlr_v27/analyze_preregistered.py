#!/usr/bin/env python3
"""Locked analysis for JMLR Project Zero v27 standard-benchmark runs."""
from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np

METHOD_ORDER=["ls","mgda","cagrad","nashmtl","fairgrad"]
SEEDS=[0,1,2,3,4]
NY_K=[2,4,8]; NY_TASKS=[0,1,2]
QM9_MAIN_K=4; QM9_TARGETS=list(range(11))
QM9_DOSE_TARGETS=[0,2,6]
QM9_DOSE_K=[2,8]

def bootstrap_ci(x,stat=np.mean,draws=20000,seed=271828):
    x=np.asarray(x,float)
    if len(x)==0:return [math.nan,math.nan]
    rng=np.random.default_rng(seed)
    idx=rng.integers(0,len(x),size=(draws,len(x)))
    vals=np.apply_along_axis(stat,1,x[idx])
    return [float(np.quantile(vals,.025)),float(np.quantile(vals,.975))]

def effect_size_paired(d):
    d=np.asarray(d,float)
    if len(d)<2 or np.std(d,ddof=1)==0:return 0.0 if np.all(d==0) else None
    return float(np.mean(d)/np.std(d,ddof=1))

def load_records(paths):
    out=[]
    for p in paths:
        obj=json.loads(Path(p).read_text())
        out.extend(obj if isinstance(obj,list) else [obj])
    return out

def key(r):
    if "refine_task" not in r or "clone_k" not in r:
        raise ValueError("Explicit refine_task/clone_k mapping required; never infer from parent/k")
    return (r["benchmark"],r["method"],int(r["seed"]),r["arm"],int(r["refine_task"]),int(r["clone_k"]))

def summarize(records):
    by={}
    issues=[]
    for r in records:
        kr=key(r)
        if kr in by:
            issues.append({"kind":"duplicate_cell","key":list(kr)})
        else:
            by[kr]=r
        if r.get("status","ok")!="ok":
            issues.append({"kind":"failed_cell","key":list(kr),"status":r.get("status")})
    failures=[r for r in records if r.get("status","ok")!="ok"]
    rows=[]
    for r in records:
        if r.get("status","ok")!="ok" or r["arm"]=="coarse":continue
        ck=(r["benchmark"],r["method"],int(r["seed"]),"coarse",-1,1)
        c=by.get(ck)
        if c is None:
            issues.append({"kind":"unmatched_refined","key":list(key(r))})
            continue
        rr={k:r.get(k) for k in ["benchmark","method","seed","arm","refine_task","clone_k"]}
        if r["benchmark"]=="nyuv2":
            rr["delta_m_diff"]=float(r["metrics"]["delta_m"]-c["metrics"]["delta_m"])
            untouched=[i for i in range(3) if i!=int(r["refine_task"])]
            ud=[]
            for i in untouched:
                a=float(r["semantic_scores"][i]); b=float(c["semantic_scores"][i])
                direction=float(r["semantic_directions"][i])
                ud.append(-direction*(a-b))
            rr["untouched_degradation_mean"]=float(np.mean(ud))
        else:
            mae=np.asarray(r["metrics"]["task_mae"],float); cm=np.asarray(c["metrics"]["task_mae"],float)
            rr["delta_m_diff"]=float(r["metrics"]["delta_m"]-c["metrics"]["delta_m"])
            untouched=[i for i in range(11) if i!=int(r["refine_task"])]
            rr["untouched_mae_change_mean"]=float(np.mean(mae[untouched]-cm[untouched]))
            rr["mean_mae_change"]=float(np.mean(mae-cm))
        if "final_param_l2_to_coarse" in r:rr["final_param_l2_to_coarse"]=float(r["final_param_l2_to_coarse"])
        if "checkpoint_update_cosines_to_coarse" in r:rr["checkpoint_update_cosines_to_coarse"]=r["checkpoint_update_cosines_to_coarse"]
        rows.append(rr)
    groups=defaultdict(list)
    for rr in rows:
        g=(rr["benchmark"],rr["method"],rr["arm"],rr.get("refine_task"),rr.get("clone_k"))
        groups[g].append(rr)
    agg=[]
    for g,rs in sorted(groups.items(),key=lambda z:str(z[0])):
        out={"benchmark":g[0],"method":g[1],"arm":g[2],"refine_task":g[3],"clone_k":g[4],"n":len(rs)}
        for metric in ["delta_m_diff","untouched_degradation_mean","untouched_mae_change_mean","mean_mae_change","final_param_l2_to_coarse"]:
            vals=[x[metric] for x in rs if metric in x]
            if vals:
                out[metric]={"seed_values":vals,"mean":float(np.mean(vals)),"median":float(np.median(vals)),"ci95_mean":bootstrap_ci(vals,np.mean),"paired_effect_size":effect_size_paired(vals)}
        agg.append(out)
    # This preliminary gate is deliberately conservative. It is NOT a replacement
    # for checking the entire frozen manifest against all expected benchmark cells.
    if not rows:
        issues.append({"kind":"no_paired_observations"})
    for g,rs in groups.items():
        distinct={int(r["seed"]) for r in rs}
        if distinct!=set(SEEDS):
            issues.append({"kind":"incomplete_paired_seeds","group":list(g),"seeds":sorted(distinct)})
    can=[a for a in agg if a["arm"]=="canonicalized"]
    if not can:
        issues.append({"kind":"missing_canonicalized_observations"})
    can_fail=[]
    for a in can:
        required=("delta_m_diff","final_param_l2_to_coarse")
        missing=[metric for metric in required if metric not in a or "mean" not in a[metric]]
        if missing:
            issues.append({"kind":"missing_canonicalization_metrics","group":{k:a.get(k) for k in ("benchmark","method","arm","refine_task","clone_k")},"metrics":missing})
            can_fail.append(a)
            continue
        dm=a["delta_m_diff"]["mean"]
        pd=a["final_param_l2_to_coarse"]["mean"]
        if not (math.isfinite(dm) and math.isfinite(pd)):
            issues.append({"kind":"nonfinite_canonicalization_metrics","group":{k:a.get(k) for k in ("benchmark","method","arm","refine_task","clone_k")}})
            can_fail.append(a)
            continue
        if abs(dm)>1e-6 or pd>1e-5 or pd<0:can_fail.append(a)
    return {"n_records":len(records),"n_failures":len(failures),"failures":failures,"paired_cells":rows,"aggregate":agg,"analysis_blocked":bool(issues),"analysis_issues":issues,"canonicalized_gate_pass":bool(can) and len(can_fail)==0 and not issues,"canonicalized_gate_failures":can_fail}

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("inputs",nargs="+"); ap.add_argument("-o","--out",required=True)
    a=ap.parse_args(); out=summarize(load_records(a.inputs)); Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)); print(a.out)
