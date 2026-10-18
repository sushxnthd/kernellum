#!/usr/bin/env python3
"""Manifest-check and aggregate all 24 frozen stacking shards."""
from __future__ import annotations
import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import scipy
from evaluate_sign_anchor_shifted import DOMAINS, canon, geomean_log
from evaluate_validation_aware_stacking import FAMILIES,DIMS,SEEDS,NOISES,METHODS,FOLDS,GRID_STEP,CANDIDATE_FLOOR,canonical

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--shard-dir",type=Path,required=True)
    ap.add_argument("--decisions",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    keys=[(f,d,s,n) for f in FAMILIES for d in DIMS for s in SEEDS for n in NOISES]
    shards=[]
    for i,key in enumerate(keys):
        path=a.shard_dir/f"shard-{i:02d}.json"
        payload=json.loads(path.read_text())
        claimed=payload.pop("canonical_sha256")
        actual=hashlib.sha256(canonical(payload).encode()).hexdigest()
        if claimed!=actual or payload["schema"]!="kernellum.validation-aware-stacking-shard.v1":
            raise SystemExit(f"invalid shard digest/schema: {path}")
        if payload["index"]!=i or tuple(payload["key"])!=key:
            raise SystemExit(f"wrong shard manifest: {path}")
        if payload["decision"]["key"]!=payload["key"] or payload["record"]["key"]!=payload["key"]:
            raise SystemExit(f"unbound shard key: {path}")
        payload["canonical_sha256"]=claimed
        shards.append(payload)
    decision_rows=[s["decision"] for s in shards]
    records=[s["record"] for s in shards]
    decisions={"schema":"kernellum.validation-aware-stacking-decisions.v1",
      "classification":"PROSPECTIVE_UNSEEN_SYNTHETIC_FAMILIES",
      "cohort":{"families":list(FAMILIES),"dimensions":list(DIMS),"seeds":list(SEEDS),"noises":list(NOISES)},
      "mechanism":{"folds":FOLDS,"grid_step":GRID_STEP,"candidate_weight_floor":CANDIDATE_FLOOR,
                   "active_non_candidate_weight":.2,"active_disagreement":.10},
      "shard_sha256":[s["canonical_sha256"] for s in shards],"rows":decision_rows}
    a.decisions.write_text(canonical(decisions))
    decision_sha=hashlib.sha256(a.decisions.read_bytes()).hexdigest()
    methods=(*METHODS,"naive","equal_average","hard_validation","stack")
    metrics={}
    for domain in DOMAINS:
        metrics[domain]={"geometric_nmse":{m:geomean_log([r["scores"][domain][m] for r in records]) for m in methods},
                         "catastrophic":{m:sum(r["scores"][domain][m]>5 for r in records) for m in methods}}
    ratios={"inside_over_candidate":metrics["inside"]["geometric_nmse"]["stack"]/metrics["inside"]["geometric_nmse"]["candidate"],
      "far_over_candidate":metrics["far_shell"]["geometric_nmse"]["stack"]/metrics["far_shell"]["geometric_nmse"]["candidate"],
      "far_over_equal_average":metrics["far_shell"]["geometric_nmse"]["stack"]/metrics["far_shell"]["geometric_nmse"]["equal_average"],
      "far_over_hard_validation":metrics["far_shell"]["geometric_nmse"]["stack"]/metrics["far_shell"]["geometric_nmse"]["hard_validation"]}
    active=[r for r in records if r["predicted_active"]]
    active_families=len({r["key"][0] for r in active})
    active_precision=sum(r["scores"]["far_shell"]["stack"]<r["scores"]["far_shell"]["candidate"] for r in active)/len(active) if active else 0.
    cc={d:metrics[d]["catastrophic"]["candidate"] for d in DOMAINS}; sc={d:metrics[d]["catastrophic"]["stack"] for d in DOMAINS}
    gates={"complete":len(records)==24,"far_improves":ratios["far_over_candidate"]<=.90,
      "inside_noninferior":ratios["inside_over_candidate"]<=1.05,
      "no_excess_catastrophe":all(sc[d]<=cc[d] for d in DOMAINS),
      "halves_far_catastrophes":cc["far_shell"]>=2 and 2*sc["far_shell"]<=cc["far_shell"],
      "beats_equal_average":ratios["far_over_equal_average"]<1.,
      "beats_hard_validation":ratios["far_over_hard_validation"]<1.,
      "four_active":len(active)>=4,"two_active_families":active_families>=2,"active_precision":active_precision>=.75}
    out={"schema":"kernellum.validation-aware-stacking-result.v1",
      "classification":"PROSPECTIVE_UNSEEN_SYNTHETIC_FAMILIES",
      "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
      "decision_sha256":decision_sha,"paths":len(records),"predicted_active_paths":len(active),
      "active_families":active_families,"active_precision":active_precision,"metrics":metrics,"ratios":ratios,
      "gates":gates,"records":records,
      "status":"PASS_EXTERNAL_REPLICATION_REQUIRED" if all(gates.values()) else "FAIL_KILL_OR_REFORMULATE",
      "smallest_claim":"The frozen conservative OOF stack was evaluated prospectively on 24 unseen synthetic-family paths; external-data transfer is not established."}
    out["canonical_sha256"]=canon(out)
    a.output.write_text(canonical(out))
    print(json.dumps({k:out[k] for k in ("status","canonical_sha256","predicted_active_paths","active_families","active_precision","ratios","gates")},indent=2,sort_keys=True))
if __name__=="__main__": main()
