"""Observation-only adaptive aggregation for transformed model stacks.

The rule preserves the ordinary weighted mean when fitted components agree and
uses the already-tested weighted median only when their disagreement exceeds an
upper envelope computed from leave-one-out predictions on observed labels.
"""
import numpy as np
from .robust_revision import combine


class AdaptiveStack:
    def __init__(self, bank):
        self.bank = bank
        self.models, self.weights = bank.selected('representation_stack')
        self.loo_components = np.column_stack([
            bank.y - bank.yscale * model['error'] for model in self.models
        ])
        self.loo_spread = np.max(self.loo_components, axis=1) - np.min(self.loo_components, axis=1)
        center = float(np.median(self.loo_spread))
        mad = float(np.median(np.abs(self.loo_spread - center)))
        self.spread_threshold = float(np.quantile(self.loo_spread, .95) + 2 * max(mad, 1e-12))

    def predict(self, x):
        x = np.asarray(x, dtype=float)
        raw = self.bank.predict(x, 'raw')
        component_values = []
        for model in self.models:
            valid = np.ones(len(x), dtype=bool)
            if model['input'] == 'log':
                for j, sign in enumerate(self.bank.sign):
                    if sign:
                        valid &= sign * x[:, j] > 0
            values = raw.copy()
            if np.any(valid):
                values[valid] = self.bank.predict_model(model, x[valid])
            component_values.append(values)
        components = np.column_stack(component_values)
        mean = combine(components, self.weights, 'mean')
        median = combine(components, self.weights, 'median')
        spread = np.max(components, axis=1) - np.min(components, axis=1)
        use_robust = spread > self.spread_threshold
        result = mean.copy()
        result[use_robust] = median[use_robust]
        if not np.isfinite(result).all():
            raise FloatingPointError('nonfinite adaptive prediction')
        return result, dict(spread_threshold=self.spread_threshold,
                            robust_fraction=float(np.mean(use_robust)),
                            components=self.bank.describe('representation_stack'))
