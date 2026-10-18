#!/usr/bin/env python3
"""Independent standard-library audit of frozen perturbation-basin gates."""
import argparse, hashlib, json, math
from pathlib import Path

DOMAINS=("inside","near_shell","far_shell")
METHODS=("candidate","independent","globalized","naive","medoid","selected")
FLOOR=math.log(1e-8)


def digest(value):
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def geomean(rows,domain,method):
    return math.exp(sum(max(r["scores"][domain][method],FLOOR) for r in rows)/len(rows))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--decisions",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    d=json.loads(a.decisions.read_text()); r=json.loads(a.result.read_text()); checks=[]
    checks += [hashlib.sha256(a.decisions.read_bytes()).hexdigest()==r["decision_sha256"],
               d["classification"]==r["classification"]=="PROSPECTIVE_UNSEEN",
               len(d["rows"])==len(r["records"])==r["paths"]==16,
               d["boundary_radii"]==[.25,.35,.5]]
    dr={tuple(x["key"]):x for x in d["rows"]}; rr={tuple(x["key"]):x for x in r["records"]}
    checks.append(dr.keys()==rr.keys())
    for key,row in dr.items():
        gate=(len(row["components"]["0.35"]["component"])>=8 and row["dispersion"]<=.20
              and row["candidate_medoid_distance"]>.45 and row["residual_ratio"]<=1.20)
        margin=min(row["occupancy"]-2/3,.20-row["dispersion"],
                   row["candidate_medoid_distance"]-.45,1.20-row["residual_ratio"])
        checks += [gate==row["override"]==rr[key]["override"],
                   abs(margin-row["stability_margin"])<=1e-12,
                   row["selected"]==("perturbed" if gate else "candidate"),
                   len(row["member_models"])==12]
        for radius in ("0.25","0.35","0.5"):
            c=row["components"][radius]
            checks += [c["medoid"] in c["component"],1<=c["basins"]<=12]
    metrics={}
    for domain in DOMAINS:
        metrics[domain]={"geometric_nmse":{m:geomean(r["records"],domain,m) for m in METHODS},
                         "catastrophic":{m:sum(x["scores"][domain][m]>5 for x in r["records"]) for m in METHODS}}
        for m in METHODS:
            checks.append(abs(metrics[domain]["geometric_nmse"][m]-r["metrics"][domain]["geometric_nmse"][m])
                          <=1e-9*max(1.0,metrics[domain]["geometric_nmse"][m]))
            checks.append(metrics[domain]["catastrophic"][m]==r["metrics"][domain]["catastrophic"][m])
    overrides=[x for x in r["records"] if x["override"]]
    precision=(sum(x["scores"]["far_shell"]["selected"]<x["scores"]["far_shell"]["candidate"] for x in overrides)/len(overrides)) if overrides else 0.0
    ratios={"inside_over_candidate":metrics["inside"]["geometric_nmse"]["selected"]/metrics["inside"]["geometric_nmse"]["candidate"],
            "far_over_candidate":metrics["far_shell"]["geometric_nmse"]["selected"]/metrics["far_shell"]["geometric_nmse"]["candidate"]}
    cc={x:metrics[x]["catastrophic"]["candidate"] for x in DOMAINS}
    sc={x:metrics[x]["catastrophic"]["selected"] for x in DOMAINS}
    gates={"complete":len(r["records"])==16,"two_overrides":len(overrides)>=2,
           "no_excess_catastrophe":all(sc[x]<=cc[x] for x in DOMAINS),
           "halves_one_domain_catastrophes":any(cc[x]>=2 and 2*sc[x]<=cc[x] for x in DOMAINS),
           "inside_noninferior":ratios["inside_over_candidate"]<=1.05,
           "far_improves":ratios["far_over_candidate"]<=.90,
           "override_precision":precision>=.75}
    checks += [len(overrides)==r["overrides"],abs(precision-r["override_precision"])<=1e-12,
               all(abs(ratios[k]-r["ratios"][k])<=1e-12*max(1.0,ratios[k]) for k in ratios),
               gates==r["gates"],("PASS" if all(gates.values()) else "FAIL")==r["status"]]
    raw=dict(r); claimed=raw.pop("canonical_sha256"); checks.append(digest(raw)==claimed)
    failures=sum(not x for x in checks)
    out={"schema":"kernellum.perturbation-basin-audit.v1","status":"PASS" if failures==0 else "FAIL",
         "checks":len(checks),"failures":failures,"source_canonical_sha256":claimed}
    out["canonical_sha256"]=digest(out)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if failures==0 else 1)


if __name__=="__main__": main()
