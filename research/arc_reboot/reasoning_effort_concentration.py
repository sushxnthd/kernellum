import json, math, statistics
from pathlib import Path
from collections import defaultdict
from huggingface_hub import HfApi, snapshot_download

REPO="arcprize/arc_agi_v2_public_eval"
api=HfApi()
files=api.list_repo_files(REPO, repo_type="dataset")
prefixes=sorted({p.split("/")[0] for p in files if "/" in p and p.endswith(".json")})

families={
 "claude45":[
   ("none","claude-opus-4-5-20251101-thinking-none",0),
   ("1k","claude-opus-4-5-20251101-thinking-1k",1),
   ("8k","claude-opus-4-5-20251101-thinking-8k",2),
   ("16k","claude-opus-4-5-20251101-thinking-16k",3),
   ("32k","claude-opus-4-5-20251101-thinking-32k",4),
   ("64k","claude-opus-4-5-20251101-thinking-64k",5),
 ],
 "gemini3flash":[
   ("minimal","gemini-3-flash-preview-thinking-minimal",0),
   ("low","gemini-3-flash-preview-thinking-low",1),
   ("medium","gemini-3-flash-preview-thinking-medium",2),
   ("high","gemini-3-flash-preview-thinking-high",3),
 ],
 "gpt51":[
   ("none","gpt-5-1-2025-11-13-thinking-none",0),
   ("low","gpt-5-1-2025-11-13-thinking-low",1),
   ("medium","gpt-5-1-2025-11-13-thinking-medium",2),
   ("high","gpt-5-1-2025-11-13-thinking-high",3),
 ],
 "gpt52":[
   ("none","gpt-5-2-2025-12-11-thinking-none",0),
   ("low","gpt-5-2-2025-12-11-thinking-low",1),
   ("medium","gpt-5-2-2025-12-11-thinking-medium",2),
   ("high","gpt-5-2-2025-12-11-thinking-high",3),
   ("xhigh","gpt-5-2-2025-12-11-thinking-xhigh",4),
 ],
 "gpt54":[
   ("low","gpt-5-4-low",0),
   ("medium","gpt-5-4-medium",1),
   ("high","gpt-5-4-high",2),
 ],
 "claude46":[
   ("low","claude-opus-4-6-thinking-120K-low",0),
   ("medium","claude-opus-4-6-thinking-120K-medium",1),
   ("high","claude-opus-4-6-thinking-120K-high",2),
   ("max","claude-opus-4-6-thinking-120K-max",3),
 ],
}
families={f:[x for x in arr if x[1] in prefixes] for f,arr in families.items()}
families={f:arr for f,arr in families.items() if len(arr)>=2}
selected=sorted({name for arr in families.values() for _,name,_ in arr})
print("FAMILIES",json.dumps(families))
print("SELECTED",json.dumps(selected))

root=Path(snapshot_download(REPO, repo_type="dataset", allow_patterns=[f"{s}/*.json" for s in selected], local_dir="/tmp/hf_arc_effort"))
gt_dir=Path("/tmp/ARC-AGI-2/data/evaluation")
truth={}
for p in gt_dir.glob("*.json"):
 d=json.loads(p.read_text()); truth[p.stem]=[x["output"] for x in d["test"]]

def canon(g):
 if not isinstance(g,list) or not g or not all(isinstance(r,list) and r for r in g): return None
 try: return tuple(tuple(int(x) for x in r) for r in g)
 except: return None
def exact(a,b): return canon(a)==canon(b)
def similarity(a,b):
 a,b=canon(a),canon(b)
 if a is None or b is None or len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)): return None
 n=sum(map(len,a))
 return sum(x==y for ra,rb in zip(a,b) for x,y in zip(ra,rb))/n if n else None

preds=defaultdict(dict)
for m in selected:
 for p in (root/m).glob("[0-9a-f]*.json"):
  if p.stem not in truth: continue
  try: arr=json.loads(p.read_text())
  except: continue
  if not isinstance(arr,list): continue
  for i,item in enumerate(arr):
   if i>=len(truth[p.stem]) or not isinstance(item,dict): continue
   a1=item.get("attempt_1",{}).get("answer") if isinstance(item.get("attempt_1"),dict) else None
   a2=item.get("attempt_2",{}).get("answer") if isinstance(item.get("attempt_2"),dict) else None
   preds[m][(p.stem,i)]=(a1,a2)

def rankdata(xs):
 order=sorted(range(len(xs)), key=lambda i: xs[i])
 ranks=[0]*len(xs); i=0
 while i<len(order):
  j=i
  while j+1<len(order) and xs[order[j+1]]==xs[order[i]]: j+=1
  r=(i+j)/2+1
  for k in range(i,j+1): ranks[order[k]]=r
  i=j+1
 return ranks
def pearson(x,y):
 if len(x)<2:return None
 mx,my=statistics.mean(x),statistics.mean(y)
 num=sum((a-mx)*(b-my) for a,b in zip(x,y))
 den=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
 return num/den if den else None
def spearman(x,y): return pearson(rankdata(x),rankdata(y))

out={}
for fam,arr in families.items():
 common=sorted(set.intersection(*[set(preds[name]) for _,name,_ in arr]))
 rows=[]
 for label,name,effort in arr:
  vals=[]
  for k in common:
   t=truth[k[0]][k[1]]
   a1,a2=preds[name][k]
   c1,c2=exact(a1,t),exact(a2,t)
   s=similarity(a1,a2)
   vals.append((c1,c2,canon(a1)==canon(a2),s))
  n=len(vals); first_fail=sum(not x[0] for x in vals)
  simvals=[x[3] for x in vals if x[3] is not None]
  row={
   "label":label,"config":name,"effort":effort,"n":n,
   "pass1":sum(x[0] for x in vals)/n if n else None,
   "pass2":sum(x[0] or x[1] for x in vals)/n if n else None,
   "second_only":sum((not x[0]) and x[1] for x in vals)/n if n else None,
   "recovery_given_first_wrong":sum((not x[0]) and x[1] for x in vals)/first_fail if first_fail else None,
   "exact_duplicate":sum(x[2] for x in vals)/n if n else None,
   "mean_similarity":statistics.mean(simvals) if simvals else None,
  }
  rows.append(row)
 metrics={}
 for metric in ["pass1","pass2","recovery_given_first_wrong","exact_duplicate","mean_similarity"]:
  ys=[r[metric] for r in rows if r[metric] is not None]
  xs=[r["effort"] for r in rows if r[metric] is not None]
  metrics[metric+"_spearman_vs_effort"]=spearman(xs,ys) if len(xs)>=3 else None
 # pass1 vs concentration within family
 for metric in ["exact_duplicate","mean_similarity","recovery_given_first_wrong"]:
  pairs=[(r["pass1"],r[metric]) for r in rows if r["pass1"] is not None and r[metric] is not None]
  metrics[metric+"_spearman_vs_pass1"]=spearman([p[0] for p in pairs],[p[1] for p in pairs]) if len(pairs)>=3 else None
 out[fam]={"common_items":len(common),"rows":rows,"correlations":metrics}

# pooled standardized within-family monotonic pair count
pair_tests=[]
for fam,d in out.items():
 rows=sorted(d["rows"], key=lambda r:r["effort"])
 for a,b in zip(rows,rows[1:]):
  pair_tests.append({
   "family":fam,"from":a["label"],"to":b["label"],
   "pass1_delta":b["pass1"]-a["pass1"],
   "duplicate_delta":b["exact_duplicate"]-a["exact_duplicate"],
   "recovery_delta":b["recovery_given_first_wrong"]-a["recovery_given_first_wrong"],
   "similarity_delta":b["mean_similarity"]-a["mean_similarity"],
  })
summary={
 "families":out,
 "adjacent_effort_steps":pair_tests,
 "counts":{
  "steps":len(pair_tests),
  "pass1_up":sum(x["pass1_delta"]>0 for x in pair_tests),
  "dup_up":sum(x["duplicate_delta"]>0 for x in pair_tests),
  "pass1_up_and_dup_up":sum(x["pass1_delta"]>0 and x["duplicate_delta"]>0 for x in pair_tests),
  "pass1_up_and_recovery_down":sum(x["pass1_delta"]>0 and x["recovery_delta"]<0 for x in pair_tests),
 }
}
Path("reasoning_effort_concentration.json").write_text(json.dumps(summary,indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
