"""Frozen external-UQ confirmation for representation-aware regression."""
import argparse,gzip,hashlib,inspect,json,os,platform,subprocess,time
from pathlib import Path
import numpy as np
import scipy
import uqtestfuns as uqtf
from kernellum.discovery.representation import RepresentationBank
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCES=['kernellum/discovery/revision.py','kernellum/discovery/aggregation.py','kernellum/discovery/representation.py',
 'experiments/representation_revision/spec.json','experiments/representation_revision/run.py','docs/REPRESENTATION_REVISION_PROTOCOL.md']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def sample_case(case,index,seed,noise,spec):
 f=getattr(uqtf,case['name'])()
 if sha(Path(inspect.getfile(type(f))))!=case['source_sha256']:raise ValueError('upstream function changed')
 f.prob_input.reset_rng(seed+1000*index)
 x=f.prob_input.get_sample(spec['pool_size']);xt=f.prob_input.get_sample(spec['test_size'])
 yp=np.asarray(f(x)).reshape(-1);yt=np.asarray(f(xt)).reshape(-1)
 if len(yp)!=len(x) or len(yt)!=len(xt) or not all(np.isfinite(z).all() for z in (x,xt,yp,yt)):
  raise ValueError('invalid upstream sample')
 y=yp+noise*np.std(yp)*np.random.default_rng(seed+1000000+index).normal(size=len(yp))
 return x,y,xt,yt


def select_coverage(x,spec,seed):
 z=2*(x-x.min(0))/np.maximum(np.ptp(x,axis=0),1e-12)-1
 ids=list(map(int,np.random.default_rng(seed).choice(len(x),spec['initial'],replace=False)))
 while len(ids)<spec['budget']:
  distances=((z[:,None]-z[ids][None,:])**2).sum(2).min(1);distances[ids]=-np.inf
  ids.append(int(np.argmax(distances)))
 return ids


def summarize(records,spec):
 expected=len(spec['cohort'])*len(spec['seeds'])*len(spec['noise_fractions'])*len(spec['methods'])
 lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in records}
 comparisons={}
 for b in spec['baselines']:
  byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
  for c in spec['cohort']:
   vals=[]
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     k=(c['name'],seed,noise)
     a=lookup[(*k,spec['primary'])]['metrics'][-1]['nmse'];bb=lookup[(*k,b)]['metrics'][-1]['nmse']
     v=np.log(max(a,spec['error_floor'])/max(bb,spec['error_floor']));vals.append(v);bynoise[str(noise)].append(v)
   byfun[c['name']]=float(np.exp(np.mean(vals)))
  comparisons[b]=dict(ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),wins=sum(v<1 for v in byfun.values()),
   win_fraction=float(np.mean([v<1 for v in byfun.values()])),by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},by_function=byfun)
 g=spec['gates'];complete=len(records)==len(lookup)==expected
 gate=complete and all(v['ratio']<=g['ratio_max'] and v['win_fraction']>=g['win_fraction_min']
                      and max(v['by_noise'].values())<=g['each_noise_ratio_max'] for v in comparisons.values())
 return dict(complete=complete,runs=len(records),functions=len(spec['cohort']),criterion_supported=gate,
             field_breakthrough_established=False,comparisons=comparisons)


def run(out):
 spec=json.loads((HERE/'spec.json').read_text())
 if uqtf.__version__!=spec['uqtestfuns']:raise ValueError('wrong uqtestfuns version')
 out.mkdir(parents=True,exist_ok=False)
 manifest=dict(source_hashes={s:sha(ROOT/s) for s in SOURCES},git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,uqtestfuns=uqtf.__version__,
  threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 records=[];start=time.perf_counter()
 with gzip.open(out/'traces.jsonl.gz','wt') as file:
  for index,case in enumerate(spec['cohort']):
   for seed in spec['seeds']:
    for noise in spec['noise_fractions']:
     x,y,xt,yt=sample_case(case,index,seed,noise,spec);ids=select_coverage(x,spec,seed)
     metrics={m:[] for m in spec['methods']}
     before=time.perf_counter()
     for budget in spec['checkpoints']:
      bank=RepresentationBank(x).fit(ids[:budget],y[ids[:budget]])
      # Model choices and all weights are fixed before receiving any test input/target.
      descriptions={m:bank.describe(m) for m in spec['methods']}
      for method in spec['methods']:
       pred=bank.predict(xt,method)
       nmse=float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30))
       if not np.isfinite(nmse):raise FloatingPointError('nonfinite score: study fails without exclusions')
       metrics[method].append(dict(budget=budget,nmse=nmse,models=descriptions[method]))
     for method in spec['methods']:
      record=dict(function=case['name'],seed=seed,noise=noise,method=method,selected=ids,observed=y[ids].tolist(),
       metrics=metrics[method],shared_fit_seconds=time.perf_counter()-before,
       input_sha256=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest())
      file.write(json.dumps(record,allow_nan=False)+'\n');file.flush();records.append(record)
   print(f"{case['name']}: {len(records)} method trials; {time.perf_counter()-start:.1f}s",flush=True)
 summary=summarize(records,spec);summary['seconds']=time.perf_counter()-start
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 manifest['output_hashes']={f:sha(out/f) for f in ('summary.json','traces.jsonl.gz')}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k!='comparisons'},indent=2))
 for b,v in summary['comparisons'].items():print(b,v['ratio'],v['wins'],v['by_noise'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
