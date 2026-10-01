"""Second arithmetic audit of robust aggregation; no candidate/runner imports."""
import hashlib,inspect,itertools,json,time
from pathlib import Path
import numpy as np
import uqtestfuns as uq
from audit_representation_revision import model_bank,select
from audit_support_revision import records
ROOT=Path(__file__).resolve().parents[1]
METHODS=('median_stack','geometric_stack','aggregate_selector')


def combinations(values,weights):
    pairs=[(float(w),values[:,i]) for i,w in enumerate(weights) if w>0]
    total=sum(w for w,_ in pairs)
    mean=sum(w*v for w,v in pairs)/total
    geometric=mean.copy(); median=np.empty(len(values))
    for i in range(len(values)):
        ordered=sorted((float(v[i]),w/total) for w,v in pairs)
        acc=0.
        for value,w in ordered:
            acc+=w
            if acc>=.5:
                median[i]=value;break
        if all(v[i]>0 for _,v in pairs) or all(v[i]<0 for _,v in pairs):
            geometric[i]=np.sign(pairs[0][1][i])*np.exp(sum(w*np.log(abs(v[i])) for w,v in pairs)/total)
    return dict(mean=mean,median=median,geometric=geometric)


def main():
    start=time.perf_counter();folder=ROOT/'results/robust_revision/development'
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text());assert uq.__version__==spec['uqtestfuns']
    manifest=json.loads((folder/'manifest.json').read_text())
    for field in ('source_hashes','output_hashes'):
        for p,sha in manifest[field].items(): assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,p
    rs=records('results/robust_revision/development/traces.jsonl.gz')
    lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in rs}
    expected=set(itertools.product([c['name'] for c in spec['cohort']],spec['seeds'],spec['noise_fractions'],METHODS))
    assert set(lookup)==expected and len(rs)==len(expected)
    prior=records('results/representation_revision/confirmation/traces.jsonl.gz')
    prior_lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in prior}
    controls={k:r['metrics'][-1]['nmse'] for k,r in prior_lookup.items()}
    for path in ('results/crossfit_revision/development/traces.jsonl.gz','results/noise_revision/development/traces.jsonl.gz','results/support_revision/development/traces.jsonl.gz'):
        for r in records(path):controls[(r['function'],r['seed'],r['noise'],r['method'])]=r['nmse']
    exactdir=ROOT/'results/representation_revision/confirmation';meta=json.loads((exactdir/'exact_nonuniform_inputs.json').read_text())
    assert hashlib.sha256((exactdir/'exact_nonuniform_inputs.npz').read_bytes()).hexdigest()==meta['sha256']
    exact=np.load(exactdir/'exact_nonuniform_inputs.npz',allow_pickle=False)
    checked=0;maximum=0.;scaled=0.;max_kkt=0.;choice_ties=0;errors={}
    for index,case in enumerate(spec['cohort']):
        fun=getattr(uq,case['name'])();assert hashlib.sha256(Path(inspect.getfile(type(fun))).read_bytes()).hexdigest()==case['source_sha256']
        for seed in spec['seeds']:
            fun.prob_input.reset_rng(seed+1000*index);x=fun.prob_input.get_sample(spec['pool_size']);xt=fun.prob_input.get_sample(spec['test_size'])
            if case['name'] in meta['columns']:
                cols=meta['columns'][case['name']]
                for arr,kind in ((x,'pool'),(xt,'test')):
                    original=exact[f"{case['name']}_{seed}_{kind}"];scale=np.maximum(abs(original).max(0),1e-12)
                    np.testing.assert_allclose(arr[:,cols]/scale,original/scale,rtol=1e-12,atol=1e-12);arr[:,cols]=original
            clean=np.asarray(fun(x)).reshape(-1);truth=np.asarray(fun(xt)).reshape(-1)
            for noise in spec['noise_fractions']:
                key=(case['name'],seed,noise);r=lookup[(*key,'median_stack')]
                reference=prior_lookup[(*key,'representation_stack')];ids=reference['selected']
                assert len(ids)==len(set(ids))==64
                y=clean+noise*np.std(clean)*np.random.default_rng(seed+1000000+index).normal(size=len(x))
                models=select(model_bank(x,xt,ids,y[ids]),'representation_stack')
                descriptions=r['model']['components'];weights=np.array([d['weight'] for d in descriptions])
                assert descriptions==reference['metrics'][-1]['models']
                assert [m['key'] for m in models]==[tuple(d[k] for k in ('input','response','family','ridge')) for d in descriptions]
                assert weights.min()>=0 and abs(weights.sum()-1)<1e-12
                e=np.column_stack([m['error'] for m in models]);gram=e.T@e/len(ids);grad=gram@weights;obj=weights@grad
                kkt=max(float(np.max(np.maximum(obj-grad,0))),float(np.max(abs(grad[weights>1e-7]-obj))))/max(float(abs(gram).max()),1e-15)
                assert kkt<2e-5;max_kkt=max(max_kkt,kkt)
                loo=y[ids,None]-max(float(y[ids].std()),1e-12)*e
                cv={kind:float(np.mean(((y[ids]-p)/max(float(y[ids].std()),1e-12))**2)) for kind,p in combinations(loo,weights).items()}
                for kind,value in cv.items():np.testing.assert_allclose(value,r['model']['loo_scores'][kind],rtol=1e-5,atol=1e-7)
                chosen=r['model']['choice'];argmin=min(cv,key=cv.get)
                if chosen!=argmin:
                    assert abs(cv[chosen]-cv[argmin])<=1e-7+1e-5*abs(cv[argmin])
                    choice_ties+=1
                predictions=combinations(np.column_stack([m['pred'] for m in models]),weights)
                for method,kind in zip(METHODS,('median','geometric',chosen)):
                    record=lookup[(*key,method)]
                    assert record['model']==r['model'] and record['selected']==ids
                    assert record['input_sha256']==hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest()
                    np.testing.assert_allclose(record['observed'],y[ids],rtol=1e-13,atol=1e-13)
                    error=float(np.mean((predictions[kind]-truth)**2)/max(float(np.var(truth)),1e-30))
                    delta=abs(error-record['nmse']);maximum=max(maximum,delta);scaled=max(scaled,delta/max(abs(record['nmse']),1e-7))
                    np.testing.assert_allclose(error,record['nmse'],rtol=2e-5,atol=1e-7);errors[(*key,method)]=error;checked+=1
        print(case['name'],checked,flush=True)
    summary=json.loads((folder/'summary.json').read_text())
    for method,comparison in summary['comparisons'].items():
        gate=True
        for control,v in comparison.items():
            logs=[];ratios=[];strata={str(n):[] for n in spec['noise_fractions']}
            for case in spec['cohort']:
                local=[]
                for seed in spec['seeds']:
                    for noise in spec['noise_fractions']:
                        key=(case['name'],seed,noise)
                        logs.append(np.log(max(errors[(*key,method)],1e-8)/max(controls[(*key,control)],1e-8)))
                        value=np.log(max(lookup[(*key,method)]['nmse'],1e-8)/max(controls[(*key,control)],1e-8))
                        local.append(value);strata[str(noise)].append(value)
                ratio=float(np.exp(np.mean(local)));ratios.append(ratio)
                np.testing.assert_allclose(ratio,v['by_function'][case['name']],rtol=1e-12)
            np.testing.assert_allclose(float(np.exp(np.mean(logs))),v['ratio'],rtol=1e-5)
            assert sum(r<1 for r in ratios)==v['wins']
            for n,values in strata.items():np.testing.assert_allclose(float(np.exp(np.mean(values))),v['by_noise'][n],rtol=1e-12)
            gate &= v['ratio']<=.8 and v['wins']/39>=.6 and max(v['by_noise'].values())<=1
        assert gate==summary['broad_gate'][method]
    result=dict(passed=True,development_only=True,checkpoint_errors_recomputed=checked,methods=3,
                max_absolute_nmse_discrepancy=maximum,max_scaled_nmse_discrepancy=scaled,max_scaled_kkt_residual=max_kkt,
                aggregation_choice_numerical_ties=choice_ties,seconds=time.perf_counter()-start,
                audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                description='Same-author second arithmetic of components, weights, aggregation, LOO choice, errors, hashes and gates; numerical LOO ties permitted within reported score tolerance; no external reproduction.')
    (folder.parent/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
