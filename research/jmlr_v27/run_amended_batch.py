#!/usr/bin/env python3
"""Run/resume frozen Tier-B cells across available GPUs, skipping completed cells."""
from __future__ import annotations
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from generate_amended_manifest import build

def completed(ledger_root,run_id):
    p=ledger_root/run_id/"ledger.json"
    if not p.exists():return False
    try:return json.loads(p.read_text()).get("status")=="complete"
    except Exception:return False

def priority(c):
    # Source trajectories first so Tier-A evidence arrives before all downstream cells.
    source = (c["benchmark"]=="nyuv2" and c["method"]=="ls" and c["arm"]=="coarse") or (c["benchmark"]=="qm9" and c["arm"]=="coarse")
    arm_order={"coarse":0,"canonicalized":1,"exposed":2}
    return (0 if source else 1,0 if c["benchmark"]=="nyuv2" else 1,arm_order[c["arm"]],c["method"],c["seed"],c.get("parent",0))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fairgrad-root",type=Path,required=True)
    ap.add_argument("--nyuv2-data",type=Path,required=True)
    ap.add_argument("--ledger-root",type=Path,required=True)
    ap.add_argument("--gpus",default="")
    ap.add_argument("--max-wall-hours",type=float,default=10.0)
    ap.add_argument("--run-ids",nargs="*")
    args=ap.parse_args()
    cells,_=build()
    byid={c["run_id"]:c for c in cells}
    if args.run_ids:
        missing=[x for x in args.run_ids if x not in byid]
        if missing:raise SystemExit(f"unknown frozen run IDs: {missing}")
        queue=[byid[x] for x in args.run_ids]
    else: queue=sorted(cells,key=priority)
    ledger=args.ledger_root.resolve();ledger.mkdir(parents=True,exist_ok=True)
    queue=[c for c in queue if not completed(ledger,c["run_id"])]
    if args.gpus.strip():
        gpus=[int(x) for x in args.gpus.split(",")]
    else:
        try:
            import torch; gpus=list(range(torch.cuda.device_count()))
        except Exception:gpus=[]
    if not gpus:raise SystemExit("no GPUs detected")
    deadline=time.time()+args.max_wall_hours*3600
    active={}
    failures=[]
    def launch(cell,gpu):
        cmd=[sys.executable,str(HERE/"run_amended_cell.py"),"--run-id",cell["run_id"],"--fairgrad-root",str(args.fairgrad_root.resolve()),"--nyuv2-data",str(args.nyuv2_data.resolve()),"--ledger-root",str(ledger),"--gpu",str(gpu)]
        log=(ledger/cell["run_id"]/"batch_launcher.log");log.parent.mkdir(parents=True,exist_ok=True)
        f=log.open("a",encoding="utf-8")
        p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,text=True)
        active[gpu]=(p,cell,f,cmd)
        print(f"LAUNCH gpu={gpu} pid={p.pid} {cell['run_id']}",flush=True)
    while queue or active:
        for gpu in gpus:
            if gpu not in active and queue and time.time()<deadline-900:
                launch(queue.pop(0),gpu)
        time.sleep(5)
        for gpu,(p,cell,f,cmd) in list(active.items()):
            rc=p.poll()
            if rc is not None:
                f.close();del active[gpu]
                print(f"DONE rc={rc} gpu={gpu} {cell['run_id']}",flush=True)
                if rc!=0:failures.append({"run_id":cell["run_id"],"returncode":rc})
        if time.time()>=deadline:
            print("Wall-time guard reached; terminating active launchers. Last completed epoch checkpoints are retained.",flush=True)
            for gpu,(p,cell,f,cmd) in list(active.items()):
                try:p.terminate()
                except Exception:pass
            time.sleep(15)
            for gpu,(p,cell,f,cmd) in list(active.items()):
                if p.poll() is None:
                    try:p.kill()
                    except Exception:pass
                f.close()
            active.clear()
            break
    summary={"remaining_frozen_cells":sum(not completed(ledger,c["run_id"]) for c in cells),"failures_this_invocation":failures,"ledger_root":str(ledger)}
    (ledger/"batch_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
