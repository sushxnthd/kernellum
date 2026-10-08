#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import math
from pathlib import Path

import h5py
import numpy as np
from dfbench import Objective
from dfbench.problems import UIFOProblem


def dec(x):
    if isinstance(x, (bytes, bytearray, np.bytes_)):
        return bytes(x).decode("utf-8").rstrip("\x00")
    return str(x)


def topo_distance(a: str, b: str) -> tuple[int, int, int]:
    ai, ab = a.split("-")
    bi, bb = b.split("-")
    if len(ai) != len(bi) or len(ab) != len(bb):
        return (10**9, 10**9, 10**9)
    di = sum(x != y for x, y in zip(ai, bi))
    db = sum(x != y for x, y in zip(ab, bb))
    return di + db, di, db


def load_params(h5, entry):
    start = int(entry["param_offset"])
    stop = start + int(entry["param_length"])
    return np.asarray(h5["bounded_params"][start:stop])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--topology-seed", type=int, default=98591154)
    ap.add_argument("--optimizer-seed", type=int, default=1791403674)
    args = ap.parse_args()

    # Only public Objective metadata is used to identify the target topology.
    problem = UIFOProblem(topology_seed=args.topology_seed)
    obj = Objective(problem, max_time=180)
    spec = obj.problem_spec
    params_spec = spec["params"]
    target_topology = params_spec["topology"]
    target_size = int(params_spec["size"])

    print("TARGET_TOPOLOGY", target_topology)
    print("TARGET_SIZE", target_size)
    print("TARGET_NPARAMS", obj.n_params)
    print("TARGET_SPEC", spec)

    with h5py.File(args.dataset, "r") as h5:
        entries = h5["entries"]
        n = len(entries)
        topologies = [dec(x) for x in entries["topology_string"][:]]
        sizes = np.asarray(entries["size"][:], dtype=int)
        losses = np.asarray(entries["loss"][:], dtype=float)
        param_lengths = np.asarray(entries["param_length"][:], dtype=int)

        counts = Counter(topologies)
        print("DATASET_ENTRIES", n)
        print("UNIQUE_TOPOLOGIES", len(counts))
        print("SIZE_COUNTS", dict(Counter(sizes.tolist())))
        print("LOSS_GLOBAL_MIN", float(np.nanmin(losses)))
        print("LOSS_GLOBAL_MEDIAN", float(np.nanmedian(losses)))
        print("LOSS_NEGATIVE_FRACTION", float(np.mean(losses < 0)))
        print("PARAM_LENGTH_MIN_MEDIAN_MAX", int(param_lengths.min()), float(np.median(param_lengths)), int(param_lengths.max()))

        exact = np.flatnonzero((sizes == target_size) & (np.asarray(topologies, dtype=object) == target_topology))
        print("EXACT_MATCH_COUNT", len(exact))
        if len(exact):
            order = exact[np.argsort(losses[exact])]
            print("EXACT_SAVED_BEST", float(losses[order[0]]))
            print("EXACT_SAVED_MEDIAN", float(np.median(losses[exact])))
            for rank, idx in enumerate(order[:10], 1):
                e = entries[int(idx)]
                print(
                    "EXACT_ENTRY",
                    rank,
                    int(idx),
                    dec(e["unique_hash"]),
                    float(e["loss"]),
                    int(e["param_length"]),
                    dec(e["initialized_from"]),
                )

            # Re-evaluate up to the three best exact-topology dataset designs under
            # the current competition objective. This is semantically safe because
            # topology and parameter ordering are identical for an exact match.
            obj.start_logging()
            for rank, idx in enumerate(order[:3], 1):
                p = load_params(h5, entries[int(idx)])
                if len(p) != obj.n_params:
                    print("EXACT_REEVAL_SKIP_LENGTH", rank, len(p), obj.n_params)
                    continue
                value, aux = obj.value_aux(p)
                print(
                    "EXACT_REEVAL",
                    rank,
                    int(idx),
                    float(value),
                    bool(aux["is_feasible"]),
                    float(aux["penalty"]),
                )
        else:
            print("EXACT_REEVAL none")

        # Structural nearest-neighbour audit, restricted to same-size topologies.
        unique_same = [t for t in counts if len(t.split("-")[0]) == target_size * target_size]
        nearest = sorted((topo_distance(target_topology, t), t, counts[t]) for t in unique_same)
        for rank, (dist, topo, count) in enumerate(nearest[:15], 1):
            idxs = np.flatnonzero(np.asarray(topologies, dtype=object) == topo)
            best = float(np.min(losses[idxs]))
            med = float(np.median(losses[idxs]))
            plens = sorted(set(int(x) for x in param_lengths[idxs]))
            print("NEAREST_TOPOLOGY", rank, dist[0], dist[1], dist[2], count, best, med, plens, topo)


if __name__ == "__main__":
    main()
