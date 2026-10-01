"""Same-author second arithmetic for support routing; no candidate imports."""
import gzip
import hashlib
import inspect
import itertools
import json
import time
from pathlib import Path
import numpy as np
import uqtestfuns as uq
from audit_representation_revision import model_bank, matrices, select

ROOT = Path(__file__).resolve().parents[1]
METHODS = tuple('support_' + p + s for p in ('box', 'leverage', 'nonlinear_leverage') for s in ('', '_stack'))


def extended_inverse(a):
    """Pivoted Gauss-Jordan in extended precision, separate from Cholesky."""
    n = len(a)
    work = np.column_stack((a, np.eye(n))).astype(np.longdouble)
    for i in range(n):
        pivot = i + int(np.argmax(abs(work[i:,i])))
        work[[i,pivot]] = work[[pivot,i]]
        work[i] /= work[i,i]
        factors = work[:,i].copy(); factors[i] = 0
        work -= factors[:,None] * work[i][None,:]
    return work[:,n:]


def records(path):
    with gzip.open(ROOT / path, 'rt') as f:
        return [json.loads(line) for line in f]


def geometry(pool, test, ids, key):
    xkind, _, family, ridge = key
    x, xt = pool.copy(), test.copy()
    if xkind == 'log':
        sign = np.where(x.min(0)>0, 1, np.where(x.max(0)<0, -1, 0))
        cols = sign != 0
        x[:, cols] = np.log(x[:, cols]*sign[cols])
        xt[:, cols] = np.log(xt[:, cols]*sign[cols])
    low, span = x.min(0), np.maximum(np.ptp(x, axis=0), 1e-12)
    x, xt = 2*(x-low)/span-1, 2*(xt-low)/span-1
    # Direct pairwise-distance kernels, augmented intercept block inverse.
    kp, kt = matrices(x, xt)[family]
    n = len(ids)
    a = np.ones((n+1, n+1)); a[-1,-1] = 0
    a[:n,:n] = kp[np.ix_(ids,ids)] + ridge*np.eye(n)
    inv = extended_inverse(a)
    cross = np.column_stack((kt[:,ids], np.ones(len(test)))).astype(np.longdouble)
    if family in ('linear', 'quadratic', 'cubic'):
        power = ('linear', 'quadratic', 'cubic').index(family)+1
        normalizer = np.mean((1+np.sum(x*x,axis=1)/x.shape[1])**power)
        diag = (1+np.sum(xt*xt,axis=1)/x.shape[1])**power/normalizer
    else:
        diag = np.ones(len(test))
    variance = np.maximum(diag - np.einsum('ij,ij->i',cross@inv,cross), 0)
    bound = max(float(np.max(1/np.diag(inv)[:n]-ridge)), 0)
    return variance > bound, bound


def main():
    start = time.perf_counter()
    base = ROOT/'results/support_revision/development'
    spec = json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    assert uq.__version__ == spec['uqtestfuns']
    manifest = json.loads((base/'manifest.json').read_text())
    for field in ('source_hashes', 'output_hashes'):
        for path, sha in manifest[field].items():
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == sha, path
    rs = records('results/support_revision/development/traces.jsonl.gz')
    lookup = {(r['function'],r['seed'],r['noise'],r['method']):r for r in rs}
    expected = set(itertools.product([c['name'] for c in spec['cohort']],spec['seeds'],spec['noise_fractions'],METHODS))
    assert set(lookup) == expected and len(rs) == len(expected)
    prior = records('results/representation_revision/confirmation/traces.jsonl.gz')
    controls = {(r['function'],r['seed'],r['noise'],r['method']):r['metrics'][-1]['nmse'] for r in prior}
    for path in ('results/crossfit_revision/development/traces.jsonl.gz', 'results/noise_revision/development/traces.jsonl.gz'):
        for r in records(path): controls[(r['function'],r['seed'],r['noise'],r['method'])] = r['nmse']
    exactdir = ROOT/'results/representation_revision/confirmation'
    meta = json.loads((exactdir/'exact_nonuniform_inputs.json').read_text())
    assert hashlib.sha256((exactdir/'exact_nonuniform_inputs.npz').read_bytes()).hexdigest() == meta['sha256']
    exact = np.load(exactdir/'exact_nonuniform_inputs.npz', allow_pickle=False)
    checked = 0; maximum = 0.; scaled = 0.; max_kkt = 0.; errors = {}
    for index, case in enumerate(spec['cohort']):
        fun = getattr(uq, case['name'])()
        assert hashlib.sha256(Path(inspect.getfile(type(fun))).read_bytes()).hexdigest() == case['source_sha256']
        for seed in spec['seeds']:
            fun.prob_input.reset_rng(seed+1000*index)
            x, xt = fun.prob_input.get_sample(spec['pool_size']), fun.prob_input.get_sample(spec['test_size'])
            if case['name'] in meta['columns']:
                cols = meta['columns'][case['name']]
                for arr, kind in ((x,'pool'),(xt,'test')):
                    original = exact[f"{case['name']}_{seed}_{kind}"]
                    scale = np.maximum(abs(original).max(0),1e-12)
                    np.testing.assert_allclose(arr[:,cols]/scale,original/scale,rtol=1e-12,atol=1e-12)
                    arr[:,cols] = original
            clean, truth = np.asarray(fun(x)).reshape(-1), np.asarray(fun(xt)).reshape(-1)
            z = 2*(x-x.min(0))/np.maximum(np.ptp(x,axis=0),1e-12)-1
            ids = list(map(int,np.random.default_rng(seed).choice(len(x),spec['initial'],replace=False)))
            while len(ids) < spec['budget']:
                dist = np.min([np.sum((z-z[i])**2,axis=1) for i in ids],axis=0)
                dist[ids] = -np.inf; ids.append(int(np.argmax(dist)))
            outside = np.any((xt<x[ids].min(0)) | (xt>x[ids].max(0)),axis=1)
            cache = {}
            for noise in spec['noise_fractions']:
                y = clean + noise*np.std(clean)*np.random.default_rng(seed+1000000+index).normal(size=len(x))
                models = model_bank(x, xt, ids, y[ids])
                raw = select(models,'raw')[0]['pred']
                for method in METHODS:
                    key = (case['name'],seed,noise,method); r = lookup[key]
                    assert r['selected'] == ids
                    assert r['input_sha256'] == hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest()
                    np.testing.assert_allclose(r['observed'],y[ids],rtol=1e-13,atol=1e-13)
                    selected = select(models,'representation_stack' if method.endswith('_stack') else 'representation')
                    descriptions = r['diagnostic']['components']
                    components = {tuple(d[k] for k in ('input','response','family','ridge')):d for d in descriptions}
                    assert len(components)==len(descriptions) and set(components) <= {m['key'] for m in selected}
                    weights = np.array([components.get(m['key'],{}).get('weight',0.) for m in selected])
                    assert weights.min() >= 0 and abs(weights.sum()-1)<1e-12
                    e = np.column_stack([m['error'] for m in selected]); gram = e.T@e/len(ids)
                    grad = gram@weights; obj = weights@grad
                    kkt = max(float(np.max(np.maximum(obj-grad,0))),float(np.max(abs(grad[weights>1e-7]-obj))))/max(float(abs(gram).max()),1e-15)
                    assert kkt<2e-5; max_kkt=max(max_kkt,kkt)
                    prediction = np.zeros(len(xt)); routed_mass = np.zeros(len(xt))
                    for m,w in zip(selected,weights):
                        if w <= 0: continue
                        d = components[m['key']]; route = np.zeros(len(xt),dtype=bool)
                        if m['key'][:2] != ('identity','identity'):
                            if m['key'] not in cache: cache[m['key']] = geometry(x,xt,ids,m['key'])
                            high,bound = cache[m['key']]
                            np.testing.assert_allclose(bound,d['variance_bound'],rtol=1e-4,atol=1e-8)
                            if method.startswith('support_box'): route = outside
                            elif not method.startswith('support_nonlinear') or m['key'][2]!='linear': route = high
                        assert float(route.mean()) == d['routed_fraction'], (key,m['key'])
                        routed_mass += w*route
                        prediction += w*np.where(route,raw,m['pred'])
                    np.testing.assert_allclose(routed_mass.mean(),r['diagnostic']['routed_weight_mean'],atol=1e-14)
                    assert float(np.mean(routed_mass>0))==r['diagnostic']['any_routed_fraction']
                    error = float(np.mean((prediction-truth)**2)/max(float(np.var(truth)),1e-30))
                    delta = abs(error-r['nmse']); maximum=max(maximum,delta); scaled=max(scaled,delta/max(abs(r['nmse']),1e-7))
                    np.testing.assert_allclose(error,r['nmse'],rtol=2e-5,atol=1e-7)
                    errors[key]=error; checked+=1
        print(case['name'],checked,flush=True)
    summary=json.loads((base/'summary.json').read_text())
    for method, comparisons in summary['comparisons'].items():
        gate=True
        for control, v in comparisons.items():
            logs=[]; bynoise={str(n):[] for n in spec['noise_fractions']}; ratios=[]
            for case in spec['cohort']:
                local=[]
                for seed in spec['seeds']:
                    for noise in spec['noise_fractions']:
                        key=(case['name'],seed,noise)
                        log=np.log(max(errors[(*key,method)],1e-8)/max(controls[(*key,control)],1e-8))
                        logs.append(log)
                        # Exact ties are assessed from recorded scores, already checked above.
                        recorded=np.log(max(lookup[(*key,method)]['nmse'],1e-8)/max(controls[(*key,control)],1e-8))
                        local.append(recorded); bynoise[str(noise)].append(recorded)
                ratio=float(np.exp(np.mean(local)));ratios.append(ratio)
                np.testing.assert_allclose(ratio,v['by_function'][case['name']],rtol=1e-12)
            np.testing.assert_allclose(float(np.exp(np.mean(logs))),v['ratio'],rtol=1e-5)
            assert sum(r<1 for r in ratios)==v['wins']
            strata={n:float(np.exp(np.mean(values))) for n,values in bynoise.items()}
            for n,r in strata.items():np.testing.assert_allclose(r,v['by_noise'][n],rtol=1e-12)
            gate &= v['ratio']<=.8 and v['wins']/len(ratios)>=.6 and max(strata.values())<=1
        assert gate==summary['broad_gate'][method]
    result=dict(passed=True,development_only=True,checkpoint_errors_recomputed=checked,methods=len(METHODS),
                max_absolute_nmse_discrepancy=maximum,max_scaled_nmse_discrepancy=scaled,max_scaled_kkt_residual=max_kkt,
                seconds=time.perf_counter()-start,audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                description='Same-author second arithmetic: model choice, stack KKT, routing masks, errors, budgets, hashes and gates; not external reproduction.')
    (base.parent/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__ == '__main__':
    main()
