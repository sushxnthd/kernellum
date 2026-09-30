"""Development candidates for acquisition after representation selection.

Output-unit IVR uses a first-order inverse-transform Jacobian. It is a heuristic,
not an exact posterior for the transformed response or a calibrated noise model.
"""
import numpy as np
from .representation import RepresentationBank
from .revision import ideal_scores
METHODS=('warped_ivr','hybrid_ivr','latent_ivr','raw_ivr','variance','maximin','random',
         'hybrid_latent','hybrid_raw','ideal','hybrid_ideal','residual_ivr','hybrid_residual')

def investigate(pool,query,method,budget=64,initial=16,refresh=4,seed=0):
 if method not in METHODS:raise ValueError('unknown acquisition')
 pool=np.asarray(pool,dtype=float)
 if not 3<=initial<=budget<=len(pool) or refresh<1:raise ValueError('invalid budget')
 rng=np.random.default_rng(seed);ids=list(map(int,rng.choice(len(pool),initial,replace=False)))
 values=[float(query(i)) for i in ids];bank=RepresentationBank(pool);revisions=[]
 if not np.isfinite(values).all():raise ValueError('nonfinite initial observations')
 x=bank.banks['identity'][0].x
 while len(ids)<budget:
  remaining=np.ones(len(pool),dtype=bool);remaining[ids]=False
  if method=='random':idx=int(rng.choice(np.flatnonzero(remaining)))
  else:
   if method=='maximin' or (method.startswith('hybrid_') and (len(ids)-initial)%4==3):
    scores=((x[:,None]-x[ids][None,:])**2).sum(2).min(1)
   else:
    if (len(ids)-initial)%refresh==0:
     bank.fit(ids,values);model=bank.eligible('raw' if method in ('raw_ivr','hybrid_raw') else 'representation')[0]
     kernelbank=bank.banks[model['input']][0];kernel=kernelbank.kernels[model['family']]
     cross=kernel[:,ids];constant=1-cross@model['u']
     covariance=kernel-cross@model['inv']@cross.T+np.outer(constant,constant)/model['denominator']
     covariance=(covariance+covariance.T)/2
     if model['response']=='identity':weights=np.ones(len(pool))
     else:
      latent=model['center']+model['scale']*(model['intercept']+cross@model['alpha'])
      # Common scale cancels ranking; log normalization avoids exponent overflow.
      logweight=2*np.minimum(latent,700);weights=np.exp(logweight-logweight.max())
     if method in ('latent_ivr','raw_ivr','hybrid_latent','hybrid_raw'):weights=np.ones(len(pool))
     if method in ('residual_ivr','hybrid_residual'):
      distances=((kernelbank.x[:,None]-kernelbank.x[ids][None,:])**2).sum(2)
      neighbor=np.exp(-distances)/np.maximum(distances,1e-12)
      local=neighbor@(model['error']**2)/np.maximum(neighbor.sum(1),1e-300)
      # Target observed prediction risk; covariance supplies fractional reduction.
      weights=np.maximum(local,1e-12)/np.maximum(np.diag(covariance),1e-12)
      weights/=weights.max()
     if method in ('ideal','hybrid_ideal'):
      yz=(np.asarray(values)-bank.y.mean())/bank.yscale
      ideal_prediction=(bank.predict_model(model,pool)-bank.y.mean())/bank.yscale
     ridge=model['ridge']
     revisions.append(dict(budget=len(ids),input=model['input'],response=model['response'],family=model['family'],ridge=ridge))
    diag=np.maximum(np.diag(covariance),0)
    if method in ('ideal','hybrid_ideal'):
     distances=((x[:,None]-x[ids][None,:])**2).sum(2)
     scores=ideal_scores(distances,ideal_prediction,(np.asarray(values)-bank.y.mean())/bank.yscale)
    else:scores=weights*diag if method=='variance' else np.mean(weights[:,None]*covariance**2,axis=0)/np.maximum(diag+ridge,1e-12)
   scores=scores.copy();scores[~remaining]=-np.inf
   if not np.isfinite(scores[remaining]).all():raise FloatingPointError('nonfinite acquisition scores')
   idx=int(np.argmax(scores))
  value=float(query(idx))
  if not np.isfinite(value):raise ValueError('nonfinite observation')
  ids.append(idx);values.append(value)
  if method not in ('maximin','random'):
   c=covariance[:,idx].copy();covariance-=np.outer(c,c)/max(float(covariance[idx,idx])+ridge,1e-12)
 return ids,values,revisions
