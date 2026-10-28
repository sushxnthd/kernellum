#!/usr/bin/env python3
import json, math, os, random, statistics, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

SEED=20261028

def canon(g):
    try:
        if not isinstance(g,(list,tuple)) or not g:return None
        rows=[]
        w=None
        for r in g:
            if not isinstance(r,(list,tuple)) or not r:return None
            rr=tuple(int(x) for x in r)
            if w is None:w=len(rr)
            if len(rr)!=w:return None
            if any(x<0 or x>9 for x in rr):return None
            rows.append(rr)
        if not rows or not rows[0] or len(rows)>30 or len(rows[0])>30:return None
        return tuple(rows)
    except Exception:return None

def tolist(c): return [list(r) for r in c]
def sigstr(c): return json.dumps(c,separators=(",",":")) if c is not None else "~INVALID"

def rot90(c):
    return tuple(tuple(row) for row in zip(*c[::-1]))
def fliplr(c):
    return tuple(tuple(reversed(r)) for r in c)
def d4(c):
    out=[];x=c
    for _ in range(4):
        out.extend([x,fliplr(x)]);x=rot90(x)
    return unique(out)

def roll(c,sh,axis):
    h,w=len(c),len(c[0])
    if axis==0:
        s=sh%h
        return c[-s:]+c[:-s] if s else c
    s=sh%w
    if not s:return c
    return tuple(tuple(list(r[-s:])+list(r[:-s])) for r in c)

def unique(xs,limit=None):
    out=[];seen=set()
    for x in xs:
        c=canon(x)
        if c is not None and c not in seen:
            seen.add(c);out.append(c)
            if limit and len(out)>=limit:break
    return out

def mixed_probes(train_inputs):
    rng=random.Random(SEED)
    out=[];seen=set()
    def add(x):
        c=canon(x)
        if c is not None and c not in seen:
            seen.add(c);out.append(c)
    for c in train_inputs:
        for x in d4(c):add(x)
        cols=sorted({v for r in c for v in r});mov=[v for v in cols if v!=0]
        for _ in range(3):
            p=mov[:];rng.shuffle(p);mp={a:b for a,b in zip(mov,p)};mp[0]=0
            add(tuple(tuple(mp.get(v,v) for v in r) for r in c))
        for sh in (1,-1):
            add(roll(c,sh,0));add(roll(c,sh,1))
    rng.shuffle(out)
    return out[:24]

def d4_probes(train_inputs):
    xs=[]
    for c in train_inputs:xs.extend(d4(c))
    return unique(xs,12)

def centrality(rep_ids,outputs_by_id,probe_indices):
    scores={}
    for sid in rep_ids:
        vals=[]
        for idx in probe_indices:
            y=canon(outputs_by_id[sid][idx]) if idx < len(outputs_by_id[sid]) else None
            if y is None:continue
            valid=[]
            for q in rep_ids:
                o=canon(outputs_by_id[q][idx]) if idx < len(outputs_by_id[q]) else None
                if o is not None:valid.append(o)
            if valid:vals.append(sum(v==y for v in valid)/len(valid))
        scores[sid]=statistics.mean(vals) if vals else 0.0
    return scores

def plurality(grids,k=2):
    cnt=Counter(g for g in grids if g is not None)
    return [g for g,_ in sorted(cnt.items(),key=lambda z:(-z[1],sigstr(z[0])))[:k]]

def weighted_vote(rep_test,weights,k=2):
    scores={}
    for sid,g in rep_test.items():
        if g is None:continue
        scores[g]=scores.get(g,0.0)+float(weights.get(sid,0.0))
    return [g for g,_ in sorted(scores.items(),key=lambda z:(-z[1],sigstr(z[0])))[:k]]

def top_classes(rep_ids,scores,meta,k=2):
    ordered=sorted(rep_ids,key=lambda s:(-scores.get(s,0.0),meta[s]["source_chars"],s))
    return ordered[:k]

def auc_binary(scores,labels):
    pos=[s for s,l in zip(scores,labels) if l==1]
    neg=[s for s,l in zip(scores,labels) if l==0]
    if not pos or not neg:return None
    tot=0.0
    for a in pos:
        for b in neg:
            tot += 1.0 if a>b else (0.5 if a==b else 0.0)
    return tot/(len(pos)*len(neg))

def run_container(bundle,image):
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        inp=td/"bundle.json";outdir=td/"out";outdir.mkdir()
        inp.write_text(json.dumps(bundle))
        cmd=[
            "docker","run","--rm",
            "--network","none","--read-only","--cap-drop","ALL",
            "--security-opt","no-new-privileges",
            "--memory","768m","--cpus","1.0","--pids-limit","96",
            "--tmpfs","/tmp:rw,noexec,nosuid,size=64m",
            "-v",f"{inp}:/input/bundle.json:ro",
            "-v",f"{outdir}:/output:rw",
            image,"/input/bundle.json","/output/results.json"
        ]
        try:
            cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=180)
        except subprocess.TimeoutExpired:
            return None,"container_timeout"
        p=outdir/"results.json"
        if cp.returncode!=0 or not p.exists():
            return None,f"container_fail:{cp.returncode}:{cp.stderr[-500:]}"
        try:return json.loads(p.read_text()),"ok"
        except Exception as e:return None,f"json:{e}"

def eval_case(case,recs,eval_dir,image):
    task_id,idxs=case.split(":");test_i=int(idxs)-1
    tp=Path(eval_dir)/f"{task_id}.json"
    if not tp.exists():return {"case":case,"status":"MISSING_TASK"}
    task=json.loads(tp.read_text())
    if test_i<0 or test_i>=len(task.get("test",[])):return {"case":case,"status":"BAD_TEST_INDEX"}
    train_inputs=[canon(p["input"]) for p in task["train"]]
    train_truth=[canon(p["output"]) for p in task["train"]]
    test_input=canon(task["test"][test_i]["input"])
    test_truth=canon(task["test"][test_i].get("output"))
    if any(x is None for x in train_inputs+train_truth+[test_input,test_truth]):
        return {"case":case,"status":"BAD_TASK_GRID"}

    probes=mixed_probes(train_inputs)
    p4=d4_probes(train_inputs)
    # Ensure D4 probes are separately evaluated even when not in mixed set.
    extra4=[x for x in p4 if x not in probes]
    all_grids=train_inputs+probes+extra4+[test_input]
    ntr=len(train_inputs);pmix=list(range(ntr,ntr+len(probes)))
    p4idx=[]
    for x in p4:
        if x in probes:p4idx.append(ntr+probes.index(x))
        else:p4idx.append(ntr+len(probes)+extra4.index(x))
    test_idx=len(all_grids)-1

    bundle={"grids":[tolist(x) for x in all_grids],
            "candidates":[{"source_id":r["source_id"],"code":r["code"]} for r in recs]}
    raw,status=run_container(bundle,image)
    if raw is None:return {"case":case,"status":"EXEC_INFRA_FAIL","error":status}

    meta={r["source_id"]:r for r in recs}
    verified={}
    exec_status={}
    for sid,res in raw.items():
        exec_status[sid]=res.get("status")
        outs=res.get("outputs",[])
        if res.get("status")!="ok" or len(outs)!=len(all_grids):continue
        ok=True
        for j,y in enumerate(train_truth):
            if canon(outs[j])!=y:ok=False;break
        if ok:verified[sid]=outs

    if len(verified)<3:
        return {"case":case,"status":"TOO_FEW_VERIFIED","raw_candidates":len(recs),
                "verified_candidates":len(verified),"exec_status_counts":dict(Counter(exec_status.values()))}

    # Semantic classes by complete mixed-probe signature.
    classes={}
    for sid,outs in verified.items():
        sg=tuple(canon(outs[i]) for i in pmix)
        classes.setdefault(sg,[]).append(sid)
    if len(classes)<3:
        return {"case":case,"status":"TOO_FEW_CLASSES","raw_candidates":len(recs),
                "verified_candidates":len(verified),"semantic_classes":len(classes)}

    reps={}
    for sg,members in classes.items():
        reps[sg]=min(members,key=lambda s:(meta[s]["source_chars"],s))
    rep_ids=list(reps.values())
    rep_test={sid:canon(verified[sid][test_idx]) for sid in rep_ids}
    distinct={g for g in rep_test.values() if g is not None}
    if len(distinct)<2:
        return {"case":case,"status":"TOO_FEW_TEST_OUTPUTS","raw_candidates":len(recs),
                "verified_candidates":len(verified),"semantic_classes":len(classes),
                "distinct_test_outputs":len(distinct)}

    c_all=centrality(rep_ids,verified,pmix)
    c_d4=centrality(rep_ids,verified,p4idx)

    B=plurality(list(rep_test.values()),2)
    Dids=top_classes(rep_ids,c_all,meta,10)
    D=[]
    for sid in Dids:
        g=rep_test[sid]
        if g is not None and g not in D:D.append(g)
        if len(D)>=2:break
    W=weighted_vote(rep_test,c_all,2)

    D4ids=top_classes(rep_ids,c_d4,meta,10)
    D4=[]
    for sid in D4ids:
        g=rep_test[sid]
        if g is not None and g not in D4:D4.append(g)
        if len(D4)>=2:break
    W4=weighted_vote(rep_test,c_d4,2)

    raw_test={sid:canon(outs[test_idx]) for sid,outs in verified.items()}
    Raw=plurality(list(raw_test.values()),2)

    def hit(sel,k=1):return int(test_truth in sel[:k])
    class_correct={sid:int(rep_test[sid]==test_truth) for sid in rep_ids}
    central_scores=[c_all[sid] for sid in rep_ids]
    labels=[class_correct[sid] for sid in rep_ids]
    auc=auc_binary(central_scores,labels)
    correct_support=sum(labels)/len(labels)
    oracle=int(any(labels))

    released_correct=[meta[s].get("released_is_correct") for s in verified]
    released_agree=None
    known=[x for x in released_correct if isinstance(x,bool)]
    if known:
        independently=[int(canon(verified[s][test_idx])==test_truth) for s in verified if isinstance(meta[s].get("released_is_correct"),bool)]
        released=[int(meta[s]["released_is_correct"]) for s in verified if isinstance(meta[s].get("released_is_correct"),bool)]
        released_agree=sum(a==b for a,b in zip(independently,released))/len(released)

    return {
      "case":case,"task_id":task_id,"status":"USABLE",
      "raw_candidates":len(recs),"verified_candidates":len(verified),
      "semantic_classes":len(classes),"distinct_test_outputs":len(distinct),
      "oracle":oracle,"correct_class_support":correct_support,
      "minority_correct":int(oracle and correct_support<0.5),
      "top1":{"B":hit(B),"D":hit(D),"W":hit(W),"D4":hit(D4),"W4":hit(W4),"Raw":hit(Raw)},
      "pass2":{"B":hit(B,2),"D":hit(D,2),"W":hit(W,2),"D4":hit(D4,2),"W4":hit(W4,2),"Raw":hit(Raw,2)},
      "mechanism":{"auc":auc,
                   "centrality_correct_mean":statistics.mean([c_all[s] for s in rep_ids if class_correct[s]]) if any(labels) else None,
                   "centrality_incorrect_mean":statistics.mean([c_all[s] for s in rep_ids if not class_correct[s]]) if not all(labels) else None},
      "released_correctness_agreement":released_agree
    }

def main():
    safe=json.load(open(sys.argv[1]))
    cases=safe.get("cases",safe)
    eval_dir=sys.argv[2]
    image=os.environ.get("LAND_RUNTIME_IMAGE","land-v7-runtime:latest")
    shard=int(os.environ.get("SHARD_ID","0"));nsh=int(os.environ.get("N_SHARDS","1"))
    keys=sorted(cases)
    chosen=[k for i,k in enumerate(keys) if i%nsh==shard]
    rows=[]
    for n,k in enumerate(chosen,1):
        row=eval_case(k,cases[k],eval_dir,image);rows.append(row)
        print("CASE_RESULT",n,k,json.dumps({x:row.get(x) for x in ["status","verified_candidates","semantic_classes","distinct_test_outputs","top1","oracle","minority_correct"]},sort_keys=True),flush=True)
    out={"summary":{"shard":shard,"n_shards":nsh,"cases":len(chosen),
                    "usable":sum(r["status"]=="USABLE" for r in rows)},"rows":rows}
    Path(sys.argv[3]).write_text(json.dumps(out,indent=2))
    print("FINAL_SUMMARY="+json.dumps(out["summary"],sort_keys=True),flush=True)

if __name__=="__main__":
    main()
