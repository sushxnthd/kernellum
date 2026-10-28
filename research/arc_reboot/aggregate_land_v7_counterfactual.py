#!/usr/bin/env python3
import json, os, random, statistics
from collections import defaultdict
from pathlib import Path

rows=[]
for p in Path(os.environ.get("SHARD_DIR","land_shards")).rglob("*.json"):
    try:d=json.loads(p.read_text())
    except Exception:continue
    rows.extend(d.get("rows",[]))

# Unique case
uniq={r.get("case"):r for r in rows if r.get("case")}
rows=[uniq[k] for k in sorted(uniq)]
usable=[r for r in rows if r.get("status")=="USABLE"]
by_task=defaultdict(list)
for r in usable:by_task[r["task_id"]].append(r)

def mean_top(label,subset=usable):
    return statistics.mean(r["top1"][label] for r in subset) if subset else None
def mean_p2(label,subset=usable):
    return statistics.mean(r["pass2"][label] for r in subset) if subset else None

B=mean_top("B");D=mean_top("D");W=mean_top("W")
gain=(D-B) if D is not None else None

task_delta={}
for t,rs in by_task.items():
    task_delta[t]=statistics.mean(r["top1"]["D"]-r["top1"]["B"] for r in rs)
dirs={
 "positive":sum(v>0 for v in task_delta.values()),
 "negative":sum(v<0 for v in task_delta.values()),
 "zero":sum(v==0 for v in task_delta.values())
}

rng=random.Random(20261028)
vals=list(task_delta.values());bs=[]
if vals:
    for _ in range(5000):
        bs.append(statistics.mean(vals[rng.randrange(len(vals))] for _ in range(len(vals))))
    bs.sort()
    ci=[bs[int(.025*len(bs))],bs[min(len(bs)-1,int(.975*len(bs)))]]
else:ci=None

oraclepos=[r for r in usable if r.get("oracle")==1]
minority=[r for r in usable if r.get("minority_correct")==1]

oracle_gain=(mean_top("D",oraclepos)-mean_top("B",oraclepos)) if oraclepos else None
minority_gain=(mean_top("D",minority)-mean_top("B",minority)) if minority else None

aucs=[r.get("mechanism",{}).get("auc") for r in usable]
aucs=[x for x in aucs if isinstance(x,(int,float))]
auc_macro=statistics.mean(aucs) if aucs else None
auc_median=statistics.median(aucs) if aucs else None
auc_gt_half=sum(x>0.5 for x in aucs) if aucs else 0

agree=[r.get("released_correctness_agreement") for r in usable]
agree=[x for x in agree if isinstance(x,(int,float))]

survival={
 "usable_cases_ge30":len(usable)>=30,
 "distinct_tasks_ge20":len(by_task)>=20,
 "D_minus_B_ge3pp":gain is not None and gain>=0.03,
 "task_bootstrap_ci_not_entirely_below_zero":ci is not None and ci[1]>=0,
 "positive_task_ids_ge5":dirs["positive"]>=5,
 "D_noninferior_oracle_positive":oracle_gain is not None and oracle_gain>=0,
 "D_positive_minority_correct":minority_gain is not None and minority_gain>0
}
coverage=survival["usable_cases_ge30"] and survival["distinct_tasks_ge20"]
survival["primary_passes"]=all(survival.values())

status_counts={}
for r in rows:status_counts[r.get("status")]=status_counts.get(r.get("status"),0)+1

summary={
 "cases_accounted":len(rows),
 "usable_cases":len(usable),
 "distinct_tasks":len(by_task),
 "status_counts":status_counts,
 "top1":{k:mean_top(k) for k in ["B","D","W","D4","W4","Raw"]},
 "pass2":{k:mean_p2(k) for k in ["B","D","W","D4","W4","Raw"]},
 "D_minus_B":gain,
 "task_bootstrap95_D_minus_B":ci,
 "task_direction":dirs,
 "oracle_positive_cases":len(oraclepos),
 "oracle_positive_D_minus_B":oracle_gain,
 "minority_correct_cases":len(minority),
 "minority_correct_D_minus_B":minority_gain,
 "mechanism":{"case_auc_n":len(aucs),"auc_macro":auc_macro,"auc_median":auc_median,"auc_gt_half":auc_gt_half},
 "released_correctness_crosscheck_mean":statistics.mean(agree) if agree else None,
 "survival":survival,
 "verdict":"PASS" if survival["primary_passes"] else ("INCONCLUSIVE_COVERAGE" if not coverage else "PRIMARY_FAIL")
}
Path(os.environ.get("OUT_FILE","land_v7_counterfactual_aggregate.json")).write_text(json.dumps({"summary":summary,"rows":rows},indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
