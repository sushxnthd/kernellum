import argparse, hashlib, json, math, os, random, statistics, subprocess, sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np

SEED=20261028

def canon(g):
    if g is None:
        return None
    try:
        a=np.asarray(g,dtype=int)
        if a.ndim!=2 or a.size==0 or max(a.shape)>30:
            return None
        if np.any(a<0) or np.any(a>9):
            return None
        return (tuple(a.shape),tuple(map(int,a.ravel())))
    except Exception:
        return None

def grid_key(c):
    if c is None:
        return "~INVALID"
    return json.dumps([list(c[0]),list(c[1])],separators=(",",":"))

def arr(c):
    return np.asarray(c[1],dtype=int).reshape(c[0])

def unique_grids(xs):
    out=[];seen=set()
    for x in xs:
        c=canon(x)
        if c is not None and c not in seen:
            seen.add(c);out.append(arr(c))
    return out

def d4(g):
    a=np.asarray(g,dtype=int)
    xs=[]
    for k in range(4):
        r=np.rot90(a,k)
        xs.extend([r,np.fliplr(r)])
    return unique_grids(xs)

def probe_sets(task_id,test_index,demos):
    allp=[]
    seen=set()
    def add(x):
        c=canon(x)
        if c is not None and c not in seen:
            seen.add(c);allp.append(arr(c))
    for d in demos:
        a=np.asarray(d["input"],dtype=int)
        for x in d4(a):
            add(x)
        cols=sorted(set(map(int,a.ravel())))
        movable=[c for c in cols if c!=0]
        base_seed=int(hashlib.sha256(f"{SEED}:{task_id}:{test_index}:{grid_key(canon(a))}".encode()).hexdigest()[:16],16)
        rng=random.Random(base_seed)
        for _ in range(3):
            p=movable[:]
            rng.shuffle(p)
            mp={c:q for c,q in zip(movable,p)}
            mp[0]=0
            add(np.vectorize(lambda v:mp.get(int(v),int(v)))(a))
        for sh in (1,-1):
            add(np.roll(a,sh,axis=0))
            add(np.roll(a,sh,axis=1))
    shuffle_seed=int(hashlib.sha256(f"{SEED}:{task_id}:{test_index}".encode()).hexdigest()[:16],16)
    random.Random(shuffle_seed).shuffle(allp)
    primary=allp[:24]

    d4p=[]
    seen4=set()
    for d in demos:
        for x in d4(d["input"]):
            c=canon(x)
            if c is not None and c not in seen4:
                seen4.add(c);d4p.append(arr(c))
                if len(d4p)>=12:
                    return primary,d4p
    return primary,d4p[:12]

def run_candidate(worker,code,grids,timeout_s=75):
    payload=json.dumps({"code":code,"grids":[np.asarray(g,dtype=int).tolist() for g in grids]},separators=(",",":"))
    try:
        p=subprocess.run(
            [sys.executable,worker],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            env={**os.environ,"PER_GRID_SECONDS":"2.0","PYTHONUNBUFFERED":"1"},
        )
        if p.returncode!=0:
            return [None]*len(grids)
        d=json.loads(p.stdout)
        outs=d.get("outputs",[])
        if len(outs)!=len(grids):
            return [None]*len(grids)
        return [canon(x) for x in outs]
    except Exception:
        return [None]*len(grids)

def centralities(class_outputs,nprobes):
    ids=list(class_outputs)
    scores={}
    for cid in ids:
        row=class_outputs[cid]
        vals=[]
        for k in range(nprobes):
            y=row[k]
            valid=[class_outputs[j][k] for j in ids if class_outputs[j][k] is not None]
            if y is None or not valid:
                vals.append(0.0)
            else:
                vals.append(sum(v==y for v in valid)/len(valid))
        scores[cid]=statistics.mean(vals) if vals else 0.0
    return scores

def plurality(grids,k=2):
    cnt=Counter(g for g in grids if g is not None)
    return [g for g,_ in sorted(cnt.items(),key=lambda z:(-z[1],grid_key(z[0])))[:k]]

def weighted_vote(pred_by_class,weights,k=2):
    scores={}
    for cid,g in pred_by_class.items():
        if g is None:
            continue
        scores[g]=scores.get(g,0.0)+float(weights.get(cid,0.0))
    return [g for g,_ in sorted(scores.items(),key=lambda z:(-z[1],grid_key(z[0])))[:k]]

def top_distinct_classes(pred_by_class,weights,class_rep_key,k=2):
    ranked=sorted(pred_by_class,key=lambda cid:(-weights.get(cid,0.0),class_rep_key[cid]))
    out=[]
    for cid in ranked:
        g=pred_by_class[cid]
        if g is not None and g not in out:
            out.append(g)
            if len(out)>=k:
                break
    return out

def rankdata(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i])
    ranks=[0.0]*len(xs)
    i=0
    while i<len(order):
        j=i+1
        while j<len(order) and xs[order[j]]==xs[order[i]]:
            j+=1
        r=(i+j-1)/2+1
        for t in range(i,j):
            ranks[order[t]]=r
        i=j
    return ranks

def pearson(x,y):
    if len(x)<2:
        return None
    mx=statistics.mean(x);my=statistics.mean(y)
    dx=[a-mx for a in x];dy=[b-my for b in y]
    den=math.sqrt(sum(a*a for a in dx)*sum(b*b for b in dy))
    return sum(a*b for a,b in zip(dx,dy))/den if den else None

def spearman(x,y):
    return pearson(rankdata(x),rankdata(y)) if len(x)>=2 else None

def auc(scores,labels):
    pos=[s for s,l in zip(scores,labels) if l==1]
    neg=[s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg:
        return None
    wins=0.0
    for p in pos:
        for n in neg:
            wins+=1 if p>n else (0.5 if p==n else 0)
    return wins/(len(pos)*len(neg))

def process_case(task_id,test_index,cands,task,worker,max_workers):
    idx=test_index-1
    demos=task.get("train",[])
    tests=task.get("test",[])
    if idx<0 or idx>=len(tests) or "output" not in tests[idx]:
        return {"task_id":task_id,"test_index":test_index,"status":"NO_TRUTH"}
    train_inputs=[np.asarray(d["input"],dtype=int) for d in demos]
    train_truth=[canon(d["output"]) for d in demos]
    test_input=np.asarray(tests[idx]["input"],dtype=int)
    truth=canon(tests[idx]["output"])
    primary,d4p=probe_sets(task_id,test_index,demos)

    # Execute candidates in parallel. One worker process handles every grid with a per-grid signal timeout.
    grids=train_inputs+primary+d4p+[test_input]
    ntrain=len(train_inputs);np1=len(primary);nd4=len(d4p)
    results={}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs={ex.submit(run_candidate,worker,c["code"],grids):c for c in cands}
        for fut in as_completed(futs):
            c=futs[fut]
            outs=fut.result()
            train_out=outs[:ntrain]
            verified=all(a==b for a,b in zip(train_out,train_truth))
            if not verified:
                continue
            p1=outs[ntrain:ntrain+np1]
            p4=outs[ntrain+np1:ntrain+np1+nd4]
            test_pred=outs[-1]
            results[c["code_sha256"]]={
                "candidate":c,
                "primary":p1,
                "d4":p4,
                "test":test_pred,
            }

    if len(results)<3:
        return {"task_id":task_id,"test_index":test_index,"status":"TOO_FEW_VERIFIED","verified_candidates":len(results)}

    # Semantic classes defined only by primary probe signature.
    sig_groups=defaultdict(list)
    for sha,r in results.items():
        sig=tuple(r["primary"])
        sig_groups[sig].append(sha)
    if len(sig_groups)<3:
        return {"task_id":task_id,"test_index":test_index,"status":"TOO_FEW_CLASSES",
                "verified_candidates":len(results),"semantic_classes":len(sig_groups)}

    class_map={}
    rep_key={}
    for cid,(sig,members) in enumerate(sorted(sig_groups.items(),key=lambda kv:repr(kv[0]))):
        rep=min(members,key=lambda sha:(results[sha]["candidate"]["normalized_source_chars"],sha))
        class_map[cid]={"members":members,"rep":rep,"signature":sig}
        rep_key[cid]=(results[rep]["candidate"]["normalized_source_chars"],rep)

    pred_by_class={cid:results[v["rep"]]["test"] for cid,v in class_map.items()}
    distinct=set(g for g in pred_by_class.values() if g is not None)
    if len(distinct)<2:
        return {"task_id":task_id,"test_index":test_index,"status":"NO_QUERY_DISAGREEMENT",
                "verified_candidates":len(results),"semantic_classes":len(class_map),
                "distinct_test_outputs":len(distinct)}

    primary_outputs={cid:results[v["rep"]]["primary"] for cid,v in class_map.items()}
    d4_outputs={cid:results[v["rep"]]["d4"] for cid,v in class_map.items()}
    cent=centralities(primary_outputs,np1)
    cent4=centralities(d4_outputs,nd4)

    B=plurality(list(pred_by_class.values()),2)
    D=top_distinct_classes(pred_by_class,cent,rep_key,2)
    W=weighted_vote(pred_by_class,cent,2)
    D4=top_distinct_classes(pred_by_class,cent4,rep_key,2)
    W4=weighted_vote(pred_by_class,cent4,2)
    raw=plurality([r["test"] for r in results.values()],2)

    support=Counter(g for g in pred_by_class.values() if g is not None)
    valid_cls=sum(support.values())
    correct_support=support.get(truth,0)
    minority_correct=(correct_support>0 and valid_cls>0 and correct_support/valid_cls<0.5)
    oracle=correct_support>0

    class_rows=[]
    for cid,v in class_map.items():
        g=pred_by_class[cid]
        class_rows.append({
            "class_id":cid,
            "members":len(v["members"]),
            "centrality":cent[cid],
            "d4_centrality":cent4[cid],
            "test_correct":int(g==truth),
            "test_valid":g is not None,
            "test_prediction":grid_key(g),
            "rep_sha":v["rep"],
        })

    scores=[x["centrality"] for x in class_rows if x["test_valid"]]
    labels=[x["test_correct"] for x in class_rows if x["test_valid"]]
    assoc=spearman(scores,labels) if len(set(labels))>1 else None
    ca=auc(scores,labels)

    def h1(sel):
        return int(bool(sel) and sel[0]==truth)
    def h2(sel):
        return int(truth in sel[:2])

    return {
        "task_id":task_id,
        "test_index":test_index,
        "status":"USABLE",
        "raw_candidates":len(cands),
        "verified_candidates":len(results),
        "semantic_classes":len(class_map),
        "distinct_test_outputs":len(distinct),
        "oracle":int(oracle),
        "minority_correct":bool(minority_correct),
        "correct_class_support":correct_support,
        "valid_class_predictions":valid_cls,
        "acc":{"B":h1(B),"D":h1(D),"W":h1(W),"D4":h1(D4),"W4":h1(W4),"raw":h1(raw)},
        "pass2":{"B":h2(B),"D":h2(D),"W":h2(W),"D4":h2(D4),"W4":h2(W4),"raw":h2(raw)},
        "centrality_correctness_spearman":assoc,
        "centrality_auc":ca,
        "classes":class_rows,
    }

def bootstrap_task_delta(rows,a="D",b="B",B=5000):
    by=defaultdict(list)
    for r in rows:
        by[r["task_id"]].append(r["acc"][a]-r["acc"][b])
    vals=[statistics.mean(v) for v in by.values()]
    if not vals:
        return None
    rng=random.Random(SEED)
    out=[]
    for _ in range(B):
        out.append(statistics.mean(vals[rng.randrange(len(vals))] for _ in range(len(vals))))
    out.sort()
    return [out[int(.025*B)],out[min(B-1,int(.975*B))]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--data",required=True)
    ap.add_argument("--worker",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--max-workers",type=int,default=6)
    args=ap.parse_args()

    groups=defaultdict(list)
    with open(args.candidates) as f:
        for line in f:
            if not line.strip():
                continue
            c=json.loads(line)
            groups[(c["task_id"],int(c["test_index"]))].append(c)

    data_root=Path(args.data)
    rows=[]
    for ci,(task_id,test_index) in enumerate(sorted(groups)):
        p=data_root/(task_id+".json")
        if not p.exists():
            rows.append({"task_id":task_id,"test_index":test_index,"status":"MISSING_TASK"})
            continue
        task=json.loads(p.read_text())
        r=process_case(task_id,test_index,groups[(task_id,test_index)],task,args.worker,args.max_workers)
        rows.append(r)
        print("CASE_RESULT="+json.dumps({k:r.get(k) for k in ["task_id","test_index","status","verified_candidates","semantic_classes","distinct_test_outputs","oracle","minority_correct","acc"]},sort_keys=True),flush=True)

    usable=[r for r in rows if r.get("status")=="USABLE"]
    tasks=set(r["task_id"] for r in usable)
    def macc(k,subset=usable):
        return statistics.mean(r["acc"][k] for r in subset) if subset else None
    def mp2(k,subset=usable):
        return statistics.mean(r["pass2"][k] for r in subset) if subset else None
    d=macc("D");b=macc("B")
    gain=d-b if d is not None else None
    ci=bootstrap_task_delta(usable)
    bydir=defaultdict(list)
    for r in usable:
        bydir[r["task_id"]].append(r["acc"]["D"]-r["acc"]["B"])
    task_delta={t:statistics.mean(v) for t,v in bydir.items()}
    dirs={"positive":sum(v>0 for v in task_delta.values()),"negative":sum(v<0 for v in task_delta.values()),"zero":sum(v==0 for v in task_delta.values())}
    op=[r for r in usable if r["oracle"]==1]
    minority=[r for r in usable if r["minority_correct"]]
    op_gain=(macc("D",op)-macc("B",op)) if op else None
    min_gain=(macc("D",minority)-macc("B",minority)) if minority else None
    assoc=[r["centrality_correctness_spearman"] for r in usable if r.get("centrality_correctness_spearman") is not None]
    aucs=[r["centrality_auc"] for r in usable if r.get("centrality_auc") is not None]

    survival={
        "usable_cases_ge30":len(usable)>=30,
        "distinct_tasks_ge20":len(tasks)>=20,
        "D_minus_B_ge3pp":gain is not None and gain>=0.03,
        "bootstrap_ci_not_entirely_below_zero":ci is not None and ci[1]>=0,
        "D_improves_ge5_tasks":dirs["positive"]>=5,
        "D_noninferior_oracle_positive":op_gain is not None and op_gain>=0,
        "D_positive_minority_correct_gain":min_gain is not None and min_gain>0,
    }
    coverage=survival["usable_cases_ge30"] and survival["distinct_tasks_ge20"]
    survival["primary_passes"]=all(survival.values())
    summary={
        "cases_total":len(rows),
        "usable_cases":len(usable),
        "distinct_tasks":len(tasks),
        "oracle_positive_cases":len(op),
        "minority_correct_cases":len(minority),
        "top1":{k:macc(k) for k in ["B","D","W","D4","W4","raw"]},
        "pass2":{k:mp2(k) for k in ["B","D","W","D4","W4","raw"]},
        "D_minus_B":gain,
        "D_minus_B_task_bootstrap95":ci,
        "task_direction":dirs,
        "oracle_positive_D_minus_B":op_gain,
        "minority_correct_D_minus_B":min_gain,
        "mean_case_spearman_centrality_correctness":statistics.mean(assoc) if assoc else None,
        "mean_case_centrality_auc":statistics.mean(aucs) if aucs else None,
        "survival":survival,
        "verdict":"PASS" if survival["primary_passes"] else ("INCONCLUSIVE_COVERAGE" if not coverage else "PRIMARY_FAIL"),
    }
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))
    Path(args.out).write_text(json.dumps({"summary":summary,"cases":rows},indent=2))

if __name__=="__main__":
    main()
