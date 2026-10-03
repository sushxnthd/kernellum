"""Same-author second arithmetic using augmented systems, no candidate imports."""
import argparse,gzip,hashlib,inspect,json,time
from pathlib import Path
import numpy as np
import uqtestfuns
from audit_representation_revision import model_bank,matrices,inverse

ROOT=Path(__file__).resolve().parents[1]
BASELINES=('representation','representation_stack','raw','raw_stack','median_stack',
 'adaptive_stack','support_nonlinear_leverage_stack','nested_winner','noise_consistent')
CONTROL_FILES=('results/representation_revision/confirmation/traces.jsonl.gz',
 'results/robust_revision/development/traces.jsonl.gz','results/support_revision/development/traces.jsonl.gz',
 'results/adaptive_revision/development/traces.jsonl.gz','results/crossfit_revision/development/traces.jsonl.gz',
 'results/noise_revision/development/traces.jsonl.gz')

def read(path):
    with gzip.open(path,'rt') as f:return [json.loads(s) for s in f]

def second_bank(pool,test,ids,y):
    n=len(y);yscale=max(float(y.std()),1e-12)
    models=[m | {'key':(*m['key'],'constant')} for m in model_bank(pool,test,ids,y)
            if m['key'][1]=='identity' or m['key'][2] not in ('quadratic','cubic')]
    signs=np.where(pool.min(0)>0,1,np.where(pool.max(0)<0,-1,0))
    for xkind in (('identity','log') if np.any(signs) else ('identity',)):
        x=pool.copy();xt=test.copy()
        if xkind=='log':
            mask=signs!=0;x[:,mask]=np.log(x[:,mask]*signs[mask]);xt[:,mask]=np.log(xt[:,mask]*signs[mask])
        low=x.min(0);span=np.maximum(np.ptp(x,axis=0),1e-12)
        x=2*(x-low)/span-1;xt=2*(xt-low)/span-1
        f=np.c_[np.ones(n),x[ids]];ft=np.c_[np.ones(len(xt)),xt];p=f.shape[1]
        if n<=p or np.linalg.matrix_rank(f)<p:continue
        bank=matrices(x,xt)
        transforms=[('identity',y)]
        if np.all(y>0):transforms.append(('log_positive',np.log(y)))
        if np.all(y<0):transforms.append(('log_negative',np.log(-y)))
        for ykind,v in transforms:
            center=v.mean();scale=max(float(v.std()),1e-12);z=(v-center)/scale
            for family in ('rbf_short','rbf_medium','rbf_long'):
                kp,kt=bank[family]
                for ridge in (1e-6,1e-3,.1):
                    augmented=np.zeros((n+p,n+p));augmented[:n,:n]=kp[np.ix_(ids,ids)]+ridge*np.eye(n)
                    augmented[:n,n:]=f;augmented[n:,:n]=f.T
                    inv=np.linalg.solve(augmented,np.eye(n+p));coef=inv@np.r_[z,np.zeros(p)]
                    diagonal=np.diag(inv)[:n]
                    if np.any(diagonal<=1e-12):continue
                    loo=z-coef[:n]/diagonal
                    error=(y-inverse(center+scale*loo,ykind))/yscale
                    with np.errstate(over='ignore',invalid='ignore'):cv=float(np.mean(error**2))
                    pred=inverse(center+scale*(kt[:,ids]@coef[:n]+ft@coef[n:]),ykind)
                    models.append(dict(key=(xkind,ykind,family,ridge,'affine'),error=error,cv=cv,pred=pred))
    return sorted(models,key=lambda m:m['cv'])

def audit(folder,out):
    start=time.perf_counter();manifest=json.loads((folder/'manifest.json').read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name,sha in manifest['source_hashes'].items():assert digest(ROOT/name)==sha,name
    for name,sha in manifest['output_hashes'].items():assert digest(folder/name)==sha,name
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uqtestfuns.__version__==spec['uqtestfuns']
    data=np.load(folder/'inputs_and_truth.npz');records=read(folder/'traces.jsonl.gz')
    lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in records}
    expected={(c['name'],s,n,m) for c in spec['cohort'] for s in spec['seeds'] for n in spec['noise_fractions'] for m in ('trend','trend_stack')}
    assert set(lookup)==expected and len(records)==len(expected)
    scores={};reference={}
    for path in CONTROL_FILES:
        for r in read(ROOT/path):
            key=(r['function'],r['seed'],r['noise'],r['method'])
            scores[key]=r['metrics'][-1]['nmse'] if 'metrics' in r else r['nmse']
            if r['method']=='representation':reference[key[:3]]=r
    checked=0;max_nmse=0.;max_kkt=0.;selection_ties=0;max_cv=0.
    for index,case in enumerate(spec['cohort']):
        name=case['name'];fun=getattr(uqtestfuns,name)()
        assert digest(Path(inspect.getfile(type(fun))))==case['source_sha256']
        for seed in spec['seeds']:
            pool=data[f'{name}_{seed}_pool'];test=data[f'{name}_{seed}_test'];truth=data[f'{name}_{seed}_truth'];clean=data[f'{name}_{seed}_clean']
            np.testing.assert_allclose(np.asarray(fun(pool)).reshape(-1),clean,rtol=1e-13,atol=1e-13)
            np.testing.assert_allclose(np.asarray(fun(test)).reshape(-1),truth,rtol=1e-13,atol=1e-13)
            sha=hashlib.sha256(pool.tobytes()+test.tobytes()).hexdigest()
            for noise in spec['noise_fractions']:
                key=(name,seed,noise);prior=reference[key];ids=prior['selected']
                assert len(ids)==len(set(ids))==64 and prior['input_sha256']==sha
                y=clean+noise*clean.std()*np.random.default_rng(seed+1000000+index).normal(size=len(pool))
                np.testing.assert_allclose(y[ids],prior['observed'],rtol=1e-13,atol=1e-13)
                models=second_bank(pool,test,ids,y[ids]);bykey={m['key']:m for m in models}
                groups={}
                for m in models:
                    group=(m['key'][0],m['key'][1],m['key'][2],m['key'][4])
                    if np.isfinite(m['cv']) and group not in groups:groups[group]=m
                top=sorted(groups.values(),key=lambda m:m['cv'])[:6]
                for method in ('trend','trend_stack'):
                    r=lookup[(*key,method)];assert r['selected']==ids and r['input_sha256']==sha
                    np.testing.assert_allclose(r['observed'],y[ids],rtol=1e-13,atol=1e-13)
                    selected=[bykey[(m['input'],m['response'],m['family'],m['ridge'],m['trend'])] for m in r['models']]
                    if method=='trend':
                        assert len(selected)==1
                        best=models[0]
                        np.testing.assert_allclose(selected[0]['cv'],best['cv'],rtol=1e-5,atol=1e-7)
                        selection_ties+=int(selected[0]['key']!=best['key'])
                    else:
                        assert len(selected)==len(top)
                        for a,b in zip(selected,top):
                            np.testing.assert_allclose(a['cv'],b['cv'],rtol=1e-5,atol=1e-7)
                            selection_ties+=int(a['key']!=b['key'])
                        for m in selected:
                            g=(m['key'][0],m['key'][1],m['key'][2],m['key'][4])
                            np.testing.assert_allclose(m['cv'],groups[g]['cv'],rtol=1e-5,atol=1e-7)
                    assert len({(m['key'][0],m['key'][1],m['key'][2],m['key'][4]) for m in selected})==len(selected)
                    for m,saved in zip(selected,r['models']):
                        np.testing.assert_allclose(m['cv'],saved['loo_nmse'],rtol=1e-5,atol=1e-7)
                        max_cv=max(max_cv,abs(m['cv']-saved['loo_nmse'])/max(abs(saved['loo_nmse']),1e-7))
                    w=np.array([m['weight'] for m in r['models']]);assert w.min()>=0 and abs(w.sum()-1)<1e-12
                    if method=='trend':assert w[0]==1
                    else:
                        errors=np.column_stack([m['error'] for m in selected]);gram=errors.T@errors/64
                        grad=gram@w;objective=w@grad;scale=max(float(abs(gram).max()),1e-15)
                        kkt=max(float(np.maximum(objective-grad,0).max()),float(abs(grad[w>1e-7]-objective).max()))/scale
                        max_kkt=max(max_kkt,kkt);assert kkt<2e-5,(key,kkt)
                    pred=sum(weight*m['pred'] for weight,m in zip(w,selected) if weight>0)
                    nmse=float(np.mean((pred-truth)**2)/max(float(np.var(truth)),1e-30))
                    np.testing.assert_allclose(nmse,r['nmse'],rtol=2e-5,atol=1e-7)
                    max_nmse=max(max_nmse,abs(nmse-r['nmse'])/max(abs(r['nmse']),1e-7))
                    scores[(*key,method)]=nmse;checked+=1
        print(name,checked,flush=True)
    summary=json.loads((folder/'summary.json').read_text());report={}
    for method in ('trend','trend_stack'):
        report[method]={}
        for baseline in BASELINES:
            function_logs=[];by_noise={str(n):[] for n in spec['noise_fractions']}
            for c in spec['cohort']:
                values=[]
                for s in spec['seeds']:
                    for n in spec['noise_fractions']:
                        k=(c['name'],s,n);v=np.log(max(scores[(*k,method)],1e-8))-np.log(max(scores[(*k,baseline)],1e-8))
                        values.append(v);by_noise[str(n)].append(v)
                mean=float(np.mean(values));function_logs.append(mean)
                np.testing.assert_allclose(np.exp(mean),summary['comparisons'][method][baseline]['by_function'][c['name']],rtol=1e-5,atol=1e-7)
            ratio=float(np.exp(np.mean(function_logs)));wins=sum(v<0 for v in function_logs)
            ratios={n:float(np.exp(np.mean(v))) for n,v in by_noise.items()}
            saved=summary['comparisons'][method][baseline]
            np.testing.assert_allclose(ratio,saved['ratio'],rtol=1e-5,atol=1e-7)
            assert wins==saved['wins']
            for n,v in ratios.items():np.testing.assert_allclose(v,saved['by_noise'][n],rtol=1e-5,atol=1e-7)
            dropped=[float(np.exp(np.delete(function_logs,i).mean())) for i in range(len(function_logs))]
            np.testing.assert_allclose([min(dropped),max(dropped)],saved['leave_one_function_out_ratio_range'],rtol=1e-5,atol=1e-7)
            report[method][baseline]=dict(ratio=ratio,wins=wins,by_noise=ratios)
    passed=all(v['ratio']<=.8 and v['wins']/39>=.6 and max(v['by_noise'].values())<=1 for v in report['trend_stack'].values())
    assert passed==summary['criterion_supported']
    result=dict(passed=True,criterion_supported=passed,outcomes_recomputed=checked,
      max_scaled_nmse_discrepancy=max_nmse,max_scaled_cv_discrepancy=max_cv,max_scaled_kkt_violation=max_kkt,
      selection_numerical_ties=selection_ties,audit_sha256=digest(Path(__file__)),seconds=time.perf_counter()-start,
      description='Same-author second arithmetic; no candidate/runner imports. Stored weights verified by convex KKT. Selection ties use reported score tolerance. No external reproduction.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();audit(a.folder,a.out)
