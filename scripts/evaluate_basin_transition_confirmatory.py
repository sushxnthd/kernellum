#!/usr/bin/env python3
"""Frozen confirmatory basin-transition continuation experiment."""
from __future__ import annotations
import argparse, hashlib, json, math, platform
from pathlib import Path
import numpy as np
import scipy
from evaluate_sign_anchor_shifted import DOMAINS, canon, cfit, geomean_log, gfit, independent_fit, log_nmse, maximin, predict, shell

FAMILIES=("rational_mixture","anisotropic_bump","warped_cauchy")
DIMS=(5,9); SEEDS=(9103,9109); NOISES=("symmetric_t","leverage_spikes")
ALPHAS=(0.0,.08,.16,.24,.32); DIRECTIONS=8

def dataset(family,dimension,seed,noise):
    family_offset={"rational_mixture":0,"anisotropic_bump":23000,"warped_cauchy":46000}[family]\n    offset=seed+103*dimension+family_offset+(0 if noise==NOISES[0] else 53000)
    rng=np.random.default_rng(offset)
    center=rng.uniform(-.3,.3,dimension)
    q=np.linalg.qr(rng.normal(size=(dimension,dimension)))[0]
    curvature=(q*rng.uniform(.3,5.5,dimension))@q.T
    direction=rng.normal(size=dimension); direction/=max(float(np.linalg.norm(direction)),1e-12)
    sign=1.0 if seed==SEEDS[0] else -1.0
    def truth(z):
        u=z-center; quad=np.einsum("ni,ij,nj->n",u,curvature,u); ridge=z@direction
        if family=="rational_mixture":
            base=.62*(1+.48*quad)**-1.18+.38*(1+1.4*quad)**-2.1
            base*=1+.18*np.sin(3.3*ridge)
        elif family=="anisotropic_bump":
            radius=np.sqrt(np.maximum(quad,0)+1e-10)
            base=np.exp(-.92*radius)*(1+.20*np.exp(-((ridge-.35)/.28)**2)-.12*np.exp(-((ridge+.40)/.22)**2))
        else:
            warp=quad*(1+.10*np.sin(2.5*ridge))
            base=(1+.66*np.maximum(warp,0))**-1.31*(1+.16*np.cos(4.1*ridge))
        return sign*base
    pool=rng.uniform(-1,1,(260,dimension)); x=pool[maximin(pool,32)]
    clean=truth(x); scale=max(float(np.std(clean)),1e-12)
    if noise==NOISES[0]:
        y=clean+scale*.22*rng.standard_t(6,size=len(x))/math.sqrt(1.5)
    else:
        eps=.09*rng.normal(size=len(x)); idx=np.argsort(np.linalg.norm(x,axis=1))[-5:]
        eps[idx]+=rng.normal(.38,.10,size=5)*np.sign(x[idx,0]+.01); y=clean+scale*eps
    req={"inside":rng.uniform(-1,1,(256,dimension)),"near_shell":shell(rng,256,dimension,1,1.6),"far_shell":shell(rng,256,dimension,1.6,3.2)}
    return x,y,req,truth,offset

def best_fit(x,y,fitters):
    bank=[]; failures=[]
    for sign in (1,-1):
      for family in ("exp_affine","exp_concave"):
       for name,fn in fitters:
        try:
            m=fn(x,y,sign,family); m["kind"]=name; bank.append(m)
        except (FloatingPointError,ValueError,np.linalg.LinAlgError) as e:
            failures.append({"kind":name,"sign":sign,"family":family,"reason":str(e)})
    if not bank: raise RuntimeError("empty fit bank")
    return min(bank,key=lambda m:(m["cv"],m["kind"],m["sign"],m["family"])),failures

def rms(a,b):
    return float(np.sqrt(np.mean((a-b)**2)))

def train_nmse(model,x,y):
    den=max(float(np.mean((y-np.mean(y))**2)),1e-12)
    return float(np.mean((predict(model,x)-y)**2)/den)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--decisions",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    rows=[]
    for family in FAMILIES:
     for dim in DIMS:
      for seed in SEEDS:
       for noise in NOISES:
        x,y,requests,truth,offset=dataset(family,dim,seed,noise)
        z=np.concatenate([requests[d] for d in DOMAINS]); scale=max(float(np.std(y)),1e-12)
        cand,fc=best_fit(x,y,(("candidate",cfit),)); glob,fg=best_fit(x,y,(("globalized",gfit),)); ind,fi=best_fit(x,y,(("independent",independent_fit),))
        naive=min((cand,glob,ind),key=lambda m:(m["cv"],m["kind"]))
        cp=predict(cand,z)/scale; transitions=[]; endpoints=[]; traces=[]; failures=fc+fg+fi
        for j in range(DIRECTIONS):
            rng=np.random.default_rng(offset+500009+10007*j)
            v=rng.normal(size=len(y)); v-=np.mean(v); v/=max(float(np.sqrt(np.mean(v*v))),1e-12)
            first=.40; trace=[]
            for alpha in ALPHAS:
                m,ff=best_fit(x,y+alpha*scale*v,(("continuation",cfit),)); failures.extend(ff)
                dist=rms(cp,predict(m,z)/scale); changed=(m["sign"]!=cand["sign"] or m["family"]!=cand["family"])
                switched=changed or dist>.35
                if first==.40 and switched: first=alpha
                trace.append({"alpha":alpha,"distance":dist,"sign":m["sign"],"family":m["family"],"cv":m["cv"],"switched":switched})
                if alpha==ALPHAS[-1]: endpoints.append(m)
            transitions.append(first); traces.append(trace)
        early=sum(t<=.16 for t in transitions)/DIRECTIONS; median=float(np.median(transitions))
        gdist=rms(cp,predict(glob,z)/scale); ratio=train_nmse(glob,x,y)/max(train_nmse(cand,x,y),1e-12)
        route=(early>=.50 and median<=.16 and gdist>.25 and ratio<=1.15)
        margin=min(early-.50,.16-median,gdist-.25,1.15-ratio)
        selected=glob if route else cand
        rows.append({"key":[family,dim,seed,noise],"candidate":cand,"globalized":glob,"independent":ind,"naive":naive,"selected":selected,
          "requests":requests,"truth":truth,"route":route,"early":early,"median":median,"gdist":gdist,"ratio":ratio,
          "transitions":transitions,"traces":traces,"failures":failures})
        print(family,dim,seed,noise,"route",route,"early",early,"median",median,"gdist",gdist,"ratio",ratio,flush=True)
    decisions={"schema":"kernellum.basin-transition-confirmatory-decisions.v1","classification":"PROSPECTIVE_CONFIRMATORY",
      "cohort":{"families":list(FAMILIES),"dimensions":list(DIMS),"seeds":list(SEEDS),"noises":list(NOISES)},
      "thresholds":{"directions":8,"alphas":list(ALPHAS),"switch_distance":.35,"min_early_fraction":.50,"max_median_transition":.16,"min_globalized_distance":.25,"max_residual_ratio":1.15},"rows":[]}
    for r in rows:
        decisions["rows"].append({"key":r["key"],"route":r["route"],"margin":min(r["early"]-.50,.16-r["median"],r["gdist"]-.25,1.15-r["ratio"]),
          "early_switch_fraction":r["early"],"median_transition_amplitude":r["median"],"globalized_distance":r["gdist"],"residual_ratio":r["ratio"],
          "transition_amplitudes":r["transitions"],"traces":r["traces"],"selected":r["selected"]["kind"],"failed_attempts":r["failures"]})
    a.decisions.write_text(json.dumps(decisions,indent=2,sort_keys=True,allow_nan=False)+"\n")
    dsha=hashlib.sha256(a.decisions.read_bytes()).hexdigest()
    methods=("candidate","independent","globalized","naive","selected"); records=[]
    for r in rows:
        scores={}
        for domain,zv in r["requests"].items():
            target=r["truth"](zv); scores[domain]={m:log_nmse(predict(r[m],zv),target) for m in methods}
        records.append({"key":r["key"],"route":r["route"],"scores":scores})
    metrics={}
    for domain in DOMAINS:
        metrics[domain]={"geometric_nmse":{m:geomean_log([r["scores"][domain][m] for r in records]) for m in methods},
          "catastrophic":{m:sum(r["scores"][domain][m]>5 for r in records) for m in methods}}
    routed=[r for r in records if r["route"]]
    precision=sum(r["scores"]["far_shell"]["selected"]<r["scores"]["far_shell"]["candidate"] for r in routed)/len(routed) if routed else 0.0
    family_routes={f:sum(r["key"][0]==f for r in routed) for f in FAMILIES}
    family_precision={f:(sum(r["key"][0]==f and r["scores"]["far_shell"]["selected"]<r["scores"]["far_shell"]["candidate"] for r in routed)/family_routes[f] if family_routes[f] else None) for f in FAMILIES}
    routed_families=sum(n>0 for n in family_routes.values())
    ratios={"inside_over_candidate":metrics["inside"]["geometric_nmse"]["selected"]/metrics["inside"]["geometric_nmse"]["candidate"],
      "far_over_candidate":metrics["far_shell"]["geometric_nmse"]["selected"]/metrics["far_shell"]["geometric_nmse"]["candidate"]}
    cc={d:metrics[d]["catastrophic"]["candidate"] for d in DOMAINS}; sc={d:metrics[d]["catastrophic"]["selected"] for d in DOMAINS}
    gates={"complete":len(records)==24,"four_routes":len(routed)>=4,"two_routed_families":routed_families>=2,"no_excess_catastrophe":all(sc[d]<=cc[d] for d in DOMAINS),
      "halves_one_domain_catastrophes":any(cc[d]>=2 and 2*sc[d]<=cc[d] for d in DOMAINS),"inside_noninferior":ratios["inside_over_candidate"]<=1.05,
      "far_improves":ratios["far_over_candidate"]<=.90,"route_precision":precision>=.75,
      "family_precision":all(family_routes[f]<2 or family_precision[f]>=.50 for f in FAMILIES)}
    out={"schema":"kernellum.basin-transition-confirmatory-result.v1","classification":"PROSPECTIVE_CONFIRMATORY","environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
      "decision_sha256":dsha,"paths":len(records),"routes":len(routed),"routed_families":routed_families,"family_routes":family_routes,"family_route_precision":family_precision,"route_precision":precision,"metrics":metrics,"ratios":ratios,"gates":gates,"records":records,
      "status":"PASS" if all(gates.values()) else "FAIL"}; out["canonical_sha256"]=canon(out)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({k:out[k] for k in ("status","canonical_sha256","routes","route_precision","ratios","gates")},indent=2))

if __name__=="__main__": main()
