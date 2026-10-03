"""Exploratory additive-error exponential models, established nonlinear regression.

Never logarithmically transforms measured responses. Exact leave-one-out refits
score signed exponential affine and concave quadratic means on the measured scale.
No claim of novel least squares or Gaussian fitting.
"""
import numpy as np
from scipy.optimize import least_squares
from .representation import RepresentationBank


def value_jacobian(theta,x,family,ceiling=40):
    n,d=x.shape
    latent=theta[0]+x@theta[1:1+d]
    jac=np.column_stack((np.ones(n),x))
    if family=='exp_concave':
        ij=np.tril_indices(d);lower=np.zeros((d,d));lower[ij]=theta[1+d:]
        cross=x@lower;latent-=np.sum(cross*cross,axis=1)
        jac=np.column_stack((jac,-2*x[:,ij[0]]*cross[:,ij[1]]))
    # Numerical ceiling during optimizer steps; derivative agrees with ceiling.
    values=np.exp(np.minimum(latent,ceiling))
    jac=values[:,None]*jac;jac[latent>ceiling]=0
    return values,jac


def start_parameters(x,y,family):
    d=x.shape[1]
    # Initialization only. All signed measured responses enter the objective.
    target=np.log(np.maximum(y,max(float(abs(y).max())*1e-4,1e-8)))
    if family=='exp_affine':return np.linalg.lstsq(np.c_[np.ones(len(x)),x],target,rcond=None)[0]
    ij=np.tril_indices(d);design=np.c_[np.ones(len(x)),x,x[:,ij[0]]*x[:,ij[1]]]
    coef=np.linalg.lstsq(design,target,rcond=None)[0]
    curvature=np.zeros((d,d));curvature[ij]=-coef[1+d:]
    curvature=curvature+curvature.T-np.diag(np.diag(curvature))
    # Cross-term coefficient is twice the symmetric quadratic entry.
    curvature=np.diag(np.diag(curvature))+.5*(curvature-np.diag(np.diag(curvature)))
    eigen,vectors=np.linalg.eigh(curvature);curvature=(vectors*np.maximum(eigen,1e-4))@vectors.T
    lower=np.linalg.cholesky(curvature)
    return np.r_[coef[:1+d],lower[ij]]


def fit_exp(x,y,family,initial=None):
    d=x.shape[1];theta=start_parameters(x,y,family) if initial is None else initial.copy()
    lo=np.full(len(theta),-np.inf);hi=np.full(len(theta),np.inf)
    if family=='exp_concave':
        ij=np.tril_indices(d);lo[1+d+np.flatnonzero(ij[0]==ij[1])]=0
    def residual(p):return value_jacobian(p,x,family)[0]-y
    def jac(p):return value_jacobian(p,x,family)[1]
    result=least_squares(residual,theta,jac=jac,bounds=(lo,hi),max_nfev=300,ftol=1e-10,xtol=1e-10,gtol=1e-10)
    if not result.success or not np.isfinite(result.x).all():raise FloatingPointError('nonlinear optimizer failed')
    if np.any(value_jacobian(result.x,x,family)[0]>=np.exp(40)):raise FloatingPointError('optimizer ceiling reached')
    return result.x


class AdditiveResponseBank(RepresentationBank):
    def fit(self,observed,values):
        super().fit(observed,values);self.nonlinear_failures=[]
        amplitude=max(float(abs(self.y).max()),1e-12)
        # Both signs are candidates; no held-out response determines fold sign.
        for xkind,(base,lo,span) in self.banks.items():
            x=base.x[self.ids]
            for sign in (1,-1):
                target=sign*self.y/amplitude
                for family in ('exp_affine','exp_concave'):
                    try:
                        theta=fit_exp(x,target,family)
                        loo=np.empty(len(x))
                        for i in range(len(x)):
                            mask=np.arange(len(x))!=i
                            # Initialize each fold from that fold alone, avoiding
                            # held-out-value influence through local basin choice.
                            fold_amplitude=max(float(abs(self.y[mask]).max()),1e-12)
                            folded=fit_exp(x[mask],sign*self.y[mask]/fold_amplitude,family)
                            loo[i]=sign*fold_amplitude*value_jacobian(folded,x[i:i+1],family)[0][0]
                        error=(self.y-loo)/self.yscale
                        self.models.append(dict(input=xkind,response='additive_positive' if sign==1 else 'additive_negative',
                            family=family,theta=theta,sign=sign,amplitude=amplitude,error=error,
                            original_cv=float(np.mean(error**2)),ridge=0.))
                    except (FloatingPointError,ValueError,np.linalg.LinAlgError) as exc:
                        self.nonlinear_failures.append(dict(input=xkind,sign=sign,family=family,reason=str(exc)))
        self.models.sort(key=lambda m:m['original_cv'])
        return self

    def predict_model(self,m,x):
        if not m['family'].startswith('exp_'):return super().predict_model(m,x)
        base,lo,span=self.banks[m['input']]
        normalized=2*(self.raw_transform(x,m['input'])-lo)/span-1
        # Legacy representation bank's exp(700) numerical ceiling at inference.
        return m['sign']*m['amplitude']*value_jacobian(m['theta'],normalized,m['family'],ceiling=700)[0]
