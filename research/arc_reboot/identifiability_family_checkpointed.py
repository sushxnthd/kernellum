import json, os, random, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import identifiability_kill_test_train_shard as core

FAMILY_INDEX = int(os.environ.get("FAMILY_INDEX", "6"))
ROOT = Path(os.environ.get("ARC_TGI_ROOT", "/tmp/ARC-TGI"))

def setup():
    sys.path.insert(0, str(ROOT))
    gens = core.load_generators(ROOT)
    name, mod, cls = gens[FAMILY_INDEX]
    random.seed(core.SEED + FAMILY_INDEX * 1000)
    np.random.seed((core.SEED + FAMILY_INDEX * 1000) % (2**32 - 1))
    gen = cls()
    tv, data = gen.create_grids()
    return gens, name, mod, cls, gen, tv, data

def screen():
    _, name, mod, cls, gen, tv, data = setup()
    start = int(os.environ["CHUNK_START"])
    end = int(os.environ["CHUNK_END"])
    demos = data["train"]
    accepted = []
    n_seen = 0
    for mi, (mspec, tree) in enumerate(core.mutations(cls.transform_input, 500)):
        n_seen = mi + 1
        if mi < start or mi >= end:
            continue
        try:
            fn = core.compile_method(tree, mod.__dict__)
        except Exception:
            continue
        ok = True
        for d in demos:
            y = core.safe_run(fn, gen, d["input"], tv)
            if y is None or not core.exact(y, d["output"]):
                ok = False
                break
        if ok:
            accepted.append({"index": mi, "spec": str(mspec)})
    out = {"family": name, "family_index": FAMILY_INDEX, "chunk_start": start, "chunk_end": end,
           "generated_mutants_seen": n_seen, "accepted": accepted}
    path = Path(os.environ.get("OUT_FILE", f"screen_{start}_{end}.json"))
    path.write_text(json.dumps(out, indent=2))
    print("SCREEN_SUMMARY=" + json.dumps({k: out[k] for k in ["family","chunk_start","chunk_end","generated_mutants_seen"]} | {"accepted_n": len(accepted)}, sort_keys=True))

def aggregate():
    _, name, mod, cls, gen, tv, data = setup()
    root = Path(os.environ.get("SCREEN_DIR", "screens"))
    idxs = {}
    for p in root.rglob("*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("family_index") != FAMILY_INDEX:
            continue
        for a in d.get("accepted", []):
            idxs[int(a["index"])] = a["spec"]
    accepted_indices = sorted(idxs)[:80]
    mutants = list(core.mutations(cls.transform_input, 500))
    accepted = []; specs = []
    for mi in accepted_indices:
        if mi >= len(mutants):
            continue
        mspec, tree = mutants[mi]
        fn = core.compile_method(tree, mod.__dict__)
        accepted.append(fn); specs.append(str(mspec))

    valid_inputs = core.fresh_inputs(gen, tv, 40)
    unique=[]; uspec=[]; seen=set()
    for fn,sp in zip(accepted,specs):
        bs=[]
        for x in valid_inputs[:8]:
            y=core.safe_run(fn,gen,x,tv); bs.append(None if y is None else core.sig(y))
        key=repr(bs)
        if key not in seen:
            seen.add(key); unique.append(fn); uspec.append(sp)
    accepted,specs=unique,uspec
    if len(accepted)<3:
        row={"family":name,"n_mutants":len(accepted),"status":"TOO_FEW"}
    else:
        demos=data["train"]; original=cls.transform_input
        valid_probes=valid_inputs[:20]
        ag_probes=core.agnostic_probes(demos,24)
        hold_inputs=valid_inputs[20:]+core.fresh_inputs(gen,tv,40)
        hold_truth=[core.safe_run(original,gen,x,tv) for x in hold_inputs]
        cv,vr=core.candidate_centrality(accepted,valid_probes,gen,tv)
        ca,ar=core.candidate_centrality(accepted,ag_probes,gen,tv)
        acc=[]
        for fn in accepted:
            good=tot=0
            for x,y in zip(hold_inputs,hold_truth):
                if y is None: continue
                p=core.safe_run(fn,gen,x,tv); tot+=1; good+=int(p is not None and core.exact(p,y))
            acc.append(good/max(1,tot))
        rv=core.spear(cv,acc); ra=core.spear(ca,acc)
        bestv=acc[max(range(len(acc)),key=lambda i:cv[i])]
        besta=acc[max(range(len(acc)),key=lambda i:ca[i])]
        import statistics
        meanacc=statistics.mean(acc)
        row={"family":name,"n_demos":len(demos),"n_mutants":len(accepted),
             "valid_probe_n":len(valid_probes),"agnostic_probe_n":len(ag_probes),"holdout_n":len(hold_inputs),
             "spearman_valid":rv,"spearman_agnostic":ra,
             "selector_valid_acc":bestv,"selector_agnostic_acc":besta,
             "mean_mutant_acc":meanacc,"perfect_mutant_frac":sum(a==1.0 for a in acc)/len(acc),
             "valid_gain":bestv-meanacc,"agnostic_gain":besta-meanacc,
             "centrality_valid":cv,"centrality_agnostic":ca,"holdout_acc":acc,"specs":specs}
    summary={"split":"ARC-TGI-Train-family6-checkpointed","global_n_families":len(core.load_generators(ROOT)),
             "family_index":FAMILY_INDEX,"n_families":1,"usable_families":int(row.get("status")!="TOO_FEW"),
             "accepted_pre_dedupe":len(accepted_indices),
             "equivalence_note":"Same deterministic first-500 mutant order and first-80 accepted stopping rule as frozen Stage B; screening only partitioned across jobs."}
    out={"summary":summary,"families":[row]}
    path=Path(os.environ.get("OUT_FILE","identifiability_family_6_checkpointed.json"))
    path.write_text(json.dumps(out,indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary|{"family_result":{k:row.get(k) for k in ["family","n_mutants","spearman_agnostic","agnostic_gain","status"]}},sort_keys=True))

if __name__=="__main__":
    mode=os.environ.get("MODE","screen")
    screen() if mode=="screen" else aggregate()
