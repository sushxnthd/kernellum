"""Same-author second-arithmetic check of all exploratory acquisition outcomes.

Reuses only the separately implemented block-system algebra from the preceding
arithmetic audit. Does not import acquisition, predictor or experiment modules.
Checks budgets and outcomes, not a second implementation of adaptive score ranks.
"""
import gzip,hashlib,inspect,itertools,json,time
from pathlib import Path
import numpy as np
import uqtestfuns as u
import audit_representation_revision as arithmetic
from audit_representation_revision import model_bank
ROOT=Path(__file__).resolve().parents[1]

# Reuse identical input-only matrices across acquisition arms. Fits and model
# choices are still recomputed independently for every distinct queried design.
original_matrices=arithmetic.matrices
matrix_cache={}
def cached_matrices(x,xt):
 key=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest()
 if key not in matrix_cache:matrix_cache[key]=original_matrices(x,xt)
 return matrix_cache[key]
arithmetic.matrices=cached_matrices

def main():
 start=time.perf_counter();spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text());seeds=spec['seeds'][:2]
 base=ROOT/'results/representation_acquisition';records=[]
 for folder in ('development','second_screen'):
  with gzip.open(base/folder/'traces.jsonl.gz','rt') as f:records.extend(json.loads(l) for l in f)
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in records};methods=sorted({r['method'] for r in records})
 expected=set(itertools.product([c['name'] for c in spec['cohort']],seeds,spec['noise_fractions'],methods))
 assert len(records)==len(lookup)==len(expected) and set(lookup)==expected
 exact_folder=ROOT/'results/representation_revision/confirmation';meta=json.loads((exact_folder/'exact_nonuniform_inputs.json').read_text())
 exact=np.load(exact_folder/'exact_nonuniform_inputs.npz',allow_pickle=False)
 assert hashlib.sha256((exact_folder/'exact_nonuniform_inputs.npz').read_bytes()).hexdigest()==meta['sha256']
 checked=0;maximum=0.;scaled=0.;errors={};finished=[]
 checkpoint=ROOT/'build/representation-acquisition-audit-checkpoint.json'
 fingerprint=hashlib.sha256(Path(__file__).read_bytes()+b''.join((base/f/'traces.jsonl.gz').read_bytes() for f in ('development','second_screen'))).hexdigest()
 if checkpoint.exists():
  saved=json.loads(checkpoint.read_text())
  if saved['fingerprint']==fingerprint:
   checked=saved['checked'];maximum=saved['maximum'];scaled=saved['scaled'];finished=saved['finished'];errors={tuple(k):v for k,v in saved['errors']}
 for index,case in enumerate(spec['cohort']):
  if case['name'] in finished:continue
  fun=getattr(u,case['name'])();assert hashlib.sha256(Path(inspect.getfile(type(fun))).read_bytes()).hexdigest()==case['source_sha256']
  for seed in seeds:
   matrix_cache.clear()
   fun.prob_input.reset_rng(seed+1000*index);x=fun.prob_input.get_sample(spec['pool_size']);xt=fun.prob_input.get_sample(spec['test_size'])
   if case['name'] in meta['columns']:
    cols=meta['columns'][case['name']]
    for arr,kind in ((x,'pool'),(xt,'test')):
     original=exact[f"{case['name']}_{seed}_{kind}"];scale=np.maximum(abs(original).max(0),1e-12)
     np.testing.assert_allclose(arr[:,cols]/scale,original/scale,atol=1e-12,rtol=1e-12);arr[:,cols]=original
   clean=np.asarray(fun(x)).reshape(-1);truth=np.asarray(fun(xt)).reshape(-1)
   initial=np.random.default_rng(seed).choice(len(x),16,replace=False).tolist()
   for noise in spec['noise_fractions']:
    y=clean+noise*np.std(clean)*np.random.default_rng(seed+1000000+index).normal(size=len(x))
    for method in methods:
     key=(case['name'],seed,noise,method);r=lookup[key];ids=r['selected'];assert len(ids)==len(set(ids))==64 and ids[:16]==initial
     assert all(0<=i<len(x) for i in ids)
     np.testing.assert_allclose(r['observed'],y[ids],rtol=1e-13,atol=1e-13)
     models=model_bank(x,xt,ids,np.asarray(r['observed']));m=models[0];recorded=r['model'][0]
     assert m['key']==tuple(recorded[k] for k in ('input','response','family','ridge')),(key,m['key'],recorded)
     error=float(np.mean((m['pred']-truth)**2)/max(float(np.var(truth)),1e-30));delta=abs(error-r['nmse'])
     maximum=max(maximum,delta);scaled=max(scaled,delta/max(abs(r['nmse']),1e-7))
     np.testing.assert_allclose(error,r['nmse'],rtol=2e-5,atol=1e-7);errors[key]=error;checked+=1
  finished.append(case['name']);checkpoint.parent.mkdir(exist_ok=True)
  checkpoint.write_text(json.dumps(dict(fingerprint=fingerprint,checked=checked,maximum=maximum,scaled=scaled,finished=finished,errors=list(errors.items())))+'\n')
  print(case['name'],checked,flush=True)
 summary=json.loads((base/'second_screen/summary.json').read_text())
 for method in methods:
  for baseline in methods:
   if method==baseline:continue
   vals=[]
   for case in spec['cohort']:
    for seed in seeds:
     for noise in spec['noise_fractions']:
      k=(case['name'],seed,noise);vals.append(np.log(max(errors[(*k,method)],1e-8)/max(errors[(*k,baseline)],1e-8)))
   np.testing.assert_allclose(float(np.exp(np.mean(vals))),summary['comparisons'][method][baseline]['ratio'],rtol=1e-5)
 result=dict(passed=True,development_only=True,checkpoint_errors_recomputed=checked,methods=len(methods),functions=len(spec['cohort']),max_absolute_nmse_discrepancy=maximum,max_scaled_nmse_discrepancy=scaled,
  seconds=time.perf_counter()-start,description='Second arithmetic outcome/budget audit by same author; no independent external reproduction or second acquisition-ranking implementation.',audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 (base/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
