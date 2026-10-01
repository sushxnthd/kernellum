"""Opened-UQ development only, with matched anchor-scoring control."""
import gzip,json,time
from pathlib import Path
import numpy as np
from kernellum.discovery.noise_revision import NoiseConsistentBank
from experiments.representation_revision.run import sample_case,select_coverage
ROOT=Path(__file__).resolve().parents[2]

def run():
 spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
 folder=ROOT/'results/noise_revision/development';folder.mkdir(parents=True,exist_ok=False)
 with gzip.open(ROOT/'results/representation_revision/confirmation/traces.jsonl.gz','rt') as f:prior=[json.loads(l) for l in f]
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r['metrics'][-1]['nmse'] for r in prior}
 records=[];start=time.perf_counter()
 with gzip.open(folder/'traces.jsonl.gz','wt') as file:
  for index,case in enumerate(spec['cohort']):
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     x,y,xt,yt=sample_case(case,index,seed,noise,spec);ids=select_coverage(x,spec,seed)
     bank=NoiseConsistentBank(x).fit(ids,y[ids])
     for method in ('noise_consistent','anchor_control'):
      description=bank.describe(method);pred=bank.predict(xt,method)
      error=float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30));assert np.isfinite(error)
      r=dict(function=case['name'],seed=seed,noise=noise,method=method,nmse=error,model=description)
      file.write(json.dumps(r)+'\n');file.flush();records.append(r)
      lookup[(r['function'],seed,noise,method)]=error
   print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
 comparisons={}
 for baseline in spec['methods']+['anchor_control']:
  byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
  for case in spec['cohort']:
   vals=[]
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     k=(case['name'],seed,noise);v=np.log(max(lookup[(*k,'noise_consistent')],1e-8)/max(lookup[(*k,baseline)],1e-8))
     vals.append(v);bynoise[str(noise)].append(v)
   byfun[case['name']]=float(np.exp(np.mean(vals)))
  comparisons[baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),wins=sum(v<1 for v in byfun.values()),by_noise={k:float(np.exp(np.mean(v))) for k,v in bynoise.items()},by_function=byfun)
 result=dict(development_only=True,runs=len(records),comparisons=comparisons,seconds=time.perf_counter()-start)
 (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 for b,v in comparisons.items():print(b,v['ratio'],v['wins'],v['by_noise'])
if __name__=='__main__':run()
