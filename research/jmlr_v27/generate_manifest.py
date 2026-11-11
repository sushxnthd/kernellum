from __future__ import annotations
import csv
from pathlib import Path

METHODS = ['ls', 'mgda', 'cagrad', 'nashmtl', 'fairgrad']
SEEDS = range(5)
QM9_TARGETS = [0,1,2,3,5,6,12,13,14,15,11]
QM9_DOSE = {0,2,12}

def rows():
    out=[]
    for method in METHODS:
        for seed in SEEDS:
            out.append(dict(dataset='nyuv2', method=method, seed=seed, arm='coarse', parent='', target_id='', k=1, epochs=200, status='PENDING'))
            for parent in range(3):
                for k in (2,4,8):
                    for arm in ('exposed','canonicalized'):
                        out.append(dict(dataset='nyuv2', method=method, seed=seed, arm=arm, parent=parent, target_id='', k=k, epochs=200, status='PENDING'))
    for method in METHODS:
        for seed in SEEDS:
            out.append(dict(dataset='qm9', method=method, seed=seed, arm='coarse', parent='', target_id='', k=1, epochs=300, status='PENDING'))
            for parent,target_id in enumerate(QM9_TARGETS):
                ks=(4,2,8) if target_id in QM9_DOSE else (4,)
                for k in ks:
                    for arm in ('exposed','canonicalized'):
                        out.append(dict(dataset='qm9', method=method, seed=seed, arm=arm, parent=parent, target_id=target_id, k=k, epochs=300, status='PENDING'))
    assert len(out)==1350
    return out

if __name__ == '__main__':
    dest=Path(__file__).with_name('manifest.csv')
    data=rows()
    with dest.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=['dataset','method','seed','arm','parent','target_id','k','epochs','status'])
        w.writeheader(); w.writerows(data)
    print(f'wrote {len(data)} cells -> {dest}')
