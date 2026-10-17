"""Prospective wider-dimensional, positive/negative and misspecified family test."""
import argparse,gzip,hashlib,json,math,os,platform,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
import scipy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from experiments.trend_boundary.run import sample_shell,error_score
from experiments.representation_revision.run import select_coverage
from experiments.trend_factorial.develop import choose
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.trend_revision import TrendBank
from kernellum.discovery.additive_response import AdditiveResponseBank
from kernellum.discovery.adaptive_revision import AdaptiveStack
from kernellum.discovery.robust_revision import RobustStack
from kernellum.discovery.support_revision import SupportRouter


def sample(family,dimension,seed,spec):
 rng=np.random.default_rng(seed+100*dimension)
 center=rng.uniform(-.4,.4,dimension);second=rng.uniform(-.6,.6,dimension)
 rotation=np.linalg.qr(rng.normal(size=(dimension,dimension)))[0]
 curvature=(rotation*rng.uniform(1,8,dimension))@rotation.T
 slope=rng.uniform(-1,1,dimension);amplitude=float(rng.uniform(.5,3))
 def truth(z):
  g=amplitude*np.exp(-np.einsum('ni,ij,nj->n',z-center,curvature,z-center))
  if family=='gaussian':return g
  if family=='negative_gaussian':return -g
  if family in ('exp_affine','power_law'):return amplitude*np.exp(z@slope)
  if family=='convex_exponential':return amplitude*np.exp(.15*np.sum(z*z,axis=1)+z@slope)
  if family=='rational_peak':return amplitude/(1+np.einsum('ni,ij,nj->n',z-center,curvature,z-center))
  if family=='sine':return np.sin(3*z@slope)+.3*np.cos(2*z[:,0]*z[:,-1])
  if family=='signed_cubic':return z@slope+.3*z[:,0]**3+.2*z[:,0]*z[:,-1]
  if family=='gaussian_mixture':return g+.7*amplitude*np.exp(-3*np.sum((z-second)**2,axis=1))
  raise ValueError(family)
 z=rng.uniform(-1,1,(spec['pool_size'],dimension))
 tests=dict(inside=rng.uniform(-1,1,(spec['tests']['inside'],dimension)),
  near_shell=sample_shell_dimension(rng,spec['tests']['near_shell'],dimension,1.5,1),
  far_shell=sample_shell_dimension(rng,spec['tests']['far_shell'],dimension,3,1.5))
 coords=lambda a:np.exp(a) if family=='power_law' else a
 parameters=dict(center=center.tolist(),second_center=second.tolist(),curvature=curvature.tolist(),slope=slope.tolist(),amplitude=amplitude)
 return coords(z),truth(z),{k:(coords(v),truth(v)) for k,v in tests.items()},parameters


def sample_shell_dimension(rng,n,d,outer,inner):
 blocks=[];count=0
 while count<n:
  z=rng.uniform(-outer,outer,(2*n,d));z=z[np.max(abs(z),axis=1)>inner];blocks.append(z);count+=len(z)
 return np.concatenate(blocks)[:n]


def summarize(rows,spec):
 lookup={(r['function'],r['seed'],r['noise'],r['domain'],r['method']):r for r in rows}
 functions=[f'{f}_{d}d' for f in spec['families'] for d in spec['dimensions']]
 expected={(f,s,n,d,m) for f in functions for s in spec['seeds'] for n in spec['noise_fractions'] for d in spec['tests'] for m in spec['methods']}
 assert len(rows)==len(lookup)==len(expected) and set(lookup)==expected
 floor=math.log(spec['error_floor']);comparisons={}
 for baseline in spec['methods']:
  if baseline==spec['primary']:continue
  byfun={};strata={};bad=[]
  for f in functions:
   values=[]
   for s in spec['seeds']:
    for n in spec['noise_fractions']:
     for d in spec['tests']:
      key=(f,s,n,d);a=lookup[(*key,spec['primary'])];b=lookup[(*key,baseline)]
      if not a['finite_prediction'] or not b['finite_prediction']:bad.append(list(key));continue
      value=max(a['log_nmse'],floor)-max(b['log_nmse'],floor)
      values.append(value);strata.setdefault(f'{n}:{d}',[]).append(value)
   byfun[f]=statistics.fmean(values) if values else None
  exp_safe=lambda v:math.exp(v) if v is not None and v<709 else None
  lr=statistics.fmean(byfun.values()) if all(v is not None for v in byfun.values()) else None
  comparisons[baseline]=dict(ratio=exp_safe(lr),log_ratio=lr,wins=sum(v is not None and v<0 for v in byfun.values()),
   by_function={f:exp_safe(v) for f,v in byfun.items()},by_function_log_ratio=byfun,
   by_stratum={k:exp_safe(statistics.fmean(v)) for k,v in strata.items()},
   by_stratum_log_ratio={k:statistics.fmean(v) for k,v in strata.items()},invalid_pairs=bad)
 g=spec['gate'];passed=all(not v['invalid_pairs'] and v['log_ratio'] is not None and v['log_ratio']<=math.log(g['ratio_max']) and
  v['wins']/len(functions)>=g['win_fraction_min'] and max(v['by_stratum_log_ratio'].values())<=math.log(g['each_noise_and_domain_ratio_max']) for v in comparisons.values())
 # Scoped prediction, deliberately separate from broad gate and tail claims.
 values=[];wins=[];exact=[];bad=[];bygroup={}
 for f in ['gaussian','negative_gaussian']:
  for dimension in spec['dimensions']:
   name=f'{f}_{dimension}d'
   for s in spec['seeds']:
    a=lookup[(name,s,0.,'inside',spec['primary'])]
    exact.append(a['finite_prediction'] and a['log_nmse']<=floor)
    for n in [v for v in spec['noise_fractions'] if v>0]:
     for d in spec['tests']:
      a=lookup[(name,s,n,d,spec['primary'])];b=lookup[(name,s,n,d,'adaptive_stack')]
      if not a['finite_prediction'] or not b['finite_prediction']:bad.append((name,s,n,d));continue
      value=max(a['log_nmse'],floor)-max(b['log_nmse'],floor);values.append(value)
      bygroup.setdefault(f'{dimension}d:{n}:{d}',[]).append(value)
      if d=='inside':wins.append(value<0)
 mg=spec['mechanism_gate'];logratio=statistics.fmean(values)
 mechanism=dict(ratio_vs_adaptive=math.exp(logratio),inside_seed_wins=sum(wins),inside_seed_trials=len(wins),
  clean_exact_trials=sum(exact),clean_trials=len(exact),invalid_pairs=bad,
  by_dimension_noise_domain={k:math.exp(statistics.fmean(v)) for k,v in bygroup.items()},
  passed=not bad and logratio<=math.log(mg['noisy_gaussian_vs_adaptive_ratio_max']) and statistics.fmean(wins)>=mg['noisy_gaussian_inside_seed_win_fraction_min'] and statistics.fmean(exact)>=mg['clean_gaussian_inside_exact_fraction_min'])
 tails={m:dict(worst_log10_nmse=max(r['log_nmse'] for r in rows if r['method']==m and r['finite_prediction'])/math.log(10),
  errors_above_one=sum(r['finite_prediction'] and r['log_nmse']>0 for r in rows if r['method']==m),nonfinite_scores=sum(not r['finite_prediction'] for r in rows if r['method']==m)) for m in spec['methods']}
 return dict(scores=len(rows),paths=len(functions)*len(spec['seeds'])*len(spec['noise_fractions']),criterion_supported=passed,
  mechanism=mechanism,comparisons=comparisons,tails=tails,field_breakthrough_established=False)


def run(out,public_freeze):
 spec=json.loads((ROOT/'experiments/additive_response/spec.json').read_text());out.mkdir(parents=True,exist_ok=False)
 paths=['experiments/additive_response/run.py','experiments/additive_response/spec.json','docs/ADDITIVE_RESPONSE_PROTOCOL.md',
  'kernellum/discovery/additive_response.py','experiments/trend_boundary/run.py','experiments/representation_revision/run.py',
  'experiments/trend_factorial/develop.py','kernellum/discovery/representation.py','kernellum/discovery/trend_revision.py',
  'kernellum/discovery/revision.py','kernellum/discovery/aggregation.py','kernellum/discovery/robust_revision.py',
  'kernellum/discovery/adaptive_revision.py','kernellum/discovery/support_revision.py']
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 manifest=dict(public_freeze=public_freeze,local_freeze=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  source_sha256={p:digest(ROOT/p) for p in paths},python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
  threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']})
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 arrays={};rows=[];parameters={};start=time.perf_counter();failures=[]
 with gzip.open(out/'traces.jsonl.gz','wt') as file:
  for family in spec['families']:
   for dimension in spec['dimensions']:
    name=f'{family}_{dimension}d'
    for seed in spec['seeds']:
     pool,clean,tests,par=sample(family,dimension,seed,spec);parameters[f'{name}_{seed}']=par
     ids=select_coverage(pool,spec,seed);arrays[f'{name}_{seed}_pool']=pool;arrays[f'{name}_{seed}_clean']=clean
     for domain,(xt,truth) in tests.items():arrays[f'{name}_{seed}_{domain}_test']=xt;arrays[f'{name}_{seed}_{domain}_truth']=truth
     for noise in spec['noise_fractions']:
      y=(clean+noise*clean.std()*np.random.default_rng(seed+1000000+dimension).normal(size=len(pool)))[ids]
      # Original fit calculated separately from augmented fit to prevent candidate mutations of controls.
      bank=RepresentationBank(pool).fit(ids,y);trend=TrendBank(bank);augmented=AdditiveResponseBank(pool).fit(ids,y)
      failures.append(dict(function=name,seed=seed,noise=noise,nonlinear_models_failed=augmented.nonlinear_failures))
      old_adaptive=AdaptiveStack(bank);new_adaptive=AdaptiveStack(augmented);robust=RobustStack(bank)
      full=[m|{'trend':'constant'} for m in bank.models];affine=[m for m in trend.models if m['trend']=='affine']
      chosen={a:choose(v) for a,v in dict(original=full,add_only=full+affine).items()}
      exponential=[m for m in augmented.models if m['family'].startswith('exp_')]
      exp_model=(exponential or bank.eligible('raw'))[0]
      for domain,(xt,truth) in tests.items():
       predictors={a:(lambda a=a:sum(w*trend.predict_model(m,xt) for m,w in zip(*chosen[a]) if w>0)) for a in chosen}
       predictors.update(adaptive_stack=lambda:old_adaptive.predict(xt)[0],median_stack=lambda:robust.predict(xt)['median_stack'],
        support_nonlinear_leverage_stack=lambda:SupportRouter(bank,xt).predict('support_nonlinear_leverage_stack')[0],
        exponential_only=lambda:augmented.predict_model(exp_model,xt),augmented_winner=lambda:augmented.predict(xt,'representation'),
        augmented_adaptive=lambda:new_adaptive.predict(xt)[0])
       for method in spec['methods']:
        selected,weights=chosen[method] if method in chosen else (([exp_model],np.ones(1)) if method=='exponential_only' else
         (augmented.selected('representation') if method=='augmented_winner' else augmented.selected('representation_stack') if method=='augmented_adaptive' else bank.selected('representation_stack')))
        metadata=[{k:m.get(k) for k in ['input','response','family','trend','ridge','original_cv']}|dict(weight=float(w),theta=m.get('theta',np.array([])).tolist(),amplitude=m.get('amplitude'),sign=m.get('sign')) for m,w in zip(selected,weights)]
        try:score=error_score(predictors[method](),truth)
        except (FloatingPointError,OverflowError,np.linalg.LinAlgError) as exc:score=dict(log_nmse=None,nmse=None,finite_prediction=False,max_abs_prediction=None,prediction_exception=str(exc))
        r=dict(function=name,seed=seed,noise=noise,domain=domain,method=method,selected=ids,observed=y.tolist(),models=metadata,
         log_response_available=bool(np.all(y>0) or np.all(y<0)),input_sha256=hashlib.sha256(pool.tobytes()+xt.tobytes()).hexdigest(),**score)
        rows.append(r);file.write(json.dumps(r,allow_nan=False)+'\n')
    print(name,len(rows),round(time.perf_counter()-start,1),flush=True)
 np.savez_compressed(out/'inputs_and_truth.npz',**arrays)
 (out/'parameters.json').write_text(json.dumps(parameters,indent=2)+'\n');(out/'optimizer_failures.json').write_text(json.dumps(failures,indent=2)+'\n')
 summary=summarize(rows,spec);(out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
 manifest['output_sha256']={p.name:digest(p) for p in out.iterdir() if p.name!='manifest.json'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(summary,indent=2,allow_nan=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--public-freeze',required=True);a=p.parse_args();run(a.out,a.public_freeze)
