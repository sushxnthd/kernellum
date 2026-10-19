#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else root/'results/nist_safety_multistart.json').read_text())
checks=[]
def ck(name,x): checks.append((name,bool(x)))
ck('schema',d['schema']=='kernellum.nist-safety-multistart.v1')
ck('pinned source',d['source']['commit']=='e270500e3efb4ff9cce91416b3f55678d6271811')
ck('twelve cases',len(d['rows'])==12)
ck('four confirmation',sum(r['partition']=='confirmation' for r in d['rows'])==4)
for r in d['rows']:
 p=root/'external/nist_strd'/f"{r['name']}.dat"
 ck(f"hash:{r['name']}",hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'])
 ck(f"failure:{r['name']}",r['incumbent']['failure']==(r['incumbent']['parameter_error']>1e-3))
 ck(f"route:{r['name']}",r['diagnostic']['routed']==(r['diagnostic']['disagreement'] is None or r['diagnostic']['disagreement']>0.25))
 ck(f"safety:{r['name']}",r['intervention']['rss']<=r['incumbent']['rss']*(1+1e-12))
conf=[r for r in d['rows'] if r['partition']=='confirmation']; routed=[r for r in conf if r['diagnostic']['routed']]
ck('confirmation routed count',d['confirmation']['routed']==len(routed))
ck('confirmation incumbent failures',d['confirmation']['incumbent_failures']==sum(r['incumbent']['failure'] for r in conf))
ck('confirmation intervention failures',d['confirmation']['intervention_failures']==sum(r['intervention']['failure'] for r in conf))
expected='PASS' if all(d['gates'].values()) else 'FAIL'
ck('status',d['status']==expected)
failed=[n for n,x in checks if not x]
print(json.dumps({'schema':'kernellum.nist-safety-multistart-audit.v1','checks':len(checks),'passed':len(checks)-len(failed),'failed':failed},indent=2))
raise SystemExit(bool(failed))
