#!/usr/bin/env python3
"""Independent standard-library audit of the prospective stacking artifact."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path

def geomean(log_values):
    return math.exp(sum(log_values) / len(log_values))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--decisions",type=Path,required=True); ap.add_argument("--result",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    d=json.loads(a.decisions.read_text()); r=json.loads(a.result.read_text()); checks={}
    checks["decision_hash"]=hashlib.sha256(a.decisions.read_bytes()).hexdigest()==r["decision_sha256"]
    checks["complete"]=len(d["rows"])==len(r["records"])==24
    checks["unique_keys"]=len({tuple(x["key"]) for x in d["rows"]})==24
    checks["weights_simplex"]=all(abs(sum(x["weights"])-1)<1e-12 and x["weights"][0]>=.5-1e-12 and all(w>=0 for w in x["weights"]) for x in d["rows"])
    checks["grid_bound"]=all(all(abs(10*w-round(10*w))<1e-10 for w in x["weights"]) for x in d["rows"])
    decision={tuple(x["key"]):x for x in d["rows"]}; records={tuple(x["key"]):x for x in r["records"]}
    checks["active_binding"]=all(bool(decision[k]["predicted_active"])==bool(records[k]["predicted_active"]) for k in records)
    methods=("candidate","globalized","independent","naive","equal_average","hard_validation","stack")
    domains=("inside","near_shell","far_shell")
    recomputed={}
    for domain in domains:
        recomputed[domain]={"geometric_nmse":{},"catastrophic":{}}
        for method in methods:
            vals=[records[k]["scores"][domain][method] for k in sorted(records)]
            recomputed[domain]["geometric_nmse"][method]=geomean(vals)
            recomputed[domain]["catastrophic"][method]=sum(v>5 for v in vals)
    checks["metrics"]=all(abs(recomputed[x][y][z]-r["metrics"][x][y][z])<1e-12 if isinstance(r["metrics"][x][y][z],float) else recomputed[x][y][z]==r["metrics"][x][y][z] for x in domains for y in ("geometric_nmse","catastrophic") for z in methods)
    active=[records[k] for k in records if records[k]["predicted_active"]]
    precision=sum(x["scores"]["far_shell"]["stack"]<x["scores"]["far_shell"]["candidate"] for x in active)/len(active) if active else 0.
    checks["active_count"]=len(active)==r["predicted_active_paths"]
    checks["active_precision"]=abs(precision-r["active_precision"])<1e-12
    checks["status"]=r["status"]==("PASS_EXTERNAL_REPLICATION_REQUIRED" if all(r["gates"].values()) else "FAIL_KILL_OR_REFORMULATE")
    out={"schema":"kernellum.validation-aware-stacking-audit.v1","checks":checks,"passed":sum(checks.values()),"total":len(checks),"status":"PASS" if all(checks.values()) else "FAIL"}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True))
    if not all(checks.values()): raise SystemExit(2)
if __name__=="__main__": main()
