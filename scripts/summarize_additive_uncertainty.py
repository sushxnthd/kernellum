"""Post-outcome descriptive seed-block bootstrap; never changes frozen gates."""
import gzip,json,math,statistics
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(832014531);floor=math.log(1e-8);reports={}
for kind,folder in [('synthetic',ROOT/'results/additive_response/confirmation'),('nist',ROOT/'results/additive_response/nist_transfer')]:
 rows=[json.loads(l) for l in gzip.open(folder/'traces.jsonl.gz','rt')]
 lookup={(r['function'],r['seed'],r.get('noise',0.),r.get('domain','held_out'),r['method']):r for r in rows}
 seeds=sorted(set(r['seed'] for r in rows));groups={}
 for label,filter_fn in [('all',lambda r:True),('noisy_gaussian',lambda r:r['function'] in ('gaussian_2d','gaussian_4d','negative_gaussian_2d','negative_gaussian_4d') and r.get('noise',0)>0),('noisy_gaussian_inside',lambda r:r['function'] in ('gaussian_2d','gaussian_4d','negative_gaussian_2d','negative_gaussian_4d') and r.get('noise',0)>0 and r.get('domain')=='inside')]:
  if kind=='nist' and label!='all':continue
  byseed=[]
  for seed in seeds:
   differences=[]
   for r in rows:
    if r['method']!='augmented_adaptive' or r['seed']!=seed or not filter_fn(r):continue
    b=lookup[(r['function'],seed,r.get('noise',0.),r.get('domain','held_out'),'adaptive_stack')]
    assert r['finite_prediction'] and b['finite_prediction']
    differences.append(max(r['log_nmse'],floor)-max(b['log_nmse'],floor))
   byseed.append(statistics.fmean(differences))
  logs=np.array(byseed);resampled=logs[rng.integers(0,len(seeds),(20000,len(seeds)))].mean(1)
  groups[label]=dict(ratio=math.exp(float(logs.mean())),seed_block_bootstrap_95_percentile_interval=np.exp(np.quantile(resampled,[.025,.975])).tolist(),seed_log_ratios=dict(zip(map(str,seeds),byseed)))
 result=dict(post_outcome_descriptive_analysis=True,gate_unchanged=True,repetitions=20000,seed=832014531,clusters='Predetermined seed, jointly across families, dimensions, paired signs, noise levels and domains.',
  scope='Conditional on these selected forms. NIST intervals describe split variation on six fixed datasets; overlapping splits are not independent physical experiments.',comparisons_to_adaptive=groups)
 (folder/'uncertainty.json').write_text(json.dumps(result,indent=2)+'\n');reports[kind]=result
print(json.dumps(reports,indent=2))
