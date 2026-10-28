import json, statistics, math
from pathlib import Path
from collections import defaultdict
from huggingface_hub import HfApi, snapshot_download

REPO="arcprize/arc_agi_v2_public_eval"
api=HfApi(); files=api.list_repo_files(REPO,repo_type="dataset")
prefixes=sorted({p.split("/")[0] for p in files if "/" in p and p.endswith(".json")})
families={
 "gemini3flash":[("minimal","gemini-3-flash-preview-thinking-minimal",0),("low","gemini-3-flash-preview-thinking-low",1),("medium","gemini-3-flash-preview-thinking-medium",2),("high","gemini-3-flash-preview-thinking-high",3)],
 "gpt51":[("none","gpt-5-1-2025-11-13-thinking-none",0),("low","gpt-5-1-2025-11-13-thinking-low",1),("medium","gpt-5-1-2025-11-13-thinking-medium",2),("high","gpt-5-1-2025-11-13-thinking-high",3)],
 "gpt52":[("none","gpt-5-2-2025-12-11-thinking-none",0),("low","gpt-5-2-2025-12-11-thinking-low",1),("medium","gpt-5-2-2025-12-11-thinking-medium",2),("high","gpt-5-2-2025-12-11-thinking-high",3),("xhigh","gpt-5-2-2025-12-11-thinking-xhigh",4)],
 "gpt54":[("low","gpt-5-4-low",0),("medium","gpt-5-4-medium",1),("high","gpt-5-4-high",2)],
 "claude45":[("none","claude-opus-4-5-20251101-thinking-none",0),("1k","claude-opus-4-5-20251101-thinking-1k",1),("8k","claude-opus-4-5-20251101-thinking-8k",2),("16k","claude-opus-4-5-20251101-thinking-16k",3),("32k","claude-opus-4-5-20251101-thinking-32k",4),("64k","claude-opus-4-5-20251101-thinking-64k",5)],
 "claude46":[("low","claude-opus-4-6-thinking-120K-low",0),("medium","claude-opus-4-6-thinking-120K-medium",1),("high","claude-opus-4-6-thinking-120K-high",2),("max","claude-opus-4-6-thinking-120K-max",3)],
}
families={f:[x for x in xs if x[1] in prefixes] for f,xs in families.items()}
families={f:xs for f,xs in families.items() if len(xs)>=2}
sel=sorted({n for xs in families.values() for _,n,_ in xs})
print("FAMILIES",json.dumps(families))
root=Path(snapshot_download(REPO,repo_type="dataset",allow_patterns=[f"{s}/*.json" for s in sel],local_dir="/tmp/hf_arc_mix"))
gt=Path("/tmp/ARC-AGI-2/data/evaluation"); truth={}
for p in gt.glob("*.json"):
 d=json.loads(p.read_text()); truth[p.stem]=[x["output"] for x in d["test"]]

def canon(g):
 if not isinstance(g,list) or not g or not all(isinstance(r,list) and r for r in g):return None
 try:return tuple(tuple(int(x) for x in r) for r in g)
 except:return None
def exact(a,b):return canon(a)==canon(b)
def getcost(at):
 if not isinstance(at,dict): return None
 md=at.get("metadata") or {}; co=md.get("cost") or {}
 for k in ("total_cost","cost","total"):
  if isinstance(co.get(k),(int,float)):return float(co[k])
 if isinstance(md.get("cost"),(int,float)):return float(md["cost"])
 return None

pred=defaultdict(dict)
for m in sel:
 for p in (root/m).glob("[0-9a-f]*.json"):
  if p.stem not in truth:continue
  try:arr=json.loads(p.read_text())
  except:continue
  if not isinstance(arr,list):continue
  for i,it in enumerate(arr):
   if i>=len(truth[p.stem]) or not isinstance(it,dict):continue
   vals=[]
   for ak in ("attempt_1","attempt_2"):
    at=it.get(ak); ans=at.get("answer") if isinstance(at,dict) else None
    vals.append((ans,getcost(at)))
   pred[m][(p.stem,i)]=vals

def bootstrap(deltas,B=5000,seed=20261028):
 import random
 rng=random.Random(seed); n=len(deltas); out=[]
 if not n:return [None,None]
 for _ in range(B):out.append(sum(deltas[rng.randrange(n)] for _ in range(n))/n)
 out.sort();return [out[int(.025*B)],out[int(.975*B)]]

out={}
for fam,xs in families.items():
 xs=sorted(xs,key=lambda x:x[2]); top=xs[-1]
 common=sorted(set.intersection(*[set(pred[n]) for _,n,_ in xs]))
 _,topname,tope=top
 famout={"common_items":len(common),"top":topname,"comparisons":[]}
 # top same pair
 same_task=[]
 for k in common:
  t=truth[k[0]][k[1]]; h1=pred[topname][k][0][0]; h2=pred[topname][k][1][0]
  same_task.append(int(exact(h1,t) or exact(h2,t)))
 same=sum(same_task)/len(common)
 for label,name,eff in xs[:-1]:
  # two symmetric matched mixed pairings: H1+L1 and H2+L2
  p1=[];p2=[]; deltas1=[];deltas2=[]; costs_same=[];costs_mix=[]
  recover_low_given_hfail=[]
  for idx,k in enumerate(common):
   t=truth[k[0]][k[1]]
   H=pred[topname][k]; L=pred[name][k]
   hs=same_task[idx]
   m1=int(exact(H[0][0],t) or exact(L[0][0],t))
   m2=int(exact(H[1][0],t) or exact(L[1][0],t))
   p1.append(m1);p2.append(m2);deltas1.append(m1-hs);deltas2.append(m2-hs)
   sc=[H[0][1],H[1][1]]; mc=[H[0][1],L[0][1]]
   if all(x is not None for x in sc):costs_same.append(sum(sc))
   if all(x is not None for x in mc):costs_mix.append(sum(mc))
   if not exact(H[0][0],t):recover_low_given_hfail.append(int(exact(L[0][0],t)))
  mixed=(statistics.mean(p1)+statistics.mean(p2))/2
  deltas=[(a+b)/2-s for a,b,s in zip(p1,p2,same_task)]
  famout["comparisons"].append({
   "lower_label":label,"lower_config":name,
   "same_top_pass2":same,
   "mixed_pass2_avg":mixed,
   "delta_mixed_minus_same":mixed-same,
   "bootstrap95_delta":bootstrap(deltas),
   "mixed_pair1":statistics.mean(p1),"mixed_pair2":statistics.mean(p2),
   "low_recovery_given_top_attempt1_wrong":statistics.mean(recover_low_given_hfail) if recover_low_given_hfail else None,
   "mean_same_cost":statistics.mean(costs_same) if costs_same else None,
   "mean_mixed_cost":statistics.mean(costs_mix) if costs_mix else None,
   "cost_ratio":statistics.mean(costs_mix)/statistics.mean(costs_same) if costs_mix and costs_same and statistics.mean(costs_same)>0 else None,
  })
 out[fam]=famout

Path("mixed_effort_portfolio.json").write_text(json.dumps(out,indent=2))
print("FINAL_SUMMARY="+json.dumps(out,sort_keys=True))
