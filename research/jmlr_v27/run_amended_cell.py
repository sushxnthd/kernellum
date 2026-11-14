#!/usr/bin/env python3
"""Execute one frozen v27 amended Tier-B cell with an auditable ledger."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from generate_amended_manifest import build

PINNED = "b58bce810e57288f7bf2c4c9effb7133b856739a"

def run_capture(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout

def sha256(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def hardware_snapshot():
    snap={"platform":platform.platform(),"python":sys.version}
    code,out=run_capture(["nvidia-smi","--query-gpu=name,memory.total,driver_version","--format=csv,noheader"])
    snap["nvidia_smi_rc"]=code
    snap["gpus"]=[x.strip() for x in out.splitlines() if x.strip()] if code==0 else []
    return snap

def find_cell(run_id):
    cells,tier_a=build()
    matches=[c for c in cells if c["run_id"]==run_id]
    if len(matches)!=1:
        raise SystemExit(f"run_id must match exactly one frozen cell; got {len(matches)}")
    return matches[0], tier_a

def ensure_pinned_and_patched(fairgrad_root: Path):
    code,out=run_capture(["git","rev-parse","HEAD"],cwd=fairgrad_root)
    if code or out.strip()!=PINNED:
        raise RuntimeError(f"FairGrad revision mismatch: got {out.strip()!r}, expected {PINNED}")
    ny=fairgrad_root/"experiments/nyuv2/trainer.py"
    qm=fairgrad_root/"experiments/quantum_chemistry/trainer.py"
    if "--jmlr-arm" not in ny.read_text() or "--jmlr-arm" not in qm.read_text():
        subprocess.run([sys.executable,str(HERE/"apply_fairgrad_v27_patch.py"),str(fairgrad_root)],check=True)
    for d in (ny.parent,qm.parent):
        (d/"save").mkdir(exist_ok=True)
        (d/"trainlogs").mkdir(exist_ok=True)

def build_command(cell, fairgrad_root, gpu, nyuv2_data, qm9_data, audit_epochs, checkpoint_path, resume_from=None):
    bench=cell["benchmark"]
    exp=fairgrad_root/"experiments"/("nyuv2" if bench=="nyuv2" else "quantum_chemistry")
    cmd=[sys.executable,"-u","trainer.py",
         "--method",cell["method"],
         "--seed",str(cell["seed"]),
         "--gpu",str(gpu),
         "--n-epochs",str(cell["epochs"]),
         "--batch-size",str(cell["batch_size"]),
         "--lr",str(cell["lr"]),
         "--nashmtl-optim-niter","20",
         "--update-weights-every","1",
         "--max_norm","1.0",
         "--c","0.4",
         "--alpha","2.0",
         "--jmlr-arm",cell["arm"],
         "--jmlr-parent",str(cell["parent"]),
         "--jmlr-k",str(cell["k"]),
         "--jmlr-run-id",cell["run_id"]]
    if audit_epochs:
        cmd += ["--jmlr-audit-epochs", ",".join(str(x) for x in audit_epochs)]
    cmd += ["--jmlr-checkpoint-path", str(checkpoint_path)]
    if resume_from is not None:
        cmd += ["--jmlr-resume-from", str(resume_from)]
    if cell.get("canonical_mgda"):
        cmd.append("--jmlr-canonical-mgda")
    if bench=="nyuv2":
        cmd += ["--model","mtan","--apply-augmentation","True"]
        if nyuv2_data:
            cmd += ["--data-path",str(Path(nyuv2_data).resolve())]
    else:
        cmd += ["--scale-y","True"]
        if qm9_data:
            cmd += ["--data-path",str(Path(qm9_data).resolve())]
    return exp,cmd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--fairgrad-root",type=Path,required=True)
    ap.add_argument("--gpu",type=int,default=0)
    ap.add_argument("--nyuv2-data")
    ap.add_argument("--qm9-data")
    ap.add_argument("--ledger-root",type=Path,default=REPO/"jmlr_v27_results")
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()

    cell,tier_a=find_cell(args.run_id)
    fairgrad=args.fairgrad_root.resolve()
    ensure_pinned_and_patched(fairgrad)

    ledger_dir=args.ledger_root.resolve()/cell["run_id"]
    ledger_dir.mkdir(parents=True,exist_ok=True)
    checkpoint_path=ledger_dir/"resume.pt"
    resume_from=checkpoint_path if checkpoint_path.exists() else None

    source_spec=tier_a[cell["benchmark"]]
    audit_epochs=source_spec["audit_epochs"] if cell["run_id"] in source_spec["source_runs"] else []
    exp,cmd=build_command(
        cell,fairgrad,args.gpu,args.nyuv2_data,args.qm9_data,audit_epochs,
        checkpoint_path=checkpoint_path,resume_from=resume_from,
    )

    if cell["benchmark"]=="nyuv2":
        data=Path(args.nyuv2_data).resolve() if args.nyuv2_data else exp/"dataset"
        if not data.exists() and not args.dry_run:
            raise FileNotFoundError(f"NYUv2 data path missing: {data}")

    prior_ledger={}
    prior_ledger_path=ledger_dir/"ledger.json"
    if prior_ledger_path.exists():
        try:
            prior_ledger=json.loads(prior_ledger_path.read_text())
        except Exception:
            prior_ledger={}
    attempt=int(prior_ledger.get("attempt",0))+1
    ledger={
        "schema":"jmlr-v27-cell-ledger-v1",
        "cell":cell,
        "fairgrad_revision":PINNED,
        "command":cmd,
        "cwd":str(exp),
        "hardware":hardware_snapshot(),
        "tier_a_audit_epochs":audit_epochs,
        "checkpoint_path":str(checkpoint_path),
        "resumed":resume_from is not None,
        "resume_from":str(resume_from) if resume_from is not None else None,
        "attempt":attempt,
        "started_unix":time.time(),
        "status":"dry-run" if args.dry_run else "running",
    }
    (ledger_dir/"ledger.json").write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n")
    if args.dry_run:
        print(json.dumps(ledger,indent=2,sort_keys=True))
        return

    log_path=ledger_dir/"stdout_stderr.log"
    with log_path.open("a",encoding="utf-8") as log:
        log.write(f"\n===== ATTEMPT {attempt} START {time.time():.6f} resumed={resume_from is not None} =====\n")
        log.flush()
        proc=subprocess.run(cmd,cwd=exp,stdout=log,stderr=subprocess.STDOUT,text=True)
        log.write(f"\n===== ATTEMPT {attempt} END {time.time():.6f} returncode={proc.returncode} =====\n")

    ledger["finished_unix"]=time.time()
    ledger["checkpoint_exists_after_run"]=checkpoint_path.exists()
    if checkpoint_path.exists():
        ledger["checkpoint_sha256"]=sha256(checkpoint_path)
        ledger["checkpoint_bytes"]=checkpoint_path.stat().st_size
    ledger["returncode"]=proc.returncode
    save_dir=exp/"save"
    artifacts=[]
    for path in sorted(save_dir.glob(f"*{cell['run_id']}*")):
        dest=ledger_dir/path.name
        shutil.copy2(path,dest)
        artifacts.append({"name":dest.name,"bytes":dest.stat().st_size,"sha256":sha256(dest)})
    ledger["artifacts"]=artifacts
    has_stats=any(x["name"].endswith(".stats") for x in artifacts)
    has_final=any(x["name"].endswith(".final.pt") for x in artifacts)
    audit_count=sum(".audit.ep" in x["name"] for x in artifacts)
    audit_ok=(not audit_epochs) or audit_count==len(audit_epochs)
    if proc.returncode==0 and has_stats and has_final and audit_ok:
        ledger["status"]="complete"
    else:
        ledger["status"]="failed"
        if proc.returncode==0:
            ledger["integrity_error"]=f"successful process missing required artifacts: stats={has_stats}, final={has_final}, audits={audit_count}/{len(audit_epochs)}"
    (ledger_dir/"ledger.json").write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"run_id":cell["run_id"],"status":ledger["status"],"returncode":proc.returncode,"artifacts":artifacts},indent=2))
    if ledger["status"]!="complete":
        raise SystemExit(1)

if __name__=="__main__":
    main()
