"""Separate forward/aggregate arithmetic; reuses nonlinear fold-fit primitive.

This is same-author partial algorithm verification, not external reproduction.
Kernel fits use augmented systems. Exponential forward evaluation and ensemble
arithmetic are separate; nonlinear LOO optimizations reuse candidate fit_exp.
"""
import gzip,hashlib,json,math,statistics,sys,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from audit_representation_revision import model_bank
from audit_trend_revision import second_bank
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from kernellum.discovery.additive_response import fit_exp


def transformed(pool,test,kind):
 signs=np.where(pool.min(0)>0,1,np.where(pool.max(0)<0,-1,0));x=pool.copy();xt=test.copy()
 if kind=='log':
  mask=signs!=0;x[:,mask]=np.log(x[:,mask]*signs[mask]);xt[:,mask]=np.log(xt[:,mask]*signs[mask])
 low=x.min(0);span=np.maximum(np.ptp(x,axis=0),1e-12)
 return 2*(x-low)/span-1,2*(xt-low)/span-1


def exponential(theta,x,family,ceiling=700):
 d=x.shape[1];latent=np.full(len(x),theta[0])+np.sum(x*theta[1:1+d],axis=1)
 jac=np.c_[np.ones(len(x)),x]
 if family=='exp_concave':
  lower=np.zeros((d,d));ij=np.tril_indices(d);lower[ij]=theta[1+d:]
  cross=np.column_stack([sum(lower[i,j]*x[:,i] for i in range(j,d)) for j in range(d)])
  latent-=sum(cross[:,j]**2 for j in range(d))
  jac=np.c_[jac,np.column_stack([-2*x[:,i]*cross[:,j] for i,j in zip(*ij)])]
 pred=np.exp(np.minimum(latent,ceiling));jac*=pred[:,None];jac[latent>ceiling]=0
 return pred,jac


def stable_score(pred,truth):
 assert np.isfinite(pred).all()
 residual=np.abs(pred-truth);largest=float(max(residual));mean=statistics.fmean(map(float,truth))
 variance=max(statistics.fmean((float(v)-mean)**2 for v in truth),1e-30)
 return -10000. if largest==0 else math.log(statistics.fmean((float(v)/largest)**2 for v in residual))+2*math.log(largest)-math.log(variance)


def weighted_median(values,w):
 result=[]
 for row in values:
  pairs=sorted((float(v),float(weight)) for v,weight in zip(row,w) if weight>0);total=0.
  for v,weight in pairs:
   total+=weight
   if total>=.5*sum(w):result.append(v);break
 return np.array(result)


def audit(folder,kind):
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 manifest=json.loads((folder/'manifest.json').read_text())
 for p,h in manifest['source_sha256'].items():assert digest(ROOT/p)==h,p
 for p,h in manifest['output_sha256'].items():assert digest(folder/p)==h,p
 rows=[json.loads(l) for l in gzip.open(folder/'traces.jsonl.gz','rt')]
 spec=json.loads((ROOT/'experiments/additive_response/spec.json').read_text());methods=spec['methods'];primary=spec['primary']
 if kind=='synthetic':
  functions=[f'{f}_{d}d' for f in spec['families'] for d in spec['dimensions']];seeds=spec['seeds'];noises=spec['noise_fractions'];domains=list(spec['tests'])
  archive=np.load(folder/'inputs_and_truth.npz',allow_pickle=False)
 else:
  functions=['Eckerle4','Gauss1','Gauss2','Lanczos3','Hahn1','Bennett5'];seeds=list(range(104401,104411));noises=[0.];domains=['held_out']
 lookup={(r['function'],r['seed'],r.get('noise',0.),r.get('domain','held_out'),r['method']):r for r in rows}
 expected={(f,s,n,d,m) for f in functions for s in seeds for n in noises for d in domains for m in methods}
 assert len(rows)==len(lookup)==len(expected) and set(lookup)==expected
 checked=0;max_scaled=0.;max_kkt=0.;nonlinear_checks=[];failures=[];second_scores={};start=time.perf_counter()
 for name in functions:
  for seed in seeds:
   if kind=='synthetic':
    pool=archive[f'{name}_{seed}_pool'];clean=archive[f'{name}_{seed}_clean'];initial=16;budget=64
    tests={d:(archive[f'{name}_{seed}_{d}_test'],archive[f'{name}_{seed}_{d}_truth']) for d in domains}
   else:
    p=ROOT/'experiments/additive_response/nist_data'/f'{name}.csv';assert digest(p)==manifest['data_manifest'][name]['csv_sha256']
    data=np.loadtxt(p,delimiter=',',skiprows=1);pool=data[:,1:];clean=data[:,0];initial=8;budget=min(64,len(pool)//2)
   norm=2*(pool-pool.min(0))/np.maximum(np.ptp(pool,axis=0),1e-12)-1
   ids=list(map(int,np.random.default_rng(seed).choice(len(pool),initial,replace=False)))
   while len(ids)<budget:
    distances=np.min([((norm-norm[i])**2).sum(1) for i in ids],axis=0);distances[ids]=-np.inf;ids.append(int(np.argmax(distances)))
   if kind=='nist':
    test_ids=[i for i in range(len(pool)) if i not in ids];tests={'held_out':(pool[test_ids],clean[test_ids])}
   test=np.concatenate([v[0] for v in tests.values()]);boundaries=np.cumsum([0]+[len(v[0]) for v in tests.values()])
   for noise in noises:
    y=(clean+noise*clean.std()*np.random.default_rng(seed+1000000+pool.shape[1]).normal(size=len(pool)))[ids] if kind=='synthetic' else clean[ids]
    yscale=max(float(y.std()),1e-12);full=model_bank(pool,test,ids,y);both=second_bank(pool,test,ids,y)
    bank={(*m['key'],'constant'):m for m in full};bank.update({m['key']:m for m in both if m['key'][-1]=='affine'})
    cache={}
    def get(desc,need_error=False):
     key=(desc['input'],desc['response'],desc['family'],desc['ridge'],desc.get('trend') or 'constant')
     if not desc['family'].startswith('exp_'):return bank[key]
     if key not in cache:
      x,xt=transformed(pool,test,desc['input']);theta=np.array(desc['theta']);sign=desc['sign'];amplitude=desc['amplitude']
      pred=sign*amplitude*exponential(theta,xt,desc['family'])[0]
      xtrain=x[ids];target=sign*y/amplitude
      def objective(t):
       v,j=exponential(t,xtrain,desc['family'],40);residual=v-target
       return float(residual@residual),2*j.T@residual
      bounds=[(None,None)]*len(theta)
      if desc['family']=='exp_concave':
       ij=np.tril_indices(pool.shape[1])
       for i in np.flatnonzero(ij[0]==ij[1]):bounds[1+pool.shape[1]+i]=(0,None)
      refit=minimize(objective,theta,method='L-BFGS-B',jac=True,bounds=bounds,options=dict(maxiter=300,ftol=1e-14,gtol=1e-9))
      orig=objective(theta)[0];improvement=max(0,float(orig-refit.fun))/max(orig,1e-12)
      nonlinear_checks.append(dict(function=name,seed=seed,noise=noise,key=list(key),success=bool(refit.success),relative_objective_improvement=improvement))
      cache[key]=dict(pred=pred,x=xtrain,sign=sign,amplitude=amplitude,desc=desc)
     m=cache[key]
     if need_error and 'error' not in m:
      loo=[]
      for i in range(len(y)):
       mask=np.arange(len(y))!=i;amplitude=max(float(abs(y[mask]).max()),1e-12)
       theta=fit_exp(m['x'][mask],m['sign']*y[mask]/amplitude,desc['family'])
       loo.append(m['sign']*amplitude*exponential(theta,m['x'][i:i+1],desc['family'],40)[0][0])
      m['error']=(y-np.array(loo))/yscale;m['cv']=float(np.mean(m['error']**2))
     return m
    for di,domain in enumerate(domains):
     xt,truth=tests[domain];section=slice(boundaries[di],boundaries[di+1])
     for method in methods:
      r=lookup[(name,seed,noise,domain,method)];assert r['selected']==ids
      np.testing.assert_allclose(r['observed'],y,rtol=1e-13,atol=1e-13)
      if kind=='synthetic':assert r['input_sha256']==hashlib.sha256(pool.tobytes()+xt.tobytes()).hexdigest()
      else:assert r['test_ids']==test_ids and set(ids).isdisjoint(test_ids)
      if method=='support_nonlinear_leverage_stack':continue
      adaptive=method in ('adaptive_stack','augmented_adaptive');median=method=='median_stack'
      models=[get(v,need_error=adaptive or median or method in ('original','add_only')) for v in r['models']]
      w=np.array([v['weight'] for v in r['models']]);assert min(w)>=0 and abs(sum(w)-1)<1e-12
      if adaptive or median or method in ('original','add_only'):
       error=np.column_stack([m['error'] for m in models]);gram=error.T@error/len(y);gradient=gram@w;obj=float(w@gradient)
       kkt=max(float(np.maximum(obj-gradient,0).max()),float(abs(gradient[w>1e-7]-obj).max()))/max(float(abs(gram).max()),1e-15)
       assert kkt<1e-4,(name,seed,noise,method,kkt);max_kkt=max(max_kkt,kkt)
       for m,d in zip(models,r['models']):np.testing.assert_allclose(m['cv'],d['original_cv'],rtol=2e-5,atol=1e-7)
      components=np.column_stack([m['pred'][section] for m in models]);pred=components@w
      if median:pred=weighted_median(components,w)
      if adaptive:
       loo=y[:,None]-yscale*error;spread=np.ptp(loo,axis=1);center=float(np.median(spread));mad=float(np.median(abs(spread-center)))
       threshold=float(np.quantile(spread,.95)+2*max(mad,1e-12));use=np.ptp(components,axis=1)>threshold
       pred[use]=weighted_median(components,w)[use]
      score=stable_score(pred,truth);relative=abs(math.expm1(score-r['log_nmse']));scaled=relative*math.exp(min(0,r['log_nmse']-math.log(1e-8)))
      allowed=2e-5+1e-7*math.exp(min(700,-r['log_nmse']))
      if relative>allowed:failures.append(dict(function=name,seed=seed,noise=noise,domain=domain,method=method,relative=relative,allowed=allowed))
      max_scaled=max(max_scaled,scaled);checked+=1;second_scores[(name,seed,noise,domain,method)]=score
  print(kind,name,checked,round(time.perf_counter()-start,1),flush=True)
 summary=json.loads((folder/'summary.json').read_text());floor=math.log(1e-8);aggregate_checks=0
 for baseline,saved in summary['comparisons'].items():
  byfun={};strata={}
  for f in functions:
   values=[]
   for s in seeds:
    for n in noises:
     for d in domains:
      a=lookup[(f,s,n,d,primary)];b=lookup[(f,s,n,d,baseline)]
      assert a['finite_prediction'] and b['finite_prediction']
      value=max(a['log_nmse'],floor)-max(b['log_nmse'],floor);values.append(value);strata.setdefault(f'{n}:{d}',[]).append(value)
   byfun[f]=statistics.fmean(values);assert math.isclose(byfun[f],saved['by_function_log_ratio'][f],abs_tol=1e-12)
  assert math.isclose(statistics.fmean(byfun.values()),saved['log_ratio'],abs_tol=1e-12)
  assert sum(v<0 for v in byfun.values())==saved['wins']
  if kind=='synthetic':
   for k,v in strata.items():assert math.isclose(statistics.fmean(v),saved['by_stratum_log_ratio'][k],abs_tol=1e-12)
  aggregate_checks+=1
 if kind=='synthetic':
  names=['gaussian_2d','gaussian_4d','negative_gaussian_2d','negative_gaussian_4d'];wins=[];exact=[];values=[]
  for f in names:
   for s in seeds:
    exact.append(lookup[(f,s,0.,'inside',primary)]['log_nmse']<=floor)
    for n in (.01,.1):
     for d in domains:
      v=max(lookup[(f,s,n,d,primary)]['log_nmse'],floor)-max(lookup[(f,s,n,d,'adaptive_stack')]['log_nmse'],floor);values.append(v)
      if d=='inside':wins.append(v<0)
  m=summary['mechanism'];assert sum(wins)==m['inside_seed_wins'] and sum(exact)==m['clean_exact_trials']
  assert math.isclose(math.exp(statistics.fmean(values)),m['ratio_vs_adaptive'],rel_tol=1e-12)
  second_exact=sum(second_scores[(f,s,0.,'inside',primary)]<=floor for f in names for s in seeds)
  assert second_exact==m['clean_exact_trials']
 else:second_exact=None
 result=dict(passed=not failures,paired_rows=len(rows),separate_forward_scores=checked,aggregate_comparisons=aggregate_checks,
  max_floor_scaled_nmse_discrepancy=max_scaled,max_scaled_simplex_kkt=max_kkt,nmse_tolerance=dict(rtol=2e-5,atol=1e-7),
  discrepancies=failures,second_clean_exact_trials=second_exact,nonlinear_full_fit_optimizer_checks=len(nonlinear_checks),
  nonlinear_second_optimizer_unsuccessful=sum(not v['success'] for v in nonlinear_checks),
  max_nonlinear_relative_objective_improvement=max((v['relative_objective_improvement'] for v in nonlinear_checks),default=0),
  verification_limits='Same author. Kernel augmented systems and separate exponential forward/ensemble arithmetic. Reuses candidate fit_exp only for nonlinear LOO coefficient optimization. Full nonlinear optimizer cross-check starts at recorded theta, so it tests local stationarity, not global optimality. Support-control pairing/aggregates checked, prediction rule not reconstructed. Stored weights checked by KKT, not independently refit. No external reproduction.',
  source_sha256={p:digest(ROOT/p) for p in ['scripts/audit_additive_response.py','scripts/audit_trend_revision.py','scripts/audit_representation_revision.py']})
 (folder/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(folder/'nonlinear_optimizer_audit.json').write_text(json.dumps(nonlinear_checks,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':
 audit(ROOT/'results/additive_response/confirmation','synthetic')
 audit(ROOT/'results/additive_response/nist_transfer','nist')
