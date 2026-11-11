#!/usr/bin/env python3
"""
Pinned MoleculeNet task-multiplicity benchmark for the JMLR manuscript.

Design
------
- Canonical public MoleculeNet Tox21 and SIDER CSVs.
- RDKit Morgan fingerprints: radius=2, 256 bits.
- Shared tanh MLP trunk (256 -> 32) with one logistic head per task.
- Missing-label masking and train-set positive-class reweighting.
- Full-batch Adam, fixed 80 epochs, no early stopping or per-condition tuning.
- Random and Bemis-Murcko scaffold splits (80/10/10).
- Paired seeds 0..4.
- Semantic task weights are normalized over task identities.
  Multiplicity k changes only the target semantic coefficient from 1 to k,
  exactly matching k equal represented child identities under the paper's
  equal-identity aggregation theorem.

The script records data SHA256s, software versions, exact configuration,
per-seed AUCs, and aggregate paired differences.
"""

from __future__ import annotations
import csv
import gzip
import hashlib
import json
import math
import os
import platform
import random
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import roc_auc_score

from rdkit import Chem, rdBase
from rdkit.Chem.Scaffolds import MurckoScaffold
try:
    from rdkit.Chem import rdFingerprintGenerator
except Exception:
    rdFingerprintGenerator = None
from rdkit import DataStructs
from rdkit.Chem import AllChem

URLS = {
    "tox21": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz",
    "sider": "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/sider.csv.gz",
}
TARGETS = {
    "tox21": ["SR-ARE"],
    "sider": ["Hepatobiliary disorders", "Reproductive system and breast disorders"],
}
CONFIG = {
    "fingerprint_radius": 2,
    "fingerprint_bits": 256,
    "hidden_dim": 32,
    "activation": "tanh",
    "optimizer": "adam",
    "learning_rate": 0.01,
    "adam_beta1": 0.9,
    "adam_beta2": 0.999,
    "adam_eps": 1e-8,
    "epochs": 80,
    "split_fractions": [0.8, 0.1, 0.1],
    "seeds": [0, 1, 2, 3, 4],
    "multiplicities": [1, 2, 4, 8],
    "splits": ["random", "scaffold"],
    "class_weighting": "positive_weight=n_negative/n_positive per task on training split",
    "loss_reduction": "per-task weighted BCE mean over labeled training examples",
    "semantic_weighting": "normalized equal identity weights; target coefficient multiplied by k",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 1000:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "task-multiplicity-jmlr-repro/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, path.open("wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)

def fingerprint(smiles: str, nbits: int, radius: int) -> np.ndarray | None:
    mol = Chem.MolFromSmiles(str(smiles))
    if mol is None:
        return None
    if rdFingerprintGenerator is not None:
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=nbits)
        fp = gen.GetFingerprint(mol)
    else:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
    arr = np.zeros((nbits,), dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr.astype(np.float32)

def scaffold(smiles: str) -> str:
    mol = Chem.MolFromSmiles(str(smiles))
    if mol is None:
        return "__invalid__"
    s = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
    return s if s else "__acyclic__:" + Chem.MolToSmiles(mol, canonical=True)

def load_dataset(name: str, path: Path):
    df = pd.read_csv(path, compression="gzip")
    smiles_col = "smiles"
    if smiles_col not in df.columns:
        raise RuntimeError(f"{name}: no smiles column; columns={list(df.columns)}")
    label_cols = [c for c in df.columns if c not in {smiles_col, "mol_id"}]
    X, Y, smiles_kept = [], [], []
    for _, row in df.iterrows():
        fp = fingerprint(row[smiles_col], CONFIG["fingerprint_bits"], CONFIG["fingerprint_radius"])
        if fp is None:
            continue
        X.append(fp)
        vals = []
        for c in label_cols:
            v = row[c]
            vals.append(np.nan if pd.isna(v) else float(v))
        Y.append(vals)
        smiles_kept.append(str(row[smiles_col]))
    X = np.asarray(X, dtype=np.float32)
    Y = np.asarray(Y, dtype=np.float32)
    return X, Y, smiles_kept, label_cols

def random_split(n: int, seed: int):
    rng = np.random.default_rng(seed)
    p = rng.permutation(n)
    ntr = int(math.floor(0.8 * n))
    nv = int(math.floor(0.1 * n))
    return p[:ntr], p[ntr:ntr+nv], p[ntr+nv:]

def scaffold_split(smiles):
    groups = {}
    for i, s in enumerate(smiles):
        groups.setdefault(scaffold(s), []).append(i)
    sets = sorted(groups.values(), key=lambda g: (-len(g), g[0]))
    n = len(smiles)
    train_cutoff = 0.8 * n
    valid_cutoff = 0.9 * n
    tr, va, te = [], [], []
    for g in sets:
        if len(tr) + len(g) <= train_cutoff:
            tr.extend(g)
        elif len(tr) + len(va) + len(g) <= valid_cutoff:
            va.extend(g)
        else:
            te.extend(g)
    return np.asarray(tr, int), np.asarray(va, int), np.asarray(te, int)

def sigmoid(x):
    x = np.clip(x, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-x))

class Adam:
    def __init__(self, params):
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0
    def step(self, params, grads):
        self.t += 1
        lr = CONFIG["learning_rate"]
        b1 = CONFIG["adam_beta1"]; b2 = CONFIG["adam_beta2"]; eps = CONFIG["adam_eps"]
        for k in params:
            g = grads[k]
            self.m[k] = b1 * self.m[k] + (1 - b1) * g
            self.v[k] = b2 * self.v[k] + (1 - b2) * (g * g)
            mh = self.m[k] / (1 - b1 ** self.t)
            vh = self.v[k] / (1 - b2 ** self.t)
            params[k] -= lr * mh / (np.sqrt(vh) + eps)

def init_params(d, h, t, seed):
    rng = np.random.default_rng(100000 + seed)
    return {
        "W": (rng.normal(size=(d, h)) / math.sqrt(d)).astype(np.float32),
        "b": np.zeros(h, np.float32),
        "V": (rng.normal(size=(h, t)) / math.sqrt(h)).astype(np.float32),
        "c": np.zeros(t, np.float32),
    }

def class_pos_weights(Ytr):
    out = np.ones(Ytr.shape[1], np.float32)
    for t in range(Ytr.shape[1]):
        m = ~np.isnan(Ytr[:, t])
        y = Ytr[m, t]
        pos = float(np.sum(y == 1)); neg = float(np.sum(y == 0))
        if pos > 0 and neg > 0:
            out[t] = np.float32(neg / pos)
    return out

def train_model(X, Y, train_idx, target_idx, multiplicity, seed):
    Xtr = X[train_idx].astype(np.float32)
    Ytr = Y[train_idx].astype(np.float32)
    n, d = Xtr.shape; T = Ytr.shape[1]; h = CONFIG["hidden_dim"]
    params = init_params(d, h, T, seed)
    opt = Adam(params)
    posw = class_pos_weights(Ytr)
    q = np.ones(T, dtype=np.float32)
    q[target_idx] = float(multiplicity)
    q /= q.sum()

    for _epoch in range(CONFIG["epochs"]):
        z = Xtr @ params["W"] + params["b"]
        H = np.tanh(z)
        logits = H @ params["V"] + params["c"]
        P = sigmoid(logits).astype(np.float32)

        dlog = np.zeros_like(P, dtype=np.float32)
        for t in range(T):
            m = ~np.isnan(Ytr[:, t])
            nv = int(np.sum(m))
            if nv == 0:
                continue
            y = Ytr[m, t]
            p = P[m, t]
            g = p.copy()
            pos = y > 0.5
            g[pos] = posw[t] * (p[pos] - 1.0)
            g[~pos] = p[~pos]
            dlog[m, t] = q[t] * g / float(nv)

        gV = H.T @ dlog
        gc = dlog.sum(axis=0)
        dH = dlog @ params["V"].T
        dz = dH * (1.0 - H * H)
        gW = Xtr.T @ dz
        gb = dz.sum(axis=0)
        grads = {"W": gW, "b": gb, "V": gV, "c": gc}
        opt.step(params, grads)
    return params

def predict(params, X):
    H = np.tanh(X.astype(np.float32) @ params["W"] + params["b"])
    return sigmoid(H @ params["V"] + params["c"])

def aucs(Y, P, idx):
    vals = []
    for t in range(Y.shape[1]):
        y = Y[idx, t]
        p = P[idx, t]
        m = ~np.isnan(y)
        yy = y[m]
        if len(yy) == 0 or len(np.unique(yy)) < 2:
            vals.append(float("nan"))
        else:
            vals.append(float(roc_auc_score(yy, p[m])))
    return vals

def mean_finite(xs):
    a = np.asarray(xs, float)
    return float(np.nanmean(a)) if np.any(np.isfinite(a)) else float("nan")

def target_index(cols, desired):
    if desired in cols:
        return cols.index(desired)
    low = desired.lower()
    matches = [i for i, c in enumerate(cols) if low in c.lower()]
    if len(matches) == 1:
        return matches[0]
    raise RuntimeError(f"Target {desired!r} not uniquely found in columns: {cols}")

def main(outdir: str):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    data_dir = out / "data"
    data_dir.mkdir(exist_ok=True)
    manifest = {
        "config": CONFIG,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
        "rdkit": rdBase.rdkitVersion,
        "data": {},
    }
    rows = []
    for name, url in URLS.items():
        path = data_dir / f"{name}.csv.gz"
        download(url, path)
        manifest["data"][name] = {
            "url": url,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        X, Y, smiles, cols = load_dataset(name, path)
        manifest["data"][name].update({
            "n_molecules_after_valid_smiles": len(X),
            "n_tasks": len(cols),
            "task_names": cols,
        })
        scaffold_idx = scaffold_split(smiles)

        for target in TARGETS[name]:
            ti = target_index(cols, target)
            for split_name in CONFIG["splits"]:
                for seed in CONFIG["seeds"]:
                    if split_name == "random":
                        tr, va, te = random_split(len(X), seed)
                    else:
                        tr, va, te = scaffold_idx
                    # Record split hashes for exact replay.
                    split_hash = hashlib.sha256(
                        np.asarray(np.concatenate([tr, [-1], va, [-2], te]), dtype=np.int64).tobytes()
                    ).hexdigest()
                    for k in CONFIG["multiplicities"]:
                        params = train_model(X, Y, tr, ti, k, seed)
                        P = predict(params, X)
                        test_auc = aucs(Y, P, te)
                        val_auc = aucs(Y, P, va)
                        peer = [x for j, x in enumerate(test_auc) if j != ti]
                        rows.append({
                            "dataset": name,
                            "target": target,
                            "target_index": ti,
                            "split": split_name,
                            "seed": seed,
                            "multiplicity": k,
                            "n_train": int(len(tr)),
                            "n_valid": int(len(va)),
                            "n_test": int(len(te)),
                            "split_sha256": split_hash,
                            "target_test_auc": test_auc[ti],
                            "peer_mean_test_auc": mean_finite(peer),
                            "all_mean_test_auc": mean_finite(test_auc),
                            "target_valid_auc": val_auc[ti],
                            "test_aucs": test_auc,
                        })
                        print("DONE", name, target, split_name, seed, k,
                              f"target={test_auc[ti]:.6f}", f"peer={mean_finite(peer):.6f}",
                              flush=True)

    pd.DataFrame(rows).to_csv(out / "per_run.csv", index=False)
    (out / "per_run.json").write_text(json.dumps(rows, indent=2))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # Paired summaries against k=1 for each dataset/target/split.
    summaries = []
    df = pd.DataFrame(rows)
    for (ds, target, split), g in df.groupby(["dataset", "target", "split"]):
        base = g[g.multiplicity == 1].set_index("seed")
        for k in [2, 4, 8]:
            cur = g[g.multiplicity == k].set_index("seed")
            common = sorted(set(base.index) & set(cur.index))
            td = np.array([cur.loc[s, "target_test_auc"] - base.loc[s, "target_test_auc"] for s in common], float)
            pdiff = np.array([cur.loc[s, "peer_mean_test_auc"] - base.loc[s, "peer_mean_test_auc"] for s in common], float)
            ad = np.array([cur.loc[s, "all_mean_test_auc"] - base.loc[s, "all_mean_test_auc"] for s in common], float)
            summaries.append({
                "dataset": ds, "target": target, "split": split, "multiplicity": k,
                "n_seeds": len(common),
                "target_delta_mean": float(np.mean(td)),
                "target_delta_sd": float(np.std(td, ddof=1)) if len(td)>1 else 0.0,
                "peer_delta_mean": float(np.mean(pdiff)),
                "peer_delta_sd": float(np.std(pdiff, ddof=1)) if len(pdiff)>1 else 0.0,
                "all_delta_mean": float(np.mean(ad)),
                "per_seed_target_delta": td.tolist(),
                "per_seed_peer_delta": pdiff.tolist(),
            })
    (out / "summary.json").write_text(json.dumps(summaries, indent=2))
    pd.DataFrame(summaries).to_csv(out / "summary.csv", index=False)
    print(json.dumps(summaries, indent=2))

if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "molecular_results"
    main(outdir)
