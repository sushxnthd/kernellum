import json, os, random, signal, statistics, sys
from pathlib import Path
from collections import Counter
import numpy as np

sys.path.insert(0,str(Path(__file__).parent))
import identifiability_kill_test_train_shard as core

SEED=core.SEED
TIMEOUT=float(os.environ.get("CALL_TIMEOUT_S","2.0"))

class T(Exception): pass
def _h(s,f): raise T()
def safe_run(fn,obj,x,tv):
    old=signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM,_h); signal.setitimer(signal.ITIMER_REAL,TIMEOUT)
        try:
            y=fn(obj,core.arr(x).copy(),tv); a=core.arr(y)
            if a.ndim!=2 or a.size==0 or max(a.shape)>60:return None
            return a
        except Exception:return None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0); signal.signal(signal.SIGALRM,old)
core.safe_run=safe_run

def dedup(xs,limit=None):
    out=[]; seen=set()
    for x in xs:
        z=core.sig(x)
        if z not in seen:
            seen.add(z); out.append(core.arr(x).copy())
            if limit and len(out)>=limit:break
    return out

def d4_probes(demos):
    xs=[]
    for d in demos: xs.extend(core.d4s(d["input"]))
    return dedup(xs,12)

def color_probes(demos):
    rng=random.Random(SEED+77); xs=[]
    for d in demos:
        a=core.arr(d["input"])
        cols=sorted(set(map(int,a.ravel()))); movable=[c for c in cols if c!=0]
        for _ in range(4):
            perm=movable[:]; rng.shuffle(perm); mp={c:p for c,p in zip(movable,perm)}; mp[0]=0
            xs.append(np.vectorize(lambda v:mp.get(int(v),int(v)))(a))
    return dedup(xs,12)

def roll_probes(demos):
    xs=[]
    for d in demos:
        a=core.arr(d["input"])
        for sh in (1,-1):
            xs.extend([np.roll(a,sh,axis=0),np.roll(a,sh,axis=1)])
    return dedup(xs,12)

def main():
    target=os.environ["FAMILY"]
    root=Path(os.environ.get("ARC_TGI_ROOT","/tmp/ARC-TGI")); sys.path.insert(0,str(root))
    gens=core.load_generators(root)
    matches=[(i,x) for i,x in enumerate(gens) if x[0]==target]
    if not matches: raise RuntimeError(f"missing family {target}")
    fi,(name,mod,cls)=matches[0]
    random.seed(SEED+fi*1000); np.random.seed((SEED+fi*1000)%(2**32-1))
    gen=cls(); tv,data=gen.create_grids(); demos=data["train"]; original=cls.transform_input

    acc=[]; specs=[]
    for mspec,tree in core.mutations(original,500):
        try: fn=core.compile_method(tree,mod.__dict__)
        except Exception:continue
        if all((lambda y,d: y is not None and core.exact(y,d["output"]))(safe_run(fn,gen,d["input"],tv),d) for d in demos):
            acc.append(fn); specs.append(str(mspec))
        if len(acc)>=80:break

    valid_inputs=core.fresh_inputs(gen,tv,40)
    unique=[]; us=[]; seen=set()
    for fn,sp in zip(acc,specs):
        key=repr([None if (y:=safe_run(fn,gen,x,tv)) is None else core.sig(y) for x in valid_inputs[:8]])
        if key not in seen:
            seen.add(key); unique.append(fn); us.append(sp)
    acc,specs=unique,us
    if len(acc)<3:
        out={"family":name,"status":"TOO_FEW","n_mutants":len(acc)}
    else:
        hold=valid_inputs[20:]+core.fresh_inputs(gen,tv,40)
        truth=[safe_run(original,gen,x,tv) for x in hold]
        hacc=[]
        for fn in acc:
            good=tot=0
            for x,y in zip(hold,truth):
                if y is None:continue
                p=safe_run(fn,gen,x,tv); tot+=1; good+=int(p is not None and core.exact(p,y))
            hacc.append(good/max(1,tot))
        probes={"all":core.agnostic_probes(demos,24),"d4":d4_probes(demos),
                "color":color_probes(demos),"roll":roll_probes(demos)}
        rows={}
        for label,ps in probes.items():
            sc,_=core.candidate_centrality(acc,ps,gen,tv)
            best=max(range(len(acc)),key=lambda i:sc[i])
            rows[label]={"n_probes":len(ps),"spearman":core.spear(sc,hacc),
                         "selector_acc":hacc[best],"mean_mutant_acc":statistics.mean(hacc),
                         "gain":hacc[best]-statistics.mean(hacc),
                         "best_spec":specs[best]}
        out={"family":name,"status":"USABLE","n_mutants":len(acc),"probe_results":rows,
             "holdout_acc":hacc}
    Path(os.environ.get("OUT_FILE","probe_ablation.json")).write_text(json.dumps(out,indent=2))
    print("FINAL_SUMMARY="+json.dumps(out,sort_keys=True))

if __name__=="__main__":main()
