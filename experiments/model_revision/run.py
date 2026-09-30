"""One frozen pass over the previously excluded higher-dimensional cohort."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import numpy as np
from kernellum.discovery.revision import ModelBank, METHODS, investigate
from kernellum.discovery.design import features, fit
from experiments.discovery_design.run import data

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE_FILES = ['kernellum/discovery/revision.py', 'kernellum/discovery/design.py',
                'experiments/model_revision/run.py', 'experiments/model_revision/spec.json',
                'experiments/discovery_design/run.py',
                'experiments/discovery_design/vendor/FeynmanEquations.csv',
                'docs/MODEL_REVISION_PROTOCOL.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equations():
    with (ROOT/'experiments/discovery_design/vendor/FeynmanEquations.csv').open(encoding='utf-8-sig') as f:
        return [r for r in csv.DictReader(f) if r['# variables'] and 4 <= int(r['# variables']) <= 9]


def compare(records, spec, a, b):
    lookup = {(r['equation'],r['seed'],r['noise'],r['method']):r for r in records}
    logs, by_noise, by_eq = [], {}, {}
    for row in equations():
        v = []
        for seed in spec['seeds']:
            for noise in spec['noise_fractions']:
                key = (row['Filename'],seed,noise)
                an = lookup[(*key,a)]['metrics'][-1]['nmse']
                bn = lookup[(*key,b)]['metrics'][-1]['nmse']
                ratio = float(np.log(max(an,spec['error_floor'])/max(bn,spec['error_floor'])))
                logs.append(ratio); v.append(ratio)
                by_noise.setdefault(str(noise),[]).append(ratio)
        by_eq[row['Filename']] = float(np.exp(np.mean(v)))
    return dict(ratio=float(np.exp(np.mean(logs))),wins=sum(v<1 for v in by_eq.values()),
                win_fraction=float(np.mean([v<1 for v in by_eq.values()])),
                by_noise={k:float(np.exp(np.mean(v))) for k,v in by_noise.items()},by_equation=by_eq)


def summarize(records, spec):
    comparisons = {b:compare(records,spec,spec['primary'],b) for b in spec['baseline_methods']}
    secondary = {b:compare(records,spec,'maximin',b) for b in ('quadratic_maximin','rbf_maximin')}
    g=spec['gates']
    def passes(c):
        return all(v['ratio']<=g['ratio_max'] and v['win_fraction']>=g['equation_win_fraction_min']
                   and max(v['by_noise'].values())<=g['each_noise_ratio_max'] for v in c.values())
    complete = len(records)==len(equations())*len(spec['seeds'])*len(spec['noise_fractions'])*len(spec['methods'])
    return dict(complete=complete,runs=len(records),equations=len(equations()),
                acquisition_gate=complete and passes(comparisons),model_revision_gate=complete and passes(secondary),
                field_breakthrough_established=False,comparisons=comparisons,model_revision_comparisons=secondary,
                median_seconds={m:float(np.median([r['seconds'] for r in records if r['method']==m])) for m in spec['methods']})


def run(out):
    spec=json.loads((HERE/'spec.json').read_text())
    out.mkdir(parents=True,exist_ok=False)
    manifest=dict(source_hashes={f:sha(ROOT/f) for f in SOURCE_FILES},python=platform.python_version(),
                  numpy=np.__version__,platform=platform.platform(),
                  git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  git_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
                  threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    records=[]; start=time.perf_counter()
    with gzip.open(out/'traces.jsonl.gz','wt',encoding='utf8') as f:
        for row in equations():
            for seed in spec['seeds']:
                for noise in spec['noise_fractions']:
                    x,y,xt,yt=data(row,seed,noise,spec)
                    for method in spec['methods']:
                        before=time.perf_counter(); calls=[]
                        def query(i):
                            if i in calls: raise RuntimeError('duplicate query')
                            calls.append(i); return y[i]
                        selected,values,revisions=investigate(x,query,method,spec['budget'],seed,spec['initial'],spec['refresh'])
                        assert calls==selected and len(calls)==spec['budget']
                        metrics=[]
                        # No test input or answer is passed to acquisition or model selection.
                        for budget in spec['checkpoints']:
                            ys=np.asarray(values[:budget]); ids=selected[:budget]
                            if method=='quadratic_maximin':
                                center=float(ys.mean()); scale=max(float(ys.std()),1e-12)
                                beta,_=fit(features(x[ids]),(ys-center)/scale)
                                prediction=center+scale*features(xt)@beta
                                model_info=[{'family':'legacy_quadratic','ridge':1e-6}]
                            else:
                                bank=ModelBank(x).fit(ids,ys,only_rbf=(method=='rbf_maximin'))
                                prediction=bank.predict(xt); model_info=bank.describe()
                            nmse=float(np.mean((prediction-yt)**2)/max(float(np.var(yt)),1e-30))
                            metrics.append(dict(budget=budget,nmse=nmse,models=model_info))
                        record=dict(equation=row['Filename'],dimensions=int(row['# variables']),seed=seed,noise=noise,
                                    method=method,selected=selected,observed=values,revisions=revisions,
                                    metrics=metrics,seconds=time.perf_counter()-before)
                        f.write(json.dumps(record,allow_nan=False)+'\n'); f.flush(); records.append(record)
            print(f"{row['Filename']}: {len(records)} runs; {time.perf_counter()-start:.1f}s",flush=True)
    summary=summarize(records,spec);summary['elapsed_seconds']=time.perf_counter()-start
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    manifest['output_hashes']={f:sha(out/f) for f in ('summary.json','traces.jsonl.gz')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if 'comparisons' not in k},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
