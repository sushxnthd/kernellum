import json, statistics
from pathlib import Path
from collections import defaultdict
from huggingface_hub import HfApi, snapshot_download

REPO="arcprize/arc_agi_v2_public_eval"
api=HfApi(); files=api.list_repo_files(REPO,repo_type="dataset")
prefixes=sorted({p.split("/")[0] for p in files if "/" in p and p.endswith(".json")})
want=[
 "gpt-5-4-pro-xhigh","gpt-5-4-high","gpt-5-4-medium",
 "claude-opus-4-8-max","claude-opus-4-8-high","claude-opus-4-6-thinking-120K-max","claude-opus-4-6-thinking-120K-high",
 "gemini-3-1-pro-preview","gemini-3-deep-think-preview","gemini-3-pro-preview",
 "grok-4.20-multi-agent-beta-0309-xhigh","kimi-k2.5","minimax-m2.5"
]
selected=[x for x in want if x in prefixes]
print("SELECTED",json.dumps(selected))
root=Path(snapshot_download(REPO,repo_type="dataset",allow_patterns=[f"{s}/*.json" for s in selected],local_dir="/tmp/hf_arc_cond"))
gt=Path("/tmp/ARC-AGI-2/data/evaluation")
truth={}
for p in gt.glob("*.json"):
 d=json.loads(p.read_text()); truth[p.stem]=[x["output"] for x in d["test"]]
def canon(g):
 if not isinstance(g,list) or not g or not all(isinstance(r,list) and r for r in g): return None
 try:return tuple(tuple(int(x) for x in r) for r in g)
 except:return None
def exact(a,b):return canon(a)==canon(b)
def sim(a,b):
 a,b=canon(a),canon(b)
 if a is None or b is None or len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)):return None
 n=sum(map(len,a));return sum(x==y for x,y in zip(sum(a,()),sum(b,())))/n if n else None

preds=defaultdict(dict)
for m in selected:
 for p in (root/m).glob("[0-9a-f]*.json"):
  if p.stem not in truth:continue
  try:a=json.loads(p.read_text())
  except:continue
  if not isinstance(a,list):continue
  for i,it in enumerate(a):
   if i>=len(truth[p.stem]) or not isinstance(it,dict):continue
   a1=it.get("attempt_1",{}).get("answer") if isinstance(it.get("attempt_1"),dict) else None
   a2=it.get("attempt_2",{}).get("answer") if isinstance(it.get("attempt_2"),dict) else None
   preds[m][(p.stem,i)]=(a1,a2)

summary={}
for m in selected:
 keys=sorted(preds[m])
 rows=[]
 for k in keys:
  t=truth[k[0]][k[1]];a1,a2=preds[m][k]
  c1,c2=exact(a1,t),exact(a2,t); dup=canon(a1) is not None and canon(a1)==canon(a2); s=sim(a1,a2)
  rows.append((c1,c2,dup,s))
 n=len(rows); wrong=[x for x in rows if not x[0]]; right=[x for x in rows if x[0]]
 ws=[x[3] for x in wrong if x[3] is not None]; rs=[x[3] for x in right if x[3] is not None]
 summary[m]={
  "n":n,"pass1":sum(x[0] for x in rows)/n if n else None,"pass2":sum(x[0] or x[1] for x in rows)/n if n else None,
  "first_wrong_n":len(wrong),
  "recovery_given_first_wrong":sum(x[1] for x in wrong)/len(wrong) if wrong else None,
  "exact_duplicate_given_first_wrong":sum(x[2] for x in wrong)/len(wrong) if wrong else None,
  "similarity_given_first_wrong":statistics.mean(ws) if ws else None,
  "exact_duplicate_given_first_correct":sum(x[2] for x in right)/len(right) if right else None,
  "similarity_given_first_correct":statistics.mean(rs) if rs else None,
 }
Path("conditional_redundancy_audit.json").write_text(json.dumps(summary,indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
