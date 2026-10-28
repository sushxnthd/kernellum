import os, signal, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import identifiability_kill_test_train_shard as core

TIMEOUT=float(os.environ.get("CALL_TIMEOUT_S","2.0"))

class CallTimeout(Exception):
    pass

def _handler(signum, frame):
    raise CallTimeout()

def timed_safe_run(fn,obj,x,tv):
    old=signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM,_handler)
        signal.setitimer(signal.ITIMER_REAL,TIMEOUT)
        try:
            y=fn(obj,core.arr(x).copy(),tv)
            a=core.arr(y)
            if a.ndim!=2 or a.size==0 or max(a.shape)>60:
                return None
            return a
        except Exception:
            return None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old)

core.safe_run=timed_safe_run

if __name__=="__main__":
    print("EXECUTION_VALIDITY_TIMEOUT_S",TIMEOUT,flush=True)
    core.main()
