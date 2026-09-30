"""Second arithmetic implementation; does not import the candidate or runner.

Verifies augmented-system fits, original-scale LOO selection, simplex KKT
conditions, measurement budget, source digests, all predictions and all gates.
This is same-author verification, not external independent reproduction.
"""
import argparse,gzip,hashlib,inspect,itertools,json,time
from pathlib import Path
import numpy as np
import uqtestfuns as uqtf
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('linear','quadratic','cubic','rbf_short','rbf_medium','rbf_long')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inverse(v,kind):return v if kind=='identity' else (1 if kind=='log_positive' else -1)*np.exp(np.minimum(v,700))

def matrices(x,xt):
 d=x.shape[1];out={}
 for i,name in enumerate(FAMILIES[:3],1):
  scale=np.mean((1+(x*x).sum(1)/d)**i)
  out[name]=((1+x@x.T/d)**i/scale,(1+xt@x.T/d)**i/scale)
 for length,name in zip((.4,.8,1.6),FAMILIES[3:]):
  out[name]=tuple(np.exp(-((v[:,None]-x[None,:])**2).sum(2)/(2*length**2*d)) for v in (x,xt))
 return out

def model_bank(pool,test,ids,ys):
 sign=np.where(pool.min(0)>0,1,np.where(pool.max(0)<0,-1,0));banks={};models=[];n=len(ids)
 for xkind in (('identity','log') if np.any(sign) else ('identity',)):
  x=pool.copy();xt=test.copy()
  if xkind=='log':
   cols=sign!=0;x[:,cols]=np.log(x[:,cols]*sign[cols]);xt[:,cols]=np.log(xt[:,cols]*sign[cols])
  low=x.min(0);span=np.maximum(np.ptp(x,axis=0),1e-12)
  banks[xkind]=matrices(2*(x-low)/span-1,2*(xt-low)/span-1)
 transforms=[('identity',ys)]
 if np.all(ys>0):transforms.append(('log_positive',np.log(ys)))
 if np.all(ys<0):transforms.append(('log_negative',np.log(-ys)))
 for xkind,bank in banks.items():
  for ykind,yt in transforms:
   center=yt.mean();scale=max(float(yt.std()),1e-12);z=(yt-center)/scale
   for name,(kp,kt) in bank.items():
    for ridge in (1e-6,1e-3,.1):
     a=np.ones((n+1,n+1));a[-1,-1]=0;a[:n,:n]=kp[np.ix_(ids,ids)]+ridge*np.eye(n)
     inv=np.linalg.solve(a,np.eye(n+1));coef=inv@np.r_[z,0]
     err=(ys-inverse(center+scale*(z-coef[:n]/np.maximum(np.diag(inv)[:n],1e-12)),ykind))/max(float(ys.std()),1e-12)
     with np.errstate(over='ignore',invalid='ignore'):cv=float(np.mean(err**2))
     models.append(dict(key=(xkind,ykind,name,ridge),error=err,cv=cv,
       pred=inverse(center+scale*(kt[:,ids]@coef[:n]+coef[-1]),ykind)))
 return sorted(models,key=lambda m:m['cv'])

def select(models,method):
 eligible=models
 if method in ('raw','raw_stack'):eligible=[m for m in models if m['key'][:2]==('identity','identity')]
 if method=='input_only':eligible=[m for m in models if m['key'][1]=='identity']
 if method=='output_only':eligible=[m for m in models if m['key'][0]=='identity']
 if method=='log_linear':
  eligible=[m for m in models if m['key'][0]=='log' and m['key'][1]!='identity' and m['key'][2]=='linear']
  eligible=eligible or [m for m in models if m['key'][:3]==('identity','identity','linear')]
 if not method.endswith('_stack'):return eligible[:1]
 chosen=[];seen=set()
 for m in eligible:
  key=m['key'][:3]
  if key not in seen and np.isfinite(m['cv']):chosen.append(m);seen.add(key)
  if len(chosen)==6:break
 return chosen

def audit(folder,out):
 start=time.perf_counter();spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
 assert uqtf.__version__==spec['uqtestfuns']
 manifest=json.loads((folder/'manifest.json').read_text())
 for name,sha in manifest['source_hashes'].items():assert digest(ROOT/name)==sha,name
 for name,sha in manifest['output_hashes'].items():assert digest(folder/name)==sha,name
 with gzip.open(folder/'traces.jsonl.gz','rt') as f:records=[json.loads(line) for line in f]
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in records}
 expected=set(itertools.product([c['name'] for c in spec['cohort']],spec['seeds'],spec['noise_fractions'],spec['methods']))
 assert len(records)==len(lookup)==len(expected) and set(lookup)==expected
 checked=0;max_error=0.;max_scaled_error=0.;max_error_case=None;max_kkt=0.;recomputed={}
 for index,case in enumerate(spec['cohort']):
  fun=getattr(uqtf,case['name'])();assert digest(Path(inspect.getfile(type(fun))))==case['source_sha256']
  for seed in spec['seeds']:
   fun.prob_input.reset_rng(seed+1000*index);x=fun.prob_input.get_sample(spec['pool_size']);xt=fun.prob_input.get_sample(spec['test_size'])
   yp=np.asarray(fun(x)).reshape(-1);yt=np.asarray(fun(xt)).reshape(-1)
   z=2*(x-x.min(0))/np.maximum(np.ptp(x,axis=0),1e-12)-1
   ids=list(map(int,np.random.default_rng(seed).choice(len(x),spec['initial'],replace=False)))
   while len(ids)<spec['budget']:
    distances=np.min([((z-z[i])**2).sum(1) for i in ids],axis=0);distances[ids]=-np.inf;ids.append(int(np.argmax(distances)))
   for noise in spec['noise_fractions']:
    y=yp+noise*np.std(yp)*np.random.default_rng(seed+1000000+index).normal(size=len(x))
    for method in spec['methods']:
     r=lookup[(case['name'],seed,noise,method)];assert r['selected']==ids
     assert r['input_sha256']==hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest()
     np.testing.assert_allclose(r['observed'],y[ids],rtol=1e-13,atol=1e-13)
     assert [v['budget'] for v in r['metrics']]==spec['checkpoints']
    for j,budget in enumerate(spec['checkpoints']):
     models=model_bank(x,xt,ids[:budget],y[ids[:budget]])
     for method in spec['methods']:
      key=(case['name'],seed,noise,method);m=lookup[key]['metrics'][j];selected=select(models,method)
      keys=[v['key'] for v in selected];stored=[(v['input'],v['response'],v['family'],v['ridge']) for v in m['models']]
      assert keys==stored,(key,budget,keys,stored)
      np.testing.assert_allclose([v['cv'] for v in selected],[v['loo_nmse'] for v in m['models']],rtol=1e-5,atol=1e-7)
      w=np.array([v['weight'] for v in m['models']]);assert w.min()>=0 and abs(w.sum()-1)<1e-12
      errors=np.column_stack([v['error'] for v in selected]);gram=errors.T@errors/budget
      grad=gram@w;obj=float(w@grad);norm=max(float(np.abs(gram).max()),1e-15)
      # Convex-simplex KKT: all coordinates have gradient >= active gradient.
      kkt=max(float(np.max(np.maximum(obj-grad,0))),float(np.max(np.abs(grad[w>1e-7]-obj))))/norm
      max_kkt=max(max_kkt,kkt);assert kkt<2e-5,(key,budget,kkt)
      pred=sum(ww*v['pred'] for ww,v in zip(w,selected) if ww>0)
      nmse=float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30))
      discrepancy=abs(nmse-m['nmse'])
      if discrepancy>max_error:max_error=discrepancy;max_error_case=dict(function=case['name'],seed=seed,noise=noise,method=method,budget=budget,recorded_nmse=m['nmse'])
      max_scaled_error=max(max_scaled_error,discrepancy/max(abs(m['nmse']),1e-7));checked+=1
      np.testing.assert_allclose(nmse,m['nmse'],rtol=2e-5,atol=1e-7)
      if budget==spec['budget']:recomputed[key]=nmse
  print(case['name'],checked,flush=True)
 summary=json.loads((folder/'summary.json').read_text());comparisons={}
 for baseline in spec['baselines']:
  byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
  for case in spec['cohort']:
   vals=[]
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     k=(case['name'],seed,noise)
     v=np.log(max(recomputed[(*k,spec['primary'])],spec['error_floor']))-np.log(max(recomputed[(*k,baseline)],spec['error_floor']))
     vals.append(v);bynoise[str(noise)].append(v)
   byfun[case['name']]=float(np.exp(np.mean(vals)))
  comparisons[baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),win_fraction=float(np.mean(np.array(list(byfun.values()))<1)),by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()})
  np.testing.assert_allclose(comparisons[baseline]['ratio'],summary['comparisons'][baseline]['ratio'],rtol=1e-5)
 g=spec['gates'];passed=all(v['ratio']<=g['ratio_max'] and v['win_fraction']>=g['win_fraction_min'] and max(v['by_noise'].values())<=g['each_noise_ratio_max'] for v in comparisons.values())
 assert passed==summary['criterion_supported']
 result=dict(passed=True,criterion_supported=passed,checkpoint_errors_recomputed=checked,runs=len(records),functions=len(spec['cohort']),
  unique_observation_trajectories=len(spec['cohort'])*len(spec['seeds'])*len(spec['noise_fractions']),max_absolute_nmse_discrepancy=max_error,max_absolute_discrepancy_case=max_error_case,max_scaled_nmse_discrepancy=max_scaled_error,max_relative_simplex_kkt_violation=max_kkt,
  description='Second arithmetic implementation by same author, not external independent reproduction.',seconds=time.perf_counter()-start,audit_sha256=digest(Path(__file__)))
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();audit(a.folder,a.out)
