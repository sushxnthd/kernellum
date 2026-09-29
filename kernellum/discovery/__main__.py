"""Recommend a next experiment from a bounded pool and actual observations."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from .design import METHODS, choose


def recommend(pool, observations, method='maximin', seed=0):
    x=np.asarray(pool['points'],dtype=float)
    low=np.asarray(pool['lower'],dtype=float)
    high=np.asarray(pool['upper'],dtype=float)
    if (x.ndim!=2 or x.shape[1]<1 or low.shape!=(x.shape[1],) or high.shape!=low.shape
            or not np.isfinite(x).all() or not np.isfinite(low).all() or not np.isfinite(high).all()
            or np.any(high<=low) or np.any(x<low) or np.any(x>high)):
        raise ValueError('provide finite points and valid bounds for every input dimension')
    indices=[r['index'] for r in observations]
    if not all(type(i)==int for i in indices):
        raise ValueError('observation indices must be integers')
    values=[r['value'] for r in observations]
    normalized=2*(x-low)/(high-low)-1
    idx=choose(normalized,indices,values,method,np.random.default_rng(seed))
    return dict(next_index=idx,inputs=x[idx].tolist(),method=method,
                observed_measurements=len(indices),measurement_executed=False,
                evidence_status='experimental_candidate_failed_frozen_gate' if method.startswith('teacher_risk') else 'baseline',
                note='Run the measurement and add its actual value before requesting the next experiment. This is not a validated scientific law.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pool',type=Path,required=True)
    parser.add_argument('--observations',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--method',choices=METHODS,default='maximin')
    parser.add_argument('--seed',type=int,default=0)
    args=parser.parse_args()
    if args.out.exists():
        parser.error('output already exists')
    pool_bytes=args.pool.read_bytes();obs_bytes=args.observations.read_bytes()
    result=recommend(json.loads(pool_bytes),json.loads(obs_bytes),args.method,args.seed)
    result['input_sha256']={'pool':hashlib.sha256(pool_bytes).hexdigest(),
                           'observations':hashlib.sha256(obs_bytes).hexdigest()}
    with args.out.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
