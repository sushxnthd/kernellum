import json, os, random, statistics
from pathlib import Path

rows=[]
for p in Path(os.environ.get("SHARD_DIR","stagec_shards")).rglob("*.json"):
    try:d=json.loads(p.read_text())
    except Exception:continue
    rows.extend(d.get("families",[]))
# unique by family index
uniq={}
for r in rows: uniq[r.get("index")]=r
rows=[uniq[k] for k in sorted(uniq)]
usable=[r for r in rows if r.get("status")=="USABLE"]

def macro(label):
    return statistics.mean(r["acc"][label] for r in usable) if usable else None

def macro2(label):
    return statistics.mean(r["pass2"][label] for r in usable) if usable else None

def micro(label):
    vals=[q[f"{label}1"] for r in usable for q in r.get("details",[])]
    return statistics.mean(vals) if vals else None

def boot_delta(B=5000):
    if not usable:return None
    vals=[r["acc"]["D"]-r["acc"]["B"] for r in usable]
    rng=random.Random(20261028); n=len(vals); out=[]
    for _ in range(B):
        out.append(statistics.mean(vals[rng.randrange(n)] for _ in range(n)))
    out.sort()
    return [out[int(.025*B)],out[min(B-1,int(.975*B))]]

macroD=macro("D"); macroB=macro("B")
gain=(macroD-macroB) if macroD is not None else None
ci=boot_delta()
improved=sum(r["acc"]["D"]>r["acc"]["B"] for r in usable)
hurt=sum(r["acc"]["D"]<r["acc"]["B"] for r in usable)
ties=len(usable)-improved-hurt

dn=sum(r.get("disagreement_n",0) for r in usable)
dD=sum((r.get("disagreement_acc_D") or 0)*r.get("disagreement_n",0) for r in usable)
dB=sum((r.get("disagreement_acc_B") or 0)*r.get("disagreement_n",0) for r in usable)
disD=dD/dn if dn else None; disB=dB/dn if dn else None
dis_gain=(disD-disB) if dn else None

survival={
    "stage_b_pass_required":True,
    "gain_ge_3pp": gain is not None and gain>=0.03,
    "bootstrap_ci_not_entirely_below_zero": ci is not None and ci[1]>=0,
    "improvement_in_ge3_families": improved>=3,
    "positive_gain_on_disagreement_queries": dis_gain is not None and dis_gain>0,
}
survival["stage_c_effect_passes"]=all(v for k,v in survival.items() if k!="stage_b_pass_required")

summary={
    "families_accounted":len(rows),"usable_families":len(usable),
    "macro_top1":{"A":macro("A"),"B":macroB,"C":macro("C"),"D":macroD,"E":macro("E")},
    "micro_top1":{"A":micro("A"),"B":micro("B"),"C":micro("C"),"D":micro("D"),"E":micro("E")},
    "macro_pass2":{"A":macro2("A"),"B":macro2("B"),"D":macro2("D"),"E":macro2("E")},
    "D_minus_B_macro":gain,"D_minus_B_bootstrap95_family":ci,
    "family_direction":{"improved":improved,"hurt":hurt,"tied":ties},
    "disagreement_queries":dn,"disagreement_D":disD,"disagreement_B":disB,"disagreement_gain":dis_gain,
    "survival":survival,
    "interpretation":"Stage C practical method survives only if Stage B independently passed and every Stage C survival gate is true."
}
Path(os.environ.get("OUT_FILE","stage_c_query_identifiability_aggregated.json")).write_text(json.dumps({"summary":summary,"families":rows},indent=2))
print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
