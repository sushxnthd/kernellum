#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from dfbench import Objective
from dfbench.problems import UIFOProblem

SOURCE_INDEX = 6602


def dec(x):
    if isinstance(x, (bytes, bytearray, np.bytes_)):
        return bytes(x).decode("utf-8").rstrip("\x00")
    return str(x)


def canon(pair):
    if pair and isinstance(pair[0], (list, tuple)):
        targets = pair
    else:
        targets = [pair]
    return tuple(sorted((str(c), str(p)) for c, p in targets))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--topology-seed", type=int, default=98591154)
    args = ap.parse_args()

    sys.path.insert(0, str(args.dataset.parent / "examples"))
    from dataset_utils import reconstruct_uifo_setup  # type: ignore

    problem = UIFOProblem(topology_seed=args.topology_seed)
    obj = Objective(problem, max_time=180)
    target_pairs = list(obj.optimization_pairs)
    target_keys = [canon(p) for p in target_pairs]
    target_index = {k: i for i, k in enumerate(target_keys)}
    bounds = np.asarray(obj.bounds, dtype=float)

    with h5py.File(args.dataset, "r") as h5:
        e = h5["entries"][SOURCE_INDEX]
        src_topo = dec(e["topology_string"])
        start = int(e["param_offset"])
        stop = start + int(e["param_length"])
        src_values = np.asarray(h5["bounded_params"][start:stop], dtype=float)
        _, src_pairs = reconstruct_uifo_setup(src_topo, int(e["size"]))
        src_map = {canon(p): float(v) for p, v in zip(src_pairs, src_values)}

    matched = [(target_index[k], src_map[k]) for k in target_keys if k in src_map]
    unmatched = [i for i, k in enumerate(target_keys) if k not in src_map]

    print("RESIDUAL_SOURCE", SOURCE_INDEX, src_topo, float(e["loss"]))
    print("RESIDUAL_MATCHED", len(matched), "UNMATCHED", len(unmatched))
    for i in unmatched:
        print("RESIDUAL_DIM", i, target_keys[i], float(bounds[0, i]), float(bounds[1, i]))

    # Build many target-valid fills before logging, while locking all semantically
    # transferred coordinates. This reduces the search from 185D to only the
    # unmatched target coordinates.
    fills = np.asarray(obj.random_params(n_samples=32), dtype=float)
    if fills.ndim == 1:
        fills = fills[None, :]

    candidates = []
    midpoint = 0.5 * (bounds[0] + bounds[1])
    bases = [midpoint] + [fills[i] for i in range(min(31, len(fills)))]
    for j, raw in enumerate(bases):
        vec = np.asarray(raw, dtype=float).copy()
        for idx, val in matched:
            vec[idx] = val
        vec = np.clip(vec, bounds[0], bounds[1])
        candidates.append((j, vec))

    obj.warmup_value_aux()
    obj.start_logging()

    results = []
    for cid, vec in candidates:
        if obj.budget_exceeded:
            break
        loss, aux = obj.value_aux(vec)
        row = (cid, float(loss), bool(aux["is_feasible"]), float(aux["penalty"]))
        results.append(row)
        print("RESIDUAL_EVAL", *row)

    feasible = [r for r in results if r[2] and np.isfinite(r[1])]
    print("RESIDUAL_EVAL_COUNT", len(results))
    print("RESIDUAL_FEASIBLE_COUNT", len(feasible))
    print("RESIDUAL_BEST_FEASIBLE", min((r[1] for r in feasible), default=float("nan")))
    if feasible:
        print("RESIDUAL_BEST_ROW", min(feasible, key=lambda r: r[1]))


if __name__ == "__main__":
    main()
