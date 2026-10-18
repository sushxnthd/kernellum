#!/usr/bin/env python3
"""Independent standard-library audit for basin-transition experiment."""
import argparse, hashlib, json, math
from pathlib import Path
DOMAINS=("inside","near_shell","far_shell"); METHODS=("candidate","independent","globalized","naive","selected"); FLOOR=math.log(1e-8)
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def gm(rows,d,m): return math.exp(sum(max(x["scores"][d][m],FLOOR) for x in rows)/len(rows))
def main():
 p=argparse.ArgumentParser(); p.add_argument("--decisions",type=Path,required=True); p.add_argument("--result",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
 d=json.loads(a.decisions.read_text()); r=json.loads(a.result.read_text()); c=[]
 c += [hashlib.sha256(a.decisions.read_bytes()).hexdigest()==r["decision_sha256"],d["classification"]==r["classification"]=="PROSPECTIVE_UNSEEN",len(d["rows"])==len(r["records"])==16]
 dr={tuple(x["key"]):x for x in d["rows"]}; rr={tuple(x["key"]):x for x in r["records"]}; c.append(dr.keys()==rr.keys())
 for k,x in dr.items():
  route=x["early_switch_fraction"]>=.50 and x["median_transition_amplitude"]<=.16 and x["globalized_distance"]>.25 and x["residual_ratio"]<=1.15
  margin=min(x["early_switch_fraction"]-.50,.16-x["median_transition_amplitude"],x["globalized_distance"]-.25,1.15-x["residual_ratio"])
  c += [route==x["route"]==rr[k]["route"],abs(margin-x["margin"])<=1e-12,x["selected"]==("globalized" if route else "candidate"),len(x["transition_amplitudes"])==8,len(x["traces"])==8]
  for t,tr in zip(x["transition_amplitudes"],x["traces"]):
   c += [len(tr)==5,[z["alpha"] for z in tr]==[0,.08,.16,.24,.32],t in [0,.08,.16,.24,.32,.40]]
 m={}
 for dom in DOMAINS:
  m[dom]={"geometric_nmse":{x:gm(r["records"],dom,x) for x in METHODS},"catastrophic":{x:sum(z["scores"][dom][x]>5 for z in r["records"]) for x in METHODS}}
  for x in METHODS: c += [abs(m[dom]["geometric_nmse"][x]-r["metrics"][dom]["geometric_nmse"][x])<=1e-9*max(1,m[dom]["geometric_nmse"][x]),m[dom]["catastrophic"][x]==r["metrics"][dom]["catastrophic"][x]]
 routed=[x for x in r["records"] if x["route"]]; precision=sum(x["scores"]["far_shell"]["selected"]<x["scores"]["far_shell"]["candidate"] for x in routed)/len(routed) if routed else 0
 ratios={"inside_over_candidate":m["inside"]["geometric_nmse"]["selected"]/m["inside"]["geometric_nmse"]["candidate"],"far_over_candidate":m["far_shell"]["geometric_nmse"]["selected"]/m["far_shell"]["geometric_nmse"]["candidate"]}
 cc={x:m[x]["catastrophic"]["candidate"] for x in DOMAINS}; sc={x:m[x]["catastrophic"]["selected"] for x in DOMAINS}
 gates={"complete":len(r["records"])==16,"two_routes":len(routed)>=2,"no_excess_catastrophe":all(sc[x]<=cc[x] for x in DOMAINS),"halves_one_domain_catastrophes":any(cc[x]>=2 and 2*sc[x]<=cc[x] for x in DOMAINS),"inside_noninferior":ratios["inside_over_candidate"]<=1.05,"far_improves":ratios["far_over_candidate"]<=.90,"route_precision":precision>=.75}
 c += [len(routed)==r["routes"],abs(precision-r["route_precision"])<=1e-12,gates==r["gates"],("PASS" if all(gates.values()) else "FAIL")==r["status"]]
 raw=dict(r); claimed=raw.pop("canonical_sha256"); c.append(digest(raw)==claimed)
 fail=sum(not x for x in c); out={"schema":"kernellum.basin-transition-audit.v1","status":"PASS" if fail==0 else "FAIL","checks":len(c),"failures":fail,"source_canonical_sha256":claimed}; out["canonical_sha256"]=digest(out)
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2)); raise SystemExit(0 if fail==0 else 1)
if __name__=="__main__": main()
