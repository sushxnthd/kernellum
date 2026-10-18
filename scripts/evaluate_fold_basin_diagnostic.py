#!/usr/bin/env python3
"""Label-blind fold-basin dispersion diagnostic on opened development paths."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]


def lower(theta: np.ndarray, d: int) -> np.ndarray:
    out = np.zeros((d, d), dtype=float)
    out[np.tril_indices(d)] = theta[1 + d :]
    return out


def mean(theta: np.ndarray, x: np.ndarray) -> np.ndarray:
    d = x.shape[1]
    projected = x @ lower(theta, d)
    exponent = theta[0] + x @ theta[1 : 1 + d] - np.einsum("ij,ij->i", projected, projected)
    return np.exp(np.minimum(exponent, 80.0))


def moment_start(x: np.ndarray, target: np.ndarray) -> np.ndarray:
    d = x.shape[1]
    positive = np.maximum(target, 0.0) + max(float(np.max(np.abs(target))) * 1e-8, 1e-12)
    log_target = np.log(positive)
    features = [np.ones(len(x)), *[x[:, j] for j in range(d)]]
    pairs = []
    for row in range(d):
        for col in range(row + 1):
            pairs.append((row, col))
            features.append(-(x[:, row] * x[:, col]) if row == col else -(2 * x[:, row] * x[:, col]))
    coef = np.linalg.lstsq(np.column_stack(features), log_target, rcond=None)[0]
    precision = np.zeros((d, d), dtype=float)
    for value, (row, col) in zip(coef[1 + d :], pairs):
        precision[row, col] = precision[col, row] = value
    values, vectors = np.linalg.eigh(precision)
    precision = (vectors * np.maximum(values, 1e-8)) @ vectors.T
    adjusted = log_target + np.einsum("ni,ij,nj->n", x, precision, x)
    linear = np.linalg.lstsq(np.column_stack((np.ones(len(x)), x)), adjusted, rcond=None)[0]
    factor = np.linalg.cholesky(precision + np.eye(d) * 1e-12)
    return np.r_[linear, factor[np.tril_indices(d)]]


def starts(x: np.ndarray, target: np.ndarray) -> list[np.ndarray]:
    d = x.shape[1]
    base = moment_start(x, target)
    affine = np.linalg.lstsq(
        np.column_stack((np.ones(len(x)), x)),
        np.log(np.maximum(target, 0.0) + max(float(np.max(np.abs(target))) * 1e-8, 1e-12)),
        rcond=None,
    )[0]
    zero = np.r_[affine, np.zeros(d * (d + 1) // 2)]
    half = base.copy(); half[1 + d :] *= math.sqrt(0.5)
    double = base.copy(); double[1 + d :] *= math.sqrt(2.0)
    perturbed = base.copy(); perturbed[1 : 1 + d] += np.array([0.25, -0.25, 0.125, -0.125])
    return [base, zero, half, double, perturbed]


def fit_from(start: np.ndarray, x: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float]:
    d = x.shape[1]
    scale = max(float(np.max(np.abs(target))), 1e-12)
    rows, cols = np.tril_indices(d)
    lo = np.full(len(start), -np.inf); hi = np.full(len(start), np.inf)
    lo[1 + d + np.flatnonzero(rows == cols)] = 0.0

    def residual(theta: np.ndarray) -> np.ndarray:
        return (mean(theta, x) - target) / scale

    result = least_squares(residual, start, jac="3-point", bounds=(lo, hi), max_nfev=600,
                           ftol=1e-11, xtol=1e-11, gtol=1e-11)
    objective = float(result.fun @ result.fun)
    if not np.isfinite(result.x).all() or not math.isfinite(objective):
        raise FloatingPointError("nonfinite restart")
    return np.asarray(result.x), objective


def load_paths() -> tuple[dict, np.lib.npyio.NpzFile, Path, Path]:
    evidence = ROOT / "results/additive_response/confirmation"
    traces = evidence / "traces.jsonl.gz"; arrays_path = evidence / "inputs_and_truth.npz"
    paths = {}
    with gzip.open(traces, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if row["method"] == "exponential_only" and row["domain"] == "inside" and row["function"] in {"gaussian_4d", "negative_gaussian_4d"}:
                paths[(row["function"], row["seed"], float(row["noise"]))] = row
    return paths, np.load(arrays_path), traces, arrays_path


def score_path(key: tuple, row: dict, arrays: np.lib.npyio.NpzFile) -> dict:
    function, seed, noise = key
    pool = arrays[f"{function}_{seed}_pool"]
    selected = np.asarray(row["selected"], dtype=int)
    observed = np.asarray(row["observed"], dtype=float)
    low = pool.min(axis=0); span = np.maximum(pool.max(axis=0) - low, 1e-12)
    x = 2.0 * (pool[selected] - low) / span - 1.0
    sign = 1 if float(np.median(observed)) >= 0 else -1
    fold_spreads=[]; objective_spreads=[]; failures=0
    for held in range(len(x)):
        mask = np.arange(len(x)) != held
        amp = max(float(np.max(np.abs(observed[mask]))), 1e-12)
        target = sign * observed[mask] / amp
        predictions=[]; objectives=[]
        for start in starts(x[mask], target):
            try:
                theta, objective = fit_from(start, x[mask], target)
                predictions.append(sign * amp * float(mean(theta, x[held : held + 1])[0]))
                objectives.append(objective)
            except (FloatingPointError, ValueError, np.linalg.LinAlgError):
                failures += 1
        if len(predictions) != 5:
            fold_spreads.append(300.0); objective_spreads.append(300.0); continue
        yscale=max(float(np.std(observed[mask])),1e-12)
        fold_spreads.append(math.log10(1.0+(max(predictions)-min(predictions))/yscale))
        objective_spreads.append(math.log10((max(objectives)+1e-12)/(min(objectives)+1e-12)))
    return {"function":function,"seed":seed,"noise":noise,"sign":sign,"folds":len(x),
            "restart_failures":failures,"score":max(fold_spreads),
            "median_fold_spread":float(np.median(fold_spreads)),
            "max_objective_spread":max(objective_spreads)}


def average_ranks(values: list[float]) -> list[float]:
    order=sorted(range(len(values)),key=lambda i:values[i]); ranks=[0.0]*len(values); j=0
    while j<len(order):
        k=j+1
        while k<len(order) and values[order[k]]==values[order[j]]: k+=1
        rank=(j+1+k)/2
        for q in range(j,k): ranks[order[q]]=rank
        j=k
    return ranks


def auc(values: list[float], labels: list[bool]) -> float:
    ranks=average_ranks(values); pos=sum(labels); neg=len(labels)-pos
    return (sum(r for r,y in zip(ranks,labels) if y)-pos*(pos+1)/2)/(pos*neg)


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); parser.add_argument("--limit",type=int)
    args=parser.parse_args(); paths,arrays,traces,arrays_path=load_paths(); keys=sorted(paths)
    if args.limit: keys=keys[:args.limit]
    scores=[]
    for number,key in enumerate(keys,1):
        record=score_path(key,paths[key],arrays); scores.append(record)
        print(f"{number}/{len(keys)} {key} score={record['score']:.6g}",flush=True)
    if args.limit:
        payload={"classification":"DEVELOPMENT_PREFLIGHT","scores":scores}
    else:
        independent=json.loads((ROOT/"results/additive_response/independent_replication_full/records.json").read_text())
        labels={(r["function"],r["seed"],float(r["noise"])):not r["winner_agrees"] for r in independent}
        y=[labels[(r["function"],r["seed"],r["noise"])] for r in scores]
        values=[r["score"] for r in scores]; noise=[r["noise"] for r in scores]; nonzero=[float(r["noise"]>0) for r in scores]
        top=sorted(range(len(scores)),key=lambda i:values[i],reverse=True)[:10]
        positives=[values[i] for i in range(len(scores)) if y[i]]; negatives=[values[i] for i in range(len(scores)) if not y[i]]
        metrics={"paths":len(scores),"positives":sum(y),"auc":auc(values,y),"top10_recall":sum(y[i] for i in top)/sum(y),
                 "positive_median":float(np.median(positives)),"negative_median":float(np.median(negatives)),
                 "median_ratio":float(np.median(positives))/max(float(np.median(negatives)),1e-15),
                 "noise_auc":auc(noise,y),"nonzero_noise_auc":auc(nonzero,y)}
        gates={"auc_090":metrics["auc"]>=0.90,"top10_all":metrics["top10_recall"]==1.0,"beats_noise":metrics["auc"]>metrics["noise_auc"]}
        for r,label in zip(scores,y): r["solver_dependent_label"]=label
        payload={"schema":"kernellum.fold-basin-diagnostic.v1","classification":"OPENED_DEVELOPMENT",
                 "metrics":metrics,"gates":gates,"status":"PASS" if all(gates.values()) else "FAIL","scores":scores,
                 "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
                 "inputs":{"traces_sha256":hashlib.sha256(traces.read_bytes()).hexdigest(),"arrays_sha256":hashlib.sha256(arrays_path.read_bytes()).hexdigest()}}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    payload["canonical_sha256"]=hashlib.sha256(canonical).hexdigest()
    args.output.write_text(json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:payload[k] for k in ("classification","metrics","gates","status","canonical_sha256") if k in payload},indent=2))


if __name__=="__main__": main()
