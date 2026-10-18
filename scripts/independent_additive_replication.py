"""Independent reconstruction of the additive-response exponential fit.

This file deliberately does not import ``fit_exp``, ``value_jacobian`` or the
candidate runner.  It consumes only the immutable public arrays/traces and uses
a separately written moment initializer plus scipy.optimize.minimize.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import least_squares, minimize


ROOT = Path(__file__).resolve().parents[1]


def _lower(theta: np.ndarray, dimension: int) -> np.ndarray:
    out = np.zeros((dimension, dimension), dtype=float)
    out[np.tril_indices(dimension)] = theta[1 + dimension :]
    return out


def mean(theta: np.ndarray, x: np.ndarray, family: str, ceiling: float) -> np.ndarray:
    """Evaluate the written-specification mean with no candidate-code calls."""
    dimension = x.shape[1]
    exponent = theta[0] + x @ theta[1 : 1 + dimension]
    if family == "exp_concave":
        projected = x @ _lower(theta, dimension)
        exponent = exponent - np.einsum("ij,ij->i", projected, projected)
    return np.exp(np.minimum(exponent, ceiling))


def moment_start(x: np.ndarray, target: np.ndarray, family: str) -> np.ndarray:
    """Build a deterministic log-shape seed, then optimize the measured response."""
    dimension = x.shape[1]
    positive = np.maximum(target, 0.0)
    positive += max(float(np.max(np.abs(target))) * 1e-8, 1e-12)
    log_target = np.log(positive)
    if family == "exp_affine":
        return np.linalg.lstsq(np.column_stack((np.ones(len(x)), x)), log_target, rcond=None)[0]

    # Estimate the entire symmetric log-quadratic, project only its curvature
    # into the concave cone, then refit intercept/slope conditional on that
    # projection. This derivation and parameterization are independent of the
    # candidate's triangular-coefficient initializer.
    features = [np.ones(len(x)), *[x[:, j] for j in range(dimension)]]
    pairs = []
    for row in range(dimension):
        for col in range(row + 1):
            pairs.append((row, col))
            features.append(-(x[:, row] * x[:, col]) if row == col else -(2.0 * x[:, row] * x[:, col]))
    coefficients = np.linalg.lstsq(np.column_stack(features), log_target, rcond=None)[0]
    precision = np.zeros((dimension, dimension), dtype=float)
    for value, (row, col) in zip(coefficients[1 + dimension :], pairs):
        precision[row, col] = precision[col, row] = value
    eigenvalues, eigenvectors = np.linalg.eigh(precision)
    precision = (eigenvectors * np.maximum(eigenvalues, 1e-8)) @ eigenvectors.T
    linear_target = log_target + np.einsum("ni,ij,nj->n", x, precision, x)
    intercept_and_slope = np.linalg.lstsq(
        np.column_stack((np.ones(len(x)), x)), linear_target, rcond=None
    )[0]
    factor = np.linalg.cholesky(precision + np.eye(dimension) * 1e-12)
    intercept = float(intercept_and_slope[0])
    slope = intercept_and_slope[1:]
    return np.r_[intercept, slope, factor[np.tril_indices(dimension)]]


def fit(x: np.ndarray, target: np.ndarray, family: str) -> tuple[np.ndarray, float, str]:
    """Minimize response-scale SSE with a distinct optimizer and numeric gradient."""
    dimension = x.shape[1]
    start = moment_start(x, target, family)
    bounds = [(None, None)] * len(start)
    if family == "exp_concave":
        rows, cols = np.tril_indices(dimension)
        for offset in np.flatnonzero(rows == cols):
            bounds[1 + dimension + int(offset)] = (0.0, None)

    scale = max(float(np.max(np.abs(target))), 1e-12)

    def objective(theta: np.ndarray) -> float:
        residual = (mean(theta, x, family, 40.0) - target) / scale
        return float(residual @ residual)

    lower = np.array([-np.inf if low is None else low for low, _ in bounds])
    upper = np.array([np.inf if high is None else high for _, high in bounds])

    def residual(theta: np.ndarray) -> np.ndarray:
        return (mean(theta, x, family, 40.0) - target) / scale

    attempts = []
    lbfgs = minimize(objective, start, method="L-BFGS-B", bounds=bounds,
                     options={"maxiter": 1000, "ftol": 1e-13, "gtol": 1e-9, "maxls": 40})
    if lbfgs.success and np.isfinite(lbfgs.fun):
        attempts.append((float(lbfgs.fun), np.asarray(lbfgs.x), "L-BFGS-B"))
    numerical = least_squares(residual, start, jac="3-point", bounds=(lower, upper),
                              max_nfev=1000, ftol=1e-12, xtol=1e-12, gtol=1e-12)
    numerical_fun = float(numerical.fun @ numerical.fun)
    if numerical.success and np.isfinite(numerical_fun):
        attempts.append((numerical_fun, np.asarray(numerical.x), "numerical-3point-least-squares"))
    if not attempts:
        powell = minimize(objective, start, method="Powell", bounds=bounds,
                          options={"maxiter": 3000, "ftol": 1e-12, "xtol": 1e-10})
        if powell.success and np.isfinite(powell.fun):
            attempts.append((float(powell.fun), np.asarray(powell.x), "Powell"))
    if not attempts:
        raise FloatingPointError("all independent optimizers failed")
    objective_value, theta, solver = min(attempts, key=lambda item: item[0])
    if not np.isfinite(theta).all():
        raise FloatingPointError("independent optimizer returned nonfinite parameters")
    if np.any(mean(theta, x, family, 40.0) >= np.exp(40.0)):
        raise FloatingPointError("optimizer ceiling reached")
    return theta, objective_value, solver


def fit_with_loo(x: np.ndarray, observed: np.ndarray, sign: int, family: str) -> dict:
    amplitude = max(float(np.max(np.abs(observed))), 1e-12)
    theta, objective, solver = fit(x, sign * observed / amplitude, family)
    loo = np.empty(len(x), dtype=float)
    fold_solvers: dict[str, int] = {}
    for held_out in range(len(x)):
        mask = np.arange(len(x)) != held_out
        fold_amplitude = max(float(np.max(np.abs(observed[mask]))), 1e-12)
        folded, _, fold_solver = fit(x[mask], sign * observed[mask] / fold_amplitude, family)
        loo[held_out] = sign * fold_amplitude * mean(folded, x[held_out : held_out + 1], family, 700.0)[0]
        fold_solvers[fold_solver] = fold_solvers.get(fold_solver, 0) + 1
    yscale = max(float(np.std(observed)), 1e-12)
    cv = float(np.mean(((observed - loo) / yscale) ** 2))
    return {"theta": theta, "amplitude": amplitude, "sign": sign, "family": family,
            "objective": objective, "cv": cv, "solver": solver, "fold_solvers": fold_solvers}


def log_nmse(prediction: np.ndarray, truth: np.ndarray) -> float:
    difference = prediction - truth
    mse = float(np.mean(difference * difference))
    return math.log(max(mse, 1e-300)) - math.log(max(float(np.var(truth)), 1e-30))


def load_candidate_rows(path: Path) -> dict:
    rows = {}
    with gzip.open(path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            base_family = row["function"].rsplit("_", 1)[0]
            if row["method"] == "exponential_only" and base_family in {"gaussian", "negative_gaussian"}:
                key = (row["function"], row["seed"], float(row["noise"]), row["domain"])
                rows[key] = row
    return rows


def summarize_records(records: list[dict], elapsed_seconds: float) -> dict:
    usable = [record for record in records if "winner" in record]
    by_domain = {}
    comparison_floor = math.log(1e-8)
    for domain in ("inside", "near_shell", "far_shell"):
        delta = [max(record["scores"][domain]["independent_log_nmse"], comparison_floor)
                 - max(record["scores"][domain]["candidate_log_nmse"], comparison_floor)
                 for record in usable]
        by_domain[domain] = {"independent_over_candidate_geometric_nmse": math.exp(float(np.mean(delta))),
                             "median_log_ratio": float(np.median(delta)), "paths": len(delta)}
    clean_inside_exact = sum(record["scores"]["inside"]["independent_log_nmse"] <= comparison_floor
                             for record in usable if record["noise"] == 0.0)
    clean_paths = sum(record["noise"] == 0.0 for record in usable)
    return {
        "classification": "REPLICATION",
        "source_commit": "949d69b1de5284a106d6ce99ab6bc95f71bb2ab6",
        "candidate_functions_imported": False,
        "paths_attempted": len(records), "paths_reproduced": len(usable),
        "candidate_winner_agreement": sum(record["winner_agrees"] for record in usable),
        "candidate_winner_trials": len(usable), "by_domain": by_domain,
        "clean_inside_exact": clean_inside_exact, "clean_paths": clean_paths,
        "elapsed_seconds": elapsed_seconds, "field_breakthrough_established": False,
    }


def run(out: Path, limit: int | None, shard_index: int = 0, shard_count: int = 1) -> None:
    evidence = ROOT / "results/additive_response/confirmation"
    traces_path = evidence / "traces.jsonl.gz"
    arrays_path = evidence / "inputs_and_truth.npz"
    candidate = load_candidate_rows(traces_path)
    arrays = np.load(arrays_path)
    path_keys = sorted({(f, s, n) for f, s, n, _ in candidate})
    if limit is not None:
        groups: dict[str, list[tuple]] = {}
        for key in path_keys:
            groups.setdefault(key[0], []).append(key)
        balanced = []
        depth = 0
        while len(balanced) < min(limit, len(path_keys)):
            for name in sorted(groups):
                if depth < len(groups[name]) and len(balanced) < limit:
                    balanced.append(groups[name][depth])
            depth += 1
        path_keys = balanced
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid shard selection")
    path_keys = path_keys[shard_index::shard_count]
    records = []
    start_time = time.perf_counter()
    for number, (function, seed, noise) in enumerate(path_keys, 1):
        reference = candidate[(function, seed, noise, "inside")]
        pool = arrays[f"{function}_{seed}_pool"]
        selected = np.asarray(reference["selected"], dtype=int)
        observed = np.asarray(reference["observed"], dtype=float)
        lo = pool.min(axis=0)
        span = np.maximum(pool.max(axis=0) - lo, 1e-12)
        x = 2.0 * (pool[selected] - lo) / span - 1.0
        models = []
        failures = []
        for sign in (1, -1):
            for family in ("exp_affine", "exp_concave"):
                try:
                    models.append(fit_with_loo(x, observed, sign, family))
                except (FloatingPointError, ValueError, np.linalg.LinAlgError) as exc:
                    failures.append({"sign": sign, "family": family, "reason": str(exc)})
        if not models:
            records.append({"function": function, "seed": seed, "noise": noise, "failures": failures})
            continue
        winner = min(models, key=lambda model: model["cv"])
        candidate_model = reference["models"][0]
        scores = {}
        for domain in ("inside", "near_shell", "far_shell"):
            test = arrays[f"{function}_{seed}_{domain}_test"]
            truth = arrays[f"{function}_{seed}_{domain}_truth"]
            normalized = 2.0 * (test - lo) / span - 1.0
            prediction = winner["sign"] * winner["amplitude"] * mean(
                winner["theta"], normalized, winner["family"], 700.0
            )
            scores[domain] = {
                "independent_log_nmse": log_nmse(prediction, truth),
                "candidate_log_nmse": float(candidate[(function, seed, noise, domain)]["log_nmse"]),
                "max_abs_prediction": float(np.max(np.abs(prediction))),
            }
        records.append({
            "function": function, "seed": seed, "noise": noise,
            "winner": {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in winner.items()},
            "candidate_winner": {"family": candidate_model["family"], "sign": candidate_model["sign"],
                                 "cv": candidate_model["original_cv"]},
            "winner_agrees": winner["family"] == candidate_model["family"] and winner["sign"] == candidate_model["sign"],
            "scores": scores, "failures": failures,
        })
        print(f"{number}/{len(path_keys)} {function} {seed} {noise:g} {winner['family']} s={winner['sign']} cv={winner['cv']:.4g}", flush=True)

    summary = summarize_records(records, time.perf_counter() - start_time)
    provenance = {
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "input_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (traces_path, arrays_path)},
    }
    out.mkdir(parents=True, exist_ok=False)
    (out / "records.json").write_text(json.dumps(records, indent=2, allow_nan=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (out / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


def merge_shards(source: Path, out: Path) -> None:
    shard_paths = sorted(source.glob("shard-*/records.json"))
    if not shard_paths:
        raise ValueError("no shard records found")
    records = []
    elapsed = 0.0
    manifests = []
    for path in shard_paths:
        records.extend(json.loads(path.read_text()))
        elapsed = max(elapsed, json.loads((path.parent / "summary.json").read_text())["elapsed_seconds"])
        manifests.append(json.loads((path.parent / "manifest.json").read_text()))
    keys = [(record["function"], record["seed"], record["noise"]) for record in records]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate paths across shards")
    records.sort(key=lambda record: (record["function"], record["seed"], record["noise"]))
    summary = summarize_records(records, elapsed)
    out.mkdir(parents=True, exist_ok=False)
    (out / "records.json").write_text(json.dumps(records, indent=2, allow_nan=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (out / "manifest.json").write_text(json.dumps({"merged_shards": len(shard_paths),
        "shard_manifests_identical": all(manifest == manifests[0] for manifest in manifests),
        "source_manifest": manifests[0]}, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--merge-shards", type=Path)
    arguments = parser.parse_args()
    if arguments.merge_shards:
        merge_shards(arguments.merge_shards, arguments.out)
    else:
        run(arguments.out, arguments.limit, arguments.shard_index, arguments.shard_count)
