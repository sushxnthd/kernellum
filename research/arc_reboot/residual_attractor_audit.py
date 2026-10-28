import json, statistics
from pathlib import Path
from collections import defaultdict, Counter
from huggingface_hub import HfApi, snapshot_download

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
models=[x for x in want if x in prefixes]
print("MODELS",json.dumps(models))
root=Path(snapshot_download(REPO,repo_type="dataset",allow_patterns=[f"{m}/*.json" for m in models],local_dir="/tmp/hf_arc_residual"))
gt=Path("/tmp/ARC-AGI-2/data/evaluation")
tasks={p.stem:json.loads(p.read_text()) for p in gt.glob("*.json")}

def canon(g):
 if not isinstance(g,list) or not g or not all(isinstance(r,list) and r for r in g):return None
 try:return tuple(tuple(int(x) for x in r) for r in g)
 except:return None
def exact(a,b):return canon(a)==canon(b)
def shape(g):
 c=canon(g);return None if c is None else (len(c),len(c[0]))
def colors(g):
 c=canon(g);return set() if c is None else set(x for r in c for x in r)
def hamming(a,b):
 a,b=canon(a),canon(b)
 if a is None or b is None or shape(a)!=shape(b):return None
 n=sum(map(len,a));return sum(x!=y for ra,rb in zip(a,b) for x,y in zip(ra,rb))/n if n else None
def gridstr(c):
 if c is None:return None
 return [list(r) for r in c]

pred=defaultdict(dict)
for m in models:
 for p in (root/m).glob("[0-9a-f]*.json"):
  if p.stem not in tasks:continue
  try:arr=json.loads(p.read_text())
  except:continue
  if not isinstance(arr,list):continue
  for i,it in enumerate(arr):
   if i>=len(tasks[p.stem]["test"]) or not isinstance(it,dict):continue
   a=[]
   for k in ("attempt_1","attempt_2"):
    at=it.get(k);a.append(at.get("answer") if isinstance(at,dict) else None)
   pred[m][(p.stem,i)]=a

allkeys=sorted({(tid,i) for tid,t in tasks.items() for i in range(len(t["test"]))})
rows=[]
for k in allkeys:
 tid,i=k;t=tasks[tid]; truth=t["test"][i]["output"]; ct=canon(truth)
 answers=[]; correct=[]
 for m in models:
  if k not in pred[m]:continue
  for j,a in enumerate(pred[m][k],1):
   ca=canon(a)
   if ca is not None:answers.append((m,j,ca))
   if exact(a,truth):correct.append((m,j))
 cnt=Counter(c for _,_,c in answers if c!=ct)
 modal,mc=(cnt.most_common(1)[0] if cnt else (None,0))
 modal_models=sorted({m for m,j,c in answers if c==modal}) if modal else []
 train=t["train"]; ti=t["test"][i]["input"]
 train_in_shapes=[shape(x["input"]) for x in train]; train_out_shapes=[shape(x["output"]) for x in train]
 feat={
  "same_shape_io_train_all":all(shape(x["input"])==shape(x["output"]) for x in train),
  "same_shape_test_truth":shape(ti)==shape(truth),
  "test_input_shape_seen_train":shape(ti) in train_in_shapes,
  "truth_output_shape_seen_train":shape(truth) in train_out_shapes,
  "test_colors_subset_train_inputs":colors(ti).issubset(set().union(*(colors(x["input"]) for x in train))),
  "truth_colors_subset_train_outputs":colors(truth).issubset(set().union(*(colors(x["output"]) for x in train))),
  "n_train":len(train),
  "input_area":shape(ti)[0]*shape(ti)[1],
  "output_area":shape(truth)[0]*shape(truth)[1],
  "area_ratio":(shape(truth)[0]*shape(truth)[1])/(shape(ti)[0]*shape(ti)[1]),
 }
 rows.append({
  "task":tid,"idx":i,"n_model_attempts":len(answers),"solved_by":correct,"n_correct_attempts":len(correct),
  "modal_wrong_count":mc,"modal_wrong_models":modal_models,"modal_wrong_grid":gridstr(modal),
  "truth":truth,"modal_wrong_hamming_to_truth":hamming(modal,ct) if modal else None,
  "features":feat
 })

uns=[r for r in rows if not r["solved_by"]]
sol=[r for r in rows if r["solved_by"]]
def avg(group,path):
 vals=[]
 for r in group:
  v=r["features"][path]
  if isinstance(v,bool):v=int(v)
  if isinstance(v,(int,float)):vals.append(v)
 return statistics.mean(vals) if vals else None
feature_summary={}
for f in ["same_shape_io_train_all","same_shape_test_truth","test_input_shape_seen_train","truth_output_shape_seen_train","test_colors_subset_train_inputs","truth_colors_subset_train_outputs","n_train","input_area","output_area","area_ratio"]:
 feature_summary[f]={"solved_mean":avg(sol,f),"unsolved_mean":avg(uns,f)}
out={
 "models":models,"n_outputs":len(rows),"n_union_solved":len(sol),"union_rate":len(sol)/len(rows),
 "n_union_unsolved":len(uns),
 "unsolved_with_shared_identical_wrong_ge2":sum(r["modal_wrong_count"]>=2 for r in uns),
 "unsolved_with_shared_identical_wrong_ge3":sum(r["modal_wrong_count"]>=3 for r in uns),
 "feature_summary":feature_summary,
 "top_unsolved_attractors":sorted(uns,key=lambda r:(-r["modal_wrong_count"],r["task"],r["idx"]))[:30],
 "near_miss_solved_by_one_model":sorted([r for r in rows if len(set(m for m,j in r["solved_by"]))==1],key=lambda r:(-r["modal_wrong_count"],r["task"]))[:30]
}
Path("residual_attractor_audit.json").write_text(json.dumps(out,indent=2))
print("FINAL_SUMMARY="+json.dumps({k:v for k,v in out.items() if k not in ("top_unsolved_attractors","near_miss_solved_by_one_model")},sort_keys=True))
print("TOP_UNSOLVED="+json.dumps([{k:r[k] for k in ("task","idx","modal_wrong_count","modal_wrong_models","modal_wrong_hamming_to_truth","features")} for r in out["top_unsolved_attractors"][:15]]))
