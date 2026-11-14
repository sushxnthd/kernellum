#!/usr/bin/env python3
"""Runtime-only probes. Outputs are never eligible benchmark evidence."""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
PINNED="b58bce810e57288f7bf2c4c9effb7133b856739a"

def nvidia():
    try:
        p=subprocess.run(["nvidia-smi","--query-gpu=index,name,memory.total","--format=csv,noheader"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        return [x for x in p.stdout.splitlines() if x.strip()]
    except FileNotFoundError:return []

def run_probe(name,cmd,cwd,outdir):
    log=outdir/f"{name}.log"
    t=time.time()
    with log.open("w",encoding="utf-8") as f:
        p=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,text=True)
    dt=time.time()-t
    return {"name":name,"returncode":p.returncode,"wall_seconds":dt,"log":str(log),"command":cmd}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fairgrad-root",type=Path,required=True)
    ap.add_argument("--nyuv2-data",type=Path)
    ap.add_argument("--gpu",type=int,default=0)
    ap.add_argument("--output-root",type=Path,default=Path("/kaggle/working/runtime_probes") if Path("/kaggle/working").exists() else Path("runtime_probes"))
    args=ap.parse_args()
    fg=args.fairgrad_root.resolve(); out=args.output_root.resolve(); out.mkdir(parents=True,exist_ok=True)
    py=sys.executable; common=["--seed","0","--gpu",str(args.gpu),"--n-epochs","1","--nashmtl-optim-niter","20","--update-weights-every","1","--max_norm","1.0","--c","0.4","--alpha","2.0","--jmlr-arm","coarse","--jmlr-parent","0","--jmlr-k","4"]
    probes=[]
    qm=fg/"experiments/quantum_chemistry"
    probes.append(run_probe("qm9_nashmtl_1epoch",
        [py,"-u","trainer.py","--method","nashmtl","--batch-size","120","--lr","0.001","--scale-y","True","--jmlr-run-id","RUNTIME_PROBE_QM9_NASH",*common],qm,out))
    if args.nyuv2_data:
        ny=fg/"experiments/nyuv2"
        for method,canon in [("ls",False),("mgda",True),("nashmtl",False)]:
            cmd=[py,"-u","trainer.py","--method",method,"--batch-size","2","--lr","0.0001","--model","mtan","--apply-augmentation","True","--data-path",str(args.nyuv2_data.resolve()),"--jmlr-run-id",f"RUNTIME_PROBE_NYU_{method.upper()}",*common]
            if canon: cmd.append("--jmlr-canonical-mgda")
            probes.append(run_probe(f"nyuv2_{method}_1epoch",cmd,ny,out))
    record={"schema":"jmlr-v27-runtime-probe-v1","eligible_as_scientific_outcome":False,"fairgrad_revision":PINNED,"gpus":nvidia(),"probes":probes}
    (out/"runtime_probe_summary.json").write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
    print(json.dumps(record,indent=2,sort_keys=True))
    if any(x["returncode"] for x in probes): raise SystemExit("one or more runtime probes failed")
    print("PASS: runtime-only probes complete; DO NOT analyze their metrics as benchmark outcomes")

if __name__=="__main__":
    main()
