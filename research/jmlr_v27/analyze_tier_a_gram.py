#!/usr/bin/env python3
"""Offline Tier-A atomicity census from a saved semantic gradient Gram system.

A Gram factor is an isometric representation of the original task gradients.
Primary combiners depend on task-gradient inner products, so the resulting
coarse/exposed/canonicalized update geometry is preserved without storing the
full network gradient vectors.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(REPO))
from research.jmlr_v27.atomicity_intervention import transform_losses

METHODS={
    "ls": {},
    "mgda_released": {},
    "mgda_canonical": {},
    "cagrad": {"c":0.4,"max_norm":0.0},
    "nashmtl": {"optim_niter":20,"update_weights_every":1,"max_norm":0.0},
    "fairgrad_alpha2": {"alpha":2.0,"max_norm":0.0},
}

def factor_gram(H: torch.Tensor):
    H=(H.double()+H.double().T)/2
    vals,vecs=torch.linalg.eigh(H)
    scale=max(float(vals.abs().max()),1.0)
    if float(vals.min()) < -1e-8*scale:
        raise ValueError(f"Gram matrix not PSD within tolerance; min eigenvalue={float(vals.min())}")
    vals=vals.clamp_min(0)
    keep=vals>1e-12*scale
    if not bool(keep.any()):
        return torch.zeros((H.shape[0],1),dtype=torch.float32)
    G=vecs[:,keep] * vals[keep].sqrt().reshape(1,-1)
    return G.float()

def _as_list(x):
    if x is None: return None
    if isinstance(x,torch.Tensor): return [float(v) for v in x.detach().cpu().reshape(-1)]
    if isinstance(x,np.ndarray): return [float(v) for v in x.reshape(-1)]
    try: return [float(v) for v in x]
    except Exception: return None

def evaluate_one(base_losses,G,method_label,arm,parent,k,fairgrad_root):
    sys.path.insert(0,str(fairgrad_root))
    from methods.weight_methods import WeightMethods
    p=torch.zeros(G.shape[1],dtype=torch.float32,requires_grad=True)
    semantic=base_losses.float()+G@p
    represented,_=transform_losses(semantic,arm,parent_task=parent,clone_k=k)
    base_method="mgda" if method_label in ("mgda_released","mgda_canonical") else (
        "fairgrad" if method_label=="fairgrad_alpha2" else method_label
    )
    wm=WeightMethods(base_method,n_tasks=len(represented),device=torch.device("cpu"),**METHODS[method_label])
    kwargs=dict(
        losses=represented,
        shared_parameters=[p],
        task_specific_parameters=[p],
        last_shared_parameters=[p],
        representation=p.reshape(1,-1),
    )
    try:
        if method_label=="mgda_canonical":
            loss,extra=wm.get_weighted_loss(**kwargs)
            (loss/float(len(represented))).backward()
        else:
            _,extra=wm.backward(**kwargs)
        grad=p.grad.detach().double()
        weights=_as_list((extra or {}).get("weights"))
        status=getattr(getattr(wm,"method",None),"prob",None)
        status=getattr(status,"status",None)
        return {"ok":True,"grad":grad,"weights":weights,"solver_status":status}
    except Exception as e:
        status=getattr(getattr(wm,"method",None),"prob",None)
        status=getattr(status,"status",None)
        return {"ok":False,"error":repr(e),"solver_status":status}

def cosine(a,b):
    den=float(a.norm()*b.norm())
    return float(torch.dot(a,b)/den) if den>0 else None

def metrics(coarse,other,parent,k):
    if not coarse["ok"] or not other["ok"]:
        return {}
    a,b=coarse["grad"],other["grad"]
    an=float(a.norm()); bn=float(b.norm())
    out={
        "coarse_norm":an,
        "arm_norm":bn,
        "norm_ratio":bn/an if an else None,
        "cosine":cosine(a,b),
        "rel_l2":float((b-a).norm())/an if an else None,
    }
    w=other.get("weights")
    wc=coarse.get("weights")
    if w is not None and len(w)>=parent+k and other.get("arm")=="exposed":
        clone=w[parent:parent+k]
        untouched=w[:parent]+w[parent+k:]
        out.update({
            "clone_total_weight":float(sum(clone)),
            "clone_per_weight":float(sum(clone)/k),
            "untouched_weight_mean":float(sum(untouched)/len(untouched)) if untouched else None,
            "clone_per_to_untouched_mean":(
                float((sum(clone)/k)/(sum(untouched)/len(untouched)))
                if untouched and sum(untouched)!=0 else None
            ),
            "coarse_parent_weight":float(wc[parent]) if wc is not None and len(wc)>parent else None,
        })
    return out

def plan_for(audit):
    run_id=audit.get("run_id","")
    if run_id.startswith("nyu__"):
        return "nyuv2",[(p,k) for p in range(3) for k in (2,4,8)]
    if run_id.startswith("qm9__"):
        pairs=[(p,4) for p in range(11)]
        for p in (0,2,6): # released target IDs 0,2,12 are positions 0,2,6
            pairs.extend([(p,2),(p,8)])
        return "qm9",pairs
    raise ValueError(f"cannot infer benchmark from run_id={run_id!r}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--audit",type=Path,required=True)
    ap.add_argument("--fairgrad-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    audit=torch.load(args.audit,map_location="cpu",weights_only=True)
    H=audit["semantic_gram"].double()
    base_losses=audit["semantic_losses"].double()
    G=factor_gram(H)
    recon=(G.double()@G.double().T)
    gram_rel=float((recon-H).norm()/H.norm().clamp_min(1e-30))
    bench,pairs=plan_for(audit)
    rows=[]
    for method in METHODS:
        # Coarse is independent of parent/k; use a valid dummy k.
        coarse=evaluate_one(base_losses,G,method,"coarse",0,2,args.fairgrad_root)
        for parent,k in pairs:
            for arm in ("exposed","canonicalized"):
                result=evaluate_one(base_losses,G,method,arm,parent,k,args.fairgrad_root)
                result["arm"]=arm
                row={
                    "benchmark":bench,
                    "source_run_id":audit.get("run_id"),
                    "epoch":int(audit["epoch"]),
                    "method":method,
                    "parent":parent,
                    "k":k,
                    "arm":arm,
                    "gram_factor_relerr":gram_rel,
                    "coarse_ok":coarse["ok"],
                    "arm_ok":result["ok"],
                    "coarse_solver_status":coarse.get("solver_status"),
                    "arm_solver_status":result.get("solver_status"),
                    "coarse_weights":coarse.get("weights"),
                    "arm_weights":result.get("weights"),
                    "error":result.get("error"),
                }
                row.update(metrics(coarse,result,parent,k))
                rows.append(row)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("\n".join(json.dumps(r,sort_keys=True,allow_nan=False) for r in rows)+"\n")
    bad_canon=[r for r in rows if r["arm"]=="canonicalized" and r["arm_ok"] and r.get("rel_l2") is not None and r["rel_l2"]>2e-5]
    summary={
        "rows":len(rows),
        "benchmark":bench,
        "source_run_id":audit.get("run_id"),
        "epoch":int(audit["epoch"]),
        "gram_factor_relerr":gram_rel,
        "solver_failures":sum(not r["arm_ok"] for r in rows),
        "canonicalized_null_violations_gt_2e-5":len(bad_canon),
    }
    print(json.dumps(summary,indent=2,sort_keys=True))
    if gram_rel>2e-6:
        raise SystemExit("Gram factorization failed tolerance")
    if bad_canon:
        raise SystemExit(f"canonicalized null violations: {len(bad_canon)}")

if __name__=="__main__":
    main()
