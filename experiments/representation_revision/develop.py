"""Development only: opened Feynman rows; no fresh confirmation claim."""
import argparse,gzip,json,time
from pathlib import Path
import numpy as np
from experiments.model_revision.run import equations
from experiments.discovery_design.run import data
from kernellum.discovery.representation import RepresentationBank,METHODS
ROOT=Path(__file__).resolve().parents[2]


def run(out):
 out.mkdir(parents=True,exist_ok=False)
 spec=json.loads((ROOT/'experiments/model_revision/spec.json').read_text())
 rows={r['Filename']:r for r in equations()}
 with gzip.open(ROOT/'results/model_revision/frozen_run/traces.jsonl.gz','rt') as f:
  records=[r for line in f if (r:=json.loads(line))['method']=='maximin']
 results=[];start=time.perf_counter()
 for record in records:
  row=rows[record['equation']];d=int(row['# variables'])
  x,y,xt,yt=data(row,record['seed'],record['noise'],spec)
  lo=np.array([float(row[f'v{i}_low']) for i in range(1,d+1)])
  hi=np.array([float(row[f'v{i}_high']) for i in range(1,d+1)])
  x=lo+(x+1)*(hi-lo)/2;xt=lo+(xt+1)*(hi-lo)/2
  bank=RepresentationBank(x).fit(record['selected'],record['observed'])
  for method in METHODS:
   pred=bank.predict(xt,method);nmse=float(np.mean((pred-yt)**2)/np.var(yt))
   results.append(dict(equation=row['Filename'],seed=record['seed'],noise=record['noise'],method=method,
                       nmse=nmse,models=bank.describe(method)))
 lookup={(r['equation'],r['seed'],r['noise'],r['method']):r['nmse'] for r in results}
 comparisons={}
 for baseline in METHODS[1:]:
  byeq={};bynoise={str(n):[] for n in spec['noise_fractions']}
  for eq in rows:
   logs=[]
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     v=np.log(max(lookup[(eq,seed,noise,'representation')],1e-8)/max(lookup[(eq,seed,noise,baseline)],1e-8))
     logs.append(v);bynoise[str(noise)].append(v)
   byeq[eq]=float(np.exp(np.mean(logs)))
  comparisons[baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(byeq.values()))))),
     wins=sum(v<1 for v in byeq.values()),by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},equation_ratios=byeq)
 with gzip.open(out/'traces.jsonl.gz','wt') as f:
  for r in results:f.write(json.dumps(r,allow_nan=False)+'\n')
 (out/'summary.json').write_text(json.dumps(dict(status='post-hoc development, not confirmation',runs=len(results),
   seconds=time.perf_counter()-start,comparisons=comparisons),indent=2)+'\n')
 for b,v in comparisons.items():print(b,round(v['ratio'],5),v['wins'],v['by_noise'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
