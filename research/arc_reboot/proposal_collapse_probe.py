import argparse, json, os, random, re, statistics, time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED_BASE=2026102800

def flatten(g):
    return tuple(tuple(int(x) for x in row) for row in g)

def valid_grid(g):
    return (
        isinstance(g,list) and g and
        all(isinstance(r,list) and r for r in g) and
        len({len(r) for r in g})==1 and
        all(isinstance(x,int) and 0<=x<=9 for r in g for x in r)
    )

def extract_grid(text):
    # Search JSON-like list-of-lists from the end; tolerate markdown around it.
    starts=[m.start() for m in re.finditer(r'\[\s*\[', text)]
    for s in reversed(starts):
        depth=0; in_str=False; esc=False
        for i in range(s,len(text)):
            ch=text[i]
            if in_str:
                if esc: esc=False
                elif ch=="\\": esc=True
                elif ch=='"': in_str=False
                continue
            if ch=='"': in_str=True
            elif ch=='[': depth+=1
            elif ch==']':
                depth-=1
                if depth==0:
                    try:
                        g=json.loads(text[s:i+1])
                        if valid_grid(g): return g
                    except Exception:
                        break
    return None

def same_shape(a,b):
    return len(a)==len(b) and len(a[0])==len(b[0])

def rot(g,k):
    a=[row[:] for row in g]
    for _ in range(k%4):
        a=[list(row) for row in zip(*a[::-1])]
    return a

def flip_lr(g): return [r[::-1] for r in g]
def flip_ud(g): return g[::-1]
def transpose(g): return [list(r) for r in zip(*g)]

def color_map_fit(train):
    mp={}
    for p in train:
        if not same_shape(p["input"],p["output"]): return None
        for ri,ro in zip(p["input"],p["output"]):
            for x,y in zip(ri,ro):
                if x in mp and mp[x]!=y: return None
                mp[x]=y
    return mp

def apply_color_map(g,mp):
    return [[mp.get(x,x) for x in r] for r in g]

def shift(g,dr,dc,bg=0):
    h,w=len(g),len(g[0])
    out=[[bg]*w for _ in range(h)]
    for i in range(h):
        for j in range(w):
            ni,nj=i+dr,j+dc
            if 0<=ni<h and 0<=nj<w:
                out[ni][nj]=g[i][j]
    return out

def train_simple_transforms(task):
    train=task["train"]
    fits=[]
    candidates=[
        ("identity", lambda g:g),
        ("rot90", lambda g:rot(g,1)),
        ("rot180", lambda g:rot(g,2)),
        ("rot270", lambda g:rot(g,3)),
        ("flip_lr", flip_lr),
        ("flip_ud", flip_ud),
        ("transpose", transpose),
    ]
    for name,fn in candidates:
        ok=True
        for p in train:
            try:
                y=fn(p["input"])
            except Exception:
                ok=False; break
            if y!=p["output"]:
                ok=False; break
        if ok: fits.append(name)

    mp=color_map_fit(train)
    if mp is not None and any(k!=v for k,v in mp.items()):
        if all(apply_color_map(p["input"],mp)==p["output"] for p in train):
            fits.append("global_color_map")

    for dr in range(-2,3):
        for dc in range(-2,3):
            if dr==0 and dc==0: continue
            if all(same_shape(p["input"],p["output"]) and shift(p["input"],dr,dc,0)==p["output"] for p in train):
                fits.append(f"shift_{dr}_{dc}")
    return fits

def changed(p): return p["input"]!=p["output"]

def eligible(task):
    if len(task.get("test",[]))!=1 or len(task.get("train",[]))<2: return False
    if not all(p.get("input") and p.get("output") for p in task["train"]): return False
    if not any(changed(p) for p in task["train"]): return False
    if any(len(p["input"])*len(p["input"][0])>144 for p in task["train"]): return False
    return bool(train_simple_transforms(task))

def complexity(task):
    train=task["train"]
    areas=[len(p["input"])*len(p["input"][0]) + len(p["output"])*len(p["output"][0]) for p in train]
    colors=set()
    for p in train:
        for g in (p["input"],p["output"]):
            colors.update(x for r in g for x in r)
    fits=train_simple_transforms(task)
    return (max(areas),len(colors),len(fits),sum(areas),len(train))

def compact(g): return json.dumps(g,separators=(",",":"))

def build_prompt(task):
    parts=[
        "You are solving an ARC (Abstraction and Reasoning Corpus) puzzle.",
        "Infer the visual transformation ONLY from the solved examples, then apply it to TEST.",
        "The output-format instructions below are not part of the puzzle rule.",
        'Return exactly one JSON object with keys "rule" and "grid".',
        '"rule" is a brief natural-language description. "grid" must be a rectangular 2-D array of integer colors 0-9.',
        "Do not copy an example unless the inferred transformation requires it. Check the rule against every solved example before answering."
    ]
    for i,p in enumerate(task["train"],1):
        parts.append(f"SOLVED {i} INPUT {compact(p['input'])}")
        parts.append(f"SOLVED {i} OUTPUT {compact(p['output'])}")
    parts.append(f"TEST INPUT {compact(task['test'][0]['input'])}")
    return "\n".join(parts)

def refine_prompt(task,previous):
    return (
        build_prompt(task)
        + "\nA previous solver produced this candidate:\n"
        + previous.strip()
        + "\nTreat it only as a fallible hypothesis. Re-derive the rule from the solved examples. "
          "Actively look for a counterexample among the solved pairs. If the candidate is wrong or underspecified, replace it. "
          'Return exactly one JSON object with keys "rule" and "grid".'
    )

def generate(model,tok,prompt,seed,max_new_tokens):
    torch.manual_seed(seed); random.seed(seed)
    text=tok.apply_chat_template([{"role":"user","content":prompt}],tokenize=False,add_generation_prompt=True)
    inputs=tok(text,return_tensors="pt")
    with torch.inference_mode():
        out=model.generate(
            **inputs,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            max_new_tokens=max_new_tokens,
            pad_token_id=tok.eos_token_id,
        )
    return tok.decode(out[0,inputs["input_ids"].shape[1]:],skip_special_tokens=True)

def exact(pred,truth):
    return pred is not None and flatten(pred)==flatten(truth)

def hamming(a,b):
    if a is None or b is None or len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)): return None
    n=sum(len(r) for r in a)
    return (sum(x!=y for ra,rb in zip(a,b) for x,y in zip(ra,rb))/n) if n else None

def boot_delta(rows,key_a,key_b,B=4000,seed=20261028):
    rng=random.Random(seed); n=len(rows)
    if not n:return None
    ds=[]
    for _ in range(B):
        sm=[rows[rng.randrange(n)] for _ in range(n)]
        ds.append(sum(r[key_b]-r[key_a] for r in sm)/n)
    ds.sort()
    return [ds[int(.025*B)],ds[min(B-1,int(.975*B))]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc-dir",default="ARC-AGI-2/data/training")
    ap.add_argument("--model",default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--tasks",type=int,default=20)
    ap.add_argument("--max-new-tokens",type=int,default=144)
    ap.add_argument("--out",default="proposal_collapse_probe_v2_results.json")
    args=ap.parse_args()

    torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))
    print("MODEL",args.model,flush=True)
    tok=AutoTokenizer.from_pretrained(args.model)
    model=AutoModelForCausalLM.from_pretrained(args.model,torch_dtype=torch.float32)
    model.eval()

    pool=[]
    for p in sorted(Path(args.arc_dir).glob("*.json")):
        task=json.loads(p.read_text())
        if eligible(task):
            pool.append((complexity(task),p.stem,task,train_simple_transforms(task)))
    pool.sort(key=lambda x:(x[0],x[1]))
    chosen=pool[:args.tasks]
    print("ELIGIBLE",len(pool),"CHOSEN",[(x[1],x[3]) for x in chosen],flush=True)

    rows=[]; t0=time.time()
    for idx,(_,tid,task,fits) in enumerate(chosen):
        truth=task["test"][0]["output"]
        base=build_prompt(task)
        s0=SEED_BASE+idx*17; s1=s0+1
        ind0_text=generate(model,tok,base,s0,args.max_new_tokens)
        ind1_text=generate(model,tok,base,s1,args.max_new_tokens)
        seq1_text=generate(model,tok,refine_prompt(task,ind0_text),s1,args.max_new_tokens)
        ind0,ind1,seq1=map(extract_grid,[ind0_text,ind1_text,seq1_text])
        both_ind=int(ind0 is not None and ind1 is not None)
        both_seq=int(ind0 is not None and seq1 is not None)
        row={
            "task_id":tid,"train_simple_transforms":fits,
            "ind0_valid":int(ind0 is not None),"ind1_valid":int(ind1 is not None),"seq1_valid":int(seq1 is not None),
            "ind0_correct":int(exact(ind0,truth)),"ind1_correct":int(exact(ind1,truth)),"seq1_correct":int(exact(seq1,truth)),
            "ind_new_class":int(both_ind and flatten(ind0)!=flatten(ind1)),
            "seq_new_class":int(both_seq and flatten(ind0)!=flatten(seq1)),
            "both_ind_valid":both_ind,"both_seq_valid":both_seq,
            "ind_hamming":hamming(ind0,ind1),"seq_hamming":hamming(ind0,seq1),
            "ind_oracle":int(exact(ind0,truth) or exact(ind1,truth)),
            "seq_oracle":int(exact(ind0,truth) or exact(seq1,truth)),
            "ind0_text":ind0_text,"ind1_text":ind1_text,"seq1_text":seq1_text,
            "truth":truth,"ind0_grid":ind0,"ind1_grid":ind1,"seq1_grid":seq1,
        }
        rows.append(row)
        print("TASK",idx+1,tid,json.dumps({k:row[k] for k in [
            "ind0_correct","ind1_correct","seq1_correct","ind_new_class","seq_new_class","ind_oracle","seq_oracle"
        ]}),flush=True)

    n=len(rows)
    def mean(k): return sum(r[k] for r in rows)/n
    def nonnull(k):
        v=[r[k] for r in rows if r[k] is not None]
        return statistics.mean(v) if v else None
    paired_valid=[r for r in rows if r["ind0_valid"] and r["ind1_valid"] and r["seq1_valid"]]

    summary={
        "version":"v2_prompt_fixed_train_easy",
        "model":args.model,"n_tasks":n,
        "task_ids":[r["task_id"] for r in rows],
        "parse_rate":{"ind0":mean("ind0_valid"),"ind1":mean("ind1_valid"),"seq1":mean("seq1_valid")},
        "correct_rate":{"ind0":mean("ind0_correct"),"ind1":mean("ind1_correct"),"seq1":mean("seq1_correct")},
        "archive_oracle":{"independent":mean("ind_oracle"),"sequential":mean("seq_oracle"),"delta_seq_minus_ind":mean("seq_oracle")-mean("ind_oracle")},
        "new_class_rate_unconditional":{"independent":mean("ind_new_class"),"sequential":mean("seq_new_class"),"delta_seq_minus_ind":mean("seq_new_class")-mean("ind_new_class")},
        "paired_valid_n":len(paired_valid),
        "new_class_rate_paired_valid":{
            "independent":statistics.mean([r["ind_new_class"] for r in paired_valid]) if paired_valid else None,
            "sequential":statistics.mean([r["seq_new_class"] for r in paired_valid]) if paired_valid else None,
        },
        "mean_hamming":{"independent":nonnull("ind_hamming"),"sequential":nonnull("seq_hamming")},
        "paired_counts":{
            "novel_ind_only":sum(r["ind_new_class"] and not r["seq_new_class"] for r in rows),
            "novel_seq_only":sum(r["seq_new_class"] and not r["ind_new_class"] for r in rows),
            "oracle_ind_only":sum(r["ind_oracle"] and not r["seq_oracle"] for r in rows),
            "oracle_seq_only":sum(r["seq_oracle"] and not r["ind_oracle"] for r in rows),
        },
        "bootstrap95_delta":{
            "new_class_seq_minus_ind":boot_delta(rows,"ind_new_class","seq_new_class"),
            "oracle_seq_minus_ind":boot_delta(rows,"ind_oracle","seq_oracle"),
        },
        "elapsed_s":time.time()-t0,
        "selection_rule":"Select smallest ARC-AGI-2 public training tasks for which at least one low-complexity transform (D4/transpose/global color-map/small translation) fits every training pair. Test outputs are never used for selection or prompting.",
        "comparison":"Attempt 0 identical. Independent attempt 1 sees the base task only. Sequential attempt 1 sees the exact attempt-0 response plus a falsification/refinement instruction. Same second-attempt seed and decoding parameters. All candidates archived.",
        "decision_gate":"Do not infer accuracy collapse unless at least one branch has nonzero archived Oracle. If |Oracle_seq-Oracle_ind| < 0.02 on a sufficiently powered competent-model run, kill proposal-collapse. Diversity is a secondary mechanism endpoint, not a substitute for accuracy."
    }
    Path(args.out).write_text(json.dumps({"summary":summary,"rows":rows},indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
