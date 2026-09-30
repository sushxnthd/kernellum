"""Export exact nonuniform input columns, verified against original trace hashes.

Run on the original arithmetic platform. Uniform RNG columns regenerate bitwise;
nonuniform inverse-distribution math can differ by a few ULPs across CPUs.
"""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
import uqtestfuns as u
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'results/representation_revision/confirmation'
spec=json.loads((ROOT/'experiments/representation_revision/spec.json').read_text())
with gzip.open(folder/'traces.jsonl.gz','rt') as f:records=[json.loads(l) for l in f]
lookup={(r['function'],r['seed']):r['input_sha256'] for r in records};arrays={};columns={};checked=0
for index,case in enumerate(spec['cohort']):
 for seed in spec['seeds']:
  fun=getattr(u,case['name'])();fun.prob_input.reset_rng(seed+1000*index)
  x=fun.prob_input.get_sample(spec['pool_size']);xt=fun.prob_input.get_sample(spec['test_size'])
  assert hashlib.sha256(x.tobytes()+xt.tobytes()).hexdigest()==lookup[(case['name'],seed)],(case['name'],seed)
  cols=[i for i,m in enumerate(fun.prob_input.marginals) if m.distribution!='uniform']
  if cols:
   columns[case['name']]=cols
   arrays[f"{case['name']}_{seed}_pool"]=x[:,cols];arrays[f"{case['name']}_{seed}_test"]=xt[:,cols]
  checked+=1
p=folder/'exact_nonuniform_inputs.npz';np.savez_compressed(p,**arrays)
manifest=dict(description='Original nonuniform input columns, reconstructed after the run and verified bit-for-bit against all original full-input hashes. Uniform columns remain seed-reconstructed. No new evaluation data.',full_input_pairs_verified=checked,columns=columns,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
(folder/'exact_nonuniform_inputs.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
