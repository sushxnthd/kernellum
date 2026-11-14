#!/usr/bin/env python3
"""Synthetic preflight for represented task-count and canonicalized-null behavior."""
from __future__ import annotations
import sys
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.jmlr_v27.atomicity_intervention import transform_losses

METHODS = {
    "ls": {},
    "mgda": {},
    "cagrad": {"c": 0.4, "max_norm": 0.0},
    "nashmtl": {"optim_niter": 20, "update_weights_every": 1, "max_norm": 0.0},
    "fairgrad": {"alpha": 2.0, "max_norm": 0.0},
}

def run(method_name, arm, k=4):
    from methods.weight_methods import WeightMethods
    p = torch.tensor([0.31, -0.47, 0.19], dtype=torch.float64, requires_grad=True)
    # Strictly positive nonlinear losses with distinct gradient geometry.
    l0 = ((p - torch.tensor([0.8,-0.1,0.2], dtype=p.dtype))**2).sum() + 0.3
    l1 = ((p - torch.tensor([-0.2,0.6,-0.4], dtype=p.dtype))**2).sum() + 0.5
    semantic = torch.stack([l0, l1])
    represented, _ = transform_losses(semantic, arm, parent_task=0, clone_k=k)
    n_tasks = len(represented)
    wm = WeightMethods(method_name, n_tasks=n_tasks, device=torch.device("cpu"), **METHODS[method_name])
    kwargs = dict(
        losses=represented,
        shared_parameters=[p],
        task_specific_parameters=[p],
        last_shared_parameters=[p],
        representation=p.reshape(1,-1),
    )
    _, extra = wm.backward(**kwargs)
    if p.grad is None:
        raise RuntimeError(f"{method_name}/{arm}: no shared gradient")
    return p.grad.detach().clone(), n_tasks, extra

def main():
    report = {}
    for method in METHODS:
        gc, nc, _ = run(method, "coarse")
        gz, nz, _ = run(method, "canonicalized")
        ge, ne, _ = run(method, "exposed")
        rel = float((gc-gz).norm() / gc.norm().clamp_min(1e-30))
        if nc != 2 or nz != 2 or ne != 5:
            raise AssertionError((method, nc, nz, ne))
        if rel > 1e-8:
            raise AssertionError(f"{method}: canonicalized null relerr={rel}")
        report[method] = {
            "coarse_tasks": nc,
            "canonicalized_tasks": nz,
            "exposed_tasks": ne,
            "canonicalized_grad_relerr": rel,
            "exposed_to_coarse_grad_l2": float((ge-gc).norm()),
        }
    print(report)
    print("PASS: five-method represented-dimension + canonicalized-null preflight")

if __name__ == "__main__":
    main()
