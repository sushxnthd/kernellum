#!/usr/bin/env python3
import ast, json, hashlib, os, re, sys
from pathlib import Path

ALLOWED_IMPORT_ROOTS={"numpy","scipy","cv2","math","collections","itertools","functools","heapq","bisect","statistics"}
BANNED_NAMES={
 "open","exec","eval","compile","input","__import__","globals","locals","vars",
 "breakpoint","help","quit","exit"
}
BANNED_ROOTS={
 "os","sys","subprocess","socket","pathlib","shutil","requests","urllib","http",
 "ftplib","multiprocessing","threading","ctypes","resource","signal","pickle","marshal"
}

def safety_check(code):
    try:tree=ast.parse(code)
    except Exception as e:return False,f"parse:{e}"
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):
            for a in n.names:
                root=a.name.split(".")[0]
                if root not in ALLOWED_IMPORT_ROOTS:
                    return False,f"import:{root}"
        elif isinstance(n,ast.ImportFrom):
            if not n.module:return False,"relative_import"
            root=n.module.split(".")[0]
            if root not in ALLOWED_IMPORT_ROOTS:
                return False,f"importfrom:{root}"
        elif isinstance(n,ast.Name):
            if n.id in BANNED_NAMES or n.id in BANNED_ROOTS:
                return False,f"name:{n.id}"
        elif isinstance(n,ast.Attribute):
            if n.attr.startswith("__"):
                return False,f"dunder:{n.attr}"
            if isinstance(n.value,ast.Name) and n.value.id in BANNED_ROOTS:
                return False,f"rootattr:{n.value.id}.{n.attr}"
    return True,"ok"

def main(inp,out):
    d=json.load(open(inp))
    kept={};stats={"total":0,"safe":0,"unsafe":0,"reasons":{}}
    for case,recs in d.items():
        kk=[]
        for r in recs:
            stats["total"]+=1
            ok,reason=safety_check(r["code"])
            r["static_safe"]=ok;r["static_safety_reason"]=reason
            if ok:
                stats["safe"]+=1;kk.append(r)
            else:
                stats["unsafe"]+=1;stats["reasons"][reason]=stats["reasons"].get(reason,0)+1
        kept[case]=kk
    json.dump({"stats":stats,"cases":kept},open(out,"w"),indent=2)
    print("SAFETY_STATS="+json.dumps(stats,sort_keys=True))
    counts={k:len(v) for k,v in kept.items()}
    print("SAFE_CASES_GE3",sum(n>=3 for n in counts.values()))
    print("SAFE_DISTINCT_TASKS_GE3",len({k.split(":")[0] for k,n in counts.items() if n>=3}))

if __name__=="__main__":
    main(sys.argv[1],sys.argv[2])
