import ast, json, math, os, random, signal, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import identifiability_kill_test_train_shard as core

SEED=core.SEED
CALL_TIMEOUT=float(os.environ.get("CALL_TIMEOUT_S","2.0"))
N_QUERIES=int(os.environ.get("N_QUERIES","32"))

class CallTimeout(Exception):
    pass

def _handler(signum, frame):
    raise CallTimeout()

def safe_run(fn,obj,x,tv):
    old=signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM,_handler)
        signal.setitimer(signal.ITIMER_REAL,CALL_TIMEOUT)
        try:
            y=fn(obj,core.arr(x).copy(),tv)
            a=core.arr(y)
            if a.ndim!=2 or a.size==0 or max(a.shape)>60:
                return None
            return a
        except Exception:
            return None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old)

core.safe_run=safe_run

def canon(a):
    if a is None:return None
    a=core.arr(a)
    return (tuple(a.shape),tuple(map(int,a.ravel())))

def canon_key(c):
    return json.dumps(c,separators=(",",":"),sort_keys=False)

def probe_signature(fn,obj,tv,probes):
    return tuple(canon(safe_run(fn,obj,x,tv)) for x in probes)

def class_centralities(classes, reps, obj, tv, probes):
    outs={}
    for cid,ri in reps.items():
        outs[cid]=[safe_run(classes[cid]["members"][ri]["fn"],obj,x,tv) for x in probes]
    scores={}
    for cid,row in outs.items():
        vals=[]
        for p,y in enumerate(row):
            if y is None:continue
            valid=[canon(outs[k][p]) for k in outs if outs[k][p] is not None]
            if not valid:continue
            cy=canon(y)
            vals.append(sum(v==cy for v in valid)/len(valid))
        scores[cid]=statistics.mean(vals) if vals else 0.0
    return scores

def top_grids_from_scores(score_by_grid,k=2):
    return [g for g,_ in sorted(score_by_grid.items(),key=lambda z:(-z[1],canon_key(z[0])))[:k]]

def plurality(grids,k=2):
    cnt=Counter(g for g in grids if g is not None)
    return [g for g,_ in sorted(cnt.items(),key=lambda z:(-z[1],canon_key(z[0])))[:k]]

def bootstrap_family_delta(family_rows,B=5000):
    vals=[r["acc"]["D"]-r["acc"]["B"] for r in family_rows]
    if not vals:return None
    rng=random.Random(20261028)
    n=len(vals); out=[]
    for _ in range(B):
        s=[vals[rng.randrange(n)] for _ in range(n)]
        out.append(statistics.mean(s))
    out.sort()
    return [out[int(.025*B)],out[min(B-1,int(.975*B))]]

def build_family(fi,name,mod,cls):
    random.seed(SEED+fi*1000); np.random.seed((SEED+fi*1000)%(2**32-1))
    gen=cls()
    try: tv,data=gen.create_grids()
    except Exception as e:
        return {"family":name,"index":fi,"status":"CREATE_FAIL","error":repr(e)}
    demos=data["train"]; original=cls.transform_input

    accepted=[]
    for mi,(mspec,tree) in enumerate(core.mutations(original,500)):
        try: fn=core.compile_method(tree,mod.__dict__)
        except Exception:continue
        ok=True
        for d in demos:
            y=safe_run(fn,gen,d["input"],tv)
            if y is None or not core.exact(y,d["output"]):
                ok=False;break
        if ok:
            accepted.append({"fn":fn,"spec":str(mspec),"mutation_index":mi,
                             "ast_size":sum(1 for _ in ast.walk(tree))})
        if len(accepted)>=80:break

    # Same Stage B seed-probe semantic deduplication.
    valid_inputs=core.fresh_inputs(gen,tv,40)
    unique=[]; seen=set()
    for m in accepted:
        bs=tuple(canon(safe_run(m["fn"],gen,x,tv)) for x in valid_inputs[:8])
        if bs not in seen:
            seen.add(bs); unique.append(m)
    accepted=unique
    if len(accepted)<3:
        return {"family":name,"index":fi,"status":"TOO_FEW","n_mutants":len(accepted)}

    probes=core.agnostic_probes(demos,24)

    # Stage C semantic classes use only the frozen agnostic probes.
    classes={}
    for m in accepted:
        sig=probe_signature(m["fn"],gen,tv,probes)
        classes.setdefault(sig,{"members":[]})["members"].append(m)
    class_ids=list(range(len(classes)))
    class_map={cid:v for cid,v in zip(class_ids,classes.values())}
    reps={}
    for cid,v in class_map.items():
        reps[cid]=min(range(len(v["members"])),
                      key=lambda i:(v["members"][i]["ast_size"],v["members"][i]["mutation_index"]))
    central=class_centralities(class_map,reps,gen,tv,probes)

    # Fixed global simplicity program, chosen before any query.
    simplest=min(accepted,key=lambda m:(m["ast_size"],m["mutation_index"]))

    # Exactly N_QUERIES valid ground-truth queries.
    queries=[]
    attempts=0
    while len(queries)<N_QUERIES and attempts<512:
        attempts+=1
        try:x=core.arr(gen.create_input(tv,{})).copy()
        except Exception:continue
        y=safe_run(original,gen,x,tv)
        if y is not None:queries.append((x,y))
    if len(queries)<N_QUERIES:
        return {"family":name,"index":fi,"status":"QUERY_FAIL","n_queries":len(queries),
                "n_mutants":len(accepted),"n_classes":len(class_map)}

    counts=Counter()
    disagreement_n=0
    disagreement_D=0; disagreement_B=0
    details=[]
    for qi,(x,truth_arr) in enumerate(queries):
        truth=canon(truth_arr)
        cand_preds=[]
        pred_by_mut={}
        for m in accepted:
            g=canon(safe_run(m["fn"],gen,x,tv))
            pred_by_mut[m["mutation_index"]]=g
            cand_preds.append(g)

        # A: raw query plurality.
        A=plurality(cand_preds,2)

        # Canonical representative prediction per semantic class.
        rep_pred={}
        for cid,v in class_map.items():
            m=v["members"][reps[cid]]
            rep_pred[cid]=pred_by_mut.get(m["mutation_index"])

        # B: one vote per class.
        B=plurality(list(rep_pred.values()),2)

        # C: globally simplest candidate.
        C=[pred_by_mut.get(simplest["mutation_index"])]

        # D: per-grid maximum class centrality.
        dscore={}
        for cid,g in rep_pred.items():
            if g is None:continue
            dscore[g]=max(dscore.get(g,-1.0),central[cid])
        D=top_grids_from_scores(dscore,2)

        # E: lexicographic centrality, simplicity, mutation index, gathering distinct grids.
        ranked=[]
        for cid,v in class_map.items():
            m=v["members"][reps[cid]]
            g=rep_pred[cid]
            ranked.append((-central[cid],m["ast_size"],m["mutation_index"],g))
        ranked.sort(key=lambda z:(z[0],z[1],z[2]))
        E=[]
        for _,_,_,g in ranked:
            if g is not None and g not in E:E.append(g)
            if len(E)>=2:break

        all_valid=set(g for g in cand_preds if g is not None)
        F=int(truth in all_valid)

        def h1(sel): return int(bool(sel) and sel[0]==truth)
        def h2(sel): return int(truth in sel[:2])
        for label,sel in [("A",A),("B",B),("C",C),("D",D),("E",E)]:
            counts[f"{label}1"]+=h1(sel)
            counts[f"{label}2"]+=h2(sel)
        counts["F"]+=F

        distinct=len(all_valid)
        if distinct>=2:
            disagreement_n+=1
            disagreement_D+=h1(D); disagreement_B+=h1(B)

        details.append({"query":qi,"distinct_outputs":distinct,
                        "A1":h1(A),"B1":h1(B),"C1":h1(C),"D1":h1(D),"E1":h1(E),
                        "A2":h2(A),"B2":h2(B),"D2":h2(D),"E2":h2(E),"oracle_any":F})

    n=len(queries)
    acc={k:counts[f"{k}1"]/n for k in "ABCDE"}
    pass2={k:counts[f"{k}2"]/n for k in "ABDE"}
    return {"family":name,"index":fi,"status":"USABLE",
            "n_mutants":len(accepted),"n_classes":len(class_map),"n_queries":n,
            "acc":acc,"pass2":pass2,"oracle_any":counts["F"]/n,
            "disagreement_n":disagreement_n,
            "disagreement_acc_D":disagreement_D/disagreement_n if disagreement_n else None,
            "disagreement_acc_B":disagreement_B/disagreement_n if disagreement_n else None,
            "details":details}

def main():
    root=Path(os.environ.get("ARC_TGI_ROOT","/tmp/ARC-TGI")); sys.path.insert(0,str(root))
    gens=core.load_generators(root)
    start=int(os.environ.get("SHARD_START","0")); end=int(os.environ.get("SHARD_END",str(len(gens))))
    rows=[]
    for fi,(name,mod,cls) in enumerate(gens):
        if start<=fi<end:
            row=build_family(fi,name,mod,cls); rows.append(row)
            print("FAMILY_RESULT",json.dumps({k:row.get(k) for k in ["family","index","status","n_mutants","n_classes","n_queries","acc"]},sort_keys=True),flush=True)
    usable=[r for r in rows if r.get("status")=="USABLE"]
    summary={"split":"ARC-TGI-Train-StageC-shard","start":start,"end":end,
             "n_families":len(rows),"usable_families":len(usable),
             "call_timeout_s":CALL_TIMEOUT,"n_queries_per_usable_family":N_QUERIES}
    out={"summary":summary,"families":rows}
    path=Path(os.environ.get("OUT_FILE","stage_c_query_identifiability_shard.json"))
    path.write_text(json.dumps(out,indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":main()
