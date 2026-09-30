"""Observed-data model revision and experimental acquisition.

LOO-selected kernel ridge models with an unpenalized constant. Mixture IVR is
an experimental moment-matching heuristic, not an exact Bayesian model average.
"""
from __future__ import annotations
import numpy as np

FAMILIES = ('linear', 'quadratic', 'cubic', 'rbf_short', 'rbf_medium', 'rbf_long')
RIDGES = (1e-6, 1e-3, 1e-1)
METHODS = ('mixture_ivr', 'winner_ivr', 'maximin', 'random', 'variance',
           'ideal', 'committee', 'quadratic_maximin', 'rbf_maximin')


def kernel(x, z, family):
    d = x.shape[1]
    if family in FAMILIES[:3]:
        degree = FAMILIES.index(family) + 1
        return (1 + x @ z.T / d) ** degree
    length = dict(rbf_short=.4, rbf_medium=.8, rbf_long=1.6)[family] * np.sqrt(d)
    distance = np.maximum((x*x).sum(1)[:, None] + (z*z).sum(1)[None, :] - 2*x@z.T, 0)
    return np.exp(-distance / (2*length**2))


def solve_model(k, y, ridge):
    """Exact LOO for kernel ridge with a fitted, unpenalized intercept."""
    inv = np.linalg.solve(k + ridge*np.eye(len(y)), np.eye(len(y)))
    u = inv.sum(axis=1)
    denominator = float(u.sum())
    projection = inv - np.outer(u, u)/denominator
    alpha = projection @ y
    intercept = float(u @ y / denominator)
    residuals = alpha / np.maximum(np.diag(projection), 1e-12)
    return dict(alpha=alpha, intercept=intercept, inv=inv, u=u,
                denominator=denominator, loo=residuals, cv=float(np.mean(residuals**2)), ridge=ridge)


class ModelBank:
    def __init__(self, x):
        self.x = np.asarray(x, dtype=float)
        if self.x.ndim != 2 or not self.x.shape[1] or not np.isfinite(self.x).all():
            raise ValueError('inputs must be a finite matrix with at least one column')
        self.kernels = {f: kernel(self.x, self.x, f) for f in FAMILIES}
        self.normalizers = {f: float(np.diag(k).mean()) for f, k in self.kernels.items()}
        self.kernels = {f: k/self.normalizers[f] for f, k in self.kernels.items()}

    def fit(self, observed, values, only_rbf=False):
        self.observed = np.asarray(observed, dtype=int)
        y = np.asarray(values, dtype=float)
        if (y.ndim != 1 or self.observed.ndim != 1 or len(y) != len(self.observed)
                or len(y) < 3 or len(set(self.observed)) != len(y)
                or np.any(self.observed < 0) or np.any(self.observed >= len(self.x))
                or not np.isfinite(y).all()):
            raise ValueError('invalid observations')
        self.center = float(y.mean())
        self.scale = max(float(y.std()), 1e-12)
        yz = (y-self.center)/self.scale
        models = []
        for family in (FAMILIES[3:] if only_rbf else FAMILIES):
            k = self.kernels[family][np.ix_(self.observed, self.observed)]
            fits = [solve_model(k, yz, ridge) for ridge in RIDGES]
            best = min(fits, key=lambda m: m['cv'])
            models.append(best | {'family':family})
        self.models = sorted(models, key=lambda m: m['cv'])
        return self

    def predict_model(self, model, x=None):
        cross = (self.kernels[model['family']][:, self.observed] if x is None else
                 kernel(np.asarray(x), self.x[self.observed], model['family']) / self.normalizers[model['family']])
        return model['intercept'] + cross @ model['alpha']

    def predict(self, x):
        return self.center + self.scale*self.predict_model(self.models[0], x)

    def posterior(self, model):
        k = self.kernels[model['family']]
        cross = k[:, self.observed]
        r = 1-cross @ model['u']
        covariance = k - cross@model['inv']@cross.T + np.outer(r,r)/model['denominator']
        return (covariance+covariance.T)/2

    def mixture(self):
        models = self.models[:3]
        cv = np.array([max(m['cv'], 1e-8) for m in models])
        weights = (cv.min()/cv)**2
        weights /= weights.sum()
        predictions = np.array([self.predict_model(m) for m in models])
        mean = weights @ predictions
        delta = predictions-mean
        covariance = sum(w*self.posterior(m) for w,m in zip(weights,models))
        covariance += delta.T @ (weights[:,None]*delta)
        noise = sum(w*m['ridge'] for w,m in zip(weights,models))
        return covariance, float(noise), predictions, weights

    def describe(self):
        return [{'family':m['family'], 'ridge':m['ridge'], 'loo_mse_standardized':m['cv']} for m in self.models]


def ivr_scores(covariance, noise):
    return np.mean(covariance**2, axis=0) / np.maximum(np.diag(covariance)+noise, 1e-12)


def ideal_scores(distances, pred, y, delta=1.0):
    """Bemporad eqs. 9b, 11, 12, 14; standardized outputs, density off."""
    w = np.exp(-distances)/np.maximum(distances, 1e-15)
    total = np.maximum(w.sum(axis=1), 1e-300)
    variance = np.sum(w*(pred[:,None]-y[None,:])**2, axis=1)/total
    exploration = 2/np.pi*np.arctan(1/total)
    return variance+delta*exploration


def investigate(x, query, method, budget=64, seed=0, initial=16, refresh=4):
    """No formulas, unmeasured labels or test arrays cross this interface."""
    if method not in METHODS:
        raise ValueError('unknown method')
    bank = ModelBank(x)
    x = bank.x
    if not 3 <= initial <= budget <= len(x) or refresh < 1:
        raise ValueError('invalid budget or refresh')
    rng = np.random.default_rng(seed)
    selected = list(map(int,rng.choice(len(x), initial, replace=False)))
    values = [float(query(i)) for i in selected]
    if not np.isfinite(values).all():
        raise ValueError('nonfinite response')
    revisions = []
    geometric = method in ('maximin','quadratic_maximin','rbf_maximin')
    while len(selected) < budget:
        available = np.ones(len(x), dtype=bool)
        available[selected] = False
        distances = ((x[:,None]-x[selected][None,:])**2).sum(2)
        if method == 'random':
            index = int(rng.choice(np.flatnonzero(available)))
        else:
            if geometric:
                scores = distances.min(axis=1)
            else:
                if (len(selected)-initial) % refresh == 0:
                    bank.fit(selected, values)
                    revisions.append(dict(budget=len(selected), models=bank.describe()))
                    if method in ('mixture_ivr','variance','committee'):
                        covariance, noise, predictions, weights = bank.mixture()
                    elif method == 'winner_ivr':
                        covariance = bank.posterior(bank.models[0])
                        noise = bank.models[0]['ridge']
                if method in ('mixture_ivr','winner_ivr'):
                    scores = ivr_scores(covariance, noise)
                elif method == 'variance':
                    scores = np.diag(covariance).copy()
                elif method == 'committee':
                    mean = weights@predictions
                    scores = np.sum(weights[:,None]*(predictions-mean)**2,axis=0)
                else:
                    # Predictor is refreshed in batches; new observed values enter IDW immediately.
                    yz = (np.asarray(values)-bank.center)/bank.scale
                    scores = ideal_scores(distances, bank.predict_model(bank.models[0]), yz)
            if not np.isfinite(scores).all():
                raise FloatingPointError('nonfinite acquisition')
            scores = scores.copy()
            scores[~available] = -np.inf
            index = int(np.argmax(scores))
        value = float(query(index))
        if not np.isfinite(value):
            raise ValueError('nonfinite response')
        selected.append(index)
        values.append(value)
        if method in ('mixture_ivr','winner_ivr','variance'):
            c = covariance[:,index].copy()
            covariance -= np.outer(c,c)/max(covariance[index,index]+noise,1e-12)
    return selected, values, revisions
