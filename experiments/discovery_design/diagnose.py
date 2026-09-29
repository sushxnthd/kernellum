"""Post-hoc diagnostic: privileged full-test fit, never an eligible method.

Quantifies the observed error floor of the fixed quadratic class. It uses all
clean evaluation labels, so it cannot guide queries or substantiate budget wins.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from experiments.discovery_design.run import data, equations
from kernellum.discovery.design import features

parser=argparse.ArgumentParser()
parser.add_argument('--records',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
spec=json.loads(Path('experiments/discovery_design/spec.json').read_text())
records=[json.loads(s) for s in args.records.read_text().splitlines()]
lookup={(r['equation'],r['seed'],r['noise'],r['method']):r for r in records}
results=[]
for row in equations():
    for seed in spec['seeds']:
        _,_,xt,yt=data(row,seed,0,spec)
        # Unpenalized full-test least squares is the exact minimum on this test set.
        a=features(xt)
        b=np.linalg.lstsq(a,yt,rcond=None)[0]
        floor=float(np.mean((a@b-yt)**2)/np.var(yt))
        for noise in spec['noise_fractions']:
            current=lookup[(row['Filename'],seed,noise,'maximin')]['metrics'][-1]['nmse']
            results.append(dict(equation=row['Filename'],seed=seed,noise=noise,
                                privileged_floor_nmse=floor,maximin_nmse=current,
                                floor_ratio=max(floor,1e-8)/max(current,1e-8)))
out=dict(post_hoc=True,privileged=True,not_a_budgeted_method=True,
         geometric_mean_floor_ratio=float(np.exp(np.mean([np.log(r['floor_ratio']) for r in results]))),
         records=results)
with args.out.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
