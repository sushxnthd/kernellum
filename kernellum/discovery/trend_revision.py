"""Exploratory universal kriging with affine trend and bounded RBF correction.

The method is established prior art. This bank tests whether replacing
log-response polynomial tails fixes the observed extrapolation/accuracy tradeoff.
"""
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from .representation import RepresentationBank, invert_response
from .revision import FAMILIES, RIDGES, kernel
from .aggregation import simplex_stack

METHODS = ('trend', 'trend_stack')


def solve_trend(k, x, y, ridge):
    """Universal affine mean; exact PRESS with the mean refitted in each fold."""
    design = np.column_stack((np.ones(len(x)), x))
    if len(x) <= design.shape[1] or np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError('affine trend is not identifiable')
    factor = cho_factor(k + ridge*np.eye(len(y)), lower=True)
    inv = cho_solve(factor, np.eye(len(y)))
    v = cho_solve(factor, design)
    information = design.T @ v
    beta = np.linalg.solve(information, design.T @ cho_solve(factor, y))
    alpha = cho_solve(factor, y-design @ beta)
    projection = inv - v @ np.linalg.solve(information, v.T)
    diagonal = np.diag(projection)
    if np.any(diagonal <= 1e-12):
        raise ValueError('leave-one-out trend is not identifiable')
    return dict(alpha=alpha, beta=beta, loo=alpha/diagonal, ridge=ridge,
                correction_bound=float(np.sum(np.abs(alpha))))


class TrendBank:
    def __init__(self, fitted_bank):
        self.bank = fitted_bank
        # Identity-response polynomial predictions remain permissible. Only the
        # nonlinear polynomial inside an exponential is removed.
        models = [m | {'trend':'constant'} for m in self.bank.models
                  if m['response']=='identity' or m['family'] not in ('quadratic','cubic')]
        transforms = [('identity', self.bank.y)]
        if np.all(self.bank.y > 0):
            transforms.append(('log_positive',np.log(self.bank.y)))
        if np.all(self.bank.y < 0):
            transforms.append(('log_negative',np.log(-self.bank.y)))
        for xkind,(base,_,_) in self.bank.banks.items():
            x = base.x[self.bank.ids]
            for ykind,values in transforms:
                center = float(values.mean()); scale = max(float(values.std()),1e-12)
                z = (values-center)/scale
                for family in FAMILIES[3:]:
                    k = base.kernels[family][np.ix_(self.bank.ids,self.bank.ids)]
                    for ridge in RIDGES:
                        try:
                            m = solve_trend(k,x,z,ridge)
                        except ValueError:
                            continue
                        loo = invert_response(center+scale*(z-m['loo']),ykind)
                        error = (self.bank.y-loo)/self.bank.yscale
                        with np.errstate(over='ignore', invalid='ignore'):
                            cv = float(np.mean(error**2))
                        models.append(m | dict(input=xkind,response=ykind,family=family,
                                      trend='affine',center=center,scale=scale,error=error,original_cv=cv))
        self.models = sorted(models, key=lambda m:m['original_cv'])

    def selected(self,method):
        if method not in METHODS:
            raise ValueError('unknown method')
        if method == 'trend':
            return self.models[:1], np.ones(1)
        selected=[];seen=set()
        for m in self.models:
            key=(m['input'],m['response'],m['family'],m['trend'])
            if key not in seen and np.isfinite(m['original_cv']):
                selected.append(m);seen.add(key)
            if len(selected)==6:
                break
        return selected, simplex_stack(np.column_stack([m['error'] for m in selected]))

    def predict_model(self,m,x):
        if m['trend']=='constant':
            return self.bank.predict_model(m,x)
        base,lo,span=self.bank.banks[m['input']]
        normalized=2*(self.bank.raw_transform(x,m['input'])-lo)/span-1
        cross=kernel(normalized,base.x[self.bank.ids],m['family'])/base.normalizers[m['family']]
        mean=np.column_stack((np.ones(len(x)),normalized)) @ m['beta']
        latent=m['center']+m['scale']*(mean+cross@m['alpha'])
        return invert_response(latent,m['response'])

    def predict(self,x,method='trend_stack'):
        selected,weights=self.selected(method)
        result=sum(w*self.predict_model(m,x) for m,w in zip(selected,weights) if w>0)
        if not np.isfinite(result).all():
            raise FloatingPointError('nonfinite trend prediction')
        return result

    def describe(self,method):
        selected,weights=self.selected(method)
        return [dict(input=m['input'],response=m['response'],family=m['family'],trend=m['trend'],
                     ridge=m['ridge'],loo_nmse=m['original_cv'],weight=float(w),
                     correction_bound=m.get('correction_bound')) for m,w in zip(selected,weights)]
