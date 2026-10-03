"""Same-author second augmented-system arithmetic; no boundary runner imports."""
import gzip,hashlib,json,math,statistics,sys
from pathlib import Path
import numpy as np
from audit_representation_revision import model_bank
from audit_trend_revision import second_bank
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'results/trend_boundary/confirmation'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((folder/'manifest.json').read_text())
for p,h in manifest['source_sha256'].items():assert digest(ROOT/p)==h,p
for p,h in manifest['output_sha256'].items():assert digest(folder/p)==h,p
spec=json.loads((ROOT/'experiments/trend_boundary/spec.json').read_text())
rows=[json.loads(l) for l in gzip.open(folder/'traces.jsonl.gz','rt')]
lookup={(r['function'],r['seed'],r['noise'],r['domain'],r['method']):r for r in rows}
expected={(f,s,n,d,m) for f in spec['functions'] for s in spec['seeds'] for n in spec['noise_fractions'] for d in spec['tests'] for m in spec['methods']}
assert len(rows)==len(lookup)==len(expected) and set(lookup)==expected
archive=np.load(folder/'inputs_and_truth.npz',allow_pickle=False)
checked=0;max_scaled=0.;max_kkt=0.
for name in spec['functions']:
 for seed in spec['seeds']:
  pool=archive[f'{name}_{seed}_pool'];clean=archive[f'{name}_{seed}_clean']
  norm=2*(pool-pool.min(0))/np.maximum(np.ptp(pool,axis=0),1e-12)-1
  ids=list(map(int,np.random.default_rng(seed).choice(len(pool),spec['initial'],replace=False)))
  while len(ids)<spec['budget']:
   distances=np.min([((norm-norm[i])**2).sum(1) for i in ids],axis=0);distances[ids]=-np.inf;ids.append(int(np.argmax(distances)))
  for noise in spec['noise_fractions']:
   y=(clean+noise*clean.std()*np.random.default_rng(seed+1000000).normal(size=len(pool)))[ids]
   for domain in spec['tests']:
    test=archive[f'{name}_{seed}_{domain}_test'];truth=archive[f'{name}_{seed}_{domain}_truth']
    full=[m|{'key':(*m['key'],'constant')} for m in model_bank(pool,test,ids,y)]
    both=second_bank(pool,test,ids,y);affine=[m for m in both if m['key'][-1]=='affine']
    retained=[m for m in both if m['key'][-1]=='constant']
    arms=dict(original=full,remove_only=retained,add_only=full+affine,both=both)
    for method in spec['methods']:
     r=lookup[(name,seed,noise,domain,method)];assert r['selected']==ids
     assert r['input_sha256']==hashlib.sha256(pool.tobytes()+test.tobytes()).hexdigest()
     np.testing.assert_allclose(r['observed'],y,rtol=1e-13,atol=1e-13)
    for method,models in arms.items():
     r=lookup[(name,seed,noise,domain,method)];bank={m['key']:m for m in models}
     selected=[bank[(m['input'],m['response'],m['family'],m['ridge'],m['trend'])] for m in r['models']]
     for m,v in zip(selected,r['models']):np.testing.assert_allclose(m['cv'],v['loo_nmse'],rtol=2e-5,atol=1e-7)
     w=np.array([v['weight'] for v in r['models']]);assert min(w)>=0 and abs(sum(w)-1)<1e-12
     errors=np.column_stack([m['error'] for m in selected]);gram=errors.T@errors/len(y);gradient=gram@w;obj=float(w@gradient)
     kkt=max(float(np.maximum(obj-gradient,0).max()),float(abs(gradient[w>1e-7]-obj).max()))/max(float(abs(gram).max()),1e-15)
     assert kkt<1e-4,(name,seed,noise,method,kkt);max_kkt=max(max_kkt,kkt)
     pred=sum(float(a)*m['pred'] for a,m in zip(w,selected) if a>0)
     assert np.isfinite(pred).all()
     residual=abs(pred-truth);largest=float(max(residual));mean=statistics.fmean(map(float,truth))
     variance=max(statistics.fmean((float(v)-mean)**2 for v in truth),1e-30)
     logscore=-10000. if largest==0 else math.log(statistics.fmean((float(v)/largest)**2 for v in residual))+2*math.log(largest)-math.log(variance)
     # Use the preceding audits' explicit NMSE rtol=2e-5, atol=1e-7.
     # Also report floor-scaled discrepancies, which can exceed rtol near zero.
     relative=abs(math.expm1(logscore-r['log_nmse']))
     scaled=relative*math.exp(min(0,r['log_nmse']-math.log(1e-8)))
     allowed=2e-5+1e-7*math.exp(min(700,-r['log_nmse']))
     assert relative<=allowed,(name,seed,noise,domain,method,relative,allowed)
     max_scaled=max(max_scaled,scaled);checked+=1
 print(name,checked,flush=True)
summary=json.loads((folder/'summary.json').read_text());floor=math.log(1e-8);comparisons=0
for baseline,saved in summary['comparisons'].items():
 byfun={};strata={}
 for f in spec['functions']:
  values=[]
  for s in spec['seeds']:
   for n in spec['noise_fractions']:
    for d in spec['tests']:
     a=lookup[(f,s,n,d,'add_only')]['log_nmse'];b=lookup[(f,s,n,d,baseline)]['log_nmse']
     value=max(a,floor)-max(b,floor);values.append(value);strata.setdefault(f'{n}:{d}',[]).append(value)
  byfun[f]=statistics.fmean(values)
  assert math.isclose(byfun[f],saved['by_function_log_ratio'][f],abs_tol=1e-12)
 assert math.isclose(statistics.fmean(byfun.values()),saved['log_ratio'],abs_tol=1e-12)
 assert sum(v<0 for v in byfun.values())==saved['wins']
 for k,v in strata.items():assert math.isclose(statistics.fmean(v),saved['by_stratum_log_ratio'][k],abs_tol=1e-12)
 comparisons+=1
result=dict(passed=True,second_predictor_scores=checked,paired_trace_rows=len(rows),aggregate_comparisons=comparisons,max_floor_scaled_nmse_discrepancy=max_scaled,max_scaled_simplex_kkt=max_kkt,
 nmse_tolerance=dict(rtol=2e-5,atol=1e-7),
 controls_prediction_arithmetic_reconstructed=False,control_pairing_and_aggregation_checked=True,external_reproduction=False,independently_refitted_simplex_weights=False,
 audit_sources={p:digest(ROOT/p) for p in ['scripts/audit_trend_boundary.py','scripts/audit_trend_revision.py','scripts/audit_representation_revision.py']})
(folder/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
