#!/usr/bin/env python3
"""
ShiftGuard temporal EMBER2024 experiment.

Protocol
--------
* EMBER2024 PDF slice only (1,000 files/week, 64 chronological weeks).
* Weeks 1-40: train a deliberately compact classifier.
* Weeks 41-52: pre-deployment non-key calibration workload.
* Weeks 53-64: untouched future workload.
* Stored key set: all malicious PDFs from weeks 1-52.
* False-positive evaluation: benign queries only.

Memory accounting is conservative: serialized classifier/preprocessing bundle
+ all backup Bloom filters. The classical Bloom filter has no model cost.
"""

from __future__ import annotations

import bisect
import csv
import json
import math
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, date
from pathlib import Path

import joblib
import numpy as np
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

SEED = 20261026
BASE_DATE = date(2023, 9, 24)
BF_C = 1.0 / (math.log(2.0) ** 2)
TARGETS = [1e-2, 3e-3, 1e-3]
RHO_GRID = [0.0, 0.01, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30]
N_SEGMENTS = 1000
N_REGIONS = 5
TOP_FEATURES = 256
DELTA = 0.05
AUDIT_NS = [250, 500, 1000]

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("SHIFTGUARD_WORK", ROOT / ".shiftguard_work"))
DATA = WORK / "ember2024_pdf"
OUT = ROOT / "research" / "shiftguard" / "results"
MODEL_PATH = OUT / "compact_pdf_model.joblib"

rng = np.random.default_rng(SEED)


def log(msg: str) -> None:
    print(msg, flush=True)


def ensure_deps() -> None:
    """Clone the reference FastPLBF implementation if absent."""
    fast = WORK / "FastPLBF"
    if not fast.exists():
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/atsukisato/FastPLBF.git", str(fast)],
            check=True,
        )
    sys.path.insert(0, str(fast / "src"))


def parse_date(x) -> date:
    if x is None:
        raise ValueError("missing first_submission_date")
    if isinstance(x, (int, float)):
        # VirusTotal dates may be Unix seconds or milliseconds.
        v = float(x)
        if v > 1e12:
            v /= 1000.0
        return datetime.fromtimestamp(v, tz=timezone.utc).date()
    s = str(x).strip()
    if s.isdigit():
        return parse_date(int(s))
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        # YYYY-MM-DD prefix is sufficient for weekly binning.
        return date.fromisoformat(s[:10])


def week_index(d: date) -> int:
    return ((d - BASE_DATE).days // 7) + 1


def download_pdf() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    # If both splits are already present, reuse them.
    jsonls = list(DATA.rglob("*.jsonl"))
    names = [p.name.lower() for p in jsonls]
    if any("train" in n for n in names) and any("test" in n for n in names):
        log(f"Reusing {len(jsonls)} JSONL files")
        return
    import thrember
    log("Downloading official EMBER2024 PDF train split...")
    thrember.download_dataset(str(DATA), split="train", file_type="PDF")
    log("Downloading official EMBER2024 PDF test split...")
    thrember.download_dataset(str(DATA), split="test", file_type="PDF")


def discover_jsonls(split: str) -> list[Path]:
    candidates = sorted(DATA.rglob("*.jsonl"))
    out = []
    for p in candidates:
        s = str(p).lower()
        if "pdf" in s and split.lower() in s:
            out.append(p)
    if not out:
        # Some archive layouts put the split in a parent directory but omit PDF
        # from individual file names. Inspect one record before accepting.
        for p in candidates:
            s = str(p).lower()
            if split.lower() not in s:
                continue
            try:
                with p.open("r", encoding="utf-8") as f:
                    rec = json.loads(next(f))
                if str(rec.get("file_type", "")).lower() == "pdf":
                    out.append(p)
            except Exception:
                pass
    if not out:
        raise RuntimeError(f"No PDF {split} JSONL files found under {DATA}")
    log(f"{split}: {len(out)} JSONL files")
    for p in out[:8]:
        log(f"  {p}")
    return out


@dataclass
class SplitData:
    X: np.ndarray
    y: np.ndarray
    weeks: np.ndarray
    keys: list[str]


def load_split(paths: list[Path], extractor, split: str) -> SplitData:
    n = 0
    for p in paths:
        with p.open("r", encoding="utf-8") as f:
            n += sum(1 for _ in f)
    log(f"Vectorizing {split}: {n:,} rows x {extractor.dim} features")
    X = np.empty((n, extractor.dim), dtype=np.float32)
    y = np.empty(n, dtype=np.int8)
    weeks = np.empty(n, dtype=np.int16)
    keys: list[str] = [""] * n

    j = 0
    for p in paths:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                X[j] = extractor.process_raw_features(rec)
                lab = rec.get("label")
                y[j] = -1 if lab is None else int(lab)
                d = parse_date(rec.get("first_submission_date"))
                weeks[j] = week_index(d)
                keys[j] = str(rec.get("sha256") or f"{split}-{j}")
                j += 1
                if j % 10000 == 0:
                    log(f"  vectorized {j:,}/{n:,}")
    return SplitData(X=X, y=y, weeks=weeks, keys=keys)


def train_compact_model(train: SplitData):
    mask = (train.weeks >= 1) & (train.weeks <= 40) & (train.y >= 0)
    m0 = mask & (train.y == 0)
    m1 = mask & (train.y == 1)
    if m0.sum() == 0 or m1.sum() == 0:
        raise RuntimeError("Training window lacks both classes")

    # Supervised univariate selection using standardized mean difference.
    mu0 = train.X[m0].mean(axis=0, dtype=np.float64)
    mu1 = train.X[m1].mean(axis=0, dtype=np.float64)
    sd = train.X[mask].std(axis=0, dtype=np.float64)
    effect = np.abs(mu1 - mu0) / (sd + 1e-6)
    effect[~np.isfinite(effect)] = 0.0
    idx = np.argsort(effect)[-TOP_FEATURES:].astype(np.int32)

    Xfit = train.X[mask][:, idx].astype(np.float64, copy=False)
    yfit = train.y[mask].astype(np.int32, copy=False)
    scaler = StandardScaler()
    Xz = scaler.fit_transform(Xfit)
    clf = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=800,
        solver="lbfgs",
        random_state=SEED,
    )
    clf.fit(Xz, yfit)

    OUT.mkdir(parents=True, exist_ok=True)
    bundle = {"feature_idx": idx, "scaler": scaler, "classifier": clf}
    joblib.dump(bundle, MODEL_PATH, compress=0)
    model_bytes = MODEL_PATH.stat().st_size
    log(f"Compact model serialized size: {model_bytes:,} bytes")

    train_scores = clf.predict_proba(scaler.transform(train.X[:, idx]))[:, 1]
    auc = roc_auc_score(train.y[mask], train_scores[mask])
    log(f"Weeks 1-40 in-window AUC: {auc:.6f}")
    return idx, scaler, clf, train_scores, int(model_bytes), float(auc)


def score_data(data: SplitData, idx, scaler, clf) -> np.ndarray:
    return clf.predict_proba(scaler.transform(data.X[:, idx]))[:, 1]


def region_idx(scores: np.ndarray, thresholds: list[float]) -> np.ndarray:
    # Mirror FastPLBF: bisect_left, with score 0 assigned to region 1.
    arr = np.searchsorted(np.asarray(thresholds), scores, side="left")
    arr[arr == 0] = 1
    k = len(thresholds) - 1
    arr = np.clip(arr, 1, k)
    return arr.astype(np.int16)


def masses(scores: np.ndarray, thresholds: list[float]) -> np.ndarray:
    ridx = region_idx(scores, thresholds)
    k = len(thresholds) - 1
    cnt = np.bincount(ridx, minlength=k + 1)[1 : k + 1].astype(float)
    if cnt.sum() == 0:
        raise RuntimeError("empty score population")
    return cnt / cnt.sum()


def tv(a: np.ndarray, b: np.ndarray) -> float:
    return 0.5 * float(np.abs(np.asarray(a) - np.asarray(b)).sum())


def worst_case_tv(h: np.ndarray, f: np.ndarray, rho: float):
    """Exact linear maximization max_q q·f s.t. TV(q,h)<=rho."""
    h = np.asarray(h, dtype=float)
    f = np.asarray(f, dtype=float)
    q = h.copy()
    budget = float(max(0.0, rho))
    donors = list(np.argsort(f))          # remove from lowest f
    recvs = list(np.argsort(-f))         # add to highest f
    di = ri = 0
    while budget > 1e-14 and di < len(donors) and ri < len(recvs):
        d = donors[di]
        r = recvs[ri]
        if f[r] <= f[d] + 1e-15:
            break
        removable = q[d]
        capacity = 1.0 - q[r]
        move = min(budget, removable, capacity)
        if move > 0:
            q[d] -= move
            q[r] += move
            budget -= move
        if q[d] <= 1e-14:
            di += 1
        if 1.0 - q[r] <= 1e-14:
            ri += 1
        if move <= 1e-16:
            if removable <= 1e-14:
                di += 1
            elif capacity <= 1e-14:
                ri += 1
            else:
                break
    return float(q @ f), q


def robust_allocation(g: np.ndarray, h: np.ndarray, F: float, rho: float):
    """Convex cutting-plane solve in x_i=-log(f_i)."""
    g = np.asarray(g, dtype=float)
    h = np.asarray(h, dtype=float)
    k = len(g)
    cuts = [h.copy()]
    x0 = np.full(k, -math.log(F), dtype=float)

    def obj(x):
        return BF_C * float(g @ x)

    def jac_obj(x):
        return BF_C * g

    for it in range(60):
        cons = []
        for q in cuts:
            q = q.copy()
            cons.append({
                "type": "ineq",
                "fun": lambda x, q=q: F - float(q @ np.exp(-x)),
                "jac": lambda x, q=q: q * np.exp(-x),
            })
        res = minimize(
            obj,
            x0,
            jac=jac_obj,
            method="SLSQP",
            bounds=[(0.0, 40.0)] * k,
            constraints=cons,
            options={"maxiter": 2000, "ftol": 1e-12, "disp": False},
        )
        if not res.success:
            raise RuntimeError(f"robust optimizer failed at rho={rho}: {res.message}")
        x = res.x
        f = np.exp(-x)
        wc, qstar = worst_case_tv(h, f, rho)
        if wc <= F * (1 + 1e-7) + 1e-12:
            return f, x, wc, len(cuts)
        cuts.append(qstar)
        x0 = x
    raise RuntimeError("cutting-plane solver did not converge")


def build_regional_filters(keys, scores, thresholds, f):
    from bloom_filter import BloomFilter
    k = len(thresholds) - 1
    idx = region_idx(np.asarray(scores), thresholds)
    filters = [None] * k
    always_true = [False] * k
    members = [[] for _ in range(k)]
    for key, r in zip(keys, idx):
        members[int(r) - 1].append(key)

    for i in range(k):
        n = len(members[i])
        if n == 0:
            filters[i] = None  # empty region: always reject
        elif f[i] >= 1.0 - 1e-12:
            always_true[i] = True
        else:
            er = float(np.clip(f[i], 1e-9, 1 - 1e-9))
            bf = BloomFilter(max_elements=max(1, n), error_rate=er)
            for key in members[i]:
                bf.add(key)
            filters[i] = bf
    return filters, always_true


def empirical_fpr(keys, scores, thresholds, filters, always_true):
    idx = region_idx(np.asarray(scores), thresholds)
    fp = 0
    for key, r in zip(keys, idx):
        i = int(r) - 1
        if always_true[i]:
            fp += 1
        elif filters[i] is None:
            pass
        elif key in filters[i]:
            fp += 1
    return fp / max(1, len(keys)), int(fp)


def multinomial_tv_radius(n: int, k: int, delta: float = DELTA) -> float:
    # Weissman/Bretagnolle-Huber-Carol L1 concentration:
    # P(||p_hat-p||_1 >= eps) <= (2^k-2) exp(-n eps^2/2).
    factor = max(2**k - 2, 1)
    eps = math.sqrt((2.0 / n) * math.log(factor / delta))
    return min(1.0, eps / 2.0)


def weekly_distributions(test_scores, test_weeks, thresholds):
    out = {}
    for w in sorted(set(int(x) for x in test_weeks)):
        s = test_scores[test_weeks == w]
        if len(s):
            out[w] = masses(s, thresholds)
    return out


def audit_upper_radii(test_scores, test_weeks, h, thresholds, n):
    k = len(h)
    conf = multinomial_tv_radius(n, k, DELTA)
    rows = []
    for w in sorted(set(int(x) for x in test_weeks)):
        s = test_scores[test_weeks == w]
        if len(s) == 0:
            continue
        take = min(n, len(s))
        rr = np.random.default_rng(SEED + w * 10000 + n)
        sel = rr.choice(len(s), size=take, replace=False)
        phat = masses(s[sel], thresholds)
        center_dist = tv(h, phat)
        upper = min(1.0, center_dist + multinomial_tv_radius(take, k, DELTA))
        rows.append({
            "week": w,
            "n": int(take),
            "tv_hat": center_dist,
            "confidence_radius": multinomial_tv_radius(take, k, DELTA),
            "upper_rho_95": upper,
        })
    return rows


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    ensure_deps()
    from PLBFs.FastPLBF import FastPLBF
    from thrember.features import PEFeatureExtractor

    download_pdf()
    train_paths = discover_jsonls("train")
    test_paths = discover_jsonls("test")

    extractor = PEFeatureExtractor()
    train = load_split(train_paths, extractor, "train")
    test = load_split(test_paths, extractor, "test")

    train_weeks = sorted(set(int(x) for x in train.weeks))
    test_weeks = sorted(set(int(x) for x in test.weeks))
    log(f"Train week range: {train_weeks[:3]} ... {train_weeks[-3:]}")
    log(f"Test week range: {test_weeks[:3]} ... {test_weeks[-3:]}")
    if min(train_weeks) > 1 or max(train_weeks) < 52:
        raise RuntimeError(f"Unexpected train weeks: {train_weeks}")
    if min(test_weeks) < 53 or max(test_weeks) < 64:
        raise RuntimeError(f"Unexpected test weeks: {test_weeks}")

    idx, scaler, clf, train_scores, model_bytes, train_auc = train_compact_model(train)
    test_scores = score_data(test, idx, scaler, clf)
    labeled_test = test.y >= 0
    test_auc = roc_auc_score(test.y[labeled_test], test_scores[labeled_test])
    log(f"Future weeks 53-64 AUC: {test_auc:.6f}")

    key_mask = (train.weeks <= 52) & (train.y == 1)
    cal_mask = (train.weeks >= 41) & (train.weeks <= 52) & (train.y == 0)
    future_benign = (test.weeks >= 53) & (test.weeks <= 64) & (test.y == 0)

    pos_keys = [k for k, m in zip(train.keys, key_mask) if m]
    pos_scores = train_scores[key_mask].astype(float)
    cal_scores = train_scores[cal_mask].astype(float)
    future_scores = test_scores[future_benign].astype(float)
    future_keys = [k for k, m in zip(test.keys, future_benign) if m]
    future_weeks = test.weeks[future_benign]

    meta = {
        "seed": SEED,
        "dataset": "EMBER2024 official PDF slice",
        "protocol": {
            "classifier_train_weeks": "1-40",
            "calibration_weeks": "41-52 benign only",
            "stored_keys": "all malicious samples from weeks 1-52",
            "future_test_weeks": "53-64 benign only for FPR",
        },
        "counts": {
            "train_rows": int(len(train.y)),
            "test_rows": int(len(test.y)),
            "model_train_rows": int(((train.weeks <= 40) & (train.y >= 0)).sum()),
            "stored_keys": int(len(pos_keys)),
            "calibration_benign": int(len(cal_scores)),
            "future_benign": int(len(future_scores)),
        },
        "model": {
            "top_features": TOP_FEATURES,
            "serialized_bytes": model_bytes,
            "train_auc_weeks_1_40": train_auc,
            "future_auc_weeks_53_64": float(test_auc),
        },
        "targets": TARGETS,
        "rho_grid": RHO_GRID,
        "N_segments": N_SEGMENTS,
        "k_regions": N_REGIONS,
    }

    result_rows = []
    audit_rows_all = []
    summary = {"meta": meta, "targets": {}}

    for F in TARGETS:
        log(f"\n=== Target FPR {F:.6g} ===")
        plbf = FastPLBF(
            list(pos_keys),
            list(map(float, pos_scores)),
            list(map(float, cal_scores)),
            float(F),
            int(N_SEGMENTS),
            int(N_REGIONS),
        )
        thresholds = [float(x) for x in plbf.t]
        f_nom = np.array(plbf.f[1:], dtype=float)
        g = masses(pos_scores, thresholds)
        h = masses(cal_scores, thresholds)
        h_future = masses(future_scores, thresholds)
        future_tv = tv(h, h_future)
        weekly = weekly_distributions(future_scores, future_weeks, thresholds)
        weekly_tvs = {int(w): tv(h, p) for w, p in weekly.items()}
        max_week_tv = max(weekly_tvs.values())

        classical_bpk = -math.log(F) / (math.log(2.0) ** 2)
        classical_bits = classical_bpk * len(pos_keys)

        nominal_backup_bits = float(plbf.memory_usage_of_backup_bf)
        nominal_total_bits = nominal_backup_bits + model_bytes * 8
        nominal_saving = 1.0 - nominal_total_bits / classical_bits
        nominal_expected_future = float(h_future @ f_nom)
        nominal_expected_cal = float(h @ f_nom)
        nominal_emp, nominal_fp = empirical_fpr(
            future_keys, future_scores, thresholds,
            plbf.backup_bloom_filters[1:], [x is None for x in []]
        ) if False else (None, None)

        # PLBF's contains() is the strongest direct empirical baseline.
        fp = 0
        for key, score in zip(future_keys, future_scores):
            if plbf.contains(key, float(score)):
                fp += 1
        nominal_emp = fp / max(1, len(future_keys))
        nominal_fp = fp

        target_obj = {
            "thresholds": thresholds,
            "g_key_mass": g.tolist(),
            "h_calibration_nonkey_mass": h.tolist(),
            "h_future_nonkey_mass": h_future.tolist(),
            "future_tv_overall": future_tv,
            "future_tv_by_week": weekly_tvs,
            "max_future_week_tv": max_week_tv,
            "classical_bpk": classical_bpk,
            "classical_total_bits": classical_bits,
            "nominal_plbf": {
                "region_fpr": f_nom.tolist(),
                "backup_bits": nominal_backup_bits,
                "model_bits": model_bytes * 8,
                "total_bits": nominal_total_bits,
                "memory_saving_vs_classical": nominal_saving,
                "calibration_expected_fpr": nominal_expected_cal,
                "future_expected_fpr": nominal_expected_future,
                "future_empirical_fpr": nominal_emp,
                "future_false_positives": nominal_fp,
            },
            "shiftguard": [],
            "audits": {},
        }

        for n in AUDIT_NS:
            audits = audit_upper_radii(future_scores, future_weeks, h, thresholds, n)
            target_obj["audits"][str(n)] = audits
            for a in audits:
                aa = dict(a)
                aa["target_fpr"] = F
                audit_rows_all.append(aa)

        dynamic_rhos = sorted(set(
            RHO_GRID
            + [min(0.95, math.ceil(max_week_tv * 1000) / 1000)]
            + [
                min(
                    0.95,
                    math.ceil(max(a["upper_rho_95"] for a in target_obj["audits"]["1000"]) * 1000) / 1000,
                )
            ]
        ))

        for rho in dynamic_rhos:
            f_rob, x_rob, wc, cuts = robust_allocation(g, h, F, rho)
            backup_bits = BF_C * len(pos_keys) * float(g @ x_rob)
            total_bits = backup_bits + model_bytes * 8
            saving = 1.0 - total_bits / classical_bits
            exp_future = float(h_future @ f_rob)

            filters, always_true = build_regional_filters(pos_keys, pos_scores, thresholds, f_rob)
            emp, emp_fp = empirical_fpr(
                future_keys, future_scores, thresholds, filters, always_true
            )
            certifies_exact_future = future_tv <= rho + 1e-12
            certified_weeks_exact = sum(v <= rho + 1e-12 for v in weekly_tvs.values())

            audits1000 = target_obj["audits"]["1000"]
            certified_weeks_audit = sum(a["upper_rho_95"] <= rho + 1e-12 for a in audits1000)

            row = {
                "target_fpr": F,
                "rho": rho,
                "backup_bits": backup_bits,
                "model_bits": model_bytes * 8,
                "total_bits": total_bits,
                "memory_saving_vs_classical": saving,
                "worst_case_certified_fpr": wc,
                "future_expected_fpr": exp_future,
                "future_empirical_fpr": emp,
                "future_false_positives": emp_fp,
                "future_tv_overall": future_tv,
                "max_future_week_tv": max_week_tv,
                "certifies_overall_future_exact": certifies_exact_future,
                "certified_weeks_exact": certified_weeks_exact,
                "certified_weeks_audit_n1000": certified_weeks_audit,
                "cuts": cuts,
                "region_fpr": f_rob.tolist(),
            }
            target_obj["shiftguard"].append(row)
            result_rows.append(row)
            log(
                f"rho={rho:.3f} save={saving*100:6.2f}% "
                f"wc={wc:.6g} future_exp={exp_future:.6g} "
                f"future_emp={emp:.6g} cert_weeks={certified_weeks_audit}/12"
            )

        summary["targets"][str(F)] = target_obj
        log(
            f"Nominal PLBF: save={nominal_saving*100:.2f}% "
            f"cal_exp={nominal_expected_cal:.6g} future_exp={nominal_expected_future:.6g} "
            f"future_emp={nominal_emp:.6g}; future TV={future_tv:.4f}, max weekly TV={max_week_tv:.4f}"
        )

    # Decisive pre-registered decision rule.
    # A) problem must be real on this temporal benchmark,
    # B) robust/certified utility must remain materially below classical memory,
    # C) 1,000-query 95% audit must be able to certify all 12 weeks with useful memory.
    decision = {}
    nominal_violations = []
    for F in TARGETS:
        nom = summary["targets"][str(F)]["nominal_plbf"]
        ratio = nom["future_expected_fpr"] / F
        nominal_violations.append(ratio)
    criterion_problem = max(nominal_violations) >= 1.25

    best_certified = {}
    for F in TARGETS:
        arr = summary["targets"][str(F)]["shiftguard"]
        feasible = [r for r in arr if r["certified_weeks_audit_n1000"] == 12]
        if feasible:
            best = max(feasible, key=lambda r: r["memory_saving_vs_classical"])
            best_certified[str(F)] = best
        else:
            best_certified[str(F)] = None

    b1 = best_certified[str(1e-2)]
    strict = [best_certified[str(3e-3)], best_certified[str(1e-3)]]
    criterion_memory = (
        b1 is not None
        and b1["memory_saving_vs_classical"] >= 0.15
        and any(x is not None and x["memory_saving_vs_classical"] >= 0.10 for x in strict)
    )
    criterion_certificate = all(
        best_certified[str(F)] is not None for F in TARGETS
    )

    decision = {
        "criterion_problem_real": {
            "pass": bool(criterion_problem),
            "rule": "At least one nominal PLBF future expected FPR >= 1.25x its target.",
            "ratios_by_target": {str(F): summary["targets"][str(F)]["nominal_plbf"]["future_expected_fpr"] / F for F in TARGETS},
        },
        "criterion_certified_memory": {
            "pass": bool(criterion_memory),
            "rule": "With 95% finite-sample certification from <=1000 benign audit queries/week: >=15% total-memory saving at F=1%, and >=10% at one stricter target.",
            "best_fully_certified_by_target": best_certified,
        },
        "criterion_certificate_availability": {
            "pass": bool(criterion_certificate),
            "rule": "A tested robustness radius certifies all 12 future weeks at 95% confidence with n<=1000/week for every target.",
        },
    }
    promote = criterion_problem and criterion_memory and criterion_certificate
    decision["verdict"] = "PROMOTE" if promote else "KILL_OR_PIVOT"
    summary["decision"] = decision

    with (OUT / "ember2024_temporal_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    if result_rows:
        cols = [k for k in result_rows[0].keys() if k != "region_fpr"]
        with (OUT / "shiftguard_curve.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for row in result_rows:
                w.writerow({k: row[k] for k in cols})

    if audit_rows_all:
        with (OUT / "audit_certificates.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(audit_rows_all[0].keys()))
            w.writeheader()
            w.writerows(audit_rows_all)

    # Compact human-readable result for the fair paper / audit trail.
    lines = [
        "# ShiftGuard EMBER2024 temporal experiment",
        "",
        f"Verdict: **{decision['verdict']}**",
        "",
        f"- Stored keys: {len(pos_keys):,}",
        f"- Calibration benign queries: {len(cal_scores):,}",
        f"- Untouched future benign queries: {len(future_scores):,}",
        f"- Compact model size: {model_bytes:,} bytes",
        f"- Future classifier AUC: {test_auc:.6f}",
        "",
        "## Pre-registered kill criteria",
        "",
    ]
    for name, obj in decision.items():
        if name == "verdict":
            continue
        lines += [f"- **{name}**: {'PASS' if obj['pass'] else 'FAIL'} — {obj['rule']}"]
    lines += ["", "## Target summaries", ""]
    for F in TARGETS:
        t = summary["targets"][str(F)]
        n = t["nominal_plbf"]
        best = best_certified[str(F)]
        lines += [
            f"### F={F:g}",
            f"- Nominal PLBF total-memory saving: {n['memory_saving_vs_classical']*100:.2f}%",
            f"- Nominal calibration expected FPR: {n['calibration_expected_fpr']:.6g}",
            f"- Nominal future expected FPR: {n['future_expected_fpr']:.6g}",
            f"- Nominal future empirical FPR: {n['future_empirical_fpr']:.6g}",
            f"- Overall future TV shift: {t['future_tv_overall']:.4f}",
            f"- Maximum weekly TV shift: {t['max_future_week_tv']:.4f}",
        ]
        if best:
            lines += [
                f"- Best fully audit-certified rho: {best['rho']:.3f}",
                f"- Certified total-memory saving: {best['memory_saving_vs_classical']*100:.2f}%",
                f"- Certified worst-case FPR: {best['worst_case_certified_fpr']:.6g}",
                f"- Actual future expected FPR: {best['future_expected_fpr']:.6g}",
            ]
        else:
            lines += ["- No tested rho fully certified all 12 weeks with the n=1000 audit."]
        lines += [""]

    (OUT / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    log("\n" + "\n".join(lines))
    log(f"Results written to {OUT}")


if __name__ == "__main__":
    main()
