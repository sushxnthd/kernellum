"""Joint acquisition/predictor interaction screen on the opened cohort."""
import gzip, hashlib, json, os, platform, time
from pathlib import Path
import numpy as np
import scipy, uqtestfuns
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.representation_acquisition import investigate
from kernellum.discovery.adaptive_revision import AdaptiveStack
from kernellum.discovery.support_revision import SupportRouter
from experiments.representation_revision.run import sample_case

ROOT = Path(__file__).resolve().parents[2]
ARMS = ('maximin', 'random', 'warped_ivr', 'hybrid_ivr', 'residual_ivr')
PREDICTORS = ('representation_stack', 'adaptive_stack', 'support_nonlinear_leverage_stack')


def run():
    spec = json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uqtestfuns.__version__ == spec['uqtestfuns']
    out = ROOT/'results/joint_revision/development'; out.mkdir(parents=True, exist_ok=False)
    sources = ['experiments/joint_revision/develop.py','kernellum/discovery/representation_acquisition.py',
               'kernellum/discovery/representation.py','kernellum/discovery/representation_acquisition.py',
               'kernellum/discovery/adaptive_revision.py','kernellum/discovery/support_revision.py',
               'experiments/representation_revision/run.py','experiments/representation_revision/spec.json']
    digest=lambda p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    manifest=dict(development_only=True,source_hashes={p:digest(p) for p in sources},python=platform.python_version(),
                  numpy=np.__version__,scipy=scipy.__version__,uqtestfuns=uqtestfuns.__version__,
                  threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    records=[];start=time.perf_counter()
    with gzip.open(out/'traces.jsonl.gz','wt') as f:
        for index,case in enumerate(spec['cohort']):
            for seed in spec['seeds'][:2]:
                for noise in spec['noise_fractions']:
                    x, y, xt, truth = sample_case(case,index,seed,noise,spec)
                    variance=max(float(np.var(truth)),1e-30)
                    for acquisition in ARMS:
                        ids, values, revisions = investigate(x,lambda i: y[i],acquisition,budget=64,initial=16,refresh=4,seed=seed)
                        y=np.asarray(values,dtype=float)
                        bank=RepresentationBank(x).fit(ids,y)
                        adaptive=AdaptiveStack(bank)
                        support=SupportRouter(bank,xt)
                        predictions={
                            'representation_stack':bank.predict(xt,'representation_stack'),
                            'adaptive_stack':adaptive.predict(xt)[0],
                            'support_nonlinear_leverage_stack':support.predict('support_nonlinear_leverage_stack')[0],
                        }
                        for predictor in PREDICTORS:
                            nmse=float(np.mean((predictions[predictor]-truth)**2)/variance)
                            assert np.isfinite(nmse)
                            r=dict(function=case['name'],seed=seed,noise=noise,acquisition=acquisition,predictor=predictor,
                                   nmse=nmse,selected=ids,observed=y.tolist(),revisions=revisions,
                                   input_sha256=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest())
                            f.write(json.dumps(r,allow_nan=False)+'\n');f.flush();records.append(r)
            print(case['name'],len(records),round(time.perf_counter()-start,1),flush=True)
    lookup={(r['function'],r['seed'],r['noise'],r['acquisition'],r['predictor']):r['nmse'] for r in records}
    comparisons={}; baselines=[('maximin','representation_stack'),('random','representation_stack'),
                               ('hybrid_ivr','representation_stack'),('hybrid_ivr','adaptive_stack'),
                               ('maximin','support_nonlinear_leverage_stack')]
    candidates=[(a,p) for a in ARMS for p in PREDICTORS]
    for candidate in candidates:
        comparisons[f'{candidate[0]}+{candidate[1]}']={}
        for baseline in baselines:
            byfun={};bynoise={str(n):[] for n in spec['noise_fractions']}
            for case in spec['cohort']:
                vals=[]
                for seed in spec['seeds'][:2]:
                    for noise in spec['noise_fractions']:
                        key=(case['name'],seed,noise)
                        v=np.log(max(lookup[(*key,*candidate)],1e-8)/max(lookup[(*key,*baseline)],1e-8))
                        vals.append(v);bynoise[str(noise)].append(v)
                byfun[case['name']]=float(np.exp(np.mean(vals)))
            comparisons[f'{candidate[0]}+{candidate[1]}'][f'{baseline[0]}+{baseline[1]}']=dict(
                ratio=float(np.exp(np.mean(np.log(list(byfun.values()))))),wins=sum(v<1 for v in byfun.values()),
                by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},by_function=byfun)
    result=dict(development_only=True,field_breakthrough_established=False,runs=len(records),functions=len(spec['cohort']),
                arms=ARMS,predictors=PREDICTORS,comparisons=comparisons,seconds=time.perf_counter()-start)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    manifest['output_hashes']={str(p.relative_to(ROOT)):digest(p) for p in (out/'summary.json',out/'traces.jsonl.gz')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for candidate,values in comparisons.items():
        print(candidate,{b:round(v['ratio'],6) for b,v in values.items()},flush=True)


if __name__ == '__main__': run()
