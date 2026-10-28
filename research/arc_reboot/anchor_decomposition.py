import argparse, json, os, random, re, statistics, sys, time
from pathlib import Path
import torch

sys.path.insert(0,str(Path(__file__).parent))
import proposal_collapse_probe as base

def extract_rule(text):
    # Prefer a JSON object carrying a string rule.
    for s in [m.start() for m in re.finditer(r'\{',text)]:
        depth=0; ins=False; esc=False
        for i in range(s,len(text)):
            ch=text[i]
            if ins:
                if esc: esc=False
                elif ch=="\\": esc=True
                elif ch=='"': ins=False
                continue
            if ch=='"': ins=True
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:
                    try:
                        o=json.loads(text[s:i+1])
                        if isinstance(o,dict) and isinstance(o.get("rule"),str):
                            return o["rule"]
                    except Exception: pass
                    break
    return None

def conditioned_prompt(task,kind,prev_text,prev_grid,prev_rule):
    b=base.build_prompt(task)
    if kind=="independent":
        return b
    if kind=="full":
        return b+("\nPREVIOUS CANDIDATE (fallible):\n"+prev_text.strip()+
                  "\nRe-derive the rule from the solved examples and actively search for a counterexample to the previous candidate. "
                  "If it is wrong, replace it. Return exactly one JSON object.")
    if kind=="grid":
        payload=json.dumps(prev_grid,separators=(",",":")) if prev_grid is not None else "UNPARSEABLE"
        return b+(f"\nA previous solver proposed this TEST OUTPUT GRID: {payload}\n"
                  "Do not assume it is correct. Re-derive the rule from the solved examples and decide the test grid yourself. "
                  "Return exactly one JSON object.")
    if kind=="rule":
        payload=prev_rule if prev_rule else "UNAVAILABLE"
        return b+(f"\nA previous solver proposed this RULE DESCRIPTION: {payload}\n"
                  "Do not assume it is correct. Re-derive the rule from the solved examples and decide the test grid yourself. "
                  "Return exactly one JSON object.")
    if kind=="anti_anchor":
        return b+("\nYou will see a previous candidate below, but use this protocol: first solve the task from the solved examples as if the candidate did not exist; "
                  "only after fixing your own answer may you compare it with the previous candidate. Keep your independently derived answer unless the solved examples falsify it.\n"
                  "PREVIOUS CANDIDATE:\n"+prev_text.strip()+"\nReturn exactly one JSON object.")
    raise ValueError(kind)

def ft(g): return base.flatten(g) if g is not None else None
def exact(a,b): return base.exact(a,b)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc-dir",default="ARC-AGI-2/data/training")
    ap.add_argument("--model",default="Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--dtype",choices=["float32","bfloat16"],default="bfloat16")
    ap.add_argument("--tasks",type=int,default=8)
    ap.add_argument("--max-new-tokens",type=int,default=180)
    ap.add_argument("--out",default="anchor_decomposition_results.json")
    args=ap.parse_args()

    torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))
    from transformers import AutoTokenizer,AutoModelForCausalLM
    tok=AutoTokenizer.from_pretrained(args.model)
    dtype=torch.bfloat16 if args.dtype=="bfloat16" else torch.float32
    model=AutoModelForCausalLM.from_pretrained(args.model,torch_dtype=dtype,low_cpu_mem_usage=True)
    model.eval()

    pool=[]
    for p in sorted(Path(args.arc_dir).glob("*.json")):
        task=json.loads(p.read_text())
        if base.eligible(task):
            pool.append((base.complexity(task),p.stem,task,base.train_simple_transforms(task)))
    pool.sort(key=lambda x:(x[0],x[1]))
    chosen=pool[:args.tasks]
    conditions=["independent","full","grid","rule","anti_anchor"]
    rows=[]; t0=time.time()
    print("MODEL",args.model,"CHOSEN",[(x[1],x[3]) for x in chosen],flush=True)

    for idx,(_,tid,task,fits) in enumerate(chosen):
        truth=task["test"][0]["output"]
        s0=base.SEED_BASE+idx*17; s1=s0+1
        p0=base.build_prompt(task)
        t0txt=base.generate(model,tok,p0,s0,args.max_new_tokens)
        g0=base.extract_grid(t0txt); r0=extract_rule(t0txt)
        rec={"task_id":tid,"train_simple_transforms":fits,"attempt0_text":t0txt,"attempt0_grid":g0,"attempt0_correct":int(exact(g0,truth)),"truth":truth,"conditions":{}}
        for kind in conditions:
            pr=conditioned_prompt(task,kind,t0txt,g0,r0)
            txt=base.generate(model,tok,pr,s1,args.max_new_tokens)
            g=base.extract_grid(txt)
            rec["conditions"][kind]={
                "text":txt,"grid":g,"valid":int(g is not None),"correct":int(exact(g,truth)),
                "repeat0":int(g is not None and g0 is not None and ft(g)==ft(g0)),
                "new_class":int(g is not None and g0 is not None and ft(g)!=ft(g0)),
                "hamming":base.hamming(g0,g),
                "archive_oracle":int(exact(g0,truth) or exact(g,truth)),
            }
        rows.append(rec)
        print("TASK",idx+1,tid,json.dumps({k:{z:rec["conditions"][k][z] for z in ["valid","correct","repeat0","archive_oracle"]} for k in conditions}),flush=True)

    summary={"model":args.model,"dtype":args.dtype,"n_tasks":len(rows),"conditions":{}}
    for kind in conditions:
        rs=[r["conditions"][kind] for r in rows]
        valid_pair=[(r,r["conditions"][kind]) for r in rows if r["attempt0_grid"] is not None and r["conditions"][kind]["grid"] is not None]
        summary["conditions"][kind]={
            "valid_rate":statistics.mean(x["valid"] for x in rs),
            "correct_rate":statistics.mean(x["correct"] for x in rs),
            "archive_oracle":statistics.mean(x["archive_oracle"] for x in rs),
            "repeat0_unconditional":statistics.mean(x["repeat0"] for x in rs),
            "repeat0_given_both_valid":statistics.mean(x["repeat0"] for _,x in valid_pair) if valid_pair else None,
            "mean_hamming":statistics.mean([x["hamming"] for x in rs if x["hamming"] is not None]) if any(x["hamming"] is not None for x in rs) else None,
        }
    summary["selection_rule"]="Same training-only easy-task selector as proposal-collapse v2; no test truth used in selection or prompting."
    summary["causal_question"]="With the second-attempt RNG seed matched, does exposing the prior grid, prior rule, or full prior response increase exact answer repetition and reduce archived Oracle relative to an independent redraw?"
    summary["elapsed_s"]=time.time()-t0
    Path(args.out).write_text(json.dumps({"summary":summary,"rows":rows},indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
