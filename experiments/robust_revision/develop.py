"""Robust aggregation screen on the opened cohort; not held-out confirmation."""
import gzip,hashlib,json,os,platform,time
from pathlib import Path
import numpy as np
import scipy,uqtestfuns
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.robust_revision import RobustStack,METHODS
from experiments.representation_revision.run import sample_case,select_coverage
ROOT=Path(__file__).resolve().parents[2]


def run():
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uqtestfuns.__version__==spec['uqtestfuns']
    folder=ROOT/'results/robust_revision/development';folder.mkdir(parents=True,exist_ok=False)
    sources=['kernellum/discovery/robust_revision.py','experiments/robust_revision/develop.py','tests/test_robust_revision.py',
             'kernellum/discovery/representation.py','kernellum/discovery/revision.py','kernellum/discovery/aggregation.py',
             'experiments/representation_revision/run.py','experiments/representation_revision/spec.json',
             'results/representation_revision/confirmation/traces.jsonl.gz','results/crossfit_revision/development/traces.jsonl.gz',
             'results/noise_revision/development/traces.jsonl.gz','results/support_revision/development/traces.jsonl.gz']
    digest=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    manifest=dict(development_only=True,source_hashes={p:digest(p) for p in sources},python=platform.python_version(),
                  numpy=np.__version__,scipy=scipy.__version__,uqtestfuns=uqtestfuns.__version__,
                  threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    lookup={}
    for path in sources[-4:]:
        with gzip.open(ROOT/path,'rt') as f:
            for line in f:
                r=json.loads(line);lookup[(r['function'],r['seed'],r['noise'],r['method'])]=r['nmse'] if 'nmse' in r else r['metrics'][-1]['nmse']
    controls=spec['methods']+['nested_winner','noise_consistent','support_nonlinear_leverage_stack']
    start=time.perf_counter();records=[]
    with gzip.open(folder/'traces.jsonl.gz','wt') as f:
        for index,case in enumerate(spec['cohort']):
            for seed in spec['seeds']:
                x,clean,xt,yt=sample_case(case,index,seed,0,spec);ids=select_coverage(x,spec,seed)
                perturbation=np.random.default_rng(seed+1000000+index).normal(size=len(x))
                for noise in spec['noise_fractions']:
                    y=clean+noise*np.std(clean)*perturbation
                    bank=RepresentationBank(x).fit(ids,y[ids]);stack=RobustStack(bank)
                    description=stack.describe();predictions=stack.predict(xt)
                    for method in METHODS:
                        error=float(np.mean((predictions[method]-yt)**2)/max(float(np.var(yt)),1e-30))
                        assert np.isfinite(error)
                        r=dict(function=case['name'],seed=seed,noise=noise,method=method,nmse=error,selected=ids,
                               observed=y[ids].tolist(),model=description,input_sha256=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest())
                        f.write(json.dumps(r,allow_nan=False)+'\n');f.flush();records.append(r)
                        lookup[(case['name'],seed,noise,method)]=error
            print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
    comparisons={};gates={}
    for method in METHODS:
        comparisons[method]={}
        for baseline in controls:
            byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
            for case in spec['cohort']:
                vals=[]
                for seed in spec['seeds']:
                    for noise in spec['noise_fractions']:
                        key=(case['name'],seed,noise)
                        v=np.log(max(lookup[(*key,method)],1e-8)/max(lookup[(*key,baseline)],1e-8))
                        vals.append(v);bynoise[str(noise)].append(v)
                byfun[case['name']]=float(np.exp(np.mean(vals)))
            comparisons[method][baseline]=dict(ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),wins=sum(v<1 for v in byfun.values()),
                                               by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},by_function=byfun)
        gates[method]=all(v['ratio']<=.8 and v['wins']/39>=.6 and max(v['by_noise'].values())<=1 for v in comparisons[method].values())
    distribution={}
    for method in list(METHODS)+controls:
        values=[v for (*_,m),v in lookup.items() if m==method]
        distribution[method]=dict(mean=float(np.mean(values)),median=float(np.median(values)),maximum=float(max(values)),p95=float(np.quantile(values,.95)))
    result=dict(development_only=True,field_breakthrough_established=False,runs=len(records),comparisons=comparisons,
                broad_gate=gates,distributions=distribution,seconds=time.perf_counter()-start)
    (folder/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    manifest['output_hashes']={str(p.relative_to(ROOT)):digest(p) for p in (folder/'summary.json',folder/'traces.jsonl.gz')}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for m,c in comparisons.items(): print(m,{b:round(v['ratio'],6) for b,v in c.items()},gates[m],flush=True)


if __name__=='__main__': run()
