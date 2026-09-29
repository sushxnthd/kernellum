"""Post-hoc development on the OPENED cohort, never confirmation evidence.

Two prespecified diagnostic variants replace direct teachers with polynomial
trend plus an RBF fit to the remaining observed residuals. They test whether
teachers' failure to represent the known student class caused the first failure.
"""
import json
from pathlib import Path
import time
import numpy as np
from kernellum.discovery.design import features, fit, risk_scores
from experiments.discovery_design.run import data, equations


def choose_residual(x, observed, values, mode='residual_mean'):
    phi=features(x)
    y=np.asarray(values)
    z=(y-y.mean())/max(float(y.std()),1e-12)
    beta,inv=fit(phi[observed],z)
    pred=phi@beta
    distances=((x[:,None]-x[observed][None,:])**2).sum(2)
    if (len(observed)-12)%4==3:
        scores=distances.min(axis=1)
    else:
        residual=z-pred[observed]
        dtrain=distances[observed]
        targets=[]
        for length in (0.3,0.6,1.2):
            kernel=np.exp(-dtrain/(2*length**2))
            alpha=np.linalg.solve(kernel+1e-4*np.eye(len(y)),residual)
            targets.append(pred+np.exp(-distances/(2*length**2))@alpha)
        targets=np.asarray(targets)
        if mode=='residual_mean':
            scores=risk_scores(phi,beta,inv,targets)
        elif mode=='residual_robust':
            scores=np.min([risk_scores(phi,beta,inv,t[None,:]) for t in targets],axis=0)
        else:
            raise ValueError(mode)
    scores[observed]=-np.inf
    return int(np.argmax(scores))


def main():
    spec=json.loads(Path('experiments/discovery_design/spec.json').read_text())
    output=Path('results/discovery_design/development.jsonl')
    with output.open('x') as f:
        for row in equations():
            for seed in spec['seeds']:
                for noise in spec['noise_fractions']:
                    x,y,xt,yt=data(row,seed,noise,spec)
                    for mode in ['residual_mean','residual_robust']:
                        start=time.perf_counter()
                        idx=list(map(int,np.random.default_rng(seed).choice(len(x),12,replace=False)))
                        while len(idx)<40:
                            idx.append(choose_residual(x,idx,y[idx],mode))
                        yy=y[idx];center=yy.mean();scale=max(float(yy.std()),1e-12)
                        b,_=fit(features(x[idx]),(yy-center)/scale)
                        nmse=float(np.mean((center+scale*features(xt)@b-yt)**2)/np.var(yt))
                        f.write(json.dumps(dict(equation=row['Filename'],seed=seed,noise=noise,method=mode,
                            selected=idx,observed=y[idx].tolist(),nmse=nmse,seconds=time.perf_counter()-start,
                            status='development_on_opened_cohort'))+'\n')
    reference=[json.loads(s) for s in Path('results/discovery_design/frozen_run/traces.jsonl').read_text().splitlines()]
    base={(r['equation'],r['seed'],r['noise']):r['metrics'][-1]['nmse'] for r in reference if r['method']=='maximin'}
    dev=[json.loads(s) for s in output.read_text().splitlines()]
    for mode in ['residual_mean','residual_robust']:
        logs=[np.log(max(r['nmse'],1e-8)/max(base[(r['equation'],r['seed'],r['noise'])],1e-8)) for r in dev if r['method']==mode]
        print(mode,'development ratio vs maximin',np.exp(np.mean(logs)))

if __name__=='__main__':main()
