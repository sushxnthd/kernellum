#!/usr/bin/env python3
import builtins, json, multiprocessing as mp, signal, sys, traceback
from pathlib import Path
import numpy as np

ALLOWED_IMPORTS={"numpy","scipy","cv2","math","collections","itertools","functools","heapq","bisect","statistics"}
REMOVED_BUILTINS={"open","eval","exec","compile","input","breakpoint","help","quit","exit"}

class CallTimeout(BaseException):
    pass

def _timeout(signum,frame):
    raise CallTimeout()

_real_import=builtins.__import__
def safe_import(name,globals=None,locals=None,fromlist=(),level=0):
    root=name.split(".")[0]
    if root not in ALLOWED_IMPORTS:
        raise ImportError(f"blocked import {root}")
    return _real_import(name,globals,locals,fromlist,level)

def safe_builtins():
    d={k:v for k,v in builtins.__dict__.items() if k not in REMOVED_BUILTINS}
    d["__import__"]=safe_import
    return d

def canon_output(x):
    try:
        a=np.asarray(x)
        if a.ndim!=2 or a.size==0 or max(a.shape)>30:return None
        if not np.issubdtype(a.dtype,np.number):return None
        if not np.all(np.isfinite(a)):return None
        if not np.all(np.equal(a,np.floor(a))):return None
        a=a.astype(int)
        if np.any(a<0) or np.any(a>9):return None
        return a.tolist()
    except BaseException:
        return None

def child(code,grids,q):
    signal.signal(signal.SIGALRM,_timeout)
    ns={"__builtins__":safe_builtins()}
    try:
        signal.setitimer(signal.ITIMER_REAL,3.0)
        exec(compile(code,"<candidate>","exec"),ns,ns)
        signal.setitimer(signal.ITIMER_REAL,0)
        fn=ns.get("solver")
        if not callable(fn):
            q.put({"status":"no_solver","outputs":[]});return
        outs=[]
        for g in grids:
            try:
                signal.setitimer(signal.ITIMER_REAL,2.0)
                y=fn(np.asarray(g,dtype=int).copy())
                signal.setitimer(signal.ITIMER_REAL,0)
                outs.append(canon_output(y))
            except CallTimeout:
                signal.setitimer(signal.ITIMER_REAL,0);outs.append(None)
            except BaseException:
                signal.setitimer(signal.ITIMER_REAL,0);outs.append(None)
        q.put({"status":"ok","outputs":outs})
    except CallTimeout:
        q.put({"status":"exec_timeout","outputs":[]})
    except BaseException as e:
        q.put({"status":"exec_error","error":repr(e),"outputs":[]})

def run_one(code,grids):
    ctx=mp.get_context("fork")
    q=ctx.Queue()
    p=ctx.Process(target=child,args=(code,grids,q))
    p.start();p.join(70)
    if p.is_alive():
        p.terminate();p.join(2)
        return {"status":"process_timeout","outputs":[]}
    try:return q.get_nowait()
    except Exception:return {"status":"no_result","outputs":[]}

def main():
    bundle=json.loads(Path(sys.argv[1]).read_text())
    grids=bundle["grids"]
    out={}
    for c in bundle["candidates"]:
        out[c["source_id"]]=run_one(c["code"],grids)
    Path(sys.argv[2]).write_text(json.dumps(out))
    print("DONE",len(out),flush=True)

if __name__=="__main__":
    main()
