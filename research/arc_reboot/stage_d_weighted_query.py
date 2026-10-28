import ast, json, os, random, statistics, sys
from collections import Counter
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).parent))
import stage_c_query_identifiability as sc

SEED=sc.SEED
N_QUERIES=sc.N_QUERIES

def dedup_grids(xs,limit=None):
    out=[]; seen=set()
    for x in xs:
        z=sc.canon(x)
        if z not in seen:
            seen.add(z); out.append(sc.core.arr(x).copy())
            if limit and len(out)>=limit: break
    return out

def d4_probes(demos):
    xs=[]
    for d in demos: xs.extend(sc.core.d4s(d["input"]))
    return dedup_grids(xs,12)

def weighted_top(rep_pred,weights,k=2):
    scores={}
    for cid,g in rep_pred.items():
        if g is None: continue
        scores[g]=scores.get(g,0.0)+float(weights.get(cid,0.0))
    return sc.top_grids_from_scores(scores,k)

def build_family(fi,name,mod,cls):
    random.seed(SEED+fi*1000); np.random.seed((SEED+fi*1000)%(2**32-1))
    gen=cls()
    try: tv,data=gen.create_grids()
    except Exception as e:
        return {"family":name,"index":fi,"status":"CREATE_FAIL","error":repr(e)}
    demos=data["train"]; original=cls.transform_input

    accepted=[]
    for mi,(mspec,tree) in enumerate(sc.core.mutations(original,500)):
        try: fn=sc.core.compile_method(tree,mod.__dict__)
        except Exception: continue
        ok=True
        for d in demos:
            y=sc.safe_run(fn,gen,d["input"],tv)
            if y is None or not sc.core.exact(y,d["output"]):
                ok=False; break
        if ok:
            accepted.append({"fn":fn,"spec":str(mspec),"mutation_index":mi,
                             "ast_size":sum(1 for _ in ast.walk(tree))})
        if len(accepted)>=80: break

    valid_inputs=sc.core.fresh_inputs(gen,tv,40)
    unique=[]; seen=set()
    for m in accepted:
        bs=tuple(sc.canon(sc.safe_run(m["fn"],gen,x,tv)) for x in valid_inputs[:8])
        if bs not in seen:
            seen.add(bs); unique.append(m)
    accepted=unique
    if len(accepted)<3:
        return {"family":name,"index":fi,"status":"TOO_FEW","n_mutants":len(accepted)}

    probes_all=sc.core.agnostic_probes(demos,24)
    classes={}
    for m in accepted:
        sig=sc.probe_signature(m["fn"],gen,tv,probes_all)
        classes.setdefault(sig,{"members":[]})["members"].append(m)
    class_map={cid:v for cid,v in enumerate(classes.values())}
    reps={}
    for cid,v in class_map.items():
        reps[cid]=min(range(len(v["members"])),
                      key=lambda i:(v["members"][i]["ast_size"],v["members"][i]["mutation_index"]))
    central_all=sc.class_centralities(class_map,reps,gen,tv,probes_all)
    central_d4=sc.class_centralities(class_map,reps,gen,tv,d4_probes(demos))

    simplest=min(accepted,key=lambda m:(m["ast_size"],m["mutation_index"]))

    queries=[]; attempts=0
    while len(queries)<N_QUERIES and attempts<512:
        attempts+=1
        try: x=sc.core.arr(gen.create_input(tv,{})).copy()
        except Exception: continue
        y=sc.safe_run(original,gen,x,tv)
        if y is not None: queries.append((x,y))
    if len(queries)<N_QUERIES:
        return {"family":name,"index":fi,"status":"QUERY_FAIL","n_queries":len(queries),
                "n_mutants":len(accepted),"n_classes":len(class_map)}

    counts=Counter()
    dis_n=0; dis_B=dis_W=dis_Wd4=0
    details=[]
    for qi,(x,truth_arr) in enumerate(queries):
        truth=sc.canon(truth_arr)
        pred_by_mut={}
        cand_preds=[]
        for m in accepted:
            g=sc.canon(sc.safe_run(m["fn"],gen,x,tv))
            pred_by_mut[m["mutation_index"]]=g; cand_preds.append(g)

        rep_pred={}
        for cid,v in class_map.items():
            m=v["members"][reps[cid]]
            rep_pred[cid]=pred_by_mut.get(m["mutation_index"])

        B=sc.plurality(list(rep_pred.values()),2)
        W=weighted_top(rep_pred,central_all,2)
        Wd4=weighted_top(rep_pred,central_d4,2)

        dscore={}
        for cid,g in rep_pred.items():
            if g is None: continue
            dscore[g]=max(dscore.get(g,-1.0),central_all[cid])
        D=sc.top_grids_from_scores(dscore,2)

        ranked=[]
        for cid,v in class_map.items():
            m=v["members"][reps[cid]]
            ranked.append((-central_all[cid],m["ast_size"],m["mutation_index"],rep_pred[cid]))
        ranked.sort(key=lambda z:(z[0],z[1],z[2]))
        E=[]
        for _,_,_,g in ranked:
            if g is not None and g not in E:E.append(g)
            if len(E)>=2:break

        C=[pred_by_mut.get(simplest["mutation_index"])]

        def h1(sel): return int(bool(sel) and sel[0]==truth)
        def h2(sel): return int(truth in sel[:2])
        sels={"B":B,"W":W,"Wd4":Wd4,"D":D,"E":E,"C":C}
        for lab,sel in sels.items():
            counts[lab+"1"]+=h1(sel)
            counts[lab+"2"]+=h2(sel)

        sem_outputs=set(g for g in rep_pred.values() if g is not None)
        if len(sem_outputs)>=2:
            dis_n+=1
            dis_B+=h1(B); dis_W+=h1(W); dis_Wd4+=h1(Wd4)

        details.append({"query":qi,"semantic_distinct_outputs":len(sem_outputs),
                        **{lab+"1":h1(sel) for lab,sel in sels.items()},
                        **{lab+"2":h2(sel) for lab,sel in sels.items()}})

    n=len(queries)
    labs=["B","W","Wd4","D","E","C"]
    acc={lab:counts[lab+"1"]/n for lab in labs}
    pass2={lab:counts[lab+"2"]/n for lab in labs}
    return {"family":name,"index":fi,"status":"USABLE","n_mutants":len(accepted),
            "n_classes":len(class_map),"n_queries":n,"acc":acc,"pass2":pass2,
            "disagreement_n":dis_n,
            "disagreement_acc_B":dis_B/dis_n if dis_n else None,
            "disagreement_acc_W":dis_W/dis_n if dis_n else None,
            "disagreement_acc_Wd4":dis_Wd4/dis_n if dis_n else None,
            "details":details}

def main():
    root=Path(os.environ.get("ARC_TGI_ROOT","/tmp/ARC-TGI")); sys.path.insert(0,str(root))
    gens=sc.core.load_generators(root)
    start=int(os.environ.get("SHARD_START","0")); end=int(os.environ.get("SHARD_END",str(len(gens))))
    rows=[]
    for fi,(name,mod,cls) in enumerate(gens):
        if start<=fi<end:
            row=build_family(fi,name,mod,cls); rows.append(row)
            print("FAMILY_RESULT",json.dumps({k:row.get(k) for k in ["family","index","status","n_mutants","n_classes","n_queries","acc","disagreement_n"]},sort_keys=True),flush=True)
    out={"summary":{"split":"ARC-TGI-Train-StageD-shard","start":start,"end":end,
                    "n_families":len(rows),"usable_families":sum(r.get("status")=="USABLE" for r in rows),
                    "n_queries_per_usable_family":N_QUERIES,"call_timeout_s":sc.CALL_TIMEOUT},
         "families":rows}
    Path(os.environ.get("OUT_FILE","stage_d_weighted_shard.json")).write_text(json.dumps(out,indent=2))
    print("FINAL_SUMMARY="+json.dumps(out["summary"],sort_keys=True),flush=True)

if __name__=="__main__":main()
