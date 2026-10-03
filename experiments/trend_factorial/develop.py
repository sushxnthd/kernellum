"""Separate removed exponential curvature from added affine RBF means."""
import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from kernellum.discovery.aggregation import simplex_stack
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.trend_revision import TrendBank
from experiments.trend_revision.develop import comparisons, CONTROL_FILES, BASELINES, read_records

ARMS=('original','remove_only','add_only','both')


def choose(models):
    selected=[];seen=set()
    for m in sorted(models,key=lambda m:m['original_cv']):
        key=(m['input'],m['response'],m['family'],m['trend'])
        if key not in seen and np.isfinite(m['original_cv']):
            selected.append(m);seen.add(key)
        if len(selected)==6:break
    return selected,simplex_stack(np.column_stack([m['error'] for m in selected]))


def run(data_path,out):
    out.mkdir(parents=True,exist_ok=False)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    prior=json.loads((ROOT/'results/trend_revision/development/manifest.json').read_text())
    assert digest(data_path)==prior['output_hashes']['inputs_and_truth.npz']
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    archive=np.load(data_path,allow_pickle=False)
    controls={};references={};trend_reference={}
    for path in CONTROL_FILES:
        for r in read_records(ROOT/path):
            key=(r['function'],r['seed'],r['noise'])
            controls[(*key,r['method'])]=r['metrics'][-1]['nmse'] if 'metrics' in r else r['nmse']
            if r['method']=='representation_stack':references[key]=r
    for r in read_records(ROOT/'results/trend_revision/development/traces.jsonl.gz'):
        if r['method']=='trend_stack':trend_reference[(r['function'],r['seed'],r['noise'])]=r
    sources=['experiments/trend_factorial/develop.py','docs/TREND_FACTORIAL_PROTOCOL.md',
        'kernellum/discovery/trend_revision.py','kernellum/discovery/representation.py',
        'kernellum/discovery/revision.py','kernellum/discovery/aggregation.py',
        'experiments/trend_revision/develop.py','experiments/representation_revision/spec.json',*CONTROL_FILES,
        'results/trend_revision/development/traces.jsonl.gz','results/trend_revision/development/manifest.json']
    manifest=dict(development_only=True,python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        data_sha256=digest(data_path),source_sha256={p:digest(ROOT/p) for p in sources},
        threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    start=time.perf_counter();count=0;max_absolute_replay_error=0.
    with gzip.open(out/'traces.jsonl.gz','wt') as stream:
        for case in spec['cohort']:
            name=case['name']
            for seed in spec['seeds']:
                pool=archive[f'{name}_{seed}_pool'];test=archive[f'{name}_{seed}_test'];truth=archive[f'{name}_{seed}_truth']
                sha=hashlib.sha256(pool.tobytes()+test.tobytes()).hexdigest()
                for noise in spec['noise_fractions']:
                    key=(name,seed,noise);r=references[key];ids=r['selected'];observed=np.array(r['observed'])
                    assert sha==r['input_sha256'] and len(ids)==len(set(ids))==64
                    bank=RepresentationBank(pool).fit(ids,observed);trend=TrendBank(bank)
                    full=[m|{'trend':'constant'} for m in bank.models]
                    retained=[m for m in trend.models if m['trend']=='constant']
                    affine=[m for m in trend.models if m['trend']=='affine']
                    arms=dict(original=full,remove_only=retained,add_only=full+affine,both=trend.models)
                    for arm in ARMS:
                        selected,weights=choose(arms[arm])
                        prediction=sum(w*trend.predict_model(m,test) for m,w in zip(selected,weights) if w>0)
                        assert np.isfinite(prediction).all()
                        nmse=float(np.mean((prediction-truth)**2)/max(float(np.var(truth)),1e-30))
                        # Scalar reduction checks the score separately, not model arithmetic.
                        scalar=math.fsum(float(a-b)**2 for a,b in zip(prediction,truth))/len(truth)/max(float(np.var(truth)),1e-30)
                        assert math.isclose(nmse,scalar,rel_tol=1e-12,abs_tol=1e-28)
                        if arm in ('original','both'):
                            expected=r['metrics'][-1]['nmse'] if arm=='original' else trend_reference[key]['nmse']
                            assert math.isclose(nmse,expected,rel_tol=2e-5,abs_tol=1e-7),(key,arm,nmse,expected)
                            max_absolute_replay_error=max(max_absolute_replay_error,abs(nmse-expected))
                        metadata=[dict(input=m['input'],response=m['response'],family=m['family'],trend=m['trend'],
                            ridge=m['ridge'],loo_nmse=m['original_cv'],weight=float(w)) for m,w in zip(selected,weights)]
                        record=dict(function=name,seed=seed,noise=noise,method=arm,nmse=nmse,
                            input_sha256=sha,models=metadata)
                        stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush();count+=1
                        controls[(*key,arm)]=nmse
            print(name,count,round(time.perf_counter()-start,1),flush=True)
    names=[c['name'] for c in spec['cohort']]
    reports={arm:comparisons(controls,names,spec['seeds'],spec['noise_fractions'],arm) for arm in ARMS}
    result=dict(development_only=True,field_breakthrough_established=False,outcomes=count,
        original_and_both_replay_outcomes=780,max_absolute_replay_nmse_difference=max_absolute_replay_error,
        comparisons=reports,seconds=time.perf_counter()-start)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    manifest['output_sha256']={p.name:digest(p) for p in (out/'summary.json',out/'traces.jsonl.gz')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for arm in ARMS:
        for baseline in ('representation_stack','adaptive_stack'):
            print(arm,baseline,json.dumps({k:v for k,v in reports[arm][baseline].items() if k!='by_function'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();run(args.data,args.out)
