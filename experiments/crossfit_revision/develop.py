"""Post-confirmation development only: nested CV of complete model selectors.

The opened UQ cohort is no longer held out. No confirmatory claim may use this
screen. All methods reuse the same 64 observations from the preceding study.
"""
import gzip,json,time
from pathlib import Path
import numpy as np
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.aggregation import simplex_stack
from experiments.representation_revision.run import sample_case,select_coverage
ROOT=Path(__file__).resolve().parents[2]
BASES=('raw','input_only','output_only','representation','raw_stack','representation_stack')

def crossfit(pool,ids,y,test,seed):
 n=len(ids);order=np.random.default_rng(seed).permutation(n);errors=np.empty((n,len(BASES)))
 for valid in np.array_split(order,5):
  train=np.setdiff1d(np.arange(n),valid)
  bank=RepresentationBank(pool).fit(np.asarray(ids)[train],y[train])
  for j,method in enumerate(BASES):errors[valid,j]=bank.predict(pool[np.asarray(ids)[valid]],method)-y[valid]
 errors/=max(float(y.std()),1e-12)
 bank=RepresentationBank(pool).fit(ids,y);pred=np.column_stack([bank.predict(test,m) for m in BASES])
 risk=(errors**2).mean(0);winner=int(np.argmin(risk));stack=simplex_stack(errors)
 inverse=1/np.maximum(risk,1e-12)**2;inverse/=inverse.sum()
 return dict(nested_winner=pred[:,winner],nested_stack=pred@stack,nested_inverse=pred@inverse),dict(risks=risk.tolist(),winner=BASES[winner],weights=stack.tolist())

def run():
 spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
 folder=ROOT/'results/crossfit_revision/development';folder.mkdir(parents=True,exist_ok=False)
 with gzip.open(ROOT/'results/representation_revision/confirmation/traces.jsonl.gz','rt') as f:prior=[json.loads(l) for l in f]
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r['metrics'][-1]['nmse'] for r in prior}
 records=[];start=time.perf_counter()
 with gzip.open(folder/'traces.jsonl.gz','wt') as file:
  for index,case in enumerate(spec['cohort']):
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     pool,y,test,truth=sample_case(case,index,seed,noise,spec);ids=select_coverage(pool,spec,seed)
     predictions,desc=crossfit(pool,ids,y[ids],test,seed+999)
     for name,pred in predictions.items():
      error=float(np.mean((pred-truth)**2)/max(float(np.var(truth)),1e-30))
      assert np.isfinite(error)
      r=dict(function=case['name'],seed=seed,noise=noise,method=name,nmse=error,selection=desc)
      file.write(json.dumps(r)+'\n');file.flush();records.append(r)
   print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
 summary={}
 for name in ('nested_winner','nested_stack','nested_inverse'):
  summary[name]={}
  for baseline in BASES:
   vals={};bynoise={str(n):[] for n in spec['noise_fractions']}
   for r in records:
    if r['method']!=name:continue
    k=(r['function'],r['seed'],r['noise'],baseline)
    v=np.log(max(r['nmse'],1e-8)/max(lookup[k],1e-8));vals.setdefault(r['function'],[]).append(v);bynoise[str(r['noise'])].append(v)
   ratios={k:float(np.exp(np.mean(v))) for k,v in vals.items()}
   summary[name][baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(ratios.values()))))),wins=sum(v<1 for v in ratios.values()),by_noise={k:float(np.exp(np.mean(v))) for k,v in bynoise.items()},by_function=ratios)
 (folder/'summary.json').write_text(json.dumps(dict(development_only=True,comparisons=summary,seconds=time.perf_counter()-start),indent=2)+'\n')
 for name,comparisons in summary.items():
  print(name,{b:(v['ratio'],v['wins'],v['by_noise']) for b,v in comparisons.items()})
if __name__=='__main__':run()
