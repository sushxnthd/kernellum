"""Opened boundary single-seed development, never confirmation evidence."""
import json,time,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from kernellum.discovery.additive_response import AdditiveResponseBank
from kernellum.discovery.adaptive_revision import AdaptiveStack
from experiments.trend_boundary.run import samples,error_score
from experiments.representation_revision.run import select_coverage

def run():
 spec=json.loads((ROOT/'experiments/trend_boundary/spec.json').read_text());rows=[];start=time.perf_counter()
 for name in spec['functions']:
  pool,clean,tests=samples(name,104001,spec);ids=select_coverage(pool,spec,104001)
  for noise in [0,.002,.02,.1]:
   y=clean+noise*clean.std()*np.random.default_rng(1104001).normal(size=len(pool))
   bank=AdditiveResponseBank(pool).fit(ids,y[ids]);adaptive=AdaptiveStack(bank)
   for domain,(xt,truth) in tests.items():
    for method in ['representation','representation_stack','adaptive']:
     pred=adaptive.predict(xt)[0] if method=='adaptive' else bank.predict(xt,method)
     models=adaptive.models if method=='adaptive' else bank.selected(method)[0]
     rows.append(dict(function=name,noise=noise,domain=domain,method=method,failures=bank.nonlinear_failures,
      models=[dict(input=m['input'],response=m['response'],family=m['family'],cv=m['original_cv']) for m in models],**error_score(pred,truth)))
   print(name,noise,round(time.perf_counter()-start,1),flush=True)
 out=ROOT/'results/additive_response/development';out.mkdir(parents=True,exist_ok=True)
 (out/'one_seed.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':run()
