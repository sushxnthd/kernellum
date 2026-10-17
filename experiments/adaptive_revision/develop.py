"""Predeclared adaptive aggregation screen on the opened cohort."""
import gzip, hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
import scipy, uqtestfuns
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.adaptive_revision import AdaptiveStack
from experiments.representation_revision.run import sample_case, select_coverage

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    with gzip.open(ROOT / path, 'rt') as f:
        return [json.loads(line) for line in f]


def run():
    spec = json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uqtestfuns.__version__ == spec['uqtestfuns']
    out = ROOT/'results/adaptive_revision/development'; out.mkdir(parents=True, exist_ok=False)
    sources = ['kernellum/discovery/adaptive_revision.py','experiments/adaptive_revision/develop.py',
               'tests/test_adaptive_revision.py','kernellum/discovery/representation.py',
               'kernellum/discovery/robust_revision.py','experiments/representation_revision/run.py',
               'experiments/representation_revision/spec.json',
               'results/representation_revision/confirmation/traces.jsonl.gz',
               'results/robust_revision/development/traces.jsonl.gz',
               'results/support_revision/development/traces.jsonl.gz']
    digest = lambda p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    manifest = dict(development_only=True, source_hashes={p:digest(p) for p in sources},
                    python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                    uqtestfuns=uqtestfuns.__version__, threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    controls = {}
    for path in ('results/representation_revision/confirmation/traces.jsonl.gz',
                 'results/robust_revision/development/traces.jsonl.gz',
                 'results/support_revision/development/traces.jsonl.gz'):
        for r in read(path):
            controls[(r['function'],r['seed'],r['noise'],r['method'])] = r['metrics'][-1]['nmse'] if 'metrics' in r else r['nmse']
    records=[]; start=time.perf_counter()
    with gzip.open(out/'traces.jsonl.gz','wt') as f:
        for index, case in enumerate(spec['cohort']):
            for seed in spec['seeds']:
                x, clean, xt, truth = sample_case(case,index,seed,0.,spec)
                ids = select_coverage(x,spec,seed)
                perturbation = np.random.default_rng(seed+1000000+index).normal(size=len(x))
                for noise in spec['noise_fractions']:
                    y = clean + noise*np.std(clean)*perturbation
                    bank = RepresentationBank(x).fit(ids,y[ids]); predictor = AdaptiveStack(bank)
                    prediction, diagnostic = predictor.predict(xt)
                    nmse = float(np.mean((prediction-truth)**2)/max(float(np.var(truth)),1e-30))
                    assert np.isfinite(nmse)
                    r = dict(function=case['name'],seed=seed,noise=noise,method='adaptive_stack',nmse=nmse,
                             selected=ids,observed=y[ids].tolist(),diagnostic=diagnostic,
                             input_sha256=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest())
                    f.write(json.dumps(r,allow_nan=False)+'\n'); f.flush(); records.append(r)
                    controls[(case['name'],seed,noise,'adaptive_stack')] = nmse
            print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
    comparisons={}; baselines=['representation_stack','median_stack','support_nonlinear_leverage_stack']
    for baseline in baselines:
        byfun={}; bynoise={str(n):[] for n in spec['noise_fractions']}
        for case in spec['cohort']:
            vals=[]
            for seed in spec['seeds']:
                for noise in spec['noise_fractions']:
                    key=(case['name'],seed,noise); value=np.log(max(controls[(*key,'adaptive_stack')],1e-8)/max(controls[(*key,baseline)],1e-8))
                    vals.append(value); bynoise[str(noise)].append(value)
            byfun[case['name']]=float(np.exp(np.mean(vals)))
        comparisons[baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),wins=sum(v<1 for v in byfun.values()),
                                   by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},by_function=byfun)
    result=dict(development_only=True,field_breakthrough_established=False,runs=len(records),functions=len(spec['cohort']),
                comparisons=comparisons,seconds=time.perf_counter()-start)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    manifest['output_hashes']={str(p.relative_to(ROOT)):digest(p) for p in (out/'summary.json',out/'traces.jsonl.gz')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(comparisons,indent=2),flush=True)


if __name__ == '__main__': run()
