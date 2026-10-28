import json, os, random, statistics
from collections import defaultdict
from pathlib import Path

folds=[]
for p in Path(os.environ.get("SHARD_DIR","dsl_shards")).rglob("*.json"):
    try:d=json.loads(p.read_text())
    except Exception:continue
    folds.extend(d.get("folds",[]))

# unique fold by task/holdout
uniq={(r["task_id"],r["holdout"]):r for r in folds}
folds=[uniq[k] for k in sorted(uniq)]
by=defaultdict(list)
for r in folds:by[r["task_id"]].append(r)

def mean(k,rows=folds):
    return statistics.mean(r[k] for r in rows) if rows else None

D=mean("D");U=mean("U");B=mean("B");D4=mean("D4");O=mean("O")
gain=D-U if D is not None else None

task_deltas={t:statistics.mean(r["D"]-r["U"] for r in rs) for t,rs in by.items()}
task_dirs={"positive":sum(v>0 for v in task_deltas.values()),
           "negative":sum(v<0 for v in task_deltas.values()),
           "zero":sum(v==0 for v in task_deltas.values())}

rng=random.Random(20261028);vals=list(task_deltas.values());bs=[]
if vals:
    for _ in range(5000):
        bs.append(statistics.mean(vals[rng.randrange(len(vals))] for _ in range(len(vals))))
    bs.sort();ci=[bs[int(.025*len(bs))],bs[min(len(bs)-1,int(.975*len(bs)))]]
else:ci=None

hard=[r for r in folds if r["distinct_heldout_outputs"]>=3]
hard_gain=(mean("D",hard)-mean("U",hard)) if hard else None

survival={
 "usable_folds_ge20":len(folds)>=20,
 "distinct_tasks_ge10":len(by)>=10,
 "D_minus_U_ge_5pp":gain is not None and gain>=0.05,
 "task_bootstrap_ci_not_entirely_below_zero":ci is not None and ci[1]>=0,
 "positive_task_direction_ge5":task_dirs["positive"]>=5,
 "nonnegative_gain_on_ge3_output_folds":hard_gain is not None and hard_gain>=0,
}
survival["transfer_passes"]=all(survival.values())

summary={
 "usable_folds":len(folds),"distinct_tasks":len(by),
 "macro":{"U":U,"B":B,"D":D,"D4":D4,"oracle":O},
 "D_minus_U":gain,"D_minus_B":(D-B) if D is not None else None,
 "D4_minus_U":(D4-U) if D4 is not None else None,
 "task_bootstrap95_D_minus_U":ci,
 "task_direction":task_dirs,
 "ge3_output_folds":len(hard),"ge3_output_D_minus_U":hard_gain,
 "survival":survival,
 "interpretation":"Primary transfer is all-probe D versus uniform semantic-class expected correctness U. D4 is secondary."
}
Path(os.environ.get("OUT_FILE","independent_dsl_transfer_aggregated.json")).write_text(json.dumps({"summary":summary,"folds":folds},indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
