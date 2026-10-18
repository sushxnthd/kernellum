"""Development screen on the opened UQ cohort, not new confirmation."""
import gzip,json,time
from pathlib import Path
import numpy as np
from kernellum.discovery.guarded import GuardedRepresentationBank
from experiments.representation_revision.run import sample_case,select_coverage
ROOT=Path(__file__).resolve().parents[2]

def run():
 spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
 folder=ROOT/'results/guarded_revision/development';folder.mkdir(parents=True,exist_ok=False)
 with gzip.open(ROOT/'results/representation_revision/confirmation/traces.jsonl.gz','rt') as f:prior=[json.loads(l) for l in f]
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r['metrics'][-1]['nmse'] for r in prior}
 records=[];start=time.perf_counter()
 with gzip.open(folder/'traces.jsonl.gz','wt') as file:
  for index,case in enumerate(spec['cohort']):
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     x,y,xt,yt=sample_case(case,index,seed,noise,spec);ids=select_coverage(x,spec,seed)
     bank=GuardedRepresentationBank(x).fit(ids,y[ids])
     for method in ('representation','representation_stack','raw','raw_stack'):
      pred=bank.predict(xt,method);error=float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30))
      assert np.isfinite(error)
      r=dict(function=case['name'],seed=seed,noise=noise,method='guarded_'+method,nmse=error,models=bank.describe(method),bounds=bank.bounds)
      file.write(json.dumps(r)+'\n');file.flush();records.append(r)
   print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
 summary={}
 for name in ('guarded_representation','guarded_representation_stack','guarded_raw','guarded_raw_stack'):
  summary[name]={}
  for baseline in spec['methods']:
   byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
   for r in records:
    if r['method']!=name:continue
    k=(r['function'],r['seed'],r['noise'],baseline)
    v=np.log(max(r['nmse'],1e-8)/max(lookup[k],1e-8));byfun.setdefault(r['function'],[]).append(v);bynoise[str(r['noise'])].append(v)
   ratios={k:float(np.exp(np.mean(v))) for k,v in byfun.items()}
   summary[name][baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(ratios.values()))))),wins=sum(v<1 for v in ratios.values()),by_noise={k:float(np.exp(np.mean(v))) for k,v in bynoise.items()},by_function=ratios)
 (folder/'summary.json').write_text(json.dumps(dict(development_only=True,comparisons=summary,seconds=time.perf_counter()-start),indent=2)+'\n')
 for name,comparisons in summary.items():print(name,{b:(v['ratio'],v['wins'],v['by_noise']) for b,v in comparisons.items()})
if __name__=='__main__':run()
