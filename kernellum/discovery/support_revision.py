"""Development-only support routing; no calibration or safety guarantee.

Uses measured inputs and the fitted kernel, never validation/test responses.
The fallback is the existing raw-input/raw-response model selector.
"""
import numpy as np
from .revision import kernel

POLICIES = ('box', 'leverage', 'nonlinear_leverage')
METHODS = tuple('support_' + p + s for p in POLICIES for s in ('', '_stack'))


def latent_variance(bank, model, x):
    """Universal-kriging latent variance and maximum observed LOO variance."""
    base, lo, span = bank.banks[model['input']]
    z = 2 * (bank.raw_transform(x, model['input']) - lo) / span - 1
    family = model['family']
    norm = base.normalizers[family]
    cross = kernel(z, base.x[bank.ids], family) / norm
    if family in ('linear', 'quadratic', 'cubic'):
        degree = ('linear', 'quadratic', 'cubic').index(family) + 1
        diagonal = (1 + np.sum(z*z, axis=1) / z.shape[1]) ** degree / norm
    else:
        diagonal = np.full(len(z), 1 / norm)
    observed = base.kernels[family][np.ix_(bank.ids, bank.ids)]
    chol = np.linalg.cholesky(observed + model['ridge'] * np.eye(len(bank.ids)))
    whitened = np.linalg.solve(chol, cross.T)
    constant = np.linalg.solve(chol, np.ones(len(bank.ids)))
    variance = diagonal - np.sum(whitened * whitened, axis=0)
    variance += (1 - whitened.T @ constant) ** 2 / float(constant @ constant)
    pdiag = np.diag(model['inv']) - model['u'] ** 2 / model['denominator']
    if np.any(pdiag <= 0):
        raise FloatingPointError('nonpositive precision diagonal')
    loo_variance = 1 / pdiag - model['ridge']
    return np.maximum(variance, 0), max(float(loo_variance.max()), 0)


class SupportRouter:
    """One prediction batch; caches component calculations across ablations."""
    def __init__(self, bank, x):
        self.bank = bank
        self.x = np.asarray(x, dtype=float)
        if self.x.ndim != 2 or self.x.shape[1] != bank.pool.shape[1] or not np.isfinite(self.x).all():
            raise ValueError('invalid prediction inputs')
        self.raw = bank.predict(self.x, 'raw')
        measured = bank.pool[bank.ids]
        self.outside = np.any((self.x < measured.min(0)) | (self.x > measured.max(0)), axis=1)
        self.cache = {}

    def component(self, model):
        key = id(model)
        if key not in self.cache:
            valid = np.ones(len(self.x), dtype=bool)
            if model['input'] == 'log':
                for j, sign in enumerate(self.bank.sign):
                    if sign:
                        valid &= sign * self.x[:, j] > 0
            prediction = self.raw.copy()
            prediction[valid] = self.bank.predict_model(model, self.x[valid])
            high = np.zeros(len(self.x), dtype=bool)
            bound = None
            transformed = model['input'] != 'identity' or model['response'] != 'identity'
            if transformed and np.any(valid):
                variance, bound = latent_variance(self.bank, model, self.x[valid])
                high[valid] = variance > bound
            self.cache[key] = (prediction, ~valid, high, bound, transformed)
        return self.cache[key]

    def predict(self, method):
        if method not in METHODS:
            raise ValueError('unknown support method')
        stacked = method.endswith('_stack')
        policy = method[len('support_'):-len('_stack')] if stacked else method[len('support_'):]
        models, weights = self.bank.selected('representation_stack' if stacked else 'representation')
        result = np.zeros(len(self.x))
        routed_mass = np.zeros(len(self.x))
        diagnostics = []
        for model, weight in zip(models, weights):
            if weight <= 0:
                continue
            prediction, invalid, high, bound, transformed = self.component(model)
            route = invalid.copy()
            if transformed:
                if policy == 'box':
                    route |= self.outside
                elif policy == 'leverage' or model['family'] != 'linear':
                    route |= high
            result += weight * np.where(route, self.raw, prediction)
            routed_mass += weight * route
            diagnostics.append(dict(input=model['input'], response=model['response'], family=model['family'],
                                    ridge=model['ridge'], weight=float(weight), variance_bound=bound,
                                    routed_fraction=float(route.mean())))
        if not np.isfinite(result).all():
            raise FloatingPointError('nonfinite routed prediction')
        return result, dict(routed_weight_mean=float(routed_mass.mean()),
                            any_routed_fraction=float(np.mean(routed_mass > 0)), components=diagnostics)
