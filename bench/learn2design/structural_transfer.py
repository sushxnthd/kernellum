#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
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


def canon(pair):
    if pair and isinstance(pair[0], (list, tuple)):
        targets = pair
    else:
        targets = [pair]
    return tuple(sorted((str(c), str(p)) for c, p in targets))


def positions(size: int):
    interior = [f"{r}{c}" for r in range(1, size + 1) for c in range(1, size + 1)]
    grid = size + 2
    boundary = [f"0{c}" for c in range(1, grid - 1)]
    for r in range(1, grid - 1):
        boundary += [f"{r}0", f"{r}{grid-1}"]
    boundary += [f"{grid-1}{c}" for c in range(1, grid - 1)]
    return interior, boundary


def topo_map(topo: str, size: int):
    a, b = topo.split("-")
    ip, bp = positions(size)
    return {**dict(zip(ip, a)), **dict(zip(bp, b))}


def referenced_positions(key, known_positions):
    refs = set()
    # Component names encode grid coordinates as 2-digit substrings: center11,
    # ml11, m10, boundary34, and space/edge names concatenate endpoints.
    for component, _prop in key:
        text = str(component)
        for pos in known_positions:
            if pos in text:
                refs.add(pos)
    return refs


def compatible_key(key, source_map, target_map, known_positions):
    refs = referenced_positions(key, known_positions)
    if not refs:
        return True
    return all(source_map.get(p) == target_map.get(p) for p in refs)


def load_params(h5, entry):
    s = int(entry["param_offset"])
    e = s + int(entry["param_length"])
    return np.asarray(h5["bounded_params"][s:e], dtype=float)


def topo_distance(a, b):
    aa, ab = a.split("-")
    ba, bb = b.split("-")
    if len(aa) != len(ba) or len(ab) != len(bb):
        return 10**9
    return sum(x != y for x, y in zip(aa, ba)) + sum(x != y for x, y in zip(ab, bb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--topology-seed", type=int, default=98591154)
    args = ap.parse_args()

    sys.path.insert(0, str(args.dataset.parent / "examples"))
    from dataset_utils import reconstruct_uifo_setup  # type: ignore

    problem = UIFOProblem(topology_seed=args.topology_seed)
    obj = Objective(problem, max_time=180)
    spec = obj.problem_spec
    target_topo = spec["params"]["topology"]
    size = int(spec["params"]["size"])
    tmap = topo_map(target_topo, size)
    known = set(tmap)
    target_keys = [canon(p) for p in obj.optimization_pairs]
    target_index = {k: i for i, k in enumerate(target_keys)}
    bounds = np.asarray(obj.bounds, dtype=float)
    midpoint = 0.5 * (bounds[0] + bounds[1])

    with h5py.File(args.dataset, "r") as h5:
        entries = h5["entries"]
        losses = np.asarray(entries["loss"][:], dtype=float)
        sizes = np.asarray(entries["size"][:], dtype=int)
        topologies = [dec(x) for x in entries["topology_string"][:]]
        same = np.flatnonzero(sizes == size)

        # Broad source pool: strong saved designs + nearest structures + sources
        # from the earlier semantic-transfer shortlist.
        global_best = same[np.argsort(losses[same])[:250]]
        by_topo = {}
        for idx in same:
            t = topologies[int(idx)]
            if t not in by_topo or losses[idx] < losses[by_topo[t]]:
                by_topo[t] = int(idx)
        nearest = sorted(by_topo, key=lambda t: topo_distance(target_topo, t))[:250]
        pool = sorted(set(global_best.tolist() + [by_topo[t] for t in nearest]))

        rows = []
        for idx in pool:
            e = entries[idx]
            src_topo = topologies[idx]
            src_values = load_params(h5, e)
            try:
                _, src_pairs = reconstruct_uifo_setup(src_topo, int(e["size"]))
            except Exception:
                continue
            if len(src_pairs) != len(src_values):
                continue
            src_map = topo_map(src_topo, size)
            src_vals = {canon(p): float(v) for p, v in zip(src_pairs, src_values)}

            common = []
            structurally_safe = []
            for key in target_keys:
                if key not in src_vals:
                    continue
                common.append(key)
                if compatible_key(key, src_map, tmap, known):
                    structurally_safe.append(key)

            safe_frac = len(structurally_safe) / len(target_keys)
            common_frac = len(common) / len(target_keys)
            char_match_frac = sum(src_map[p] == tmap[p] for p in known) / len(known)
            # Prefer physically compatible coordinate coverage, then high-quality
            # source loss. Character overlap is a tie-breaker only.
            score = (-safe_frac, float(losses[idx]), -char_match_frac)
            rows.append((score, idx, structurally_safe, safe_frac, common_frac,
                         char_match_frac, float(losses[idx]), src_topo, src_vals))

        rows.sort(key=lambda x: x[0])
        print("STRUCT_TARGET", target_topo, "nparams", obj.n_params)
        print("STRUCT_POOL", len(pool), "VALID", len(rows))
        for rank, r in enumerate(rows[:20], 1):
            _, idx, safe, sf, cf, cm, sl, topo, _ = r
            print("STRUCT_SHORTLIST", rank, idx, "safe", sf, "common", cf,
                  "charmatch", cm, "safe_n", len(safe), "saved", sl,
                  "dist", topo_distance(target_topo, topo), topo)

        # Controls and structural transfers. Alternate random and midpoint fill
        # for non-transferable coordinates.
        random_bases = np.asarray(obj.random_params(n_samples=16), dtype=float)
        if random_bases.ndim == 1:
            random_bases = random_bases[None, :]
        evals = []
        for j in range(4):
            evals.append((f"random_{j}", random_bases[j].copy(), 0.0, None))

        for j, r in enumerate(rows[:12]):
            _, idx, safe_keys, sf, _cf, _cm, sl, _topo, src_vals = r
            base = random_bases[(j + 4) % len(random_bases)].copy() if j % 2 == 0 else midpoint.copy()
            for key in safe_keys:
                base[target_index[key]] = src_vals[key]
            base = np.clip(base, bounds[0], bounds[1])
            evals.append((f"struct_{idx}", base, sf, sl))

        obj.warmup_value_aux()
        obj.start_logging()
        results = []
        for name, vec, frac, saved in evals:
            if obj.budget_exceeded:
                break
            loss, aux = obj.value_aux(vec)
            row = (name, float(loss), bool(aux["is_feasible"]), float(aux["penalty"]), frac, saved)
            results.append(row)
            print("STRUCT_EVAL", *row)

        feasible = [r for r in results if r[2] and np.isfinite(r[1])]
        struct_feas = [r for r in feasible if r[0].startswith("struct_")]
        random_feas = [r for r in feasible if r[0].startswith("random_")]
        print("STRUCT_EVAL_COUNT", len(results))
        print("STRUCT_FEASIBLE_COUNT", len(feasible))
        print("STRUCT_RANDOM_BEST", min((r[1] for r in random_feas), default=float("nan")))
        print("STRUCT_TRANSFER_BEST", min((r[1] for r in struct_feas), default=float("nan")))
        if struct_feas:
            print("STRUCT_BEST_ROW", min(struct_feas, key=lambda r: r[1]))


if __name__ == "__main__":
    main()
