"""Pool-based experimental design with an explicit observed-label boundary.

The proposed criterion estimates the change in integrated squared prediction
error after one ridge update, using a flexible committee as a provisional target.
It is a research candidate, not an established improvement or calibrated oracle.
"""
from __future__ import annotations
from itertools import combinations_with_replacement
import numpy as np

METHODS = ('random', 'maximin', 'variance', 'integrated_variance',
           'committee', 'igs', 'teacher_risk', 'teacher_risk_pure')
RIDGE = 1e-6


def features(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ValueError('inputs must be a finite matrix')
    return np.column_stack([np.ones(len(x)), *x.T,
        *(x[:, i] * x[:, j] for i, j in combinations_with_replacement(range(x.shape[1]), 2))])


def fit(phi, y):
    """Constant ridge penalty, including intercept; caller controls label scaling."""
    inv = np.linalg.inv(phi.T @ phi + RIDGE * np.eye(phi.shape[1]))
    return inv @ phi.T @ y, inv


def teachers(x, observed, y):
    """Three RBF kernel ridge models; only observed labels enter the fit."""
    train = x[observed]
    dtrain = np.maximum(((train[:, None] - train[None, :]) ** 2).sum(2), 0)
    dpool = np.maximum(((x[:, None] - train[None, :]) ** 2).sum(2), 0)
    center = float(np.mean(y))
    predictions = []
    for length in (0.3, 0.6, 1.2):
        kernel = np.exp(-dtrain / (2 * length ** 2))
        alpha = np.linalg.solve(kernel + 1e-4 * np.eye(len(y)), y - center)
        predictions.append(center + np.exp(-dpool / (2 * length ** 2)) @ alpha)
    return np.asarray(predictions)


def risk_scores(phi, beta, inv, targets):
    """Exact *proxy* risk decrease for a hypothetical ridge update.

Each teacher supplies both the candidate label and evaluation-pool targets.
These are predictions, not unqueried observations. Positive scores indicate
predicted improvement, with no guarantee that the teachers are correct.
"""
    pred = phi @ beta
    v = inv @ phi.T
    gain = v / (1 + np.einsum('ij,ji->i', phi, v))
    gram = phi.T @ phi / len(phi)
    gain_norm = np.einsum('ij,ij->j', gain, gram @ gain)
    residual = targets - pred
    error_projection = (pred - targets) @ phi / len(phi)
    delta = 2 * residual * (error_projection @ gain) + residual ** 2 * gain_norm
    return -delta.mean(axis=0)


def choose(x, observed, y, method, rng):
    """Select one row. API intentionally accepts no unobserved outputs."""
    x = np.asarray(x, dtype=float)
    observed = np.asarray(observed, dtype=int)
    y = np.asarray(y, dtype=float)
    if method not in METHODS:
        raise ValueError('unknown method')
    if (x.ndim != 2 or not np.isfinite(x).all() or len(observed) != len(y)
            or len(observed) < 2 or len(set(observed)) != len(observed)
            or np.any(observed < 0) or np.any(observed >= len(x))
            or not np.isfinite(y).all()):
        raise ValueError('invalid observed data')
    available = np.ones(len(x), dtype=bool)
    available[observed] = False
    if not available.any():
        raise ValueError('pool exhausted')
    if method == 'random':
        return int(rng.choice(np.flatnonzero(available)))
    distances = ((x[:, None] - x[observed][None, :]) ** 2).sum(2)
    # Every fourth acquired point after the common 12-point start is coverage.
    if method == 'maximin' or (method == 'teacher_risk' and (len(observed) - 12) % 4 == 3):
        scores = distances.min(axis=1)
    else:
        scale = max(float(np.std(y)), 1e-12)
        z = (y - y.mean()) / scale
        phi = features(x)
        beta, inv = fit(phi[observed], z)
        v = inv @ phi.T
        leverage = np.einsum('ij,ji->i', phi, v)
        if method == 'variance':
            scores = leverage
        elif method == 'integrated_variance':
            gram = phi.T @ phi / len(phi)
            scores = np.einsum('ij,ij->j', v, gram @ v) / (1 + leverage)
        elif method == 'igs':
            scores = (distances * ((phi @ beta)[:, None] - z[None, :]) ** 2).min(axis=1)
        else:
            target = teachers(x, observed, z)
            scores = target.var(axis=0) if method == 'committee' else risk_scores(phi, beta, inv, target)
    scores = np.asarray(scores, dtype=float)
    if not np.isfinite(scores).all():
        raise FloatingPointError('nonfinite acquisition')
    scores[~available] = -np.inf
    return int(np.argmax(scores))


def investigate(x, query, method='teacher_risk', budget=40, seed=0, initial=12):
    """Run an investigation against a one-index/one-response measurement function."""
    x = np.asarray(x, dtype=float)
    if not 2 <= initial <= budget <= len(x):
        raise ValueError('require 2 <= initial <= budget <= pool size')
    rng = np.random.default_rng(seed)
    selected = list(map(int, rng.choice(len(x), initial, replace=False)))
    values = [float(query(i)) for i in selected]
    if not np.isfinite(values).all():
        raise ValueError('nonfinite measurement')
    while len(selected) < budget:
        idx = choose(x, selected, values, method, rng)
        value = float(query(idx))
        if not np.isfinite(value):
            raise ValueError('nonfinite measurement')
        selected.append(idx)
        values.append(value)
    return selected, values
