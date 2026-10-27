import argparse, json, os, random, re, statistics, time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def flatten(g):
    return tuple(tuple(int(x) for x in row) for row in g)

def valid_grid(g):
    return isinstance(g, list) and len(g) > 0 and all(isinstance(r, list) and len(r) > 0 for r in g) and len({len(r) for r in g}) == 1 and all(isinstance(x, int) and 0 <= x <= 9 for r in g for x in r)

def extract_grid(text):
    # Prefer JSON object with a grid field.
    candidates = []
    for m in re.finditer(r'\{.*?\}', text, flags=re.S):
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and valid_grid(obj.get("grid")):
                candidates.append(obj["grid"])
        except Exception:
            pass
    if candidates:
        return candidates[-1]
    # Then try any balanced-looking list-of-lists substrings, from latest to earliest.
    starts = [m.start() for m in re.finditer(r'\[\s*\[', text)]
    for s in reversed(starts):
        depth = 0
        in_str = False
        esc = False
        for i in range(s, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\\\':
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    frag = text[s:i+1]
                    try:
                        g = json.loads(frag)
                        if valid_grid(g):
                            return g
                    except Exception:
                        break
    return None

def changed(train_pair):
    return train_pair["input"] != train_pair["output"]

def complexity(task):
    train = task["train"]
    areas = [len(p["input"]) * len(p["input"][0]) + len(p["output"]) * len(p["output"][0]) for p in train]
    colors = set()
    for p in train:
        for g in (p["input"], p["output"]):
            colors.update(x for r in g for x in r)
    return (max(areas), len(colors), sum(areas), len(train))

def eligible(task):
    if len(task.get("test", [])) != 1 or len(task.get("train", [])) < 2:
        return False
    train = task["train"]
    if not any(changed(p) for p in train):
        return False
    for p in train:
        if not p["input"] or not p["output"]:
            return False
        if len(p["input"]) != len(p["output"]) or len(p["input"][0]) != len(p["output"][0]):
            return False
        if len(p["input"]) * len(p["input"][0]) > 144:
            return False
    return True

def compact_grid(g):
    return json.dumps(g, separators=(",", ":"))

def build_prompt(task):
    parts = [
        "Solve this ARC task. Infer the transformation from every solved example and apply it to the test input.",
        'Return ONLY compact JSON: {"rule":"at most 18 words","grid":[[...]]}. No markdown.'
    ]
    for i,p in enumerate(task["train"],1):
        parts.append(f"E{i} input={compact_grid(p['input'])} output={compact_grid(p['output'])}")
    parts.append("TEST input="+compact_grid(task["test"][0]["input"]))
    return "\n".join(parts)

def refine_prompt(task, previous):
    return build_prompt(task) + "\nPREVIOUS ATTEMPT="+previous.strip() + \
        "\nCritically test that attempt against ALL examples. If it is wrong or underspecified, replace it with a genuinely different rule. Return ONLY the required compact JSON."

def generate(model, tok, prompt, seed, max_new_tokens):
    torch.manual_seed(seed)
    random.seed(seed)
    msgs=[{"role":"user","content":prompt}]
    text=tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs=tok(text, return_tensors="pt")
    with torch.inference_mode():
        out=model.generate(
            **inputs,
            do_sample=True,
            temperature=0.8,
            top_p=0.95,
            max_new_tokens=max_new_tokens,
            pad_token_id=tok.eos_token_id,
        )
    gen=out[0, inputs["input_ids"].shape[1]:]
    return tok.decode(gen, skip_special_tokens=True)

def exact(pred, truth):
    return pred is not None and flatten(pred)==flatten(truth)

def novelty(a,b):
    return a is not None and b is not None and flatten(a)!=flatten(b)

def hamming(a,b):
    if a is None or b is None or len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)):
        return None
    n=sum(len(r) for r in a)
    if not n: return None
    return sum(x!=y for ra,rb in zip(a,b) for x,y in zip(ra,rb))/n

def boot_delta(rows, key_a, key_b, B=5000, seed=20261028):
    rng=random.Random(seed)
    n=len(rows)
    ds=[]
    for _ in range(B):
        sample=[rows[rng.randrange(n)] for _ in range(n)]
        ds.append(sum(r[key_b]-r[key_a] for r in sample)/n)
    ds.sort()
    return [ds[int(.025*B)], ds[int(.975*B)]]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--arc-dir", default="ARC-AGI-2/data/training")
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--tasks", type=int, default=20)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--out", default="proposal_collapse_probe_results.json")
    args=ap.parse_args()

    torch.set_num_threads(max(1, min(4, os.cpu_count() or 2)))
    print("MODEL", args.model, flush=True)
    tok=AutoTokenizer.from_pretrained(args.model)
    model=AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32)
    model.eval()

    pool=[]
    for p in sorted(Path(args.arc_dir).glob("*.json")):
        task=json.loads(p.read_text())
        if eligible(task):
            pool.append((complexity(task), p.stem, task))
    pool.sort(key=lambda x:(x[0],x[1]))
    chosen=pool[:args.tasks]
    print("ELIGIBLE",len(pool),"CHOSEN",[x[1] for x in chosen], flush=True)

    rows=[]
    t0=time.time()
    for idx,(_,tid,task) in enumerate(chosen):
        truth=task["test"][0]["output"]
        base=build_prompt(task)
        seed0=2026102800+idx*17
        seed1=seed0+1

        ind0_text=generate(model,tok,base,seed0,args.max_new_tokens)
        ind1_text=generate(model,tok,base,seed1,args.max_new_tokens)
        seq1_text=generate(model,tok,refine_prompt(task,ind0_text),seed1,args.max_new_tokens)

        ind0=extract_grid(ind0_text)
        ind1=extract_grid(ind1_text)
        seq1=extract_grid(seq1_text)

        row={
            "task_id":tid,
            "ind0_valid":int(ind0 is not None),
            "ind1_valid":int(ind1 is not None),
            "seq1_valid":int(seq1 is not None),
            "ind0_correct":int(exact(ind0,truth)),
            "ind1_correct":int(exact(ind1,truth)),
            "seq1_correct":int(exact(seq1,truth)),
            "ind_novel":int(novelty(ind0,ind1)),
            "seq_novel":int(novelty(ind0,seq1)),
            "ind_hamming":hamming(ind0,ind1),
            "seq_hamming":hamming(ind0,seq1),
            "ind_oracle":int(exact(ind0,truth) or exact(ind1,truth)),
            "seq_oracle":int(exact(ind0,truth) or exact(seq1,truth)),
            "ind0_text":ind0_text,
            "ind1_text":ind1_text,
            "seq1_text":seq1_text,
            "truth":truth,
            "ind0_grid":ind0,
            "ind1_grid":ind1,
            "seq1_grid":seq1,
        }
        rows.append(row)
        print("TASK",idx+1,tid,json.dumps({k:row[k] for k in ["ind0_correct","ind1_correct","seq1_correct","ind_novel","seq_novel","ind_oracle","seq_oracle"]}), flush=True)

    n=len(rows)
    def mean(k): return sum(r[k] for r in rows)/n
    def mean_nonnull(k):
        vals=[r[k] for r in rows if r[k] is not None]
        return sum(vals)/len(vals) if vals else None

    summary={
        "model":args.model,
        "n_tasks":n,
        "task_ids":[r["task_id"] for r in rows],
        "parse_rate":{"ind0":mean("ind0_valid"),"ind1":mean("ind1_valid"),"seq1":mean("seq1_valid")},
        "correct_rate":{"ind0":mean("ind0_correct"),"ind1":mean("ind1_correct"),"seq1":mean("seq1_correct")},
        "novelty_rate":{"independent_second":mean("ind_novel"),"sequential_second":mean("seq_novel"),"delta_seq_minus_ind":mean("seq_novel")-mean("ind_novel")},
        "mean_hamming":{"independent":mean_nonnull("ind_hamming"),"sequential":mean_nonnull("seq_hamming")},
        "archive_oracle":{"independent":mean("ind_oracle"),"sequential":mean("seq_oracle"),"delta_seq_minus_ind":mean("seq_oracle")-mean("ind_oracle")},
        "paired_counts":{
            "novel_ind_only":sum(r["ind_novel"] and not r["seq_novel"] for r in rows),
            "novel_seq_only":sum(r["seq_novel"] and not r["ind_novel"] for r in rows),
            "oracle_ind_only":sum(r["ind_oracle"] and not r["seq_oracle"] for r in rows),
            "oracle_seq_only":sum(r["seq_oracle"] and not r["ind_oracle"] for r in rows),
        },
        "bootstrap95_delta":{
            "novelty_seq_minus_ind":boot_delta(rows,"ind_novel","seq_novel"),
            "oracle_seq_minus_ind":boot_delta(rows,"ind_oracle","seq_oracle"),
        },
        "elapsed_s":time.time()-t0,
        "selection_rule":"20 simplest eligible ARC-AGI-2 public training tasks; selection uses demos/test-input metadata only, never test outputs",
        "comparison":"Attempt 0 identical. Independent attempt 1 sees base prompt only; sequential attempt 1 sees the exact attempt-0 response plus a refinement instruction. Same second-attempt seed and decoding parameters. All candidates archived."
    }
    result={"summary":summary,"rows":rows}
    Path(args.out).write_text(json.dumps(result,indent=2))
    print("FINAL_SUMMARY="+json.dumps(summary,sort_keys=True), flush=True)

if __name__=="__main__":
    main()
