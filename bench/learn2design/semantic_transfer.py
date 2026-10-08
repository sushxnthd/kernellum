#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from dfbench import Objective
from dfbench.problems import UIFOProblem


def dec(x):
    if isinstance(x, (bytes, bytearray, np.bytes_)):
        return bytes(x).decode("utf-8").rstrip("\x00")
    return str(x)


def topo_distance(a: str, b: str) -> int:
    ai, ab = a.split("-")
    bi, bb = b.split("-")
    if len(ai) != len(bi) or len(ab) != len(bb):
        return 10**9
    return sum(x != y for x, y in zip(ai, bi)) + sum(x != y for x, y in zip(ab, bb))


def canon(pair):
    if pair and isinstance(pair[0], (list, tuple)):
        targets = pair
    else:
        targets = [pair]
    return tuple(sorted((str(c), str(p)) for c, p in targets))


def load_params(h5, entry):
    s = int(entry["param_offset"])
    e = s + int(entry["param_length"])
    return np.asarray(h5["bounded_params"][s:e], dtype=float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--topology-seed", type=int, default=98591154)
    args = ap.parse_args()

    # Use the official released helper only offline in this diagnostic to decode
    # source parameter semantics. A final submission will use a preprocessed
    # compact artifact and public Objective.optimization_pairs only.
    sys.path.insert(0, str(args.dataset.parent / "examples"))
    from dataset_utils import reconstruct_uifo_setup  # type: ignore

    problem = UIFOProblem(topology_seed=args.topology_seed)
    obj = Objective(problem, max_time=180)
    spec = obj.problem_spec
    target_topo = spec["params"]["topology"]
    target_size = int(spec["params"]["size"])
    target_pairs = list(obj.optimization_pairs)
    target_keys = [canon(p) for p in target_pairs]
    target_key_to_idx = {k: i for i, k in enumerate(target_keys)}
    bounds = np.asarray(obj.bounds, dtype=float)
    midpoint = 0.5 * (bounds[0] + bounds[1])

    print("TRANSFER_TARGET", target_topo, target_size, obj.n_params)

    with h5py.File(args.dataset, "r") as h5:
        entries = h5["entries"]
        losses = np.asarray(entries["loss"][:], dtype=float)
        sizes = np.asarray(entries["size"][:], dtype=int)
        topologies = [dec(x) for x in entries["topology_string"][:]]

        # Candidate pool = strongest saved designs plus best designs among the
        # structurally closest topologies. This avoids assuming that Hamming
        # proximity alone predicts parameter transferability.
        same = np.flatnonzero(sizes == target_size)
        global_best = same[np.argsort(losses[same])[:50]]

        by_topo = {}
        for idx in same:
            t = topologies[int(idx)]
            prev = by_topo.get(t)
            if prev is None or losses[idx] < losses[prev]:
                by_topo[t] = int(idx)
        nearest_topos = sorted(by_topo, key=lambda t: topo_distance(target_topo, t))[:60]
        nearest_best = np.array([by_topo[t] for t in nearest_topos], dtype=int)
        pool = sorted(set(global_best.tolist() + nearest_best.tolist()))

        scored = []
        for idx in pool:
            e = entries[idx]
            src_topo = topologies[idx]
            src_params = load_params(h5, e)
            try:
                _, src_pairs = reconstruct_uifo_setup(src_topo, int(e["size"]))
            except Exception as exc:
                print("RECON_FAIL", idx, type(exc).__name__, str(exc))
                continue
            if len(src_pairs) != len(src_params):
                print("RECON_LENGTH_FAIL", idx, len(src_pairs), len(src_params))
                continue
            src_map = {canon(p): float(v) for p, v in zip(src_pairs, src_params)}
            matches = [(target_key_to_idx[k], src_map[k]) for k in target_keys if k in src_map]
            match_count = len(matches)
            match_frac = match_count / len(target_keys)
            dist = topo_distance(target_topo, src_topo)
            # Match fraction is the primary transfer criterion; then source
            # quality and structural distance break ties.
            score = (-match_frac, float(losses[idx]), dist)
            scored.append((score, idx, matches, match_frac, dist, float(losses[idx]), src_topo))

        scored.sort(key=lambda x: x[0])
        print("TRANSFER_POOL", len(pool), "RECONSTRUCTED", len(scored))
        for rank, row in enumerate(scored[:20], 1):
            _, idx, _, mf, dist, sl, topo = row
            print("TRANSFER_SHORTLIST", rank, idx, "match", mf, "dist", dist, "saved", sl, topo)

        # Pre-generate bounded baselines before logging. We evaluate pure random
        # controls and semantically transferred candidates under the same target.
        random_bases = np.asarray(obj.random_params(n_samples=8), dtype=float)
        if random_bases.ndim == 1:
            random_bases = random_bases[None, :]

        evals = []
        for j in range(min(4, len(random_bases))):
            evals.append((f"random_{j}", random_bases[j].copy(), 0.0, None))

        # Use the 12 most semantically aligned prototypes; alternate random and
        # midpoint fills so unmatched coordinates are not confounded with one fill.
        for j, row in enumerate(scored[:12]):
            _, idx, matches, mf, dist, sl, topo = row
            base = random_bases[j % len(random_bases)].copy() if j % 2 == 0 else midpoint.copy()
            for ti, value in matches:
                base[ti] = value
            base = np.clip(base, bounds[0], bounds[1])
            evals.append((f"transfer_{idx}", base, mf, sl))

        # Scalar value-only path is CPU-safe and sufficient to test basin entry.
        obj.warmup_value_aux()
        obj.start_logging()
        results = []
        for name, vec, mf, src_loss in evals:
            if obj.budget_exceeded:
                break
            loss, aux = obj.value_aux(vec)
            row = (name, float(loss), bool(aux["is_feasible"]), float(aux["penalty"]), mf, src_loss)
            results.append(row)
            print("TRANSFER_EVAL", *row)

        feasible = [r for r in results if r[2] and np.isfinite(r[1])]
        random_feas = [r for r in feasible if r[0].startswith("random_")]
        transfer_feas = [r for r in feasible if r[0].startswith("transfer_")]
        print("TRANSFER_EVAL_COUNT", len(results))
        print("TRANSFER_FEASIBLE_COUNT", len(feasible))
        print("RANDOM_BEST_FEASIBLE", min((r[1] for r in random_feas), default=float("nan")))
        print("TRANSFER_BEST_FEASIBLE", min((r[1] for r in transfer_feas), default=float("nan")))
        if transfer_feas:
            print("TRANSFER_BEST_ROW", min(transfer_feas, key=lambda r: r[1]))


if __name__ == "__main__":
    main()
