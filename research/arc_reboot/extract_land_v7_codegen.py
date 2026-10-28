import argparse, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

FILE_RE=re.compile(r"([a-f0-9]{8})_(\d+)_step_([A-Za-z0-9_]+)\.json$")

def normalize_code(code):
    code=code.replace("\r\n","\n").replace("\r","\n")
    lines=[ln.rstrip() for ln in code.strip().splitlines()]
    while lines and lines[-1].strip().startswith(chr(96)*3):
        lines.pop()
    return "\n".join(lines).strip()+"\n"

def extract_code(resp):
    if not isinstance(resp,str) or "def solver" not in resp:
        return None
    s=resp.strip()
    if s.startswith("{") and s.endswith("}"):
        try:
            d=json.loads(s)
            if isinstance(d,dict):
                for k in ("python","code","solution","content"):
                    v=d.get(k)
                    if isinstance(v,str) and "def solver" in v:
                        q=extract_code(v)
                        if q:
                            return q
        except Exception:
            pass
    area=s.split("### FINAL SOLUTION ###")[-1] if "### FINAL SOLUTION ###" in s else s
    fence=chr(96)*3
    blocks=re.findall(re.escape(fence)+r"(?:python)?\s*(.*?)"+re.escape(fence),area,re.S|re.I)
    for b in reversed(blocks):
        if "def solver" in b:
            return normalize_code(b[b.find("def solver"):])
    i=area.rfind("def solver")
    base=area
    if i<0:
        i=s.rfind("def solver")
        base=s
    if i>=0:
        return normalize_code(base[i:])
    return None

def walk(obj,path=()):
    if isinstance(obj,dict):
        if "Full raw LLM response" in obj:
            yield path,obj
        for k,v in obj.items():
            if isinstance(v,(dict,list)):
                yield from walk(v,path+(str(k),))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            if isinstance(v,(dict,list)):
                yield from walk(v,path+(str(i),))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--logs",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=Path(args.logs)
    outp=Path(args.out)
    seen=set()
    rows=[]
    stats=Counter()
    per_case=defaultdict(int)
    files=sorted(root.rglob("*.json"))
    stats["json_files"]=len(files)
    for fp in files:
        m=FILE_RE.search(fp.name)
        if not m:
            continue
        task_id,test_s,step=m.groups()
        test_index=int(test_s)
        try:
            data=json.loads(fp.read_text(errors="replace"))
        except Exception:
            stats["json_parse_fail"]+=1
            continue
        for path,node in walk(data):
            path_s="/".join(path)
            raw=node.get("Full raw LLM response","")
            is_codegen=("codegen" in path_s.lower()) or ("def solver" in raw)
            if not is_codegen:
                continue
            stats["call_like_codegen"]+=1
            code=extract_code(raw)
            if not code:
                stats["no_code"]+=1
                continue
            v=node.get("verification_details") or {}
            vstatus=v.get("status") if isinstance(v,dict) else None
            if vstatus=="PASS":
                stats["metadata_verified_pass"]+=1
            sha=hashlib.sha256(code.encode()).hexdigest()
            key=(task_id,test_index,sha)
            if key in seen:
                stats["duplicate_code_same_case"]+=1
                continue
            seen.add(key)
            row={
                "task_id":task_id,
                "test_index":test_index,
                "step":step,
                "source_file":str(fp.relative_to(root)),
                "call_path":path_s,
                "code_sha256":sha,
                "code":code,
                "normalized_source_chars":len(code),
                "verification_status":vstatus,
                "land_is_correct":node.get("is_correct"),
                "land_extracted_grid":node.get("Extracted grid"),
                "requested_model":node.get("requested_model"),
                "actual_model":node.get("actual_model"),
                "cost":node.get("total_cost"),
            }
            rows.append(row)
            per_case[(task_id,test_index)]+=1
    rows.sort(key=lambda r:(r["task_id"],r["test_index"],r["code_sha256"]))
    with outp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r,separators=(",",":"))+"\\n")
    counts=sorted(per_case.values())
    summary={
        **stats,
        "unique_candidates":len(rows),
        "cases_with_code":len(per_case),
        "cases_ge3_code":sum(v>=3 for v in per_case.values()),
        "max_candidates_case":max(counts) if counts else 0,
        "median_candidates_case":counts[len(counts)//2] if counts else 0,
    }
    print("EXTRACT_SUMMARY="+json.dumps(summary,sort_keys=True))
    top=sorted(per_case.items(),key=lambda kv:(-kv[1],kv[0]))[:30]
    print("TOP_CASES="+json.dumps([{"task":k[0],"test":k[1],"n":v} for k,v in top]))
    Path(str(outp)+".summary.json").write_text(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
