"""Frozen development screen. Test targets enter scoring only."""
import argparse,gzip,hashlib,inspect,json,os,platform,time
from pathlib import Path
import numpy as np
import scipy,uqtestfuns
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.trend_revision import TrendBank,METHODS
from experiments.representation_revision.run import sample_case,select_coverage

ROOT=Path(__file__).resolve().parents[2]
CONTROL_FILES=(
 'results/representation_revision/confirmation/traces.jsonl.gz',
 'results/robust_revision/development/traces.jsonl.gz',
 'results/support_revision/development/traces.jsonl.gz',
 'results/adaptive_revision/development/traces.jsonl.gz',
 'results/crossfit_revision/development/traces.jsonl.gz',
 'results/noise_revision/development/traces.jsonl.gz')
BASELINES=('representation','representation_stack','raw','raw_stack','median_stack',
 'adaptive_stack','support_nonlinear_leverage_stack','nested_winner','noise_consistent')

def read_records(path):
    with gzip.open(path,'rt') as f:return [json.loads(line) for line in f]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def comparisons(scores,functions,seeds,noises,method):
    result={}
    for baseline in BASELINES:
        byfun={};bynoise={str(n):[] for n in noises}
        for name in functions:
            values=[]
            for seed in seeds:
                for noise in noises:
                    key=(name,seed,noise)
                    value=np.log(max(scores[(*key,method)],1e-8)/max(scores[(*key,baseline)],1e-8))
                    values.append(value);bynoise[str(noise)].append(value)
            byfun[name]=float(np.exp(np.mean(values)))
        logs=np.log(list(byfun.values()));ratio=float(np.exp(logs.mean()))
        leave_one_out=[float(np.exp(np.delete(logs,i).mean())) for i in range(len(logs))]
        wins=sum(v<1 for v in byfun.values())
        result[baseline]=dict(ratio=ratio,wins=wins,win_fraction=wins/len(functions),
          by_noise={n:float(np.exp(np.mean(v))) for n,v in bynoise.items()},by_function=byfun,
          leave_one_function_out_ratio_range=[min(leave_one_out),max(leave_one_out)])
    return result

def run(out):
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uqtestfuns.__version__==spec['uqtestfuns']
    out.mkdir(parents=True,exist_ok=False)
    sources=['kernellum/discovery/trend_revision.py','kernellum/discovery/representation.py',
      'kernellum/discovery/revision.py','kernellum/discovery/aggregation.py',
      'experiments/trend_revision/develop.py','scripts/audit_trend_revision.py','scripts/audit_representation_revision.py',
      'tests/test_trend_revision.py','docs/TREND_REVISION_PROTOCOL.md',
      'experiments/representation_revision/run.py','experiments/representation_revision/spec.json',
      'results/representation_revision/confirmation/exact_nonuniform_inputs.npz',
      'results/representation_revision/confirmation/exact_nonuniform_inputs.json',*CONTROL_FILES]
    manifest=dict(development_only=True,source_hashes={p:digest(ROOT/p) for p in sources},
      python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
      uqtestfuns=uqtestfuns.__version__,threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    controls={};reference={}
    for path in CONTROL_FILES:
        for r in read_records(ROOT/path):
            controls[(r['function'],r['seed'],r['noise'],r['method'])]=r['metrics'][-1]['nmse'] if 'metrics' in r else r['nmse']
            if r['method']=='representation':reference[(r['function'],r['seed'],r['noise'])]=r
    # Fail before any candidate evaluation if a named control is unavailable.
    for case in spec['cohort']:
        for seed in spec['seeds']:
            for noise in spec['noise_fractions']:
                for method in BASELINES:assert (case['name'],seed,noise,method) in controls,method
    archived=np.load(ROOT/'results/representation_revision/confirmation/exact_nonuniform_inputs.npz')
    columns=json.loads((ROOT/'results/representation_revision/confirmation/exact_nonuniform_inputs.json').read_text())['columns']
    records=[];arrays={};start=time.perf_counter()
    with gzip.open(out/'traces.jsonl.gz','wt') as output:
        for index,case in enumerate(spec['cohort']):
            name=case['name'];fun=getattr(uqtestfuns,name)()
            assert digest(Path(inspect.getfile(type(fun))))==case['source_sha256']
            for seed in spec['seeds']:
                x,clean,xt,truth=sample_case(case,index,seed,0.,spec)
                if name in columns:
                    for values,kind in ((x,'pool'),(xt,'test')):
                        original=archived[f'{name}_{seed}_{kind}'];cols=columns[name]
                        scale=np.maximum(abs(original).max(0),1e-12)
                        np.testing.assert_allclose(values[:,cols]/scale,original/scale,rtol=1e-12,atol=1e-12)
                        values[:,cols]=original
                    clean=np.asarray(fun(x)).reshape(-1);truth=np.asarray(fun(xt)).reshape(-1)
                arrays[f'{name}_{seed}_pool']=x;arrays[f'{name}_{seed}_test']=xt
                arrays[f'{name}_{seed}_truth']=truth;arrays[f'{name}_{seed}_clean']=clean
                ids=select_coverage(x,spec,seed)
                sha=hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest()
                perturbation=np.random.default_rng(seed+1000000+index).normal(size=len(x))
                for noise in spec['noise_fractions']:
                    y=clean+noise*np.std(clean)*perturbation
                    prior=reference[(name,seed,noise)]
                    assert ids==prior['selected'] and sha==prior['input_sha256']
                    np.testing.assert_allclose(y[ids],prior['observed'],rtol=1e-13,atol=1e-13)
                    bank=TrendBank(RepresentationBank(x).fit(ids,y[ids]))
                    for method in METHODS:
                        pred=bank.predict(xt,method)
                        nmse=float(np.mean((pred-truth)**2)/max(float(np.var(truth)),1e-30))
                        assert np.isfinite(nmse)
                        r=dict(function=name,seed=seed,noise=noise,method=method,nmse=nmse,
                          selected=ids,observed=y[ids].tolist(),models=bank.describe(method),input_sha256=sha)
                        output.write(json.dumps(r,allow_nan=False)+'\n');output.flush();records.append(r)
                        controls[(name,seed,noise,method)]=nmse
            print(name,len(records),round(time.perf_counter()-start,1),flush=True)
    np.savez_compressed(out/'inputs_and_truth.npz',**arrays)
    names=[c['name'] for c in spec['cohort']]
    reports={m:comparisons(controls,names,spec['seeds'],spec['noise_fractions'],m) for m in METHODS}
    primary=reports['trend_stack']
    passed=all(v['ratio']<=.8 and v['win_fraction']>=.6 and max(v['by_noise'].values())<=1 for v in primary.values())
    summary=dict(development_only=True,field_breakthrough_established=False,criterion_supported=passed,
      runs=len(records),functions=len(names),primary='trend_stack',comparisons=reports,
      error_statistics={m:dict(arithmetic_mean_nmse=float(np.mean([r['nmse'] for r in records if r['method']==m])),
      worst_nmse=max(r['nmse'] for r in records if r['method']==m)) for m in METHODS},seconds=time.perf_counter()-start)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest['output_hashes']={p.name:digest(p) for p in (out/'summary.json',out/'traces.jsonl.gz',out/'inputs_and_truth.npz')}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='comparisons'},indent=2),flush=True)
    for m,report in reports.items():
        for b,v in report.items():print(m,b,v['ratio'],v['wins'],v['by_noise'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
