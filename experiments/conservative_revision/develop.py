"""Explicitly post-hoc development on opened model-revision data."""
import argparse
import gzip
import json
from pathlib import Path
import time
import numpy as np
from experiments.model_revision.run import equations
from experiments.discovery_design.run import data
from kernellum.discovery.revision import ModelBank
from kernellum.discovery.aggregation import METHODS,aggregate_weights

ROOT=Path(__file__).resolve().parents[2]


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    spec=json.loads((ROOT/'experiments/model_revision/spec.json').read_text())
    rows={r['Filename']:r for r in equations()}
    with gzip.open(ROOT/'results/model_revision/frozen_run/traces.jsonl.gz','rt') as f:
        records=[r for line in f if (r:=json.loads(line))['method']=='maximin']
    results=[];start=time.perf_counter()
    for record in records:
        x,y,xt,yt=data(rows[record['equation']],record['seed'],record['noise'],spec)
        bank=ModelBank(x).fit(record['selected'],record['observed'])
        residuals=np.column_stack([m['loo'] for m in bank.models])
        families=[m['family'] for m in bank.models]
        predictions=np.column_stack([bank.center+bank.scale*bank.predict_model(m,xt) for m in bank.models])
        for method in METHODS:
            weights=aggregate_weights(residuals,families,method,record['seed'])
            pred=predictions@weights
            nmse=float(np.mean((pred-yt)**2)/np.var(yt))
            results.append(dict(equation=record['equation'],seed=record['seed'],noise=record['noise'],
                                method=method,nmse=nmse,weights=weights.tolist(),families=families))
    lookup={(r['equation'],r['seed'],r['noise'],r['method']):r['nmse'] for r in results}
    summary={}
    for candidate in METHODS[4:]:
        summary[candidate]={}
        for baseline in METHODS[:4]:
            vals=[];byeq={};bynoise={str(n):[] for n in spec['noise_fractions']}
            for eq in rows:
                v=[]
                for seed in spec['seeds']:
                    for noise in spec['noise_fractions']:
                        z=np.log(max(lookup[(eq,seed,noise,candidate)],1e-8)/max(lookup[(eq,seed,noise,baseline)],1e-8))
                        v.append(z);vals.append(z);bynoise[str(noise)].append(z)
                byeq[eq]=float(np.exp(np.mean(v)))
            summary[candidate][baseline]=dict(ratio=float(np.exp(np.mean(vals))),wins=sum(v<1 for v in byeq.values()),
                by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},equation_ratios=byeq)
    with gzip.open(out/'traces.jsonl.gz','wt') as f:
        for r in results:f.write(json.dumps(r)+'\n')
    (out/'summary.json').write_text(json.dumps(dict(status='post-hoc development, not confirmation',
        runs=len(results),seconds=time.perf_counter()-start,comparisons=summary),indent=2)+'\n')
    for c,group in summary.items():print(c,{b:(round(v['ratio'],5),v['wins']) for b,v in group.items()})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
