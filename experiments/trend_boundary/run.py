"""Prospective synthetic mechanism boundaries; frozen predictors, shared labels."""
import argparse,gzip,hashlib,json,math,os,platform,subprocess,sys,time
from pathlib import Path
import numpy as np
import scipy
from scipy.special import logsumexp

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from experiments.representation_revision.run import select_coverage
from experiments.trend_factorial.develop import choose
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.trend_revision import TrendBank
from kernellum.discovery.adaptive_revision import AdaptiveStack
from kernellum.discovery.robust_revision import RobustStack
from kernellum.discovery.support_revision import SupportRouter


def response(name,z):
    u,v=z.T
    if name=='log_affine':return np.exp(.5+.8*u-.35*v)
    if name=='log_quadratic':return np.exp(.5-.7*u*u-1.1*v*v+.3*u*v)
    if name=='peaked_log_quadratic':return np.exp(.3-8*u*u-12*v*v+3*u*v)
    if name=='shifted_gaussian':return np.exp(-5*((u-.4)**2+(.5*v+.2)**2))
    if name=='rational_peak':return 1/(1+10*(u+.5)**2+6*(v-.2)**2)
    if name=='signed_cubic':return u+.2*v+.4*u*v+.3*u**3
    if name=='power_law':return 3*np.exp(1.7*u-.8*v)
    raise ValueError(name)


def sample_shell(rng,n,outer,inner):
    blocks=[];count=0
    while count<n:
        z=rng.uniform(-outer,outer,(2*n,2));z=z[np.max(abs(z),axis=1)>inner]
        blocks.append(z);count+=len(z)
    return np.concatenate(blocks)[:n]


def samples(name,seed,spec):
    rng=np.random.default_rng(seed)
    z=rng.uniform(-1,1,(spec['pool_size'],2))
    tests=dict(inside=rng.uniform(-1,1,(spec['tests']['inside'],2)),
        near_shell=sample_shell(rng,spec['tests']['near_shell'],1.5,1),
        far_shell=sample_shell(rng,spec['tests']['far_shell'],3,1.5))
    coordinates=lambda a:np.exp(a) if name=='power_law' else a
    return coordinates(z),response(name,z),{k:(coordinates(v),response(name,v)) for k,v in tests.items()}


def error_score(pred,truth):
    if not np.isfinite(pred).all():return dict(log_nmse=None,nmse=None,finite_prediction=False,max_abs_prediction=None)
    difference=abs(pred-truth)
    with np.errstate(divide='ignore'):
        value=float(logsumexp(2*np.log(difference))-math.log(len(truth))-math.log(max(float(np.var(truth)),1e-30)))
    if not math.isfinite(value):
        if np.all(difference==0):value=-10000.
        else:raise FloatingPointError('nonfinite log error')
    scalar=math.fsum((float(v)/max(float(difference.max()),1e-300))**2 for v in difference)/len(truth)
    if difference.max()>0:
        check=math.log(scalar)+2*math.log(float(difference.max()))-math.log(max(float(np.var(truth)),1e-30))
        assert math.isclose(value,check,rel_tol=1e-12,abs_tol=1e-12)
    return dict(log_nmse=value,nmse=math.exp(value) if -745<value<709 else (0. if value<=-745 else None),
        exact_zero_error=bool(np.all(difference==0)),finite_prediction=True,max_abs_prediction=float(abs(pred).max()))


def run(out,public_freeze):
    spec=json.loads((ROOT/'experiments/trend_boundary/spec.json').read_text());out.mkdir(parents=True,exist_ok=False)
    source=['experiments/trend_boundary/run.py','experiments/trend_boundary/spec.json','docs/TREND_BOUNDARY_PROTOCOL.md',
        'experiments/trend_factorial/develop.py','experiments/representation_revision/run.py',
        'kernellum/discovery/representation.py','kernellum/discovery/trend_revision.py',
        'kernellum/discovery/revision.py','kernellum/discovery/aggregation.py',
        'kernellum/discovery/robust_revision.py','kernellum/discovery/adaptive_revision.py','kernellum/discovery/support_revision.py']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest=dict(public_freeze=public_freeze,local_freeze=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={p:digest(ROOT/p) for p in source},python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    records=[];arrays={};count=0;start=time.perf_counter();signs=[]
    with gzip.open(out/'traces.jsonl.gz','wt') as file:
        for name in spec['functions']:
            for seed in spec['seeds']:
                pool,clean,tests=samples(name,seed,spec);ids=select_coverage(pool,spec,seed)
                perturbation=np.random.default_rng(seed+1000000).normal(size=len(pool))
                arrays[f'{name}_{seed}_pool']=pool;arrays[f'{name}_{seed}_clean']=clean
                for domain,(xt,truth) in tests.items():
                    arrays[f'{name}_{seed}_{domain}_test']=xt;arrays[f'{name}_{seed}_{domain}_truth']=truth
                for noise in spec['noise_fractions']:
                    y=clean+noise*clean.std()*perturbation;observed=y[ids]
                    signs.append(dict(function=name,seed=seed,noise=noise,log_response_available=bool(np.all(observed>0) or np.all(observed<0))))
                    bank=RepresentationBank(pool).fit(ids,observed);trend=TrendBank(bank)
                    full=[m|{'trend':'constant'} for m in bank.models]
                    retained=[m for m in trend.models if m['trend']=='constant'];affine=[m for m in trend.models if m['trend']=='affine']
                    modelsets=dict(original=full,remove_only=retained,add_only=full+affine,both=trend.models)
                    selections={a:choose(v) for a,v in modelsets.items()}
                    adaptive=AdaptiveStack(bank);robust=RobustStack(bank)
                    for domain,(xt,truth) in tests.items():
                        predictors={a:(lambda a=a:sum(w*trend.predict_model(m,xt) for m,w in zip(*selections[a]) if w>0)) for a in modelsets}
                        predictors.update(adaptive_stack=lambda:adaptive.predict(xt)[0],median_stack=lambda:robust.predict(xt)['median_stack'],
                            support_nonlinear_leverage_stack=lambda:SupportRouter(bank,xt).predict('support_nonlinear_leverage_stack')[0])
                        for method in spec['methods']:
                            try:
                                score=error_score(predictors[method](),truth)
                            except (FloatingPointError,OverflowError,np.linalg.LinAlgError) as exc:
                                score=dict(log_nmse=None,nmse=None,finite_prediction=False,max_abs_prediction=None,prediction_exception=str(exc))
                            selected,weights=selections[method] if method in selections else bank.selected('representation_stack')
                            metadata=[dict(input=m['input'],response=m['response'],family=m['family'],trend=m.get('trend','constant'),
                                ridge=m['ridge'],loo_nmse=m['original_cv'],weight=float(w)) for m,w in zip(selected,weights)]
                            r=dict(function=name,seed=seed,noise=noise,domain=domain,method=method,
                                selected=ids,observed=observed.tolist(),models=metadata,
                                input_sha256=hashlib.sha256(pool.tobytes()+xt.tobytes()).hexdigest(),**score)
                            records.append(r);file.write(json.dumps(r,allow_nan=False)+'\n');count+=1
            print(name,count,round(time.perf_counter()-start,1),flush=True)
    np.savez_compressed(out/'inputs_and_truth.npz',**arrays)
    (out/'sign_availability.json').write_text(json.dumps(signs,indent=2)+'\n')
    summary=summarize(records,spec)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    manifest['output_sha256']={p.name:digest(p) for p in out.iterdir() if p.name!='manifest.json'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='comparisons'},indent=2),flush=True)
    for b,v in summary['comparisons'].items():print(b,v['ratio'],v['wins'],v['by_stratum'],flush=True)


def summarize(rows,spec):
    lookup={(r['function'],r['seed'],r['noise'],r['domain'],r['method']):r for r in rows}
    expected={(f,s,n,d,m) for f in spec['functions'] for s in spec['seeds'] for n in spec['noise_fractions'] for d in spec['tests'] for m in spec['methods']}
    assert len(rows)==len(lookup)==len(expected)
    invalid=[list(k) for k,r in lookup.items() if not r['finite_prediction']]
    if invalid:return dict(complete=True,scores=len(rows),criterion_supported=False,nonfinite_predictions=invalid,comparisons={},field_breakthrough_established=False)
    reports={};floor=math.log(spec['error_floor'])
    for baseline in spec['methods']:
        if baseline==spec['primary']:continue
        byfun={};strata={}
        for f in spec['functions']:
            logs=[]
            for s in spec['seeds']:
                for n in spec['noise_fractions']:
                    for d in spec['tests']:
                        k=(f,s,n,d)
                        a=max(lookup[(*k,spec['primary'])]['log_nmse'],floor);b=max(lookup[(*k,baseline)]['log_nmse'],floor)
                        logs.append(a-b);strata.setdefault(f'{n}:{d}',[]).append(a-b)
            byfun[f]=float(np.mean(logs))
        logratio=float(np.mean(list(byfun.values())));logstrata={k:float(np.mean(v)) for k,v in strata.items()}
        exp_safe=lambda v:math.exp(v) if v<709 else None
        reports[baseline]=dict(ratio=exp_safe(logratio),log_ratio=logratio,wins=sum(v<0 for v in byfun.values()),
            by_function={f:exp_safe(v) for f,v in byfun.items()},by_function_log_ratio=byfun,
            by_stratum={k:exp_safe(v) for k,v in logstrata.items()},by_stratum_log_ratio=logstrata)
    g=spec['gate'];passed=all(v['log_ratio']<=math.log(g['ratio_max']) and v['wins']/len(spec['functions'])>=g['win_fraction_min']
        and max(v['by_stratum_log_ratio'].values())<=math.log(g['each_noise_and_domain_ratio_max']) for v in reports.values())
    named=('log_affine','log_quadratic','shifted_gaussian','power_law')
    exact={f:sum(lookup[(f,s,0.,'inside','add_only')]['log_nmse']<=floor for s in spec['seeds']) for f in named}
    tails={m:dict(worst_log10_nmse=max(r['log_nmse'] for r in rows if r['method']==m)/math.log(10),
        errors_above_one=sum(r['log_nmse']>0 for r in rows if r['method']==m)) for m in spec['methods']}
    return dict(complete=True,scores=len(rows),observation_paths=280,criterion_supported=passed,
        field_breakthrough_established=False,exact_family_prediction_counts=exact,
        exact_family_prediction_passed=all(v>=9 for v in exact.values()),comparisons=reports,tail_diagnostics=tails)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--public-freeze',required=True)
    a=p.parse_args();run(a.out,a.public_freeze)
