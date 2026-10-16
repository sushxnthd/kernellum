#!/usr/bin/env python3
"""Opened-cohort kill screen for deterministic robust solver controls."""
from __future__ import annotations
import argparse, hashlib, json, math, platform, sys
from pathlib import Path
import numpy as np
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_sign_anchor_shifted as prior

METHODS=("single","globalized3","globalized9","ensemble9","stable9")
DOMAINS=prior.DOMAINS
FACTORS=(0.25,0.50,0.75,1.00,1.25,1.50,2.00,3.00,4.00)

def canonical(x):
 raw=json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
 return hashlib.sha256(raw).hexdigest()

def starts(x,target,family):
 base=prior.start_parameters(x,target,family)
 cut=1 if family=="exp_affine" else 1+x.shape[1]
 out=[]
 for factor in FACTORS:
  theta=base.copy(); theta[cut:]*=factor
  if not any(np.array_equal(theta,old[1]) for old in out):
   out.append((factor,theta))
 return out

def fit_bank(x,y,sign,family,counter):
 amp=max(float(np.max(np.abs(y))),1e-12); target=sign*y/amp
 records=[]; failures=[]
 for factor,initial in starts(x,target,family):
  counter["attempted"]+=1
  try:
   theta=prior.fit_exp(x,target,family,initial)
   pred=prior.value_jacobian(theta,x,family,700)[0]
   obj=float(np.sum((pred-target)**2))
   records.append({"factor":factor,"theta":theta,"objective":obj,"train_prediction":pred})
   counter["successful"]+=1
  except (FloatingPointError,ValueError,np.linalg.LinAlgError) as exc:
   failures.append({"factor":factor,"reason":str(exc)})
 if not records:
  raise FloatingPointError("all deterministic starts failed")
 return amp,target,records,failures

def choose(records,target,family,method):
 if method=="single":
  pool=[r for r in records if r["factor"]==1.0]
  return min(pool,key=lambda r:r["objective"])
 if method=="globalized3":
  factors=(0.5,1.0,1.5) if family=="exp_affine" else (0.5,1.0,2.0)
  return min([r for r in records if r["factor"] in factors],key=lambda r:r["objective"])
 if method=="globalized9":
  return min(records,key=lambda r:r["objective"])
 if method=="ensemble9":
  return {"ensemble":[r["theta"] for r in records]}
 if method=="stable9":
  matrix=np.stack([r["train_prediction"] for r in records])
  median=np.median(matrix,axis=0); scale=max(float(np.var(target)),1e-12)
  return min(records,key=lambda r:r["objective"]/len(target)+0.25*
             float(np.mean((r["train_prediction"]-median)**2))/scale)
 raise ValueError(method)

def predict_choice(choice,x,family):
 if "ensemble" in choice:
  return np.median(np.stack([prior.value_jacobian(t,x,family,700)[0]
                             for t in choice["ensemble"]]),axis=0)
 return prior.value_jacobian(choice["theta"],x,family,700)[0]

def fit_family(x,y,sign,family,counter):
 failures=[]
 try:
  amp,target,full,failed=fit_bank(x,y,sign,family,counter)
  failures.extend(failed); loo_banks=[]
  for i in range(len(x)):
   mask=np.arange(len(x))!=i
   fa,ft,bank,failed=fit_bank(x[mask],y[mask],sign,family,counter)
   failures.extend({"loo_index":i,**row} for row in failed)
   loo_banks.append((i,fa,ft,bank))
 except (FloatingPointError,ValueError,np.linalg.LinAlgError) as exc:
  failures.append({"method":"all","reason":"family unavailable: "+str(exc)})
  return {},failures
 scale=max(float(np.std(y)),1e-12); fitted={}
 for method in METHODS:
  try:
   choice=choose(full,target,family,method); loo=[]
   for i,fa,ft,bank in loo_banks:
    c=choose(bank,ft,family,method)
    value=float(predict_choice(c,x[i:i+1],family)[0])
    loo.append(sign*fa*value)
   fitted[method]={"sign":sign,"family":family,"amplitude":amp,"choice":choice,
                   "cv":float(np.mean(((y-np.asarray(loo))/scale)**2))}
  except (FloatingPointError,ValueError,np.linalg.LinAlgError) as exc:
   failures.append({"method":method,"reason":"method unavailable: "+str(exc)})
 return fitted,failures

def model_prediction(model,x):
 return model["sign"]*model["amplitude"]*predict_choice(
  model["choice"],x,model["family"])

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True)
 a=ap.parse_args(); rows=[]; counter={"attempted":0,"successful":0}
 for shape in prior.SHAPES:
  for d in prior.DIMS:
   for seed in prior.SEEDS:
    for noise in prior.NOISES:
     x,y,tests=prior.dataset(shape,d,seed,noise)
     candidates={m:[] for m in METHODS}; failures=[]
     for sign in (1,-1):
      for family in ("exp_affine","exp_concave"):
       fitted,failed=fit_family(x,y,sign,family,counter)
       failures.extend({"sign":sign,"family":family,**row} for row in failed)
       for method,model in fitted.items(): candidates[method].append(model)
     empty=[m for m in METHODS if not candidates[m]]
     if empty: raise RuntimeError(f"empty method banks for {shape} {d} {seed} {noise}: {empty}; {failures}")
     winners={m:min(candidates[m],key=lambda q:q["cv"]) for m in METHODS}
     scores={}
     for domain,(z,truth) in tests.items():
      scores[domain]={m:prior.log_nmse(model_prediction(winners[m],z),truth)
                      for m in METHODS}
     rows.append({"key":[shape,d,seed,noise],
                  "winner":{m:{"sign":winners[m]["sign"],
                               "family":winners[m]["family"],
                               "cv":winners[m]["cv"]} for m in METHODS},
                  "scores":scores,"failed_fits":failures})
     print(shape,d,seed,noise,{m:winners[m]["cv"] for m in METHODS},flush=True)
 metrics={}
 for domain in DOMAINS:
  metrics[domain]={
   "geometric_nmse":{m:prior.geomean_log([r["scores"][domain][m] for r in rows])
                     for m in METHODS},
   "catastrophic":{m:sum(r["scores"][domain][m]>5 for r in rows)
                   for m in METHODS}}
 single_total=sum(metrics[d]["catastrophic"]["single"] for d in DOMAINS)
 gates={}
 for method in METHODS[1:]:
  gates[method]={
   "complete":len(rows)==16,
   "no_excess_catastrophe":all(metrics[d]["catastrophic"][method]<=
                               metrics[d]["catastrophic"]["single"] for d in DOMAINS),
   "half_total_catastrophes":sum(metrics[d]["catastrophic"][method] for d in DOMAINS)
                              <=0.5*single_total,
   "inside_noninferior":metrics["inside"]["geometric_nmse"][method] <=
                         1.10*metrics["inside"]["geometric_nmse"]["single"],
   "near_noninferior":metrics["near_shell"]["geometric_nmse"][method] <=
       1.10*min(metrics["near_shell"]["geometric_nmse"]["single"],
                metrics["near_shell"]["geometric_nmse"]["globalized3"]),
   "far_noninferior":metrics["far_shell"]["geometric_nmse"][method] <=
       1.10*min(metrics["far_shell"]["geometric_nmse"]["single"],
                metrics["far_shell"]["geometric_nmse"]["globalized3"])}
 status={m:all(gates[m].values()) for m in METHODS[1:]}
 payload={"schema":"kernellum.robust-solver-control-development.v1",
  "classification":"OPENED_COHORT_DEVELOPMENT","protocol_commit":
  "0955587c1f717143af35443e026fa2ad3c73605f",
  "environment":{"python":platform.python_version(),"numpy":np.__version__,
                 "scipy":scipy.__version__},
  "paths":len(rows),"optimization_counts":counter,"metrics":metrics,
  "gates":gates,"survivors":[m for m in METHODS[1:] if status[m]],
  "status":"ADVANCE" if any(status.values()) else "KILL_SOLVER_BASIN_KERNEL",
  "rows":rows}
 payload["canonical_sha256"]=canonical(payload)
 a.output.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n")
 print(json.dumps({k:payload[k] for k in
  ("status","survivors","optimization_counts","metrics","gates",
   "canonical_sha256")},indent=2))
if __name__=="__main__": main()
