import ast, copy, importlib.util, inspect, json, math, os, random, statistics, sys, textwrap, traceback
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

SEED=20261028
random.seed(SEED); np.random.seed(SEED)

def arr(x): return np.asarray(x, dtype=int)
def sig(x):
    a=arr(x)
    return (tuple(a.shape), tuple(map(int,a.ravel())))
def exact(a,b):
    try:return np.array_equal(arr(a),arr(b))
    except:return False

def rankdata(xs):
    order=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0.0]*len(xs); i=0
    while i<len(order):
        j=i
        while j+1<len(order) and xs[order[j+1]]==xs[order[i]]: j+=1
        q=(i+j)/2+1
        for k in range(i,j+1):r[order[k]]=q
        i=j+1
    return r
def pearson(x,y):
    if len(x)<2:return None
    mx,my=statistics.mean(x),statistics.mean(y)
    d=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/d if d else None
def spear(x,y): return pearson(rankdata(x),rankdata(y))

class Sites(ast.NodeVisitor):
    def __init__(self): self.s=[]
    def visit_Constant(self,n):
        if isinstance(n.value,int) and not isinstance(n.value,bool) and -30<=n.value<=30:
            self.s.append(("const",n))
        self.generic_visit(n)
    def visit_Compare(self,n):
        for i,o in enumerate(n.ops):
            if isinstance(o,(ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq)):
                self.s.append(("cmp",(n,i)))
        self.generic_visit(n)
    def visit_BinOp(self,n):
        if isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.FloorDiv)):
            self.s.append(("bin",n))
        self.generic_visit(n)
    def visit_BoolOp(self,n):
        if isinstance(n.op,(ast.And,ast.Or)): self.s.append(("bool",n))
        self.generic_visit(n)
    def visit_Call(self,n):
        if isinstance(n.func,ast.Name) and n.func.id in ("min","max"):
            self.s.append(("minmax",n))
        self.generic_visit(n)

def locate(tree,target_kind,target_index):
    v=Sites(); v.visit(tree)
    items=[x for x in v.s if x[0]==target_kind]
    return items[target_index][1] if target_index<len(items) else None

def mutations(fn,max_mutants=300):
    src=textwrap.dedent(inspect.getsource(fn))
    base=ast.parse(src)
    sv=Sites();sv.visit(base)
    specs=[]
    for kind in ("const","cmp","bin","bool","minmax"):
        n=sum(1 for k,_ in sv.s if k==kind)
        for idx in range(n):
            if kind=="const":
                for delta in (-2,-1,1,2):specs.append((kind,idx,delta))
            elif kind=="cmp": specs.append((kind,idx,None))
            elif kind=="bin": specs.append((kind,idx,None))
            elif kind=="bool": specs.append((kind,idx,None))
            else: specs.append((kind,idx,None))
    random.Random(SEED).shuffle(specs)
    seen=set()
    for spec in specs[:max_mutants]:
        kind,idx,param=spec
        t=copy.deepcopy(base); node=locate(t,kind,idx)
        if node is None:continue
        try:
            if kind=="const":
                if node.value in (0,1) and param<0: continue
                node.value=int(node.value)+param
            elif kind=="cmp":
                parent,i=node; o=parent.ops[i]
                mp={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
                parent.ops[i]=mp[type(o)]()
            elif kind=="bin":
                mp={ast.Add:ast.Sub,ast.Sub:ast.Add,ast.Mult:ast.FloorDiv,ast.FloorDiv:ast.Mult}
                node.op=mp[type(node.op)]()
            elif kind=="bool": node.op=ast.Or() if isinstance(node.op,ast.And) else ast.And()
            elif kind=="minmax": node.func.id="max" if node.func.id=="min" else "min"
            ast.fix_missing_locations(t)
            key=ast.dump(t,include_attributes=False)
            if key in seen:continue
            seen.add(key)
            yield spec,t
        except Exception:continue

def compile_method(tree,globals_ns):
    ns=dict(globals_ns)
    code=compile(tree,"<mutant>","exec")
    exec(code,ns,ns)
    return ns["transform_input"]

def safe_run(fn,obj,x,tv):
    try:
        y=fn(obj,arr(x).copy(),tv)
        a=arr(y)
        if a.ndim!=2 or a.size==0 or max(a.shape)>60:return None
        return a
    except Exception:return None

def d4s(g):
    a=arr(g); out=[]
    for k in range(4):
        r=np.rot90(a,k)
        out += [r, np.fliplr(r)]
    uniq=[]; seen=set()
    for x in out:
        z=sig(x)
        if z not in seen:seen.add(z);uniq.append(x.copy())
    return uniq

def agnostic_probes(demos,limit=24):
    rng=random.Random(SEED+77); out=[]; seen=set()
    for d in demos:
        a=arr(d["input"])
        for x in d4s(a):
            z=sig(x)
            if z not in seen:seen.add(z);out.append(x)
        # label-free color permutations, preserving zero when present
        cols=sorted(set(map(int,a.ravel())))
        movable=[c for c in cols if c!=0]
        for rep in range(3):
            perm=movable[:];rng.shuffle(perm);mp={c:p for c,p in zip(movable,perm)};mp[0]=0
            x=np.vectorize(lambda v:mp.get(int(v),int(v)))(a)
            z=sig(x)
            if z not in seen:seen.add(z);out.append(x)
        # cyclic spatial perturbations preserve dimensions
        for sh in [1,-1]:
            for x in (np.roll(a,sh,axis=0),np.roll(a,sh,axis=1)):
                z=sig(x)
                if z not in seen:seen.add(z);out.append(x)
    rng.shuffle(out)
    return out[:limit]

def candidate_centrality(cands,probes,obj,tv):
    # semantic quotient on each probe, then average fraction agreeing with candidate.
    outs=[]
    for fn in cands:
        outs.append([safe_run(fn,obj,x,tv) for x in probes])
    scores=[]
    valid_rates=[]
    entropies=[]
    for i,row in enumerate(outs):
        vals=[]; valid=0
        for p in range(len(probes)):
            col=[outs[j][p] for j in range(len(cands))]
            valid_col=[x for x in col if x is not None]
            if row[p] is None or not valid_col:continue
            valid+=1
            counts=Counter(sig(x) for x in valid_col)
            vals.append(counts[sig(row[p])]/len(valid_col))
        scores.append(statistics.mean(vals) if vals else 0.0)
        valid_rates.append(valid/max(1,len(probes)))
    return scores,valid_rates

def load_generators(root):
    files=sorted((root/"Generators/ARC-AGI-2/Train").glob("task*.py"))
    out=[]
    for i,p in enumerate(files):
        name="arc_tgi_"+p.stem
        spec=importlib.util.spec_from_file_location(name,p)
        mod=importlib.util.module_from_spec(spec)
        try:spec.loader.exec_module(mod)
        except Exception as e:
            print("IMPORT_FAIL",p.name,repr(e));continue
        classes=[c for _,c in inspect.getmembers(mod,inspect.isclass) if c.__module__==name and c.__name__.endswith("Generator")]
        if classes:out.append((p.stem,mod,classes[0]))
    return out

def fresh_inputs(gen,tv,n):
    xs=[]
    for _ in range(n):
        try: xs.append(arr(gen.create_input(tv,{})).copy())
        except Exception: pass
    return xs

def main():
    root=Path(os.environ.get("ARC_TGI_ROOT","/tmp/ARC-TGI"))
    sys.path.insert(0,str(root))
    gens=load_generators(root)
    shard_start=int(os.environ.get("SHARD_START","0"))
    shard_end=int(os.environ.get("SHARD_END",str(len(gens))))
    out_file=os.environ.get("OUT_FILE","identifiability_kill_test_shard.json")
    print("GENERATORS",[x[0] for x in gens])
    print("SHARD",shard_start,shard_end)
    results=[]
    for fi,(name,mod,cls) in enumerate(gens):
        if not (shard_start <= fi < shard_end):
            continue
        fam_rng=random.Random(SEED+fi*1000)
        random.seed(SEED+fi*1000);np.random.seed((SEED+fi*1000)%(2**32-1))
        gen=cls()
        try: tv,data=gen.create_grids()
        except Exception as e:
            print("CREATE_FAIL",name,repr(e));continue
        demos=data["train"]
        original=cls.transform_input
        accepted=[]; specs=[]
        for mspec,tree in mutations(original,500):
            try: fn=compile_method(tree,mod.__dict__)
            except Exception:continue
            ok=True
            for d in demos:
                y=safe_run(fn,gen,d["input"],tv)
                if y is None or not exact(y,d["output"]):
                    ok=False;break
            if ok:
                accepted.append(fn);specs.append(str(mspec))
            if len(accepted)>=80:break
        # quotient duplicate mutant behavior using a seed probe set
        valid_inputs=fresh_inputs(gen,tv,40)
        unique=[];uspec=[]; seen=set()
        for fn,sp in zip(accepted,specs):
            bs=[]
            for x in valid_inputs[:8]:
                y=safe_run(fn,gen,x,tv);bs.append(None if y is None else sig(y))
            key=repr(bs)
            if key not in seen:
                seen.add(key);unique.append(fn);uspec.append(sp)
        accepted,specs=unique,uspec
        if len(accepted)<3:
            results.append({"family":name,"n_mutants":len(accepted),"status":"TOO_FEW"})
            print("FAMILY",name,"TOO_FEW",len(accepted));continue

        # Exclude true/original transform from candidate pool by construction.
        valid_probes=valid_inputs[:20]
        ag_probes=agnostic_probes(demos,24)
        hold_inputs=valid_inputs[20:]+fresh_inputs(gen,tv,40)
        hold_truth=[safe_run(original,gen,x,tv) for x in hold_inputs]

        cv,vr=candidate_centrality(accepted,valid_probes,gen,tv)
        ca,ar=candidate_centrality(accepted,ag_probes,gen,tv)
        acc=[]
        for fn in accepted:
            good=tot=0
            for x,y in zip(hold_inputs,hold_truth):
                if y is None:continue
                p=safe_run(fn,gen,x,tv);tot+=1;good+=int(p is not None and exact(p,y))
            acc.append(good/max(1,tot))
        rv=spear(cv,acc);ra=spear(ca,acc)
        bestv=acc[max(range(len(acc)),key=lambda i:cv[i])]
        besta=acc[max(range(len(acc)),key=lambda i:ca[i])]
        meanacc=statistics.mean(acc)
        perfect=sum(a==1.0 for a in acc)/len(acc)
        row={"family":name,"n_demos":len(demos),"n_mutants":len(accepted),
             "valid_probe_n":len(valid_probes),"agnostic_probe_n":len(ag_probes),"holdout_n":len(hold_inputs),
             "spearman_valid":rv,"spearman_agnostic":ra,
             "selector_valid_acc":bestv,"selector_agnostic_acc":besta,
             "mean_mutant_acc":meanacc,"perfect_mutant_frac":perfect,
             "valid_gain":bestv-meanacc,"agnostic_gain":besta-meanacc,
             "centrality_valid":cv,"centrality_agnostic":ca,"holdout_acc":acc,"specs":specs}
        results.append(row)
        print("FAMILY",name,json.dumps({k:row[k] for k in ["n_mutants","spearman_valid","spearman_agnostic","selector_valid_acc","selector_agnostic_acc","mean_mutant_acc"]}))

    usable=[r for r in results if r.get("status")!="TOO_FEW"]
    def med(k):
        v=[r[k] for r in usable if r.get(k) is not None]
        return statistics.median(v) if v else None
    summary={
      "split":"ARC-TGI-Train-shard","global_n_families":len(gens),"shard_start":shard_start,"shard_end":shard_end,"n_families":len(results),"usable_families":len(usable),
      "median_spearman_valid":med("spearman_valid"),
      "median_spearman_agnostic":med("spearman_agnostic"),
      "median_valid_gain":med("valid_gain"),
      "median_agnostic_gain":med("agnostic_gain"),
      "valid_positive_corr":sum((r.get("spearman_valid") or 0)>0 for r in usable),
      "agnostic_positive_corr":sum((r.get("spearman_agnostic") or 0)>0 for r in usable),
      "valid_gain_gt_10pp":sum((r.get("valid_gain") or 0)>.10 for r in usable),
      "agnostic_gain_gt_10pp":sum((r.get("agnostic_gain") or 0)>.10 for r in usable),
      "kill_rule":"Practical claim survives only if >=6 usable families, median agnostic Spearman >=0.30, and median agnostic selector gain >=0.10. Valid-probe result alone is mechanism evidence only."
    }
    out={"summary":summary,"families":results}
    Path(out_file).write_text(json.dumps(out,indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True))

if __name__=="__main__":main()
