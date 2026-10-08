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


def refs_for_key(key, known):
    refs = set()
    for comp, _ in key:
        text = str(comp)
        for pos in known:
            if pos in text:
                refs.add(pos)
    return refs


def effective(loss: float, feasible: bool, penalty: float) -> float:
    if np.isfinite(loss) and feasible:
        return loss
    l = loss if np.isfinite(loss) else 1e3
    p = penalty if np.isfinite(penalty) else 1e3
    return 10.0 + l + 100.0 * p


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
    lo, hi = bounds[0], bounds[1]
    span = np.maximum(hi - lo, 1e-12)

    with h5py.File(args.dataset, "r") as h5:
        e = h5["entries"][SOURCE_INDEX]
        src_topo = dec(e["topology_string"])
        s = int(e["param_offset"])
        stop = s + int(e["param_length"])
        vals = np.asarray(h5["bounded_params"][s:stop], dtype=float)
        _, src_pairs = reconstruct_uifo_setup(src_topo, int(e["size"]))
        src_vals = {canon(p): float(v) for p, v in zip(src_pairs, vals)}

    smap = topo_map(src_topo, size)
    changed_positions = {p for p in known if smap.get(p) != tmap.get(p)}

    # Coherent semantic warm start: copy every source coordinate that has an
    # identically named target coordinate; target-only coordinates use midpoint.
    x0 = 0.5 * (lo + hi)
    matched = 0
    for key in target_keys:
        if key in src_vals:
            x0[target_index[key]] = src_vals[key]
            matched += 1
    x0 = np.clip(x0, lo, hi)
    q0 = np.clip((x0 - lo) / span, 0.0, 1.0)

    changed_mask = np.zeros(obj.n_params, dtype=float)
    for i, key in enumerate(target_keys):
        refs = refs_for_key(key, known)
        if (not refs and key not in src_vals) or any(p in changed_positions for p in refs) or key not in src_vals:
            changed_mask[i] = 1.0
    if changed_mask.sum() == 0:
        changed_mask[:] = 1.0

    print("SPSA_TARGET", target_topo)
    print("SPSA_SOURCE", SOURCE_INDEX, src_topo)
    print("SPSA_MATCHED", matched, "NPARAMS", obj.n_params)
    print("SPSA_CHANGED_POSITIONS", len(changed_positions), sorted(changed_positions))
    print("SPSA_CHANGED_DIMS", int(changed_mask.sum()))

    rng = np.random.default_rng(1791403674)
    # Four full-space and four changed-region SPSA pairs.
    probes = []
    for label, mask, c in (("full", np.ones(obj.n_params), 0.008), ("changed", changed_mask, 0.015)):
        for j in range(4):
            d = rng.choice([-1.0, 1.0], size=obj.n_params) * mask
            probes.append((label, j, c, d))

    obj.warmup_value_aux()
    obj.start_logging()

    def evaluate(tag, q):
        x = lo + np.clip(q, 0.0, 1.0) * span
        loss, aux = obj.value_aux(x)
        lf = float(loss)
        feas = bool(aux["is_feasible"])
        pen = float(aux["penalty"])
        sc = effective(lf, feas, pen)
        print("SPSA_EVAL", tag, lf, feas, pen, sc)
        return lf, feas, pen, sc

    base = evaluate("base", q0)
    gradients = {"full": np.zeros(obj.n_params), "changed": np.zeros(obj.n_params)}
    counts = {"full": 0, "changed": 0}

    for label, j, c, d in probes:
        if obj.budget_exceeded:
            break
        plus = evaluate(f"{label}_{j}_plus", q0 + c * d)
        if obj.budget_exceeded:
            break
        minus = evaluate(f"{label}_{j}_minus", q0 - c * d)
        deriv = (plus[3] - minus[3]) / (2.0 * c)
        gradients[label] += deriv * d
        counts[label] += 1
        print("SPSA_PAIR", label, j, "deriv", deriv)

    best = (base[0], "base") if base[1] else (float("inf"), "base")
    for label in ("full", "changed"):
        if counts[label] == 0 or obj.budget_exceeded:
            continue
        g = gradients[label] / counts[label]
        if label == "changed":
            g *= changed_mask
        norm = float(np.linalg.norm(g))
        print("SPSA_GRAD", label, "pairs", counts[label], "norm", norm)
        if not np.isfinite(norm) or norm <= 1e-12:
            continue
        direction = g / norm
        for step in (0.01, 0.03, 0.06):
            if obj.budget_exceeded:
                break
            out = evaluate(f"{label}_step_{step}", q0 - step * direction)
            if out[1] and out[0] < best[0]:
                best = (out[0], f"{label}_step_{step}")

    print("SPSA_BEST_FEASIBLE", best[0], best[1])


if __name__ == "__main__":
    main()
