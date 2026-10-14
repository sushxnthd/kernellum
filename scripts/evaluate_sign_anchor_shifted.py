#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, platform, sys
from pathlib import Path
import numpy as np
import scipy

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from kernellum.discovery.additive_response import fit_exp, start_parameters, value_jacobian
from scripts.independent_additive_replication import fit_with_loo as independent_fit, mean as independent_mean

DOMAINS=("inside","near_shell","far_shell"); FLOOR=math.log(1e-8)
SHAPES=("skew_gaussian","student_peak"); DIMS=(3,5); SEEDS=(3101,3102); NOISES=("heteroscedastic_gaussian","student_t3")

def canon(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def log_nmse(p,y): return math.log(max(float(np.mean((p-y)**2)),1e-300))-math.log(max(float(np.var(y)),1e-30))
def geomean_log(xs): return math.exp(sum(max(x,FLOOR) for x in xs)/len(xs))

def shell(rng,n,d,lo,hi):
 out=[]
 while len(out)<n:
  z=rng.uniform(-hi,hi,(3*n,d)); z=z[(np.max(abs(z),axis=1)>lo)&(np.max(abs(z),axis=1)<=hi)]; out.extend(z.tolist())
 return np.asarray(out[:n])

def maximin(x,k):
 ids=[int(np.argmin(np.sum(x*x,axis=1)))]; best=np.sum((x-x[ids[0]])**2,axis=1)
 while len(ids)<k:
  best[ids]=-1; j=int(np.argmax(best)); ids.append(j); best=np.minimum(best,np.sum((x-x[j])**2,axis=1))
 return np.asarray(ids)

def dataset(shape,d,seed,noise):
 rng=np.random.default_rng(seed+100*d+(0 if shape==SHAPES[0] else 10000)+(0 if noise==NOISES[0] else 20000))
 center=rng.uniform(-.25,.25,d); q=np.linalg.qr(rng.normal(size=(d,d)))[0]; curv=(q*rng.uniform(.8,4,d))@q.T; slope=rng.normal(size=d); slope/=max(np.linalg.norm(slope),1e-12)
 sign=1 if seed==3101 else -1
 def truth(z):
  u=z-center; quad=np.einsum("ni,ij,nj->n",u,curv,u)
  if shape=="skew_gaussian": base=np.exp(-quad)*(1+.25*np.tanh(1.5*z@slope))
  else: base=(1+quad/3.)**-2
  return sign*base
 pool=rng.uniform(-1,1,(128,d)); ids=maximin(pool,20); clean=truth(pool[ids]); scale=.35*max(float(np.std(clean)),1e-12)
 if noise=="heteroscedastic_gaussian": eps=rng.normal(size=20)*(.5+abs(pool[ids,0]))
 else: eps=rng.standard_t(3,size=20)/math.sqrt(3)
 observed=clean+scale*eps
 tests={"inside":rng.uniform(-1,1,(256,d)),"near_shell":shell(rng,256,d,1,1.5),"far_shell":shell(rng,256,d,1.5,3)}
 return pool[ids],observed,{k:(z,truth(z)) for k,z in tests.items()}

def cfit(x,y,sign,family):
 amp=max(float(np.max(abs(y))),1e-12); target=sign*y/amp; theta=fit_exp(x,target,family); loo=[]
 for i in range(len(x)):
  mask=np.arange(len(x))!=i; fa=max(float(np.max(abs(y[mask]))),1e-12); ft=fit_exp(x[mask],sign*y[mask]/fa,family); loo.append(sign*fa*value_jacobian(ft,x[i:i+1],family,700)[0][0])
 cv=float(np.mean(((y-np.asarray(loo))/max(float(np.std(y)),1e-12))**2))
 return {"theta":theta,"amplitude":amp,"sign":sign,"family":family,"cv":cv,"kind":"candidate"}

def starts(x,target,family):
 base=start_parameters(x,target,family); out=[base]
 if family=="exp_affine":
  a=base.copy(); a[1:]*=.5; b=base.copy(); b[1:]*=1.5
 else:
  d=x.shape[1]; a=base.copy(); a[1+d:]*=.5; b=base.copy(); b[1+d:]*=2.
 out.extend((a,b)); return out

def gsingle(x,target,family):
 best=None
 for initial in starts(x,target,family):
  try:
   theta=fit_exp(x,target,family,initial); res=value_jacobian(theta,x,family)[0]-target; obj=float(res@res)
   if best is None or obj<best[0]: best=(obj,theta)
  except (FloatingPointError,ValueError,np.linalg.LinAlgError): pass
 if best is None: raise FloatingPointError("all globalized starts failed")
 return best[1]

def gfit(x,y,sign,family):
 amp=max(float(np.max(abs(y))),1e-12); theta=gsingle(x,sign*y/amp,family); loo=[]
 for i in range(len(x)):
  mask=np.arange(len(x))!=i; fa=max(float(np.max(abs(y[mask]))),1e-12); ft=gsingle(x[mask],sign*y[mask]/fa,family); loo.append(sign*fa*value_jacobian(ft,x[i:i+1],family,700)[0][0])
 cv=float(np.mean(((y-np.asarray(loo))/max(float(np.std(y)),1e-12))**2))
 return {"theta":theta,"amplitude":amp,"sign":sign,"family":family,"cv":cv,"kind":"globalized"}

def predict(m,x):
 if m["kind"]=="independent": return m["sign"]*m["amplitude"]*independent_mean(m["theta"],x,m["family"],700)
 return m["sign"]*m["amplitude"]*value_jacobian(m["theta"],x,m["family"],700)[0]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--decisions",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); fitted=[]
 for shape in SHAPES:
  for d in DIMS:
   for seed in SEEDS:
    for noise in NOISES:
     x,y,tests=dataset(shape,d,seed,noise); cm=[]; im=[]; gm=[]
     for sign in (1,-1):
      for family in ("exp_affine","exp_concave"):
       cm.append(cfit(x,y,sign,family)); q=independent_fit(x,y,sign,family); q["kind"]="independent"; im.append(q); gm.append(gfit(x,y,sign,family))
     c=min(cm,key=lambda z:z["cv"]); i=min(im,key=lambda z:z["cv"]); g=min(gm,key=lambda z:z["cv"])
     naive=i if i["cv"]<c["cv"] else c; anchor=c if c["sign"]!=i["sign"] else naive
     fitted.append({"key":[shape,d,seed,noise],"candidate":c,"independent":i,"globalized":g,"naive_kind":naive["kind"],"anchor_kind":anchor["kind"],"sign_disagreement":c["sign"]!=i["sign"],"tests":tests})
     print(shape,d,seed,noise,"signs",c["sign"],i["sign"],"cv",c["cv"],i["cv"],flush=True)
 decisions={"schema":"kernellum.sign-anchor-shifted-decisions.v1","rows":[{"key":r["key"],"candidate_sign":r["candidate"]["sign"],"candidate_family":r["candidate"]["family"],"candidate_cv":r["candidate"]["cv"],"independent_sign":r["independent"]["sign"],"independent_family":r["independent"]["family"],"independent_cv":r["independent"]["cv"],"globalized_sign":r["globalized"]["sign"],"globalized_family":r["globalized"]["family"],"globalized_cv":r["globalized"]["cv"],"naive_kind":r["naive_kind"],"anchor_kind":r["anchor_kind"],"sign_disagreement":r["sign_disagreement"]} for r in fitted]}
 a.decisions.write_text(json.dumps(decisions,indent=2,sort_keys=True)+"\n"); dsha=hashlib.sha256(a.decisions.read_bytes()).hexdigest()
 records=[]
 for r in fitted:
  models={k:r[k] for k in ("candidate","independent","globalized")}; models["naive"]=r[r["naive_kind"]]; models["anchor"]=r[r["anchor_kind"]]
  scores={}
  for domain,(z,truth) in r["tests"].items(): scores[domain]={k:log_nmse(predict(m,z),truth) for k,m in models.items()}
  records.append({"key":r["key"],"sign_disagreement":r["sign_disagreement"],"scores":scores})
 metrics={}; methods=("candidate","independent","naive","anchor","globalized")
 for domain in DOMAINS:
  metrics[domain]={"geometric_nmse":{m:geomean_log([r["scores"][domain][m] for r in records]) for m in methods},"catastrophic":{m:sum(r["scores"][domain][m]>5 for r in records) for m in methods}}
 disagreements=[r for r in records if r["sign_disagreement"]]; better=sum(r["scores"]["far_shell"]["anchor"]<r["scores"]["far_shell"]["naive"]-1e-12 for r in disagreements)
 ratios={"anchor_inside_over_candidate":metrics["inside"]["geometric_nmse"]["anchor"]/metrics["inside"]["geometric_nmse"]["candidate"],"anchor_far_over_naive":metrics["far_shell"]["geometric_nmse"]["anchor"]/metrics["far_shell"]["geometric_nmse"]["naive"],"anchor_far_over_globalized":metrics["far_shell"]["geometric_nmse"]["anchor"]/metrics["far_shell"]["geometric_nmse"]["globalized"]}
 gates={"complete":len(records)==16,"two_disagreements":len(disagreements)>=2,"conditional_win_rate":len(disagreements)>=2 and better/len(disagreements)>=.75,"anchor_no_excess_catastrophe":all(metrics[d]["catastrophic"]["anchor"]<=min(metrics[d]["catastrophic"]["candidate"],metrics[d]["catastrophic"]["naive"]) for d in DOMAINS),"inside_noninferior":ratios["anchor_inside_over_candidate"]<=1.05,"far_beats_naive":ratios["anchor_far_over_naive"]<=.90,"far_near_globalized":ratios["anchor_far_over_globalized"]<=1.10,"globalized_tail_control":all(metrics[d]["catastrophic"]["globalized"]<=metrics[d]["catastrophic"]["candidate"] for d in DOMAINS)}
 payload={"schema":"kernellum.sign-anchor-shifted.v1","classification":"PROSPECTIVE_SHIFTED","environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},"decision_sha256":dsha,"paths":len(records),"sign_disagreements":len(disagreements),"conditional_anchor_wins":better,"metrics":metrics,"ratios":ratios,"gates":gates,"records":records,"status":"PASS" if all(gates.values()) else "FAIL"}; payload["canonical_sha256"]=canon(payload); a.output.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({k:payload[k] for k in ("status","canonical_sha256","sign_disagreements","conditional_anchor_wins","ratios","gates")},indent=2))
if __name__=="__main__": main()
