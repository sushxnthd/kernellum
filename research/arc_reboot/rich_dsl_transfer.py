import json, os, random, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

SEED=20261028
MAX_PROGRAMS=20000

# Independent solver imports come from pinned external repo via PYTHONPATH.
from app import config
from app.search.enumerator import enumerate_programs
from app.dsl.interpreter import run_tokens

PROGRAMS=[]
for seq in enumerate_programs(config.DSL_MAX_DEPTH):
    PROGRAMS.append(tuple(int(x) for x in seq))
    if len(PROGRAMS)>=MAX_PROGRAMS:break

def canon(x):
    try:
        a=np.asarray(x,dtype=int)
        if a.ndim!=2 or a.size==0:return None
        if max(a.shape)>30:return None
        if np.any(a<0) or np.any(a>9):return None
        return (tuple(a.shape),tuple(map(int,a.ravel())))
    except Exception:return None

def arr(c):
    shape,flat=c
    return np.asarray(flat,dtype=int).reshape(shape)

def sigstr(c):
    return json.dumps(c,separators=(",",":")) if c is not None else "~INVALID"

def run(seq,g):
    try:return canon(run_tokens(list(seq),np.asarray(g,dtype=int)))
    except Exception:return None

def unique_arrays(xs,limit=None):
    out=[];seen=set()
    for a in xs:
        c=canon(a)
        if c is not None and c not in seen:
            seen.add(c);out.append(arr(c))
            if limit and len(out)>=limit:break
    return out

def d4(g):
    a=np.asarray(g,dtype=int)
    xs=[]
    for k in range(4):
        r=np.rot90(a,k)
        xs.extend([r,np.fliplr(r)])
    return unique_arrays(xs)

def mixed_probes(retained):
    rng=random.Random(SEED+77);out=[];seen=set()
    def add(a):
        c=canon(a)
        if c is not None and c not in seen:
            seen.add(c);out.append(arr(c))
    for g in retained:
        a=np.asarray(g,dtype=int)
        for x in d4(a):add(x)
        cols=sorted(set(map(int,a.ravel())))
        movable=[c for c in cols if c!=0]
        for _ in range(3):
            p=movable[:];rng.shuffle(p);mp={c:q for c,q in zip(movable,p)};mp[0]=0
            x=np.vectorize(lambda v:mp.get(int(v),int(v)))(a);add(x)
        for sh in (1,-1):
            add(np.roll(a,sh,axis=0));add(np.roll(a,sh,axis=1))
    rng.shuffle(out)
    return out[:24]

def d4_probes(retained):
    xs=[]
    for g in retained:xs.extend(d4(g))
    return unique_arrays(xs,12)

def class_centrality_from_signatures(rep_sigs):
    ids=list(rep_sigs)
    scores={}
    nprobe=len(next(iter(rep_sigs.values()))) if rep_sigs else 0
    for pid,row in rep_sigs.items():
        vals=[]
        for k in range(nprobe):
            y=row[k]
            if y is None:continue
            valid=[rep_sigs[q][k] for q in ids if rep_sigs[q][k] is not None]
            if valid:vals.append(sum(v==y for v in valid)/len(valid))
        scores[pid]=statistics.mean(vals) if vals else 0.0
    return scores

def centrality_eval(reps,probes):
    sigs={pi:tuple(run(PROGRAMS[pi],g) for g in probes) for pi in reps}
    return class_centrality_from_signatures(sigs)

def plurality(gs):
    cnt=Counter(g for g in gs if g is not None)
    if not cnt:return None
    return sorted(cnt.items(),key=lambda z:(-z[1],sigstr(z[0])))[0][0]

def process_task(path):
    tid=path.stem
    try:t=json.loads(path.read_text())
    except Exception:return []
    train=t.get("train",[])
    if len(train)<2:return []
    ins=[np.asarray(p["input"],dtype=int) for p in train]
    truth=[canon(p["output"]) for p in train]
    if any(x is None for x in truth):return []

    # Fixed program-pool outputs on all labeled demonstration inputs.
    pred=[]
    for seq in PROGRAMS:
        pred.append([run(seq,g) for g in ins])

    rows=[]
    for hold in range(len(train)):
        kept=[j for j in range(len(train)) if j!=hold]
        cand=[pi for pi,row in enumerate(pred) if all(row[j]==truth[j] for j in kept)]
        if len(cand)<3:continue

        retained=[ins[j] for j in kept]
        probes=mixed_probes(retained)
        if not probes:continue

        # Evaluate complete mixed-probe behavior exactly once per consistent candidate.
        cand_sigs={}
        classes=defaultdict(list)
        for pi in cand:
            sg=tuple(run(PROGRAMS[pi],g) for g in probes)
            cand_sigs[pi]=sg;classes[sg].append(pi)
        if len(classes)<3:continue

        reps={}
        for sg,members in classes.items():
            reps[sg]=min(members,key=lambda i:(len(PROGRAMS[i]),PROGRAMS[i]))

        held={pi:pred[pi][hold] for pi in reps.values()}
        distinct={g for g in held.values() if g is not None}
        if len(distinct)<2:continue

        y=truth[hold]
        U=sum(g==y for g in held.values())/len(held)
        B=int(plurality(list(held.values()))==y)

        rep_sigs={pi:cand_sigs[pi] for pi in reps.values()}
        cs=class_centrality_from_signatures(rep_sigs)
        best=min(reps.values(),key=lambda i:(-cs[i],len(PROGRAMS[i]),PROGRAMS[i]))
        D=int(held[best]==y)

        p4=d4_probes(retained)
        c4=centrality_eval(list(reps.values()),p4) if p4 else {i:0.0 for i in reps.values()}
        best4=min(reps.values(),key=lambda i:(-c4[i],len(PROGRAMS[i]),PROGRAMS[i]))
        D4=int(held[best4]==y)
        O=int(any(g==y for g in held.values()))

        rows.append({"task_id":tid,"holdout":hold,"raw_candidates":len(cand),
                     "semantic_classes":len(classes),"distinct_heldout_outputs":len(distinct),
                     "U":U,"B":B,"D":D,"D4":D4,"O":O,
                     "D_centrality":cs[best],"D_tokens":list(PROGRAMS[best]),
                     "D4_centrality":c4[best4],"D4_tokens":list(PROGRAMS[best4])})
    return rows

def main():
    root=Path(os.environ.get("RICH_DSL_ROOT","/tmp/richdsl"))
    files=sorted((root/"data/training").glob("*.json"))
    start=int(os.environ.get("TASK_START","0"));end=int(os.environ.get("TASK_END",str(len(files))))
    rows=[]
    print("PROGRAM_COUNT",len(PROGRAMS),"TASK_COUNT",len(files),flush=True)
    for idx,p in enumerate(files):
        if start<=idx<end:
            r=process_task(p);rows.extend(r)
            if r:print("TASK",idx,p.stem,"usable_folds",len(r),flush=True)
    summary={"task_start":start,"task_end":end,"tasks_total":len(files),
             "program_count":len(PROGRAMS),"n_folds":len(rows),
             "n_tasks":len(set(r["task_id"] for r in rows))}
    Path(os.environ.get("OUT_FILE","rich_dsl_transfer_shard.json")).write_text(json.dumps({"summary":summary,"folds":rows},indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":main()
