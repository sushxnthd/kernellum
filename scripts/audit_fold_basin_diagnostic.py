#!/usr/bin/env python3
"""Sequential score and independent metric audit for the frozen development result."""
import argparse,hashlib,json,math,sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from scripts import evaluate_fold_basin_diagnostic as core

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("result",type=Path); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    result=json.loads(a.result.read_text()); ordered=sorted(result["scores"],key=lambda r:r["score"],reverse=True)
    keys={(r["function"],r["seed"],float(r["noise"])) for r in ordered[:10]}
    keys|={(r["function"],r["seed"],float(r["noise"])) for r in result["scores"] if r["solver_dependent_label"]}
    paths,arrays,_,_=core.load_paths(); mismatches=[]; checked=[]
    frozen={(r["function"],r["seed"],float(r["noise"])):r for r in result["scores"]}
    for key in sorted(keys):
        row=core.score_path(key,paths[key],arrays); delta=abs(row["score"]-frozen[key]["score"])
        checked.append({"key":list(key),"score":row["score"],"absolute_delta":delta})
        if delta>1e-10: mismatches.append({"key":list(key),"absolute_delta":delta})
    labels=[bool(r["solver_dependent_label"]) for r in result["scores"]]; values=[float(r["score"]) for r in result["scores"]]
    auc=core.auc(values,labels); top=sorted(range(len(values)),key=lambda i:values[i],reverse=True)[:10]
    metric_ok=abs(auc-result["metrics"]["auc"])<1e-15 and sum(labels[i] for i in top)/sum(labels)==result["metrics"]["top10_recall"]
    out={"status":"PASS" if not mismatches and metric_ok else "FAIL","sequential_paths":len(checked),"score_mismatches":mismatches,
         "metric_recalculation_match":metric_ok,"checked":checked,"source_canonical_sha256":result["canonical_sha256"]}
    canonical=json.dumps(out,sort_keys=True,separators=(",",":"),allow_nan=False).encode(); out["canonical_sha256"]=hashlib.sha256(canonical).hexdigest()
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n"); print(json.dumps({k:out[k] for k in ("status","sequential_paths","score_mismatches","metric_recalculation_match","canonical_sha256")},indent=2))

if __name__=="__main__": main()
