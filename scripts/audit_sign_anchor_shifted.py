#!/usr/bin/env python3
import argparse, hashlib, json, math
from pathlib import Path
DOMAINS=("inside","near_shell","far_shell")
def canonical(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--decisions",type=Path,required=True); p.add_argument("--result",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); d=json.loads(a.decisions.read_text()); r=json.loads(a.result.read_text()); checks=[]
 checks.append(r["decision_sha256"]==hashlib.sha256(a.decisions.read_bytes()).hexdigest()); checks.append(len(d["rows"])==r["paths"]==16)
 disagreements=sum(x["sign_disagreement"] for x in d["rows"]); checks.append(disagreements==r["sign_disagreements"])
 for x in d["rows"]: checks.append(x["anchor_kind"]==("candidate" if x["sign_disagreement"] else x["naive_kind"]))
 better=sum(x["sign_disagreement"] and x["scores"]["far_shell"]["anchor"]<x["scores"]["far_shell"]["naive"]-1e-12 for x in r["records"]); checks.append(better==r["conditional_anchor_wins"])
 for domain in DOMAINS:
  for m in ("candidate","independent","naive","anchor","globalized"):
   vals=[max(x["scores"][domain][m],math.log(1e-8)) for x in r["records"]]; gm=math.exp(sum(vals)/len(vals)); cat=sum(x["scores"][domain][m]>5 for x in r["records"]); checks.extend((abs(gm-r["metrics"][domain]["geometric_nmse"][m])<1e-15,cat==r["metrics"][domain]["catastrophic"][m]))
 ratios={"anchor_inside_over_candidate":r["metrics"]["inside"]["geometric_nmse"]["anchor"]/r["metrics"]["inside"]["geometric_nmse"]["candidate"],"anchor_far_over_naive":r["metrics"]["far_shell"]["geometric_nmse"]["anchor"]/r["metrics"]["far_shell"]["geometric_nmse"]["naive"],"anchor_far_over_globalized":r["metrics"]["far_shell"]["geometric_nmse"]["anchor"]/r["metrics"]["far_shell"]["geometric_nmse"]["globalized"]}; checks.extend(abs(ratios[k]-r["ratios"][k])<1e-15 for k in ratios)
 g={"complete":r["paths"]==16,"two_disagreements":disagreements>=2,"conditional_win_rate":disagreements>=2 and better/disagreements>=.75,"anchor_no_excess_catastrophe":all(r["metrics"][d]["catastrophic"]["anchor"]<=min(r["metrics"][d]["catastrophic"]["candidate"],r["metrics"][d]["catastrophic"]["naive"]) for d in DOMAINS),"inside_noninferior":ratios["anchor_inside_over_candidate"]<=1.05,"far_beats_naive":ratios["anchor_far_over_naive"]<=.90,"far_near_globalized":ratios["anchor_far_over_globalized"]<=1.10,"globalized_tail_control":all(r["metrics"][d]["catastrophic"]["globalized"]<=r["metrics"][d]["catastrophic"]["candidate"] for d in DOMAINS)}; checks.append(g==r["gates"]); base=dict(r); digest=base.pop("canonical_sha256"); checks.append(canonical(base)==digest)
 out={"schema":"kernellum.sign-anchor-shifted-audit.v1","status":"PASS" if all(checks) else "FAIL","checks":len(checks),"failures":sum(not x for x in checks),"source_canonical_sha256":digest}; out["canonical_sha256"]=canonical(out); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2)); raise SystemExit(0 if all(checks) else 1)
if __name__=="__main__": main()
