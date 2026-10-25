#!/usr/bin/env python3
"""Reproduce the ShiftGuard Elec2 temporal experiment.

Protocol (fixed before inspecting future labels):
- first 60% of chronological rows: train a compact logistic scorer
- next 20%: historical non-key calibration distribution
- final 20%: untouched future stream
- positives from the first 80% form the stored key set
- future negatives are approximate-membership non-key queries
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from scipy.optimize import minimize

DATA_COMMIT = "4ee6b377a6710fa352e8fef1bbe3cbe29e7bcc57"
DATA_URL = f"https://raw.githubusercontent.com/vlosing/incrementalLearning/{DATA_COMMIT}/datasets/elec2/elec2_data.dat"
LABEL_URL = f"https://raw.githubusercontent.com/vlosing/incrementalLearning/{DATA_COMMIT}/datasets/elec2/elec2_label.dat"
SEED = 20261026
K = 8
TARGETS = (1e-2, 3e-3, 1e-3)
DELTA = 0.05
BF_C = 1.0 / math.log(2.0) ** 2

def fetch(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with urlopen(url) as r, path.open("wb") as f:
        f.write(r.read())

def load(root: Path):
    data, labels = root / "elec2_data.dat", root / "elec2_label.dat"
    fetch(DATA_URL, data); fetch(LABEL_URL, labels)
    X = np.loadtxt(data, delimiter=",", dtype=np.float64)
    y = np.loadtxt(labels, dtype=np.int8)
    if len(X) != len(y): raise RuntimeError("data/label length mismatch")
    return X, y

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -35.0, 35.0)))

def train_logistic(X, y, epochs=320):
    mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.zeros(Z.shape[1]); b = 0.0
    pos = int(y.sum()); neg = len(y) - pos
    wp, wn = len(y)/(2*max(1,pos)), len(y)/(2*max(1,neg))
    lr, l2 = 0.25, 0.002
    for epoch in range(epochs):
        p = sigmoid(Z @ w + b); cw = np.where(y == 1, wp, wn); err = (p-y)*cw
        w -= lr * (Z.T @ err / len(y) + l2*w); b -= lr * float(err.mean())
        if epoch in (120,220): lr *= 0.5
    return {"mean":mu,"std":sd,"w":w,"b":float(b)}

def predict(model, X):
    return sigmoid(((X-model["mean"])/model["std"]) @ model["w"] + model["b"])

def thresholds(cal_scores):
    q = np.quantile(cal_scores, np.arange(1,K)/K, method="higher")
    return np.r_[0.0,q,1.0]

def mass(scores, th):
    r = np.searchsorted(th, scores, side="left"); r[r == 0] = 1
    r = np.clip(r-1,0,len(th)-2)
    c = np.bincount(r,minlength=len(th)-1).astype(float)
    return c/c.sum()

def nominal(g,h,F):
    lo,hi=1e-12,1e12
    for _ in range(260):
        mu=math.sqrt(lo*hi); f=np.where(h>0,np.minimum(1,g/(mu*h)),1)
        if float(h@f)>F: lo=mu
        else: hi=mu
    return np.where(h>0,np.minimum(1,g/(hi*h)),1)

def worst_tv(h,f,rho):
    q=h.copy(); donors=list(np.argsort(f)); recv=list(np.argsort(-f)); di=ri=0; budget=float(rho)
    while budget>1e-14 and di<len(f) and ri<len(f):
        d,r=donors[di],recv[ri]
        if f[r] <= f[d] + 1e-15: break
        move=min(budget,q[d],1-q[r])
        if move>0: q[d]-=move; q[r]+=move; budget-=move
        if q[d] <= 1e-14: di+=1
        if 1-q[r] <= 1e-14: ri+=1
        if move <= 1e-16: break
    return float(q@f),q

def robust(g,h,F,rho):
    cuts=[h.copy()]; x0=np.full(len(g),-math.log(F))
    for _ in range(80):
        cons=[{"type":"ineq","fun":lambda x,q=q:F-float(q@np.exp(-x)),
               "jac":lambda x,q=q:q*np.exp(-x)} for q in cuts]
        res=minimize(lambda x:BF_C*float(g@x),x0,jac=lambda x:BF_C*g,method="SLSQP",
                     bounds=[(0,40)]*len(g),constraints=cons,
                     options={"maxiter":3000,"ftol":1e-13})
        if not res.success: raise RuntimeError(res.message)
        f=np.exp(-res.x); wc,qstar=worst_tv(h,f,rho)
        if wc <= F*(1+1e-8)+1e-12: return f,wc,len(cuts)
        cuts.append(qstar); x0=res.x
    raise RuntimeError("cutting planes did not converge")

def radius(n,delta=DELTA):
    return min(1.0, math.sqrt((2/n)*math.log((2**K-2)/delta))/2)

def model_bytes(model,th):
    p={"mean":model["mean"].tolist(),"std":model["std"].tolist(),"w":model["w"].tolist(),
       "b":model["b"],"thresholds":th.tolist()}
    return len(json.dumps(p,separators=(",",":")).encode())

def bits(g,f,nkeys,mbytes):
    return BF_C*nkeys*float(g@(-np.log(np.maximum(f,1e-15)))) + 8*mbytes

def run(root: Path):
    np.random.seed(SEED); X,y=load(root); n=len(y); tr=int(.6*n); ce=int(.8*n)
    model=train_logistic(X[:tr],y[:tr]); s=predict(model,X); idx=np.arange(n)
    key=(idx<ce)&(y==1); cal=(idx>=tr)&(idx<ce)&(y==0); fut=(idx>=ce)&(y==0)
    th=thresholds(s[cal]); g=mass(s[key],th); h0=mass(s[cal],th); hf=mass(s[fut],th)
    mb=model_bytes(model,th); nkeys=int(key.sum()); fut_rows=np.flatnonzero(fut)
    out={"dataset":{"rows":n,"features":X.shape[1],"source_commit":DATA_COMMIT},
         "counts":{"train":tr,"calibration":ce-tr,"future":n-ce,"stored_keys":nkeys,
                   "calibration_negatives":int(cal.sum()),"future_negatives":int(fut.sum())},
         "regions":{"k":K,"thresholds":th.tolist(),"g":g.tolist(),"historical_h":h0.tolist(),
                    "future_h":hf.tolist()},
         "adaptive":{}}
    for F in TARGETS:
        classic=BF_C*nkeys*(-math.log(F)); f0=nominal(g,h0,F); runs=[]
        for start in (0,1000):
            a=fut_rows[start:start+500]; hold=fut_rows[start+500:start+1000]
            ha,hh=mass(s[a],th),mass(s[hold],th); fr,wc,cuts=robust(g,ha,F,radius(500))
            runs.append({"audit_n":500,"holdout_n":500,"rho95":radius(500),
                         "static_holdout_ratio":float(hh@f0/F),
                         "certified_worst_fpr":wc,"holdout_ratio":float(hh@fr/F),
                         "saving_pct":100*(1-bits(g,fr,nkeys,mb)/classic),"cuts":cuts})
        out["adaptive"][str(F)]=runs
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",type=Path,default=Path(".shiftguard_elec2"))
    ap.add_argument("--out",type=Path,default=Path("elec2_temporal_results.json")); a=ap.parse_args()
    r=run(a.data_dir); a.out.write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))

if __name__=="__main__": main()
