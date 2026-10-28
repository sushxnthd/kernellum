import json, os, random, statistics
from pathlib import Path

rows=[]
for p in Path(os.environ.get("SHARD_DIR","stage_d_shards")).rglob("*.json"):
    try:d=json.loads(p.read_text())
    except Exception:continue
    rows.extend(d.get("families",[]))
uniq={}
for r in rows: uniq[r.get("index")]=r
rows=[uniq[k] for k in sorted(uniq)]
usable=[r for r in rows if r.get("status")=="USABLE"]

def macro(label):
    return statistics.mean(r["acc"][label] for r in usable) if usable else None
def micro(label):
    vals=[q[label+"1"] for r in usable for q in r.get("details",[])]
    return statistics.mean(vals) if vals else None
def macro2(label):
    return statistics.mean(r["pass2"][label] for r in usable) if usable else None
def boot_delta(label_a,label_b,B=5000):
    if not usable:return None
    vals=[r["acc"][label_a]-r["acc"][label_b] for r in usable]
    rng=random.Random(20261028); n=len(vals); out=[]
    for _ in range(B):
        out.append(statistics.mean(vals[rng.randrange(n)] for _ in range(n)))
    out.sort()
    return [out[int(.025*B)],out[min(B-1,int(.975*B))]]

mW=macro("W"); mB=macro("B")
gain=mW-mB if mW is not None else None
ci=boot_delta("W","B")
improved=sum(r["acc"]["W"]>r["acc"]["B"] for r in usable)
hurt=sum(r["acc"]["W"]<r["acc"]["B"] for r in usable)
ties=len(usable)-improved-hurt
dn=sum(r.get("disagreement_n",0) for r in usable)
dW=sum((r.get("disagreement_acc_W") or 0)*r.get("disagreement_n",0) for r in usable)
dB=sum((r.get("disagreement_acc_B") or 0)*r.get("disagreement_n",0) for r in usable)
disW=dW/dn if dn else None; disB=dB/dn if dn else None
dis_gain=disW-disB if dn else None

survival={
  "stage_b_passed":True,
  "stage_c_single_class_primary_failed":True,
  "gain_ge_3pp":gain is not None and gain>=0.03,
  "bootstrap_ci_not_entirely_below_zero":ci is not None and ci[1]>=0,
  "improvement_in_ge3_families":improved>=3,
  "positive_gain_on_disagreement_queries":dis_gain is not None and dis_gain>0,
}
survival["stage_d_effect_passes"]=all(survival.values())

summary={
 "families_accounted":len(rows),"usable_families":len(usable),
 "macro_top1":{k:macro(k) for k in ["B","W","Wd4","D","E","C"]},
 "micro_top1":{k:micro(k) for k in ["B","W","Wd4","D","E","C"]},
 "macro_pass2":{k:macro2(k) for k in ["B","W","Wd4","D","E","C"]},
 "W_minus_B_macro":gain,"W_minus_B_bootstrap95_family":ci,
 "family_direction":{"improved":improved,"hurt":hurt,"tied":ties},
 "disagreement_queries":dn,"disagreement_B":disB,"disagreement_W":disW,
 "disagreement_gain":dis_gain,
 "secondary_Wd4_minus_B_macro":(macro("Wd4")-mB) if mB is not None else None,
 "survival":survival,
 "interpretation":"W_all is the preregistered Stage D primary. W_D4 is secondary and cannot rescue a failed W_all primary."
}
Path(os.environ.get("OUT_FILE","stage_d_weighted_aggregated.json")).write_text(json.dumps({"summary":summary,"families":rows},indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
