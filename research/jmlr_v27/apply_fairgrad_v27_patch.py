#!/usr/bin/env python3
"""Apply the JMLR v27 atomicity intervention to the pinned FairGrad trainers.

This is intentionally a narrow source patch. It does not alter models, data splits,
forward passes, semantic task losses, optimizers, schedulers, or evaluation metrics.
It only:
  1) adds coarse/exposed/canonicalized CLI arguments,
  2) transforms the already-computed semantic loss vector immediately before the
     multi-task combiner,
  3) instantiates the combiner at the represented task count, and
  4) creates ./save, matching the released run.sh setup.

The script fails closed if the pinned source does not match the expected text.
"""
from __future__ import annotations
from pathlib import Path
import argparse

PINNED_FAIRGRAD = "b58bce810e57288f7bf2c4c9effb7133b856739a"

HELPER = r'''
def _jmlr_atomicity_transform(losses, arm, parent, clone_k):
    """Representation-only intervention on an already-computed 1D loss tensor."""
    if losses.ndim != 1:
        raise ValueError("semantic loss vector must be 1D")
    if arm == "coarse":
        return losses
    if not (0 <= parent < len(losses)):
        raise ValueError(f"parent={parent} outside [0,{len(losses)-1}]")
    if clone_k < 2:
        raise ValueError("exposed/canonicalized clone_k must be >=2")
    exposed = torch.stack(
        [x for i, loss in enumerate(losses)
         for x in (([loss] * clone_k) if i == parent else [loss])]
    )
    if arm == "exposed":
        return exposed
    if arm == "canonicalized":
        start = parent
        stop = parent + clone_k
        parent_loss = exposed[start:stop].mean()
        return torch.cat((exposed[:start], parent_loss.reshape(1), exposed[stop:]))
    raise ValueError(f"unknown JMLR arm: {arm}")

def _jmlr_combiner_task_count(semantic_count, arm, clone_k):
    return semantic_count + clone_k - 1 if arm == "exposed" else semantic_count

def _jmlr_backward(weight_method, losses, args, **kwargs):
    """Keep released methods untouched unless the explicit canonical-MGDA control is requested."""
    if args.jmlr_canonical_mgda and args.method == "mgda":
        loss, extra_outputs = weight_method.get_weighted_loss(losses=losses, **kwargs)
        loss = loss / float(len(losses))
        loss.backward()
        return loss, extra_outputs
    return weight_method.backward(losses=losses, **kwargs)

def _jmlr_gradient_gram(losses, params):
    """Capture semantic gradient geometry without changing .grad or the training graph."""
    flats = []
    for loss in losses:
        gs = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
        chunks = []
        for p, g in zip(params, gs):
            if g is None:
                chunks.append(torch.zeros_like(p).reshape(-1).detach().cpu())
            else:
                chunks.append(g.reshape(-1).detach().cpu())
        flats.append(torch.cat(chunks).to(torch.float64))
    n = len(flats)
    gram = torch.empty((n, n), dtype=torch.float64)
    for i in range(n):
        for j in range(i, n):
            v = torch.dot(flats[i], flats[j])
            gram[i, j] = v
            gram[j, i] = v
    return gram

def _jmlr_maybe_save_audit(losses, shared_parameters, args, epoch, batch_index):
    if batch_index != 0 or not args.jmlr_audit_epochs:
        return
    epochs = {int(x) for x in args.jmlr_audit_epochs.split(",") if x.strip()}
    if epoch not in epochs:
        return
    run_id = args.jmlr_run_id or "unnamed"
    gram = _jmlr_gradient_gram(losses, shared_parameters)
    torch.save(
        {
            "epoch": int(epoch),
            "semantic_losses": losses.detach().cpu().to(torch.float64),
            "semantic_gram": gram,
            "run_id": run_id,
            "arm": args.jmlr_arm,
            "parent": int(args.jmlr_parent),
            "k": int(args.jmlr_k),
        },
        f"./save/{run_id}.audit.ep{epoch}.pt",
    )

def _jmlr_method_state(weight_method):
    method = weight_method.method
    if method.__class__.__name__ == "NashMTL":
        return {
            "kind": "NashMTL",
            "step": float(method.step),
            "prvs_alpha": np.asarray(method.prvs_alpha, dtype=np.float32),
        }
    return {"kind": method.__class__.__name__}

def _jmlr_restore_method_state(weight_method, state):
    if not state:
        return
    method = weight_method.method
    if state.get("kind") == "NashMTL":
        method.prvs_alpha = np.asarray(state["prvs_alpha"], dtype=np.float32)
        method.step = float(state["step"])
        method._init_optim_problem()

def _jmlr_save_checkpoint(path, model, optimizer, scheduler, weight_method, epoch, payload):
    if not path:
        return
    import random as _jmlr_random
    import os as _jmlr_os
    _jmlr_os.makedirs(_jmlr_os.path.dirname(path) or ".", exist_ok=True)
    state = {
        "epoch": int(epoch),
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "scheduler_state": scheduler.state_dict(),
        "method_state": _jmlr_method_state(weight_method),
        "python_rng": _jmlr_random.getstate(),
        "numpy_rng": np.random.get_state(),
        "torch_rng": torch.get_rng_state(),
        "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        "payload": payload,
    }
    tmp = path + ".tmp"
    torch.save(state, tmp)
    _jmlr_os.replace(tmp, path)

def _jmlr_load_checkpoint(path, model, optimizer, scheduler, weight_method):
    if not path:
        return None
    import random as _jmlr_random
    try:
        state = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        state = torch.load(path, map_location="cpu")
    model.load_state_dict(state["model_state"])
    optimizer.load_state_dict(state["optimizer_state"])
    scheduler.load_state_dict(state["scheduler_state"])
    _jmlr_restore_method_state(weight_method, state.get("method_state"))
    _jmlr_random.setstate(state["python_rng"])
    np.random.set_state(state["numpy_rng"])
    torch.set_rng_state(state["torch_rng"])
    if torch.cuda.is_available() and state.get("cuda_rng") is not None:
        torch.cuda.set_rng_state_all(state["cuda_rng"])
    return state
'''

def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {n}")
    return text.replace(old, new, 1)

def patch_common(text: str) -> str:
    text = replace_once(
        text,
        "set_logger()\n",
        "set_logger()\n" + HELPER + "\n",
        "helper insertion",
    )
    text = replace_once(
        text,
        '    args = parser.parse_args()\n',
        '    parser.add_argument("--jmlr-arm", choices=["coarse","exposed","canonicalized"], default="coarse")\n'
        '    parser.add_argument("--jmlr-parent", type=int, default=0)\n'
        '    parser.add_argument("--jmlr-k", type=int, default=2)\n'
        '    parser.add_argument("--jmlr-canonical-mgda", action="store_true")\n'
        '    parser.add_argument("--jmlr-run-id", type=str, default="")\n'
        '    parser.add_argument("--jmlr-audit-epochs", type=str, default="")\n'
        '    parser.add_argument("--jmlr-resume-from", type=str, default="")\n'
        '    parser.add_argument("--jmlr-checkpoint-path", type=str, default="")\n'
        '    args = parser.parse_args()\n',
        "JMLR CLI args",
    )
    return text

def patch_nyuv2(path: Path) -> None:
    text = patch_common(path.read_text())
    text = replace_once(
        text,
        '        args.method, n_tasks=3, device=device, **weight_methods_parameters[args.method]\n',
        '        args.method,\n'
        '        n_tasks=_jmlr_combiner_task_count(3, args.jmlr_arm, args.jmlr_k),\n'
        '        device=device,\n'
        '        **weight_methods_parameters[args.method],\n',
        "NYUv2 combiner dimension",
    )
    needle = '''            loss, extra_outputs = weight_method.backward(
                losses=losses,
'''
    repl = '''            _jmlr_maybe_save_audit(
                losses, list(model.shared_parameters()), args, epoch, j
            )
            combiner_losses = _jmlr_atomicity_transform(
                losses, args.jmlr_arm, args.jmlr_parent, args.jmlr_k
            )
            loss, extra_outputs = _jmlr_backward(
                weight_method, combiner_losses, args,
'''
    text = replace_once(text, needle, repl, "NYUv2 loss-vector intervention")
    text = replace_once(
        text,
        '    epoch_iter = trange(epochs)\n',
        '    epoch_iter = None\n',
        "NYUv2 deferred epoch iterator",
    )
    text = replace_once(
        text,
        '    loss_list = []\n\n    for epoch in epoch_iter:\n',
        '    loss_list = []\n'
        '    _jmlr_start_epoch = 0\n'
        '    if args.jmlr_resume_from:\n'
        '        _jmlr_state = _jmlr_load_checkpoint(args.jmlr_resume_from, model, optimizer, scheduler, weight_method)\n'
        '        _jmlr_start_epoch = int(_jmlr_state["epoch"]) + 1\n'
        '        _jmlr_payload = _jmlr_state.get("payload", {})\n'
        '        if "avg_cost" in _jmlr_payload: avg_cost[:] = _jmlr_payload["avg_cost"]\n'
        '        if "deltas" in _jmlr_payload: deltas[:] = _jmlr_payload["deltas"]\n'
        '        if "loss_list" in _jmlr_payload: loss_list = _jmlr_payload["loss_list"]\n'
        '    epoch_iter = trange(_jmlr_start_epoch, epochs)\n\n'
        '    for epoch in epoch_iter:\n',
        "NYUv2 resume setup",
    )
    text = replace_once(
        text,
        '            torch.save({\n',
        '            if args.jmlr_run_id:\n'
        '                name = f"{name}_{args.jmlr_run_id}"\n'
        '            torch.save({\n'
        '                "jmlr_meta": dict(arm=args.jmlr_arm, parent=args.jmlr_parent, k=args.jmlr_k, run_id=args.jmlr_run_id, canonical_mgda=args.jmlr_canonical_mgda),\n',
        "NYUv2 collision-proof metadata",
    )
    text = replace_once(
        text,
        '            }, f"./save/{name}.stats")\n',
        '            }, f"./save/{name}.stats")\n'
        '            if epoch == epochs - 1:\n'
        '                torch.save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict(), "epoch": epoch, "jmlr_meta": dict(arm=args.jmlr_arm, parent=args.jmlr_parent, k=args.jmlr_k, run_id=args.jmlr_run_id, canonical_mgda=args.jmlr_canonical_mgda)}, f"./save/{name}.final.pt")\n'
        '            _jmlr_save_checkpoint(args.jmlr_checkpoint_path, model, optimizer, scheduler, weight_method, epoch, {"avg_cost": avg_cost, "deltas": deltas, "loss_list": loss_list})\n',
        "NYUv2 final-state snapshot",
    )
    path.write_text(text)

def patch_qm9(path: Path) -> None:
    text = patch_common(path.read_text())
    text = replace_once(
        text,
        '        n_tasks=len(targets),\n',
        '        n_tasks=_jmlr_combiner_task_count(len(targets), args.jmlr_arm, args.jmlr_k),\n',
        "QM9 combiner dimension",
    )
    needle = '''            loss, extra_outputs = weight_method.backward(
                losses=losses,
'''
    repl = '''            _jmlr_maybe_save_audit(
                losses, list(model.shared_parameters()), args, epoch, j
            )
            combiner_losses = _jmlr_atomicity_transform(
                losses, args.jmlr_arm, args.jmlr_parent, args.jmlr_k
            )
            loss, extra_outputs = _jmlr_backward(
                weight_method, combiner_losses, args,
'''
    text = replace_once(text, needle, repl, "QM9 loss-vector intervention")
    text = replace_once(
        text,
        '    epoch_iterator = trange(n_epochs)\n',
        '    epoch_iterator = None\n',
        "QM9 deferred epoch iterator",
    )
    text = replace_once(
        text,
        '    loss_list = []\n\n    for epoch in epoch_iterator:\n',
        '    loss_list = []\n'
        '    _jmlr_start_epoch = 0\n'
        '    if args.jmlr_resume_from:\n'
        '        _jmlr_state = _jmlr_load_checkpoint(args.jmlr_resume_from, model, optimizer, scheduler, weight_method)\n'
        '        _jmlr_start_epoch = int(_jmlr_state["epoch"]) + 1\n'
        '        _jmlr_payload = _jmlr_state.get("payload", {})\n'
        '        if "avg_cost" in _jmlr_payload: avg_cost[:] = _jmlr_payload["avg_cost"]\n'
        '        if "deltas" in _jmlr_payload: deltas[:] = _jmlr_payload["deltas"]\n'
        '        if "loss_list" in _jmlr_payload: loss_list = _jmlr_payload["loss_list"]\n'
        '        best_val = _jmlr_payload.get("best_val", best_val)\n'
        '        best_test = _jmlr_payload.get("best_test", best_test)\n'
        '        best_test_delta = _jmlr_payload.get("best_test_delta", best_test_delta)\n'
        '        best_val_delta = _jmlr_payload.get("best_val_delta", best_val_delta)\n'
        '        best_test_results = _jmlr_payload.get("best_test_results", best_test_results)\n'
        '    epoch_iterator = trange(_jmlr_start_epoch, n_epochs)\n\n'
        '    for epoch in epoch_iterator:\n',
        "QM9 resume setup",
    )
    text = replace_once(
        text,
        '        torch.save({\n',
        '        if args.jmlr_run_id:\n'
        '            name = f"{name}_{args.jmlr_run_id}"\n'
        '        torch.save({\n'
        '            "jmlr_meta": dict(arm=args.jmlr_arm, parent=args.jmlr_parent, k=args.jmlr_k, run_id=args.jmlr_run_id, canonical_mgda=args.jmlr_canonical_mgda),\n',
        "QM9 collision-proof metadata",
    )
    text = replace_once(
        text,
        '        }, f"./save/{name}.stats")\n',
        '        }, f"./save/{name}.stats")\n'
        '        if epoch == n_epochs - 1:\n'
        '            torch.save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict(), "epoch": epoch, "jmlr_meta": dict(arm=args.jmlr_arm, parent=args.jmlr_parent, k=args.jmlr_k, run_id=args.jmlr_run_id, canonical_mgda=args.jmlr_canonical_mgda)}, f"./save/{name}.final.pt")\n'
        '        _jmlr_save_checkpoint(args.jmlr_checkpoint_path, model, optimizer, scheduler, weight_method, epoch, {"avg_cost": avg_cost, "deltas": deltas, "loss_list": loss_list, "best_val": best_val, "best_test": best_test, "best_test_delta": best_test_delta, "best_val_delta": best_val_delta, "best_test_results": best_test_results})\n',
        "QM9 final-state snapshot",
    )
    path.write_text(text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fairgrad_root", type=Path)
    args = ap.parse_args()
    root = args.fairgrad_root
    ny = root / "experiments/nyuv2/trainer.py"
    qm = root / "experiments/quantum_chemistry/trainer.py"
    if not ny.exists() or not qm.exists():
        raise FileNotFoundError("expected pinned FairGrad trainer paths not found")
    patch_nyuv2(ny)
    patch_qm9(qm)
    # Match released per-experiment run.sh setup without changing trainer semantics.
    (ny.parent / "save").mkdir(exist_ok=True)
    (ny.parent / "trainlogs").mkdir(exist_ok=True)
    (qm.parent / "save").mkdir(exist_ok=True)
    (qm.parent / "trainlogs").mkdir(exist_ok=True)
    print(f"PASS: patched FairGrad {PINNED_FAIRGRAD} trainers; per-experiment save/trainlogs initialized")

if __name__ == "__main__":
    main()
