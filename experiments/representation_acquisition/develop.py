"""Exploratory acquisition test on opened functions; two fixed prior seeds."""
import gzip,json,time
from pathlib import Path
import numpy as np
from kernellum.discovery.representation_acquisition import investigate
METHODS=('warped_ivr','hybrid_ivr','latent_ivr','raw_ivr','variance','maximin','random')
from kernellum.discovery.representation import RepresentationBank
from experiments.representation_revision.run import sample_case
ROOT=Path(__file__).resolve().parents[2]

def run():
 spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text());spec['seeds']=spec['seeds'][:2]
 folder=ROOT/'results/representation_acquisition/development';folder.mkdir(parents=True,exist_ok=False)
 records=[];start=time.perf_counter()
 with gzip.open(folder/'traces.jsonl.gz','wt') as f:
  for index,case in enumerate(spec['cohort']):
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     x,y,xt,yt=sample_case(case,index,seed,noise,spec)
     for method in METHODS:
      calls=[]
      def query(i):calls.append(i);return y[i]
      ids,values,revisions=investigate(x,query,method,seed=seed)
      assert calls==ids and len(ids)==len(set(ids))==64
      bank=RepresentationBank(x).fit(ids,values);description=bank.describe('representation')
      pred=bank.predict(xt,'representation');error=float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30))
      assert np.isfinite(error)
      r=dict(function=case['name'],seed=seed,noise=noise,method=method,nmse=error,selected=ids,observed=values,revisions=revisions,model=description)
      f.write(json.dumps(r)+'\n');f.flush();records.append(r)
   print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r['nmse'] for r in records};comparisons={}
 for method in METHODS:
  comparisons[method]={}
  for baseline in METHODS:
   if baseline==method:continue
   byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
   for case in spec['cohort']:
    vals=[]
    for seed in spec['seeds']:
     for noise in spec['noise_fractions']:
      k=(case['name'],seed,noise);v=np.log(max(lookup[(*k,method)],1e-8)/max(lookup[(*k,baseline)],1e-8))
      vals.append(v);bynoise[str(noise)].append(v)
    byfun[case['name']]=float(np.exp(np.mean(vals)))
   comparisons[method][baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),wins=sum(v<1 for v in byfun.values()),by_noise={k:float(np.exp(np.mean(v))) for k,v in bynoise.items()},by_function=byfun)
 summary=dict(development_only=True,runs=len(records),seeds=spec['seeds'],comparisons=comparisons,seconds=time.perf_counter()-start)
 (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 for method in METHODS:print(method,{b:(v['ratio'],v['wins']) for b,v in comparisons[method].items()})
if __name__=='__main__':run()
