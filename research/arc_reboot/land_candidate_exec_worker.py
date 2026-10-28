import contextlib, io, json, os, resource, signal, sys, traceback
import numpy as np

MAX_DIM=30
PER_GRID_SECONDS=float(os.environ.get("PER_GRID_SECONDS","2.0"))

class GridTimeout(Exception):
    pass

def _alarm(signum,frame):
    raise GridTimeout()

def canonical_output(y):
    try:
        a=np.asarray(y)
        if a.ndim!=2 or a.size==0 or max(a.shape)>MAX_DIM:
            return None
        if not np.issubdtype(a.dtype,np.number):
            return None
        if not np.all(np.isfinite(a)):
            return None
        if not np.all(a==np.rint(a)):
            return None
        a=np.rint(a).astype(int)
        if np.any(a<0) or np.any(a>9):
            return None
        return a.tolist()
    except BaseException:
        return None

def one(code,grid):
    old=signal.signal(signal.SIGALRM,_alarm)
    signal.setitimer(signal.ITIMER_REAL,PER_GRID_SECONDS)
    try:
        ns={"np":np,"numpy":np}
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(code,"<candidate>","exec"),ns,ns)
            fn=ns.get("solver")
            if not callable(fn):
                return None
            y=fn(np.asarray(grid,dtype=int).copy())
        return canonical_output(y)
    except BaseException:
        return None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old)

def main():
    try:
        # Hard caps inside the already network-disabled outer container.
        resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
        resource.setrlimit(resource.RLIMIT_NPROC,(32,32))
    except Exception:
        pass
    payload=json.load(sys.stdin)
    code=payload["code"]
    grids=payload["grids"]
    out=[one(code,g) for g in grids]
    sys.stdout.write(json.dumps({"outputs":out},separators=(",",":")))

if __name__=="__main__":
    main()
