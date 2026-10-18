#!/usr/bin/env python3
"""Prospective perturbation-basin stability experiment (frozen thresholds)."""
from __future__ import annotations

import argparse, hashlib, json, math, platform
from pathlib import Path

import numpy as np
import scipy

from evaluate_sign_anchor_shifted import (
    DOMAINS, canon, cfit, geomean_log, gfit, independent_fit,
    log_nmse, maximin, predict, shell,
)

FAMILIES=("rational_quadratic_ripple","anisotropic_laplace")
DIMS=(3,7)
SEEDS=(7301,7307)
NOISES=("symmetric_t","leverage_spikes")
PERTURBATIONS=12
GRAPH_RADIUS=0.35
RADII=(0.25,0.35,0.50)


def dataset(family, dimension, seed, noise):
    offset=seed+97*dimension+(0 if family==FAMILIES[0] else 19000)+(0 if noise==NOISES[0] else 31000)
    rng=np.random.default_rng(offset)
    center=rng.uniform(-.25,.25,dimension)
    q=np.linalg.qr(rng.normal(size=(dimension,dimension)))[0]
    curvature=(q*rng.uniform(.35,5.0,dimension))@q.T
    direction=rng.normal(size=dimension); direction/=max(float(np.linalg.norm(direction)),1e-12)
    sign=1.0 if seed==SEEDS[0] else -1.0
    def truth(z):
        u=z-center
        quad=np.einsum("ni,ij,nj->n",u,curvature,u)
        ridge=z@direction
        if family==FAMILIES[0]:
            base=(1.0+.72*quad)**-1.38*(1.0+.19*np.sin(3.1*ridge))
        else:
            radius=np.sqrt(np.maximum(quad,0.0)+1e-10)
            base=np.exp(-1.12*radius)*(1.0+.17*np.cos(2.4*ridge))
        return sign*base
    pool=rng.uniform(-1,1,(224,dimension))
    x=pool[maximin(pool,28)]
    clean=truth(x); scale=max(float(np.std(clean)),1e-12)
    if noise==NOISES[0]:
        y=clean+scale*.20*rng.standard_t(5,size=len(x))/math.sqrt(5/3)
    else:
        eps=.10*rng.normal(size=len(x))
        leverage=np.argsort(np.linalg.norm(x,axis=1))[-4:]
        eps[leverage]+=rng.normal(.35,.12,size=4)*np.sign(x[leverage,0]+.01)
        y=clean+scale*eps
    requests={
        "inside":rng.uniform(-1,1,(256,dimension)),
        "near_shell":shell(rng,256,dimension,1.0,1.6),
        "far_shell":shell(rng,256,dimension,1.6,3.2),
    }
    return x,y,requests,truth,offset


def best_fit(x,y,fitters):
    bank=[]; failures=[]
    for sign in (1,-1):
        for family in ("exp_affine","exp_concave"):
            for name,fn in fitters:
                try:
                    model=fn(x,y,sign,family); model["kind"]=name; bank.append(model)
                except (FloatingPointError,ValueError,np.linalg.LinAlgError) as exc:
                    failures.append({"kind":name,"sign":sign,"family":family,"reason":str(exc)})
    if not bank: raise RuntimeError(f"empty fit bank: {failures}")
    return min(bank,key=lambda m:(m["cv"],m["kind"],m["sign"],m["family"])),failures


def prediction(model,z,scale):
    return predict(model,z)/scale


def rms(a,b):
    d=a-b
    return float(np.sqrt(np.mean(d*d)))


def component_medoid(preds,radius):
    n=len(preds)
    adj=[[rms(preds[i],preds[j])<=radius for j in range(n)] for i in range(n)]
    seen=set(); components=[]
    for start in range(n):
        if start in seen: continue
        stack=[start]; seen.add(start); comp=[]
        while stack:
            i=stack.pop(); comp.append(i)
            for j in range(n):
                if adj[i][j] and j not in seen: seen.add(j); stack.append(j)
        components.append(sorted(comp))
    components.sort(key=lambda c:(-len(c),c))
    comp=components[0]
    medoid=min(comp,key=lambda i:(sum(rms(preds[i],preds[j]) for j in comp)/len(comp),i))
    dispersion=sum(rms(preds[medoid],preds[j]) for j in comp)/len(comp)
    return comp,medoid,dispersion,len(components)


def train_nmse(model,x,y):
    denom=max(float(np.mean((y-np.mean(y))**2)),1e-12)
    return float(np.mean((predict(model,x)-y)**2)/denom)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--decisions",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    fitted=[]
    zcache={}
    for family in FAMILIES:
      for dimension in DIMS:
       for seed in SEEDS:
        for noise in NOISES:
            x,y,requests,truth,offset=dataset(family,dimension,seed,noise)
            z=np.concatenate([requests[d] for d in DOMAINS]); scale=max(float(np.std(y)),1e-12)
            candidate,fail_c=best_fit(x,y,(("candidate",cfit),))
            independent,fail_i=best_fit(x,y,(("independent",independent_fit),))
            globalized,fail_g=best_fit(x,y,(("globalized",gfit),))
            naive=min((candidate,independent,globalized),key=lambda m:(m["cv"],m["kind"]))
            members=[]; failures=fail_c+fail_i+fail_g
            for p in range(PERTURBATIONS):
                prng=np.random.default_rng(offset+100003+7919*p)
                omit=np.sort(prng.choice(len(x),size=4,replace=False))
                keep=np.ones(len(x),dtype=bool); keep[omit]=False
                yp=y[keep].copy()
                if p>=6:
                    jitter=prng.normal(size=len(yp)); jitter-=np.mean(jitter)
                    yp=yp+.035*scale*jitter
                model,failed=best_fit(x[keep],yp,(("perturbed",cfit),))
                model["perturbation"]=p
                members.append(model); failures.extend(failed)
            preds=[prediction(m,z,scale) for m in members]
            components={}
            for radius in RADII:
                comp,medoid,dispersion,count=component_medoid(preds,radius)
                components[str(radius)]={"component":comp,"medoid":medoid,"dispersion":dispersion,"basins":count}
            primary=components[str(GRAPH_RADIUS)]
            medoid=members[primary["medoid"]]
            cand_pred=prediction(candidate,z,scale)
            distance=rms(cand_pred,preds[primary["medoid"]])
            ratio=train_nmse(medoid,x,y)/max(train_nmse(candidate,x,y),1e-12)
            occupancy=len(primary["component"])/PERTURBATIONS
            gate=(len(primary["component"])>=8 and primary["dispersion"]<=.20 and distance>.45 and ratio<=1.20)
            margin=min(occupancy-2/3,.20-primary["dispersion"],distance-.45,1.20-ratio)
            selected=medoid if gate else candidate
            fitted.append({"key":[family,dimension,seed,noise],"candidate":candidate,"independent":independent,
                "globalized":globalized,"naive":naive,"medoid":medoid,"selected":selected,"members":members,
                "requests":requests,"truth":truth,"gate":gate,"margin":margin,"occupancy":occupancy,
                "dispersion":primary["dispersion"],"distance":distance,"residual_ratio":ratio,
                "components":components,"failures":failures})
            print(family,dimension,seed,noise,"override",gate,"occupancy",occupancy,
                  "dispersion",primary["dispersion"],"distance",distance,"ratio",ratio,flush=True)

    decisions={"schema":"kernellum.perturbation-basin-decisions.v1","classification":"PROSPECTIVE_UNSEEN",
      "thresholds":{"members":12,"graph_radius":.35,"min_component":8,"max_dispersion":.20,
                    "min_candidate_separation":.45,"max_residual_ratio":1.20},
      "boundary_radii":list(RADII),"rows":[]}
    for row in fitted:
        decisions["rows"].append({"key":row["key"],"override":row["gate"],"stability_margin":row["margin"],
          "occupancy":row["occupancy"],"dispersion":row["dispersion"],
          "candidate_medoid_distance":row["distance"],"residual_ratio":row["residual_ratio"],
          "components":row["components"],"selected":row["selected"]["kind"],
          "member_models":[{"perturbation":m["perturbation"],"sign":m["sign"],"family":m["family"],"cv":m["cv"]} for m in row["members"]],
          "failed_attempts":row["failures"]})
    args.decisions.write_text(json.dumps(decisions,indent=2,sort_keys=True,allow_nan=False)+"\n")
    decision_sha=hashlib.sha256(args.decisions.read_bytes()).hexdigest()

    methods=("candidate","independent","globalized","naive","medoid","selected")
    records=[]
    for row in fitted:
        scores={}
        for domain,z in row["requests"].items():
            target=row["truth"](z)
            scores[domain]={m:log_nmse(predict(row[m],z),target) for m in methods}
        records.append({"key":row["key"],"override":row["gate"],"scores":scores})
    metrics={}
    for domain in DOMAINS:
        metrics[domain]={"geometric_nmse":{m:geomean_log([r["scores"][domain][m] for r in records]) for m in methods},
                         "catastrophic":{m:sum(r["scores"][domain][m]>5 for r in records) for m in methods}}
    overrides=[r for r in records if r["override"]]
    precision=(sum(r["scores"]["far_shell"]["selected"]<r["scores"]["far_shell"]["candidate"] for r in overrides)/len(overrides)) if overrides else 0.0
    ratios={"inside_over_candidate":metrics["inside"]["geometric_nmse"]["selected"]/metrics["inside"]["geometric_nmse"]["candidate"],
            "far_over_candidate":metrics["far_shell"]["geometric_nmse"]["selected"]/metrics["far_shell"]["geometric_nmse"]["candidate"]}
    cc={d:metrics[d]["catastrophic"]["candidate"] for d in DOMAINS}
    sc={d:metrics[d]["catastrophic"]["selected"] for d in DOMAINS}
    gates={"complete":len(records)==16,"two_overrides":len(overrides)>=2,
           "no_excess_catastrophe":all(sc[d]<=cc[d] for d in DOMAINS),
           "halves_one_domain_catastrophes":any(cc[d]>=2 and 2*sc[d]<=cc[d] for d in DOMAINS),
           "inside_noninferior":ratios["inside_over_candidate"]<=1.05,
           "far_improves":ratios["far_over_candidate"]<=.90,
           "override_precision":precision>=.75}
    payload={"schema":"kernellum.perturbation-basin-result.v1","classification":"PROSPECTIVE_UNSEEN",
      "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
      "decision_sha256":decision_sha,"paths":len(records),"overrides":len(overrides),
      "override_precision":precision,"metrics":metrics,"ratios":ratios,"gates":gates,"records":records,
      "status":"PASS" if all(gates.values()) else "FAIL"}
    payload["canonical_sha256"]=canon(payload)
    args.output.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({k:payload[k] for k in ("status","canonical_sha256","overrides","override_precision","ratios","gates")},indent=2))


if __name__=="__main__": main()
