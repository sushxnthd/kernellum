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
        '                torch.save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict(), "epoch": epoch, "jmlr_meta": dict(arm=args.jmlr_arm, parent=args.jmlr_parent, k=args.jmlr_k, run_id=args.jmlr_run_id, canonical_mgda=args.jmlr_canonical_mgda)}, f"./save/{name}.final.pt")\n',
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
        '            torch.save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "scheduler_state": scheduler.state_dict(), "epoch": epoch, "jmlr_meta": dict(arm=args.jmlr_arm, parent=args.jmlr_parent, k=args.jmlr_k, run_id=args.jmlr_run_id, canonical_mgda=args.jmlr_canonical_mgda)}, f"./save/{name}.final.pt")\n',
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
