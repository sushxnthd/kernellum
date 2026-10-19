#!/usr/bin/env python3
import hashlib,json,math,re,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

def source_bytes(path):
 return path.read_bytes().rstrip(b'\r\n')+b'\n'

ROOT=Path(__file__).resolve().parents[1]
NAMES=['Misra1a','Misra1b','Misra1c','Rat43','Lanczos1','Lanczos3','MGH09','MGH10','Lanczos2','MGH17','Misra1d','Rat42']
CONFIRM={'Lanczos2','MGH17','Misra1d','Rat42'}

def model(name,b,x):
 with np.errstate(all='ignore'):
  if name=='Misra1a': return b[0]*(1-np.exp(-b[1]*x))
  if name=='Misra1b': return b[0]*(1-(1+b[1]*x/2)**-2)
  if name=='Misra1c': return b[0]*(1-(1+2*b[1]*x)**-.5)
  if name=='Misra1d': return b[0]*b[1]*x/(1+b[1]*x)
  if name.startswith('Lanczos'): return b[0]*np.exp(-b[1]*x)+b[2]*np.exp(-b[3]*x)+b[4]*np.exp(-b[5]*x)
  if name=='Rat42': return b[0]/(1+np.exp(b[1]-b[2]*x))
  if name=='Rat43': return b[0]/((1+np.exp(b[1]-b[2]*x))**(1/b[3]))
  if name=='MGH09': return b[0]*(x*x+x*b[1])/(x*x+x*b[2]+b[3])
  if name=='MGH10': return b[0]*np.exp(b[1]/(x+b[2]))
  if name=='MGH17': return b[0]+b[1]*np.exp(-x*b[3])+b[2]*np.exp(-x*b[4])
 raise KeyError(name)

def parse(name):
 p=ROOT/'external/nist_strd'/f'{name}.dat'; lines=p.read_text().splitlines()
 n=int(lines[31].strip().split()[0]); starts=[[],[]]; cert=[]
 for line in lines[40:40+n]:
  vals=[float(v) for v in line.split('=')[1].split()]
  starts[0].append(vals[0]);starts[1].append(vals[1]);cert.append(vals[2])
 rss=float(next(x.split(':')[1] for x in lines if x.strip().startswith('Residual Sum of Squares')))
 data=[]
 for line in lines[60:]:
  try: vals=[float(v) for v in line.split()]
  except ValueError: continue
  if len(vals)>=2:data.append(vals)
 a=np.array(data,float)
 return {'x':a[:,1],'y':a[:,0],'starts':[np.array(s,float) for s in starts],'cert':np.array(cert,float),'cert_rss':rss,'sha256':hashlib.sha256(source_bytes(p)).hexdigest()}

def fit(name,x,y,start):
 def resid(b):
  pred=model(name,b,x)
  if pred.shape!=y.shape or not np.all(np.isfinite(pred)): return np.full_like(y,1e100)
  return pred-y
 try:
  z=least_squares(resid,start,method='trf',jac='3-point',xtol=1e-13,ftol=1e-13,gtol=1e-13,max_nfev=5000)
  pred=model(name,z.x,x); safe=np.all(np.isfinite(z.x)) and np.all(np.isfinite(pred))
  span=max(float(np.ptp(y)),1e-12); safe=safe and bool(np.all(pred>=np.min(y)-2*span) and np.all(pred<=np.max(y)+2*span))
  return {'theta':z.x,'rss':float(np.sum((pred-y)**2)) if safe else math.inf,'safe':safe,'success':bool(z.success),'nfev':int(z.nfev)}
 except Exception:return {'theta':np.full(len(start),np.nan),'rss':math.inf,'safe':False,'success':False,'nfev':0}

def err(theta,cert):
 if not np.all(np.isfinite(theta)):return math.inf
 return float(np.max(np.abs(theta-cert)/np.maximum(1,np.abs(cert))))

rows=[]
for name in NAMES:
 d=parse(name); f1=fit(name,d['x'],d['y'],d['starts'][0]); f2=fit(name,d['x'],d['y'],d['starts'][1])
 if f1['safe'] and f2['safe']:
  disagreement=float(np.max(np.abs(f1['theta']-f2['theta'])/np.maximum(1,np.maximum(np.abs(f1['theta']),np.abs(f2['theta'])))))
 else: disagreement=math.inf
 routed=(not f1['safe']) or (not f2['safe']) or disagreement>0.25
 candidates=[f1,f2]
 rng=np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8],'big'))
 center=np.where(np.abs(d['starts'][1])>0,d['starts'][1],d['starts'][0])
 scale=np.maximum(np.abs(center),np.maximum(np.abs(d['starts'][0]-d['starts'][1]),1e-3))
 for _ in range(32): candidates.append(fit(name,d['x'],d['y'],center+rng.normal(0,1,len(center))*scale))
 best=min((z for z in candidates if z['safe']),key=lambda z:z['rss'],default=f1)
 override=bool(routed and best['safe'] and (not f1['safe'] or best['rss']<f1['rss']*(1-1e-10)))
 chosen=best if override else f1
 rows.append({'name':name,'partition':'confirmation' if name in CONFIRM else 'development','sha256':d['sha256'],'diagnostic':{'disagreement':disagreement if math.isfinite(disagreement) else None,'routed':routed},'incumbent':{'rss':f1['rss'],'parameter_error':err(f1['theta'],d['cert']),'failure':err(f1['theta'],d['cert'])>1e-3},'start2':{'rss':f2['rss'],'parameter_error':err(f2['theta'],d['cert'])},'intervention':{'override':override,'rss':chosen['rss'],'parameter_error':err(chosen['theta'],d['cert']),'failure':err(chosen['theta'],d['cert'])>1e-3},'certified_rss':d['cert_rss']})

def summary(part):
 xs=[r for r in rows if r['partition']==part]; routed=[r for r in xs if r['diagnostic']['routed']]
 incfails=sum(r['incumbent']['failure'] for r in xs); intfails=sum(r['intervention']['failure'] for r in xs)
 routedfails=sum(r['incumbent']['failure'] for r in routed); removed=sum(r['incumbent']['failure'] and not r['intervention']['failure'] for r in routed)
 precision=(routedfails/len(routed)) if routed else 0
 return {'cases':len(xs),'routed':len(routed),'diagnostic_precision':precision,'incumbent_failures':incfails,'intervention_failures':intfails,'routed_failures':routedfails,'routed_failures_removed':removed,'overrides':sum(r['intervention']['override'] for r in xs),'rss_worsenings':sum(r['intervention']['rss']>r['incumbent']['rss']*(1+1e-12) for r in xs),'max_incumbent_error':max(r['incumbent']['parameter_error'] for r in xs),'max_intervention_error':max(r['intervention']['parameter_error'] for r in xs)}

conf=summary('confirmation')
gates={'all_complete':len(rows)==12,'route_count':1<=conf['routed']<=3,'precision':conf['diagnostic_precision']>=.75,'half_routed_failures_removed':conf['routed_failures']>0 and 2*conf['routed_failures_removed']>=conf['routed_failures'],'no_rss_worsening':conf['rss_worsenings']==0,'no_nonrouted_override':all(r['diagnostic']['routed'] or not r['intervention']['override'] for r in rows if r['partition']=='confirmation'),'max_error_not_worse':conf['max_intervention_error']<=conf['max_incumbent_error']}
out={'schema':'kernellum.nist-safety-multistart.v1','source':{'repository':'lmfit/lmfit-py','commit':'e270500e3efb4ff9cce91416b3f55678d6271811'},'rule':{'disagreement_threshold':0.25,'parameter_failure_threshold':1e-3,'perturbations':32},'development':summary('development'),'confirmation':conf,'gates':gates,'status':'PASS' if all(gates.values()) else 'FAIL','rows':rows}
json.dump(out,sys.stdout,indent=2,sort_keys=True,allow_nan=False);print()
