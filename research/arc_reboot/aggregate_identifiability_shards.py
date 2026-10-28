import json, statistics, glob
from pathlib import Path

files=sorted(glob.glob("shards/*.json"))
families=[]
global_n=None
for f in files:
    d=json.loads(Path(f).read_text())
    s=d.get("summary",{})
    if global_n is None:
        global_n=s.get("global_n_families")
    families.extend(d.get("families",[]))

usable=[r for r in families if r.get("status")!="TOO_FEW"]
def med(k):
    vals=[r.get(k) for r in usable if r.get(k) is not None]
    return statistics.median(vals) if vals else None

summary={
    "split":"ARC-TGI-Train-frozen-sharded",
    "shard_files":len(files),
    "expected_global_families":global_n,
    "observed_families":len(families),
    "complete": global_n is not None and len(families)==global_n,
    "usable_families":len(usable),
    "median_spearman_valid":med("spearman_valid"),
    "median_spearman_agnostic":med("spearman_agnostic"),
    "median_valid_gain":med("valid_gain"),
    "median_agnostic_gain":med("agnostic_gain"),
    "valid_positive_corr":sum((r.get("spearman_valid") or 0)>0 for r in usable),
    "agnostic_positive_corr":sum((r.get("spearman_agnostic") or 0)>0 for r in usable),
    "valid_gain_gt_10pp":sum((r.get("valid_gain") or 0)>.10 for r in usable),
    "agnostic_gain_gt_10pp":sum((r.get("agnostic_gain") or 0)>.10 for r in usable),
}
summary["stage_b_pass"]=bool(
    summary["complete"]
    and summary["usable_families"]>=6
    and summary["median_spearman_agnostic"] is not None
    and summary["median_spearman_agnostic"]>=0.30
    and summary["median_agnostic_gain"] is not None
    and summary["median_agnostic_gain"]>=0.10
)
summary["kill_rule"]="PASS only if complete 55-family replication, >=6 usable families, median agnostic Spearman >=0.30, median agnostic selector gain >=0.10."
out={"summary":summary,"families":families}
Path("identifiability_train_replication_aggregated.json").write_text(json.dumps(out,indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
