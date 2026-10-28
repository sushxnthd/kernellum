#!/usr/bin/env python3
import ast, hashlib, json, os, re, sys, textwrap
from pathlib import Path

CODE_BLOCK_RE=re.compile(r"```python\s*(.*?)```",re.S)

def extract_solver(raw):
    if not raw:return None
    code=None
    if "### FINAL SOLUTION ###" in raw:
        tail=raw.split("### FINAL SOLUTION ###")[-1]
        blocks=CODE_BLOCK_RE.findall(tail)
        for b in reversed(blocks):
            if "def solver" in b:
                code=b.strip();break
    if code is None:
        for b in reversed(CODE_BLOCK_RE.findall(raw)):
            if "def solver" in b:
                code=b.strip();break
    if code is None and "def solver" in raw:
        lines=raw.splitlines()
        i=next((i for i,l in enumerate(lines) if "def solver" in l),None)
        if i is not None: code="\n".join(lines[i:])
    if not code or "def solver" not in code:return None
    try:
        tree=ast.parse(code)
    except Exception:return None
    if not any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="solver" for n in ast.walk(tree)):
        return None
    return code

def normalize_source(code):
    try:
        tree=ast.parse(code)
        return ast.unparse(tree)
    except Exception:
        return "\n".join(l.rstrip() for l in code.strip().splitlines())

def source_id(code):
    n=normalize_source(code)
    return hashlib.sha256(n.encode()).hexdigest()

def find_calls(obj,path=()):
    if isinstance(obj,dict):
        # Land call object
        if "Full raw LLM response" in obj:
            yield path,obj
        for k,v in obj.items():
            yield from find_calls(v,path+(str(k),))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from find_calls(v,path+(str(i),))

def task_key_from_name(name):
    m=re.search(r"([a-f0-9]{8})_(\d+)_step_",name)
    if not m:return None
    return m.group(1),int(m.group(2))

def extract_candidates(log_root,out_path):
    by_case={}
    files=list(Path(log_root).rglob("*.json"))
    for p in files:
        key=task_key_from_name(p.name)
        if not key:continue
        try:data=json.loads(p.read_text(errors="replace"))
        except Exception:continue
        for path,call in find_calls(data):
            path_s="/".join(path)
            # Primary candidate pool: codegen-like calls only.
            if "codegen" not in path_s.lower() and "codegen" not in p.name.lower():
                continue
            vd=call.get("verification_details") or {}
            status=vd.get("status")
            if status!="PASS":
                continue
            raw=call.get("Full raw LLM response","")
            code=extract_solver(raw)
            if not code:continue
            sid=source_id(code)
            rec={
                "task_id":key[0],"test_index_1based":key[1],
                "source_id":sid,"code":code,
                "source_chars":len(normalize_source(code)),
                "file":str(p.relative_to(log_root)),
                "path":path_s,
                "model":call.get("model"),
                "verification_status":status,
                "released_is_correct":call.get("is_correct"),
                "released_extracted_grid":call.get("Extracted grid")
            }
            case=f"{key[0]}:{key[1]}"
            by_case.setdefault(case,{})[sid]=rec
    out={k:list(v.values()) for k,v in by_case.items()}
    Path(out_path).write_text(json.dumps(out,indent=2))
    print("CASES",len(out))
    print("CANDIDATES",sum(map(len,out.values())))
    counts=sorted(((k,len(v)) for k,v in out.items()),key=lambda z:-z[1])
    print("TOP_CASES",json.dumps(counts[:40]))

if __name__=="__main__":
    extract_candidates(Path(sys.argv[1]),sys.argv[2])
