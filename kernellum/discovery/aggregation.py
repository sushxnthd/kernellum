"""Conservative model aggregation research candidates and established controls.

Bootstrap quantiles here are heuristics, not confidence bounds: LOO errors are
correlated and model hyperparameters were selected using the same observations.
"""
from itertools import combinations
import numpy as np

METHODS=('winner','rbf_only','stacking','inverse_cv','pair_blend',
         'conservative_05','conservative_10','conservative_25')


def simplex_stack(errors):
    """Solve small convex stacking QP by enumerating simplex faces."""
    errors=np.asarray(errors,dtype=float)
    n,k=errors.shape
    gram=errors.T@errors/n
    best=np.eye(k)[int(np.argmin(np.diag(gram)))];best_loss=float(best@gram@best)
    regularizer=max(float(np.trace(gram)/k)*1e-12,1e-18)
    for size in range(2,k+1):
        for active in combinations(range(k),size):
            sub=gram[np.ix_(active,active)]+regularizer*np.eye(size)
            z=np.linalg.solve(sub,np.ones(size))
            if z.sum()<=0:continue
            z=z/z.sum()
            if z.min() < -1e-9:continue
            z=np.maximum(z,0);z/=z.sum()
            w=np.zeros(k);w[list(active)]=z
            loss=float(w@gram@w)
            if loss<best_loss:best=w;best_loss=loss
    return best


def aggregate_weights(errors,families,method,seed=0):
    e=np.asarray(errors,dtype=float)
    if e.ndim!=2 or len(families)!=e.shape[1] or len(e)<3 or not np.isfinite(e).all():
        raise ValueError('invalid out-of-fold residual matrix')
    if method not in METHODS:raise ValueError('unknown aggregation method')
    risk=np.mean(e**2,axis=0);k=e.shape[1]
    rbfs=[i for i,f in enumerate(families) if f.startswith('rbf')]
    polynomials=[i for i,f in enumerate(families) if not f.startswith('rbf')]
    if not rbfs or not polynomials:raise ValueError('require polynomial and RBF families')
    base=min(rbfs,key=lambda i:risk[i]);poly=min(polynomials,key=lambda i:risk[i])
    if method in ('winner','rbf_only'):
        return np.eye(k)[int(np.argmin(risk)) if method=='winner' else base]
    if method=='stacking':return simplex_stack(e)
    if method=='inverse_cv':
        r=np.maximum(risk,1e-8);w=(r.min()/r)**2;return w/w.sum()
    difference=e[:,poly]-e[:,base]
    cross=e[:,base]*difference;square=difference**2
    if method=='pair_blend':
        fraction=np.clip(-cross.mean()/max(square.mean(),1e-18),0,1)
    else:
        q={'conservative_05':.05,'conservative_10':.1,'conservative_25':.25}[method]
        draw=np.random.default_rng(seed).integers(0,len(e),size=(256,len(e)))
        fractions=np.clip(-cross[draw].mean(1)/np.maximum(square[draw].mean(1),1e-18),0,1)
        fraction=float(np.quantile(fractions,q))
    w=np.zeros(k);w[base]=1-fraction;w[poly]=fraction
    return w
