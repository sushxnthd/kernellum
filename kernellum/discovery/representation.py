"""Observed-data selection of identity/log input and response representations.

This is a benchmarkable implementation of established transformation ideas, not
an assertion that logarithmic regression or warped kernels are new.
"""
import numpy as np
from .revision import ModelBank, FAMILIES, RIDGES, solve_model, kernel
from .aggregation import simplex_stack

METHODS=('representation','raw','raw_stack','input_only','output_only','log_linear','representation_stack')


def invert_response(values,kind):
    if kind=='identity':return values
    with np.errstate(over='ignore',invalid='ignore'):
        result=np.exp(np.minimum(values,700))
    return result if kind=='log_positive' else -result


class RepresentationBank:
    def __init__(self,pool):
        self.pool=np.asarray(pool,dtype=float)
        if self.pool.ndim!=2 or not np.isfinite(self.pool).all():raise ValueError('invalid pool')
        self.sign=np.where(self.pool.min(0)>0,1,np.where(self.pool.max(0)<0,-1,0))
        self.banks={}
        for kind in (('identity','log') if np.any(self.sign) else ('identity',)):
            v=self.raw_transform(self.pool,kind)
            lo=v.min(0);span=np.maximum(v.max(0)-lo,1e-12)
            norm=2*(v-lo)/span-1
            self.banks[kind]=(ModelBank(norm),lo,span)

    def raw_transform(self,x,kind):
        v=np.asarray(x,dtype=float).copy()
        if kind=='log':
            for j,sign in enumerate(self.sign):
                if sign:
                    if np.any(sign*v[:,j]<=0):raise ValueError('prediction input outside observed sign domain')
                    v[:,j]=np.log(sign*v[:,j])
        return v

    def fit(self,observed,values):
        self.ids=np.asarray(observed,dtype=int);self.y=np.asarray(values,dtype=float)
        if (len(self.ids)!=len(self.y) or len(self.y)<3 or len(set(self.ids))!=len(self.ids)
            or np.any(self.ids<0) or np.any(self.ids>=len(self.pool)) or not np.isfinite(self.y).all()):
            raise ValueError('invalid observations')
        self.yscale=max(float(np.std(self.y)),1e-12)
        transforms=[('identity',self.y)]
        if np.all(self.y>0):transforms.append(('log_positive',np.log(self.y)))
        if np.all(self.y<0):transforms.append(('log_negative',np.log(-self.y)))
        models=[]
        for xkind,(bank,_,_) in self.banks.items():
            for ykind,yt in transforms:
                center=float(yt.mean());scale=max(float(yt.std()),1e-12);z=(yt-center)/scale
                for family in FAMILIES:
                    k=bank.kernels[family][np.ix_(self.ids,self.ids)]
                    for ridge in RIDGES:
                        model=solve_model(k,z,ridge)
                        loo_prediction=invert_response(center+scale*(z-model['loo']),ykind)
                        residual=(self.y-loo_prediction)/self.yscale
                        with np.errstate(over='ignore',invalid='ignore'):cv=float(np.mean(residual**2))
                        models.append(model|dict(input=xkind,response=ykind,family=family,center=center,
                                               scale=scale,error=residual,original_cv=cv))
        self.models=sorted(models,key=lambda m:m['original_cv'])
        if not np.isfinite(self.models[0]['original_cv']):raise FloatingPointError('all models failed')
        return self

    def eligible(self,method):
        if method not in METHODS:raise ValueError('unknown method')
        if method in ('raw','raw_stack'):return [m for m in self.models if m['input']=='identity' and m['response']=='identity']
        if method=='input_only':return [m for m in self.models if m['response']=='identity']
        if method=='output_only':return [m for m in self.models if m['input']=='identity']
        if method=='log_linear':
            valid=[m for m in self.models if m['input']=='log' and m['response']!='identity' and m['family']=='linear']
            return valid or [m for m in self.models if m['input']=='identity' and m['response']=='identity' and m['family']=='linear']
        return self.models

    def selected(self,method):
        models=self.eligible(method)
        if not method.endswith('_stack'):return models[:1],np.ones(1)
        # One best ridge per representation/family; at most six best groups.
        chosen=[];seen=set()
        for m in models:
            key=(m['input'],m['response'],m['family'])
            if key not in seen and np.isfinite(m['original_cv']):
                chosen.append(m);seen.add(key)
            if len(chosen)==6:break
        weights=simplex_stack(np.column_stack([m['error'] for m in chosen]))
        return chosen,weights

    def predict_model(self,m,x):
        bank,lo,span=self.banks[m['input']]
        norm=2*(self.raw_transform(x,m['input'])-lo)/span-1
        k=kernel(norm,bank.x[self.ids],m['family'])/bank.normalizers[m['family']]
        prediction=m['center']+m['scale']*(m['intercept']+k@m['alpha'])
        return invert_response(prediction,m['response'])

    def predict(self,x,method='representation'):
        models,weights=self.selected(method)
        result=sum(w*self.predict_model(m,x) for m,w in zip(models,weights) if w>0)
        if not np.isfinite(result).all():raise FloatingPointError('nonfinite prediction')
        return result

    def describe(self,method):
        models,weights=self.selected(method)
        return [dict(input=m['input'],response=m['response'],family=m['family'],ridge=m['ridge'],
                     loo_nmse=m['original_cv'],weight=float(w)) for m,w in zip(models,weights)]
