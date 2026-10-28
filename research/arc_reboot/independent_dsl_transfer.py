import itertools, json, math, os, random, statistics
from collections import Counter, defaultdict
from pathlib import Path

SEED=20261028
MAX_DEPTH=6

def canon(g):
    try:
        if not isinstance(g,(list,tuple)) or not g:return None
        rows=[]
        w=None
        for r in g:
            if not isinstance(r,(list,tuple)) or not r:return None
            rr=tuple(int(x) for x in r)
            if any(x<0 or x>9 for x in rr):return None
            if w is None:w=len(rr)
            if len(rr)!=w:return None
            rows.append(rr)
        return tuple(rows)
    except Exception:return None

def to_list(c):
    return [list(r) for r in c]

def sigstr(c):
    return json.dumps(c,separators=(",",":")) if c is not None else "~INVALID"

# Exact quickstart primitives.
def tophalf(grid):
    return grid[:len(grid)//2]

def rot90(grid):
    return list(zip(*grid[::-1]))

def hmirror(grid):
    return grid[::-1]

def compress(grid):
    ri=[i for i,r in enumerate(grid) if len(set(r))==1]
    ci=[j for j,c in enumerate(zip(*grid)) if len(set(c))==1]
    return [[v for j,v in enumerate(r) if j not in ci] for i,r in enumerate(grid) if i not in ri]

def trim(grid):
    return [r[1:-1] for r in grid[1:-1]]

PRIMS={"compress":compress,"hmirror":hmirror,"rot90":rot90,"tophalf":tophalf,"trim":trim}
PNAMES=sorted(PRIMS)

def program_string(tup):
    return "lambda grid: "+"".join(x+"(" for x in tup)+"grid"+")"*len(tup)

PROGRAMS=[]
for d in range(1,MAX_DEPTH+1):
    for tup in itertools.product(PNAMES,repeat=d):
        PROGRAMS.append({"ops":tup,"depth":d,"string":program_string(tup)})

def run_program(p,g):
    try:
        x=g
        # quickstart string p1(p2(...grid)); execute inside-out.
        for name in reversed(p["ops"]):
            x=PRIMS[name](x)
        return canon(x)
    except Exception:
        return None

def d4(c):
    # numpy-free D4 over canonical tuple grids.
    def r90(a):
        return tuple(tuple(row) for row in zip(*a[::-1]))
    def flr(a):
        return tuple(tuple(reversed(r)) for r in a)
    out=[]; x=c
    for _ in range(4):
        out.extend([x,flr(x)])
        x=r90(x)
    return unique(out)

def unique(xs,limit=None):
    out=[]; seen=set()
    for x in xs:
        c=canon(x)
        if c is not None and c not in seen:
            seen.add(c);out.append(c)
            if limit and len(out)>=limit:break
    return out

def roll(c,shift,axis):
    h,w=len(c),len(c[0])
    if axis==0:
        s=shift%h
        return c[-s:]+c[:-s] if s else c
    s=shift%w
    if not s:return c
    return tuple(tuple(list(r[-s:])+list(r[:-s])) for r in c)

def mixed_probes(retained_inputs):
    rng=random.Random(SEED+77)
    out=[];seen=set()
    def add(c):
        if c is not None and c not in seen:
            seen.add(c);out.append(c)
    for c in retained_inputs:
        for x in d4(c):add(x)
        cols=sorted({x for r in c for x in r}); movable=[x for x in cols if x!=0]
        for _ in range(3):
            perm=movable[:];rng.shuffle(perm);mp={a:b for a,b in zip(movable,perm)};mp[0]=0
            x=tuple(tuple(mp.get(v,v) for v in r) for r in c);add(x)
        for sh in (1,-1):
            add(roll(c,sh,0));add(roll(c,sh,1))
    rng.shuffle(out)
    return out[:24]

def d4_probes(retained_inputs):
    out=[]
    for c in retained_inputs:out.extend(d4(c))
    return unique(out,12)

def centralities(class_reps, probes):
    # class_reps maps class signature -> program id
    ids=list(class_reps.values())
    outs={pid:[run_program(PROGRAMS[pid],to_list(x)) for x in probes] for pid in ids}
    sc={}
    for pid,row in outs.items():
        vals=[]
        for k,y in enumerate(row):
            if y is None:continue
            valid=[outs[q][k] for q in ids if outs[q][k] is not None]
            if valid:
                vals.append(sum(v==y for v in valid)/len(valid))
        sc[pid]=statistics.mean(vals) if vals else 0.0
    return sc

def plurality(grids):
    cnt=Counter(g for g in grids if g is not None)
    if not cnt:return None
    return sorted(cnt.items(),key=lambda z:(-z[1],sigstr(z[0])))[0][0]

def task_boot_ci(folds,B=5000):
    by=defaultdict(list)
    for r in folds:by[r["task_id"]].append(r["D"]-r["U"])
    vals=[statistics.mean(v) for v in by.values()]
    if not vals:return None
    rng=random.Random(SEED);n=len(vals);bs=[]
    for _ in range(B):
        bs.append(statistics.mean(vals[rng.randrange(n)] for _ in range(n)))
    bs.sort()
    return [bs[int(.025*B)],bs[min(B-1,int(.975*B))]]

def process_task(tid,task):
    train=task.get("train",[])
    if len(train)<2:return []
    ins=[canon(x["input"]) for x in train]; outs=[canon(x["output"]) for x in train]
    if any(x is None for x in ins+outs):return []

    # Precompute every program on every demonstration input exactly once.
    pred=[[None]*len(train) for _ in PROGRAMS]
    for pi,p in enumerate(PROGRAMS):
        for j,g in enumerate(ins):
            pred[pi][j]=run_program(p,to_list(g))

    rows=[]
    for hold in range(len(train)):
        retained=[j for j in range(len(train)) if j!=hold]
        cand=[pi for pi in range(len(PROGRAMS)) if all(pred[pi][j]==outs[j] for j in retained)]
        if len(cand)<3:continue

        rp=[ins[j] for j in retained]
        probes=mixed_probes(rp)
        d4p=d4_probes(rp)
        if not probes:continue

        # quotient by full primary-probe signature
        cls=defaultdict(list)
        for pi in cand:
            sg=tuple(run_program(PROGRAMS[pi],to_list(x)) for x in probes)
            cls[sg].append(pi)
        if len(cls)<3:continue

        reps={}
        for sg,members in cls.items():
            reps[sg]=min(members,key=lambda i:(PROGRAMS[i]["depth"],PROGRAMS[i]["string"]))

        held={pi:pred[pi][hold] for pi in reps.values()}
        distinct={g for g in held.values() if g is not None}
        if len(distinct)<2:continue

        truth=outs[hold]
        U=sum(g==truth for g in held.values())/len(held)
        Bgrid=plurality(list(held.values()));B=int(Bgrid==truth)

        sc=centralities(reps,probes)
        best=min(reps.values(),key=lambda i:(-sc[i],PROGRAMS[i]["depth"],PROGRAMS[i]["string"]))
        D=int(held[best]==truth)

        sc4=centralities(reps,d4p) if d4p else {i:0 for i in reps.values()}
        best4=min(reps.values(),key=lambda i:(-sc4[i],PROGRAMS[i]["depth"],PROGRAMS[i]["string"]))
        D4=int(held[best4]==truth)
        O=int(any(g==truth for g in held.values()))

        rows.append({"task_id":tid,"holdout":hold,"raw_candidates":len(cand),"semantic_classes":len(cls),
                     "distinct_heldout_outputs":len(distinct),"U":U,"B":B,"D":D,"D4":D4,"O":O,
                     "D_centrality":sc[best],"D_program":PROGRAMS[best]["string"],
                     "D4_centrality":sc4[best4],"D4_program":PROGRAMS[best4]["string"]})
    return rows

def main():
    root=Path(os.environ.get("QUICKSTART_ROOT","/tmp/arc-agi-quickstart"))
    data=json.loads((root/"data/arc-agi_training_challenges.json").read_text())
    tids=sorted(data)
    start=int(os.environ.get("TASK_START","0"));end=int(os.environ.get("TASK_END",str(len(tids))))
    rows=[]
    for idx,tid in enumerate(tids):
        if start<=idx<end:
            r=process_task(tid,data[tid]);rows.extend(r)
            if r:print("TASK",idx,tid,"usable_folds",len(r),flush=True)
    summary={"task_start":start,"task_end":end,"tasks_total":len(tids),"n_folds":len(rows),
             "n_tasks":len(set(r["task_id"] for r in rows)),"programs":len(PROGRAMS)}
    Path(os.environ.get("OUT_FILE","dsl_transfer_shard.json")).write_text(json.dumps({"summary":summary,"folds":rows},indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":main()
