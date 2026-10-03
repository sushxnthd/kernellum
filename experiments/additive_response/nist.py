"""Targeted external transfer with frozen predictor and NIST certified fit."""
import argparse,csv,gzip,hashlib,json,math,os,platform,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
import scipy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from experiments.additive_response.run import error_score,choose,select_coverage
from kernellum.discovery.additive_response import AdditiveResponseBank,fit_exp,value_jacobian
from kernellum.discovery.representation import RepresentationBank
from kernellum.discovery.trend_revision import TrendBank
from kernellum.discovery.adaptive_revision import AdaptiveStack
from kernellum.discovery.robust_revision import RobustStack
from kernellum.discovery.support_revision import SupportRouter

def run(out,public_freeze):
 out.mkdir(parents=True,exist_ok=False);datafolder=ROOT/'experiments/additive_response/nist_data'
 data_manifest=json.loads((datafolder/'manifest.json').read_text());spec=json.loads((ROOT/'experiments/additive_response/spec.json').read_text())
 names=['Eckerle4','Gauss1','Gauss2','Lanczos3','Hahn1','Bennett5'];seeds=range(104401,104411);rows=[];start=time.perf_counter()
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 sources=['experiments/additive_response/nist.py','docs/ADDITIVE_RESPONSE_NIST_PROTOCOL.md','experiments/additive_response/run.py',
 'kernellum/discovery/additive_response.py','kernellum/discovery/representation.py','kernellum/discovery/trend_revision.py',
 'kernellum/discovery/revision.py','kernellum/discovery/aggregation.py','kernellum/discovery/robust_revision.py',
 'kernellum/discovery/adaptive_revision.py','kernellum/discovery/support_revision.py']
 manifest=dict(public_freeze=public_freeze,local_freeze=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  source_sha256={p:digest(ROOT/p) for p in sources},data_manifest=data_manifest,python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with gzip.open(out/'traces.jsonl.gz','wt') as file:
  for name in names:
   path=datafolder/(name+'.csv');assert digest(path)==data_manifest[name]['csv_sha256']
   data=np.loadtxt(path,delimiter=',',skiprows=1);pool=data[:,1:];truth=data[:,0];assert len(data)==data_manifest[name]['rows']
   for seed in seeds:
    ids=select_coverage(pool,dict(initial=8,budget=min(64,len(pool)//2)),seed)
    test_ids=[i for i in range(len(pool)) if i not in ids];xt=pool[test_ids];yt=truth[test_ids];y=truth[ids]
    bank=RepresentationBank(pool).fit(ids,y);trend=TrendBank(bank);augmented=AdditiveResponseBank(pool).fit(ids,y)
    old=AdaptiveStack(bank);new=AdaptiveStack(augmented);robust=RobustStack(bank)
    full=[m|{'trend':'constant'} for m in bank.models];affine=[m for m in trend.models if m['trend']=='affine']
    chosen={a:choose(v) for a,v in dict(original=full,add_only=full+affine).items()}
    exponential=[m for m in augmented.models if m['family'].startswith('exp_')];exp_model=(exponential or bank.eligible('raw'))[0]
    predictors={a:(lambda a=a:sum(w*trend.predict_model(m,xt) for m,w in zip(*chosen[a]) if w>0)) for a in chosen}
    predictors.update(adaptive_stack=lambda:old.predict(xt)[0],median_stack=lambda:robust.predict(xt)['median_stack'],
     support_nonlinear_leverage_stack=lambda:SupportRouter(bank,xt).predict('support_nonlinear_leverage_stack')[0],
     exponential_only=lambda:augmented.predict_model(exp_model,xt),augmented_winner=lambda:augmented.predict(xt,'representation'),augmented_adaptive=lambda:new.predict(xt)[0])
    for method in spec['methods']:
     selected,weights=chosen[method] if method in chosen else (([exp_model],np.ones(1)) if method=='exponential_only' else
      augmented.selected('representation') if method=='augmented_winner' else augmented.selected('representation_stack') if method=='augmented_adaptive' else bank.selected('representation_stack'))
     try:score=error_score(predictors[method](),yt)
     except (FloatingPointError,OverflowError,np.linalg.LinAlgError) as exc:score=dict(log_nmse=None,nmse=None,finite_prediction=False,max_abs_prediction=None,prediction_exception=str(exc))
     metadata=[{k:m.get(k) for k in ['input','response','family','trend','ridge','original_cv']}|dict(weight=float(w),theta=m.get('theta',np.array([])).tolist(),sign=m.get('sign'),amplitude=m.get('amplitude')) for m,w in zip(selected,weights)]
     row=dict(function=name,seed=seed,method=method,selected=ids,test_ids=test_ids,observed=y.tolist(),models=metadata,
      nonlinear_failures=augmented.nonlinear_failures,**score);rows.append(row);file.write(json.dumps(row,allow_nan=False)+'\n')
   print(name,len(rows),round(time.perf_counter()-start,1),flush=True)
 lookup={(r['function'],r['seed'],r['method']):r for r in rows};assert len(rows)==len(lookup)==480
 floor=math.log(1e-8);comparisons={}
 for control in spec['methods']:
  if control==spec['primary']:continue
  byfun={};invalid=[]
  for name in names:
   values=[]
   for seed in seeds:
    a=lookup[(name,seed,spec['primary'])];b=lookup[(name,seed,control)]
    if not a['finite_prediction'] or not b['finite_prediction']:invalid.append((name,seed));continue
    values.append(max(a['log_nmse'],floor)-max(b['log_nmse'],floor))
   byfun[name]=statistics.fmean(values) if values else None
  lr=statistics.fmean(byfun.values()) if all(v is not None for v in byfun.values()) else None
  exp_safe=lambda v:math.exp(v) if v is not None and v<709 else None
  comparisons[control]=dict(ratio=exp_safe(lr),log_ratio=lr,wins=sum(v is not None and v<0 for v in byfun.values()),by_function={f:exp_safe(v) for f,v in byfun.items()},by_function_log_ratio=byfun,invalid_pairs=invalid)
 data=np.loadtxt(datafolder/'Eckerle4.csv',delimiter=',',skiprows=1);x=data[:,1:];y=data[:,0]
 low=x.min(0);span=np.ptp(x,axis=0);z=2*(x-low)/span-1;amplitude=max(abs(y));theta=fit_exp(z,y/amplitude,'exp_concave')
 prediction=amplitude*value_jacobian(theta,z,'exp_concave')[0];rss=math.fsum(float(v)**2 for v in prediction-y)
 a,b,l=theta;sd=float(span[0]/(2*math.sqrt(2)*abs(l)));center=float(low[0]+span[0]/2+span[0]*b/(4*l*l))
 params=[float(amplitude*math.exp(a+b*b/(4*l*l))*sd),sd,center];cert=[1.5543827178,4.0888321754,451.54121844]
 diagnostic=dict(rss=rss,certified_rss=.0014635887487,rss_relative_error=abs(rss/.0014635887487-1),parameters=params,certified_parameters=cert,
  max_parameter_relative_error=max(abs(p/c-1) for p,c in zip(params,cert)),held_out_evidence=False)
 diagnostic['passed']=diagnostic['rss_relative_error']<=1e-6 and diagnostic['max_parameter_relative_error']<=1e-5
 v=comparisons['adaptive_stack'];summary=dict(scores=480,paths=60,comparisons=comparisons,
  transfer_criterion_supported=not v['invalid_pairs'] and v['log_ratio'] is not None and v['log_ratio']<=math.log(.8) and v['wins']>=4,
  certified_fit_check=diagnostic,field_breakthrough_established=False,
  tails={m:dict(worst_log10_nmse=max(r['log_nmse'] for r in rows if r['method']==m and r['finite_prediction'])/math.log(10),nonfinite_scores=sum(not r['finite_prediction'] for r in rows if r['method']==m)) for m in spec['methods']})
 (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n');manifest['output_sha256']={p.name:digest(p) for p in out.iterdir() if p.name!='manifest.json'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--public-freeze',required=True);a=p.parse_args();run(a.out,a.public_freeze)
