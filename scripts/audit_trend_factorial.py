"""Same-author second predictor arithmetic and independent trace aggregation."""
import argparse
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path

import numpy as np
from audit_representation_revision import model_bank
from audit_trend_revision import second_bank, read, CONTROL_FILES, BASELINES

ROOT=Path(__file__).resolve().parents[1]
ARMS=('original','remove_only','add_only','both')


def audit(folder,data_path,out):
    manifest=json.loads((folder/'manifest.json').read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(data_path)==manifest['data_sha256']
    for path,sha in manifest['source_sha256'].items():assert digest(ROOT/path)==sha,path
    for name,sha in manifest['output_sha256'].items():assert digest(folder/name)==sha,name
    spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
    records=read(folder/'traces.jsonl.gz');lookup={(r['function'],r['seed'],r['noise'],r['method']):r for r in records}
    expected={(c['name'],s,z,a) for c in spec['cohort'] for s in spec['seeds'] for z in spec['noise_fractions'] for a in ARMS}
    assert len(records)==len(lookup)==len(expected) and set(lookup)==expected
    observed={};scores={}
    for p in CONTROL_FILES:
        for r in read(ROOT/p):
            key=(r['function'],r['seed'],r['noise'])
            scores[(*key,r['method'])]=r['metrics'][-1]['nmse'] if 'metrics' in r else r['nmse']
            if r['method']=='representation_stack':observed[key]=r
    data=np.load(data_path,allow_pickle=False);checked=0;largest_abs=0.;largest_kkt=0.;choice_ties=0
    for case in spec['cohort']:
        name=case['name']
        for seed in spec['seeds']:
            pool=data[f'{name}_{seed}_pool'];test=data[f'{name}_{seed}_test'];truth=data[f'{name}_{seed}_truth']
            for noise in spec['noise_fractions']:
                key=(name,seed,noise);r=observed[key];ids=r['selected'];y=np.array(r['observed'])
                full=[m|{'key':(*m['key'],'constant')} for m in model_bank(pool,test,ids,y)]
                both=second_bank(pool,test,ids,y)
                affine=[m for m in both if m['key'][-1]=='affine']
                retained=[m for m in both if m['key'][-1]=='constant']
                arms=dict(original=full,remove_only=retained,add_only=full+affine,both=both)
                for arm in ARMS:
                    row=lookup[(*key,arm)];bank={m['key']:m for m in arms[arm]}
                    chosen=[];weights=[]
                    group_best={}
                    for m in sorted(arms[arm],key=lambda m:m['cv']):
                        k=m['key'];group=(k[0],k[1],k[2],k[4])
                        if np.isfinite(m['cv']) and group not in group_best:group_best[group]=m
                    ranked=list(group_best.values());cutoff=ranked[min(6,len(ranked))-1]['cv']
                    for desc in row['models']:
                        k=(desc['input'],desc['response'],desc['family'],desc['ridge'],desc['trend'])
                        m=bank[k];g=(k[0],k[1],k[2],k[4]);best=group_best[g]
                        np.testing.assert_allclose(m['cv'],desc['loo_nmse'],rtol=2e-5,atol=1e-7)
                        tolerance=1e-7+2e-5*max(abs(best['cv']),abs(cutoff))
                        assert m['cv']<=best['cv']+tolerance and m['cv']<=cutoff+tolerance
                        if m['key']!=best['key']:choice_ties+=1
                        chosen.append(m);weights.append(desc['weight'])
                    w=np.array(weights);assert w.min()>=-1e-9 and abs(w.sum()-1)<1e-9
                    error=np.column_stack([m['error'] for m in chosen]);gram=error.T@error/len(y)
                    gradient=gram@w;lagrange=float(w@gradient);active=w>1e-8
                    kkt=max(float(abs(gradient[active]-lagrange).max(initial=0)),float(np.maximum(lagrange-gradient[~active],0).max(initial=0)))
                    relative=kkt/max(float(abs(gram).max()),1e-12);assert relative<1e-4
                    largest_kkt=max(largest_kkt,relative)
                    prediction=sum(float(weight)*m['pred'] for weight,m in zip(w,chosen) if weight>0)
                    mean=math.fsum(map(float,truth))/len(truth)
                    variance=max(math.fsum((float(v)-mean)**2 for v in truth)/len(truth),1e-30)
                    nmse=math.fsum((float(a)-float(b))**2 for a,b in zip(prediction,truth))/len(truth)/variance
                    assert math.isclose(nmse,row['nmse'],rel_tol=2e-5,abs_tol=1e-7),(key,arm,nmse,row['nmse'])
                    largest_abs=max(largest_abs,abs(nmse-row['nmse']));checked+=1;scores[(*key,arm)]=row['nmse']
        print(name,checked,flush=True)
    summary=json.loads((folder/'summary.json').read_text());comparisons=0;win_ties=[]
    second_gate={a:True for a in ARMS};recorded_gate={a:True for a in ARMS}
    for arm in ARMS:
        for control in BASELINES:
            p=summary['comparisons'][arm][control]
            byfun={}
            for case in spec['cohort']:
                n=case['name'];values=[math.log(max(scores[(n,s,z,arm)],1e-8))-math.log(max(scores[(n,s,z,control)],1e-8)) for s in spec['seeds'] for z in spec['noise_fractions']]
                byfun[n]=math.exp(statistics.fmean(values))
                assert math.isclose(byfun[n],p['by_function'][n],rel_tol=1e-12)
            assert math.isclose(math.exp(statistics.fmean(map(math.log,byfun.values()))),p['ratio'],rel_tol=1e-12)
            second_wins=sum(v<1 for v in byfun.values())
            if second_wins!=p['wins']:
                disagreement=[n for n,v in byfun.items() if (v<1)!=(p['by_function'][n]<1)]
                assert disagreement and all(abs(byfun[n]-1)<1e-12 and abs(p['by_function'][n]-1)<1e-12 for n in disagreement)
                win_ties.append(dict(arm=arm,control=control,functions=disagreement,
                    recorded_wins=p['wins'],second_wins=second_wins))
            second_ratio=math.exp(statistics.fmean(map(math.log,byfun.values())))
            second_noise=[]
            for z in spec['noise_fractions']:
                v=[math.log(max(scores[(c['name'],s,z,arm)],1e-8))-math.log(max(scores[(c['name'],s,z,control)],1e-8)) for c in spec['cohort'] for s in spec['seeds']]
                assert math.isclose(math.exp(statistics.fmean(v)),p['by_noise'][str(z)],rel_tol=1e-12)
                second_noise.append(math.exp(statistics.fmean(v)))
            second_gate[arm] &= second_ratio<=.8 and second_wins/len(byfun)>=.6 and max(second_noise)<=1
            recorded_gate[arm] &= p['ratio']<=.8 and p['win_fraction']>=.6 and max(p['by_noise'].values())<=1
            comparisons+=1
    assert second_gate==recorded_gate
    result=dict(passed=True,second_arithmetic_outcomes=checked,aggregate_comparisons= comparisons,
        max_absolute_nmse_difference=largest_abs,max_scaled_simplex_kkt=largest_kkt,
        ridge_choice_numerical_ties=choice_ties,same_author_verification=True,
        aggregate_win_numerical_ties=win_ties,recorded_criterion=recorded_gate,second_criterion=second_gate,
        audit_source_sha256={p:digest(ROOT/p) for p in ('scripts/audit_trend_factorial.py',
            'scripts/audit_trend_revision.py','scripts/audit_representation_revision.py')},
        independently_refitted_simplex_weights=False,external_reproduction=False)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();audit(a.folder,a.data,a.out)
