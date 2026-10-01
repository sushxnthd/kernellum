"""Exploratory delta-method noise correction for logarithmic responses.

Three permanently observed anchors fix the noise-weight reference scale. They
are excluded from LOO scoring, making the remaining analytic LOO predictions
exact refits at a fixed ridge and weighting rule. No test labels enter fitting.
The delta method is an approximation; observed-response weights can be biased.
"""
import numpy as np
from .representation import RepresentationBank,invert_response
from .revision import FAMILIES,RIDGES

class NoiseConsistentBank(RepresentationBank):
 def fit(self,observed,values):
  super().fit(observed,values)
  if len(self.y)<7:raise ValueError('need three anchors and at least four validation observations')
  self.anchor=max(float(np.sqrt(np.mean(self.y[:3]**2))),1e-12)
  for m in self.models:
   m['weighting']='uniform';m['original_cv']=float(np.mean(m['error'][3:]**2))
  models=self.models.copy();n=len(self.y)
  transforms=[]
  if np.all(self.y>0):transforms=[('log_positive',np.log(self.y))]
  if np.all(self.y<0):transforms=[('log_negative',np.log(-self.y))]
  noise_shape=np.clip((self.anchor/np.maximum(np.abs(self.y),1e-12))**2,1e-6,1e6)
  for xkind,(bank,_,_) in self.banks.items():
   for ykind,yt in transforms:
    center=float(yt.mean());scale=max(float(yt.std()),1e-12);z=(yt-center)/scale
    for family in FAMILIES:
     k=bank.kernels[family][np.ix_(self.ids,self.ids)]
     for ridge in RIDGES:
      inv=np.linalg.solve(k+ridge*np.diag(noise_shape),np.eye(n));u=inv.sum(1);den=float(u.sum())
      projection=inv-np.outer(u,u)/den;alpha=projection@z;intercept=float(u@z/den)
      loo=alpha/np.maximum(np.diag(projection),1e-12)
      pred=invert_response(center+scale*(z-loo),ykind);err=(self.y-pred)/self.yscale
      with np.errstate(over='ignore',invalid='ignore'):cv=float(np.mean(err[3:]**2))
      models.append(dict(input=xkind,response=ykind,family=family,ridge=ridge,center=center,scale=scale,
                         alpha=alpha,intercept=intercept,error=err,original_cv=cv,weighting='delta',noise_shape=noise_shape))
  self.models=sorted(models,key=lambda m:m['original_cv']);return self
 def predict(self,x,method='noise_consistent'):
  if method=='noise_consistent':model=self.models[0]
  elif method=='anchor_control':model=next(m for m in self.models if m['weighting']=='uniform')
  else:raise ValueError('unknown method')
  result=self.predict_model(model,x)
  if not np.isfinite(result).all():raise FloatingPointError('nonfinite prediction')
  return result
 def describe(self,method='noise_consistent'):
  model=self.models[0] if method=='noise_consistent' else next(m for m in self.models if m['weighting']=='uniform')
  return {k:model[k] for k in ('input','response','family','ridge','original_cv','weighting')}
