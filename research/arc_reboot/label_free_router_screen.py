import json, math, statistics, hashlib
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from huggingface_hub import HfApi, snapshot_download
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

REPO="arcprize/arc_agi_v2_public_eval"
api=HfApi(); files=api.list_repo_files(REPO,repo_type="dataset")
prefixes=sorted({p.split("/")[0] for p in files if "/" in p and p.endswith(".json")})
want=[
 "gpt-5-4-pro-xhigh","gpt-5-4-high",
 "claude-opus-4-8-max","claude-opus-4-8-high",
 "claude-opus-4-6-thinking-120K-high",
 "gemini-3-1-pro-preview","gemini-3-deep-think-preview",
 "grok-4.20-multi-agent-beta-0309-xhigh",
 "gpt-5-2-pro-2025-12-11-high",
 "claude-opus-4-5-20251101-thinking-64k"
]
models=[m for m in want if m in prefixes]
print("MODELS",json.dumps(models))
root=Path(snapshot_download(REPO,repo_type="dataset",allow_patterns=[f"{m}/*.json" for m in models],local_dir="/tmp/hf_arc_router"))
gt=Path("/tmp/ARC-AGI-2/data/evaluation")
tasks={p.stem:json.loads(p.read_text()) for p in gt.glob("*.json")}

def canon(g):
 if not isinstance(g,list) or not g or not all(isinstance(r,list) and r for r in g): return None
 try:
  c=tuple(tuple(int(x) for x in r) for r in g)
  if len({len(r) for r in c})!=1:return None
  return c
 except:return None
def shape(c): return (len(c),len(c[0]))
def colors(c): return set(x for r in c for x in r)
def ham(a,b):
 if shape(a)!=shape(b):return None
 n=sum(map(len,a)); return sum(x!=y for ra,rb in zip(a,b) for x,y in zip(ra,rb))/n
def med(xs):
 return statistics.median(xs) if xs else 0.0

pred=defaultdict(dict)
for m in models:
 for p in (root/m).glob("[0-9a-f]*.json"):
  if p.stem not in tasks:continue
  try:arr=json.loads(p.read_text())
  except:continue
  if not isinstance(arr,list):continue
  for i,it in enumerate(arr):
   if i>=len(tasks[p.stem]["test"]) or not isinstance(it,dict):continue
   out=[]
   for key in ("attempt_1","attempt_2"):
    at=it.get(key); out.append(canon(at.get("answer")) if isinstance(at,dict) else None)
   pred[m][(p.stem,i)]=out

items=[]
for tid,t in tasks.items():
 for i,test in enumerate(t["test"]):
  truth=canon(test["output"]); inp=canon(test["input"])
  if truth is None or inp is None:continue
  candidates=defaultdict(list)
  for mi,m in enumerate(models):
   for ai,c in enumerate(pred[m].get((tid,i),[None,None])):
    if c is not None:candidates[c].append((mi,ai))
  if candidates:
   items.append({"tid":tid,"idx":i,"task":t,"truth":truth,"inp":inp,"cands":dict(candidates)})
print("ITEMS",len(items))

def fold(tid,k=5):
 return int(hashlib.sha256(tid.encode()).hexdigest()[:8],16)%k

def task_struct(task,inp):
 train=task["train"]
 out_shapes=[(len(p["output"]),len(p["output"][0])) for p in train]
 in_shapes=[(len(p["input"]),len(p["input"][0])) for p in train]
 out_colors=set()
 for p in train:
  out_colors |= {x for r in p["output"] for x in r}
 ratios=[]
 dhdw=[]
 for p in train:
  ih,iw=len(p["input"]),len(p["input"][0]); oh,ow=len(p["output"]),len(p["output"][0])
  ratios.append((oh/ih,ow/iw)); dhdw.append((oh-ih,ow-iw))
 return out_shapes,in_shapes,out_colors,ratios,dhdw

def model_priors(train_items):
 # correctness per attempt and pass@2 from training fold only
 stats=[]
 for mi,m in enumerate(models):
  a1=a2=anyp=n=0
  for it in train_items:
   p=pred[m].get((it["tid"],it["idx"]))
   if not p:continue
   n+=1
   c1=p[0]==it["truth"]; c2=p[1]==it["truth"]
   a1+=c1;a2+=c2;anyp+=(c1 or c2)
  # beta smoothing
  stats.append(((a1+1)/(n+2),(a2+1)/(n+2),(anyp+1)/(n+2)))
 return stats

def feats(it,c,support,priors):
 task,inp=it["task"],it["inp"]
 out_shapes,in_shapes,out_colors,ratios,dhdw=task_struct(task,inp)
 total_attempts=sum(len(v) for v in it["cands"].values())
 uniq_models=sorted(set(mi for mi,ai in support))
 dup_models=sum(1 for mi in uniq_models if sum(1 for x in support if x[0]==mi)>=2)
 reli=[priors[mi][ai] for mi,ai in support]
 passrel=[priors[mi][2] for mi in uniq_models]
 ch,cw=shape(c); ih,iw=shape(inp)
 ratio=(ch/ih,cw/iw); delta=(ch-ih,cw-iw)
 other=[x for x in it["cands"] if x!=c and shape(x)==shape(c)]
 hd=[ham(c,x) for x in other]; hd=[x for x in hd if x is not None]
 f=[
  len(support)/max(1,total_attempts),
  len(uniq_models)/max(1,len(models)),
  dup_models/max(1,len(models)),
  max(reli) if reli else 0, statistics.mean(reli) if reli else 0,
  max(passrel) if passrel else 0, statistics.mean(passrel) if passrel else 0,
  sum(math.log(max(1e-4,r)/(max(1e-4,1-r))) for r in reli),
  float(shape(c)==shape(inp)),
  float(shape(c) in out_shapes),
  float(ratio in ratios),
  float(delta in dhdw),
  float(colors(c).issubset(out_colors)),
  len(colors(c)-out_colors),
  ch*cw/(ih*iw),
  min([abs(ratio[0]-r[0])+abs(ratio[1]-r[1]) for r in ratios] or [10]),
  statistics.mean(hd) if hd else 1.0,
  min(hd) if hd else 1.0,
  len(it["cands"]),
 ]
 # model identity/support attempt indicators
 for mi in range(len(models)):
  f.append(float(any(x[0]==mi for x in support)))
 for mi in range(len(models)):
  f.append(float(any(x==(mi,0) for x in support)))
  f.append(float(any(x==(mi,1) for x in support)))
 return f

def rank_baselines(it,priors):
 rows=[]
 for c,sup in it["cands"].items():
  count=len(sup)
  rel=sum(priors[mi][ai] for mi,ai in sup)
  passrel=sum(priors[mi][2] for mi in set(mi for mi,ai in sup))
  rows.append((c,count,rel,passrel))
 majority=[x[0] for x in sorted(rows,key=lambda x:(x[1],x[2]),reverse=True)[:2]]
 weighted=[x[0] for x in sorted(rows,key=lambda x:(x[2],x[1]),reverse=True)[:2]]
 passweighted=[x[0] for x in sorted(rows,key=lambda x:(x[3],x[1]),reverse=True)[:2]]
 return majority,weighted,passweighted

def hit(sel,truth):return any(c==truth for c in sel)

all_fold=[]
for fidx in range(5):
 train=[x for x in items if fold(x["tid"])!=fidx]
 test=[x for x in items if fold(x["tid"])==fidx]
 pri=model_priors(train)
 X=[];y=[]
 for it in train:
  for c,sup in it["cands"].items():
   X.append(feats(it,c,sup,pri));y.append(int(c==it["truth"]))
 clf=make_pipeline(StandardScaler(),LogisticRegression(C=0.5,max_iter=500,class_weight="balanced"))
 clf.fit(np.asarray(X),np.asarray(y))
 # best static model according to training pass@2
 bestmi=max(range(len(models)),key=lambda mi:pri[mi][2])
 metrics=Counter(); n=0
 detailed=[]
 for it in test:
  n+=1
  cands=list(it["cands"])
  scores=clf.predict_proba(np.asarray([feats(it,c,it["cands"][c],pri) for c in cands]))[:,1]
  learned=[c for _,c in sorted(zip(scores,cands),key=lambda z:z[0],reverse=True)[:2]]
  maj,wgt,pw=rank_baselines(it,pri)
  bp=[c for c in pred[models[bestmi]].get((it["tid"],it["idx"]),[]) if c is not None][:2]
  oracle=cands
  metrics["learned"]+=hit(learned,it["truth"])
  metrics["majority"]+=hit(maj,it["truth"])
  metrics["weighted"]+=hit(wgt,it["truth"])
  metrics["passweighted"]+=hit(pw,it["truth"])
  metrics["bestmodel"]+=hit(bp,it["truth"])
  metrics["oracle"]+=hit(oracle,it["truth"])
  detailed.append({"tid":it["tid"],"idx":it["idx"],"learned":int(hit(learned,it["truth"])),"best":int(hit(bp,it["truth"])),"oracle":int(hit(oracle,it["truth"]))})
 all_fold.append({"fold":fidx,"n":n,"best_model":models[bestmi],"metrics":{k:v/n for k,v in metrics.items()},"counts":dict(metrics),"detailed":detailed})
 print("FOLD",fidx,json.dumps(all_fold[-1]["metrics"],sort_keys=True))

tot=Counter();N=0
for r in all_fold:
 N+=r["n"]
 for k,v in r["counts"].items():tot[k]+=v
summary={k:v/N for k,v in tot.items()}
# paired learned vs best model exact sign test counts
L=[];B=[]
for r in all_fold:
 for d in r["detailed"]:
  L.append(d["learned"]);B.append(d["best"])
learn_only=sum(l and not b for l,b in zip(L,B));best_only=sum(b and not l for l,b in zip(L,B))
summary["learned_only"]=learn_only;summary["best_only"]=best_only
Path("label_free_router_screen.json").write_text(json.dumps({"models":models,"summary":summary,"folds":all_fold},indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
