"""Second arithmetic implementation; imports no Kernellum or experiment modules.

Recreates samples and all checkpoint predictions using augmented block solves,
checks the complete trial grid and label budget, and independently recomputes gates.
This is same-author verification, not independent external reproduction.
"""
import argparse
import ast
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def formula_value(formula,names,x):
    env=dict(zip(names,x.T));env['pi']=np.pi
    functions={'ln':np.log,'exp':np.exp,'sqrt':np.sqrt,'sin':np.sin,'cos':np.cos,
               'tanh':np.tanh,'arcsin':np.arcsin}
    ops={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.Mult:lambda a,b:a*b,
         ast.Div:lambda a,b:a/b,ast.Pow:lambda a,b:a**b}
    def visit(n):
        if isinstance(n,ast.Expression):return visit(n.body)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return n.value
        if isinstance(n,ast.Name):return env[n.id]
        if isinstance(n,ast.BinOp):return ops[type(n.op)](visit(n.left),visit(n.right))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -visit(n.operand)
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.UAdd):return visit(n.operand)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and len(n.args)==1 and not n.keywords:
            return functions[n.func.id](visit(n.args[0]))
        raise ValueError('unsupported formula')
    return np.broadcast_to(visit(ast.parse(formula,mode='eval')),(len(x),)).copy()


def samples(row,seed,noise,spec):
    n=int(row['# variables'])
    rng=np.random.default_rng(np.random.SeedSequence([seed,int(row['Number'])]))
    pool=rng.uniform(-1,1,(spec['pool_size'],n));test=rng.uniform(-1,1,(spec['test_size'],n))
    low=np.array([float(row[f'v{i}_low']) for i in range(1,n+1)])
    high=np.array([float(row[f'v{i}_high']) for i in range(1,n+1)])
    names=[row[f'v{i}_name'] for i in range(1,n+1)]
    yp=formula_value(row['Formula'],names,low+(pool+1)*(high-low)/2)
    yt=formula_value(row['Formula'],names,low+(test+1)*(high-low)/2)
    measured=yp+noise*np.std(yp)*rng.normal(size=len(yp))
    return pool,measured,test,yt


def kernels(pool,test):
    dim=pool.shape[1]
    result={}
    for degree,name in enumerate(('linear','quadratic','cubic'),1):
        normalizer=np.mean((1+np.sum(pool**2,axis=1)/dim)**degree)
        result[name]=((1+pool@pool.T/dim)**degree/normalizer,
                      (1+test@pool.T/dim)**degree/normalizer)
    for length,name in zip((.4,.8,1.6),('rbf_short','rbf_medium','rbf_long')):
        matrices=[]
        for x in (pool,test):
            # Broadcasting implementation, unlike production dot-product distance.
            distance=np.sum((x[:,None,:]-pool[None,:,:])**2,axis=2)
            matrices.append(np.exp(-distance/(2*length**2*dim)))
        result[name]=tuple(matrices)
    return result


def predict(matrices,ids,ys,only_rbf=False):
    center=float(ys.mean());scale=max(float(ys.std()),1e-12)
    z=(ys-center)/scale;n=len(ids);best=None
    for name,(pool,test) in matrices.items():
        if only_rbf and not name.startswith('rbf'):continue
        gram=pool[np.ix_(ids,ids)]
        for ridge in (1e-6,1e-3,.1):
            a=np.empty((n+1,n+1));a[:n,:n]=gram+ridge*np.eye(n)
            a[-1,:n]=1;a[:n,-1]=1;a[-1,-1]=0
            inverse=np.linalg.solve(a,np.eye(n+1))
            coefficients=inverse@np.r_[z,0.]
            loo=coefficients[:n]/np.maximum(np.diag(inverse)[:n],1e-12)
            cv=float(np.mean(loo**2))
            if best is None or cv<best[0]:best=(cv,name,ridge,coefficients)
    cv,name,ridge,coef=best
    return center+scale*(matrices[name][1][:,ids]@coef[:-1]+coef[-1]),name,ridge


def quadratic(x,ids,ys,test):
    def phi(v):
        return np.column_stack([np.ones(len(v)),v,*[v[:,i]*v[:,j] for i,j in itertools.combinations_with_replacement(range(v.shape[1]),2)]])
    a=phi(x[ids]);center=ys.mean();scale=max(float(ys.std()),1e-12)
    # Augmented least squares, as opposed to production normal-equation inverse.
    beta=np.linalg.lstsq(np.vstack([a,.001*np.eye(a.shape[1])]),
                         np.r_[(ys-center)/scale,np.zeros(a.shape[1])],rcond=None)[0]
    return center+scale*phi(test)@beta


def compare(lookup,rows,spec,a,b):
    byeq={};bynoise={str(n):[] for n in spec['noise_fractions']}
    for row in rows:
        logs=[]
        for seed in spec['seeds']:
            for noise in spec['noise_fractions']:
                key=(row['Filename'],seed,noise)
                aa=lookup[(*key,a)]['metrics'][-1]['nmse'];bb=lookup[(*key,b)]['metrics'][-1]['nmse']
                v=np.log(max(aa,spec['error_floor']))-np.log(max(bb,spec['error_floor']))
                logs.append(v);bynoise[str(noise)].append(v)
        byeq[row['Filename']]=float(np.exp(np.mean(logs)))
    return dict(ratio=float(np.exp(np.mean(np.log(list(byeq.values()))))),
                win_fraction=float(np.mean(np.array(list(byeq.values()))<1)),
                by_noise={k:float(np.exp(np.mean(v))) for k,v in bynoise.items()})


def audit(folder,out):
    start=time.perf_counter();spec=json.loads((ROOT/'experiments/model_revision/spec.json').read_text())
    manifest=json.loads((folder/'manifest.json').read_text())
    for rel,digest in manifest['source_hashes'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
    for rel,digest in manifest['output_hashes'].items():
        assert hashlib.sha256((folder/rel).read_bytes()).hexdigest()==digest,rel
    with (ROOT/'experiments/discovery_design/vendor/FeynmanEquations.csv').open(encoding='utf-8-sig') as f:
        allrows=list(csv.DictReader(f))
    rows=[r for r in allrows if r['# variables'] and 4<=int(r['# variables'])<=9]
    prior={r['Filename'] for r in allrows if r['# variables'] and int(r['# variables'])<=3}
    assert not prior.intersection(r['Filename'] for r in rows)
    with gzip.open(folder/'traces.jsonl.gz','rt') as f:records=[json.loads(line) for line in f]
    lookup={(r['equation'],r['seed'],r['noise'],r['method']):r for r in records}
    expected=set(itertools.product([r['Filename'] for r in rows],spec['seeds'],spec['noise_fractions'],spec['methods']))
    assert len(records)==len(lookup)==len(expected) and set(lookup)==expected
    max_error=0.;checked=0;changed_model=0
    for row in rows:
        for seed in spec['seeds']:
            for noise in spec['noise_fractions']:
                x,y,test,yt=samples(row,seed,noise,spec);matrices=kernels(x,test)
                initial=list(map(int,np.random.default_rng(seed).choice(len(x),spec['initial'],replace=False)))
                shared=lookup[(row['Filename'],seed,noise,'maximin')]['selected']
                for method in spec['methods']:
                    record=lookup[(row['Filename'],seed,noise,method)]
                    ids=record['selected'];vals=np.asarray(record['observed'])
                    assert len(ids)==len(set(ids))==len(vals)==spec['budget']
                    assert ids[:spec['initial']]==initial
                    assert all(0<=i<len(x) for i in ids)
                    np.testing.assert_allclose(vals,y[ids],rtol=1e-13,atol=1e-13)
                    if method in ('maximin','quadratic_maximin','rbf_maximin'):assert ids==shared
                    assert [m['budget'] for m in record['metrics']]==spec['checkpoints']
                    for m in record['metrics']:
                        b=m['budget'];ys=vals[:b];ii=ids[:b]
                        if method=='quadratic_maximin':pred=quadratic(x,ii,ys,test)
                        else:
                            pred,name,ridge=predict(matrices,ii,ys,method=='rbf_maximin')
                            if name!=m['models'][0]['family'] or ridge!=m['models'][0]['ridge']:changed_model+=1
                        nmse=float(np.mean((pred-yt)**2)/max(float(np.var(yt)),1e-30))
                        error=abs(nmse-m['nmse']);max_error=max(error,max_error);checked+=1
                        np.testing.assert_allclose(nmse,m['nmse'],rtol=2e-5,atol=1e-7)
        print(f"audit {row['Filename']}: {checked} checkpoint errors",flush=True)
    summary=json.loads((folder/'summary.json').read_text())
    comparisons={b:compare(lookup,rows,spec,spec['primary'],b) for b in spec['baseline_methods']}
    secondary={b:compare(lookup,rows,spec,'maximin',b) for b in ('quadratic_maximin','rbf_maximin')}
    g=spec['gates']
    def passes(c):return all(v['ratio']<=g['ratio_max'] and v['win_fraction']>=g['equation_win_fraction_min'] and max(v['by_noise'].values())<=g['each_noise_ratio_max'] for v in c.values())
    assert passes(comparisons)==summary['acquisition_gate']
    assert passes(secondary)==summary['model_revision_gate']
    for k,v in comparisons.items():np.testing.assert_allclose(v['ratio'],summary['comparisons'][k]['ratio'],rtol=1e-12)
    for k,v in secondary.items():np.testing.assert_allclose(v['ratio'],summary['model_revision_comparisons'][k]['ratio'],rtol=1e-12)
    result=dict(passed=True,runs=len(records),equations=len(rows),measurement_calls=len(records)*spec['budget'],
                checkpoint_errors_recomputed=checked,max_absolute_nmse_discrepancy=max_error,
                model_choice_disagreements=changed_model,acquisition_gate=passes(comparisons),
                model_revision_gate=passes(secondary),seconds=time.perf_counter()-start,
                description='Second arithmetic implementation by the same author; no external independent reproduction.',
                audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();audit(args.folder,args.out)
