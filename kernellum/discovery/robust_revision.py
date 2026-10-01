"""Exploratory robust combinations of the existing selected kernel stack.

These are established aggregation operations, not claims of new methodology.
All weights and aggregation selection depend only on observed responses.
"""
import numpy as np

METHODS = ('median_stack', 'geometric_stack', 'aggregate_selector')


def combine(predictions, weights, kind):
    values = np.asarray(predictions, dtype=float)
    weights = np.asarray(weights, dtype=float)
    active = weights > 0
    values, weights = values[:, active], weights[active]
    weights = weights / weights.sum()
    if kind == 'mean':
        return values @ weights
    if kind == 'median':
        order = np.argsort(values, axis=1, kind='stable')
        ordered = np.take_along_axis(values, order, axis=1)
        cumulative = np.cumsum(np.broadcast_to(weights, values.shape)[np.arange(len(values))[:,None], order], axis=1)
        index = np.argmax(cumulative >= .5, axis=1)
        return ordered[np.arange(len(values)), index]
    if kind == 'geometric':
        result = values @ weights
        same_sign = np.all(values > 0, axis=1) | np.all(values < 0, axis=1)
        result[same_sign] = np.sign(values[same_sign,0])*np.exp(np.log(abs(values[same_sign]))@weights)
        return result
    raise ValueError('unknown combination')


class RobustStack:
    def __init__(self, bank):
        self.bank = bank
        self.models, self.weights = bank.selected('representation_stack')
        loo = np.column_stack([bank.y - bank.yscale*m['error'] for m in self.models])
        self.cv = {}
        for kind in ('mean', 'median', 'geometric'):
            prediction = combine(loo, self.weights, kind)
            self.cv[kind] = float(np.mean(((bank.y-prediction)/bank.yscale)**2))
        self.choice = min(self.cv, key=self.cv.get)

    def predict(self, x):
        components = np.column_stack([self.bank.predict_model(m,x) for m in self.models])
        combinations = {kind: combine(components,self.weights,kind) for kind in ('mean','median','geometric')}
        result = dict(median_stack=combinations['median'], geometric_stack=combinations['geometric'],
                      aggregate_selector=combinations[self.choice])
        if not all(np.isfinite(v).all() for v in result.values()):
            raise FloatingPointError('nonfinite robust prediction')
        return result

    def describe(self):
        return dict(choice=self.choice, loo_scores=self.cv, components=self.bank.describe('representation_stack'))
