#!/usr/bin/env python3
"""Parallel orchestration for the frozen fold-basin score function."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import scipy

from scripts import evaluate_fold_basin_diagnostic as core

ROOT = Path(__file__).resolve().parents[1]


def score_batch(keys: list[tuple]) -> list[dict]:
    paths, arrays, _, _ = core.load_paths()
    return [core.score_path(tuple(key), paths[tuple(key)], arrays) for key in keys]


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); parser.add_argument("--unlabeled",type=Path,required=True); parser.add_argument("--workers",type=int,default=6)
    args=parser.parse_args(); paths,_,traces,arrays_path=core.load_paths(); keys=sorted(paths)
    batches=[keys[i::args.workers] for i in range(args.workers)]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        parts=list(executor.map(score_batch,batches))
    scores=sorted([row for part in parts for row in part],key=lambda r:(r["function"],r["seed"],r["noise"]))
    unlabeled={"schema":"kernellum.fold-basin-scores.v1","scores":scores}
    raw=json.dumps(unlabeled,sort_keys=True,indent=2,allow_nan=False)+"\n"; args.unlabeled.write_text(raw)
    unlabeled_sha=hashlib.sha256(raw.encode()).hexdigest()

    independent=json.loads((ROOT/"results/additive_response/independent_replication_full/records.json").read_text())
    labels={(r["function"],r["seed"],float(r["noise"])):not r["winner_agrees"] for r in independent}
    y=[labels[(r["function"],r["seed"],r["noise"])] for r in scores]
    values=[r["score"] for r in scores]; noise=[r["noise"] for r in scores]; nonzero=[float(r["noise"]>0) for r in scores]
    top=sorted(range(len(scores)),key=lambda i:values[i],reverse=True)[:10]
    positives=[values[i] for i in range(len(scores)) if y[i]]; negatives=[values[i] for i in range(len(scores)) if not y[i]]
    metrics={"paths":len(scores),"positives":sum(y),"auc":core.auc(values,y),"top10_recall":sum(y[i] for i in top)/sum(y),
             "positive_median":float(np.median(positives)),"negative_median":float(np.median(negatives)),
             "median_ratio":float(np.median(positives))/max(float(np.median(negatives)),1e-15),
             "noise_auc":core.auc(noise,y),"nonzero_noise_auc":core.auc(nonzero,y)}
    gates={"auc_090":metrics["auc"]>=0.90,"top10_all":metrics["top10_recall"]==1.0,"beats_noise":metrics["auc"]>metrics["noise_auc"]}
    for row,label in zip(scores,y): row["solver_dependent_label"]=label
    payload={"schema":"kernellum.fold-basin-diagnostic.v1","classification":"OPENED_DEVELOPMENT","metrics":metrics,"gates":gates,
             "status":"PASS" if all(gates.values()) else "FAIL","scores":scores,"unlabeled_scores_sha256":unlabeled_sha,
             "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
             "inputs":{"traces_sha256":hashlib.sha256(traces.read_bytes()).hexdigest(),"arrays_sha256":hashlib.sha256(arrays_path.read_bytes()).hexdigest()}}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode(); payload["canonical_sha256"]=hashlib.sha256(canonical).hexdigest()
    args.output.write_text(json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"metrics":metrics,"gates":gates,"status":payload["status"],"canonical_sha256":payload["canonical_sha256"],"unlabeled_scores_sha256":unlabeled_sha},indent=2))


if __name__=="__main__": main()
