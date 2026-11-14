#!/usr/bin/env python3
"""Bootstrap a Kaggle/L4-style environment for JMLR Project Zero v27."""
from __future__ import annotations
import argparse, importlib, json, os, platform, shutil, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
PINNED="b58bce810e57288f7bf2c4c9effb7133b856739a"

def run(cmd,cwd=None,check=True):
    print("+"," ".join(map(str,cmd)),flush=True)
    return subprocess.run(list(map(str,cmd)),cwd=cwd,check=check,text=True)

def capture(cmd,cwd=None):
    try:
        p=subprocess.run(list(map(str,cmd)),cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        return p.returncode,p.stdout
    except FileNotFoundError as e:
        return 127,repr(e)

def ensure_modules():
    need=[]
    for mod,pkg in [("cvxpy","cvxpy"),("ecos","ecos"),("torch_geometric","torch-geometric"),("wandb","wandb")]:
        try: importlib.import_module(mod)
        except Exception: need.append(pkg)
    if need:
        run([sys.executable,"-m","pip","install","-q",*need])

def ensure_fairgrad(root:Path):
    if not root.exists():
        run(["git","clone","-q","https://github.com/OptMN-Lab/FairGrad.git",str(root)])
    code,out=capture(["git","rev-parse","HEAD"],cwd=root)
    if code or out.strip()!=PINNED:
        run(["git","fetch","-q","origin"],cwd=root)
        run(["git","checkout","-q",PINNED],cwd=root)
    code,out=capture(["git","rev-parse","HEAD"],cwd=root)
    if code or out.strip()!=PINNED:
        raise RuntimeError(f"could not lock FairGrad to {PINNED}: {out}")
    run([sys.executable,"-m","pip","install","-q","-e",str(root),"--no-deps"])
    run([sys.executable,str(HERE/"apply_fairgrad_v27_patch.py"),str(root)])
    return root

def validate_nyuv2(root:Path):
    for split in ("train","val"):
        for sub in ("image","label","depth","normal"):
            p=root/split/sub
            if not p.is_dir() or not any(p.glob("*.npy")):
                return False
    return True

def ensure_nyuv2(root:Path,download:bool):
    if validate_nyuv2(root): return root
    if not download: return None
    root.parent.mkdir(parents=True,exist_ok=True)
    archive=root.parent/"nyuv2.zip"
    url="https://www.dropbox.com/s/p2nn02wijg7peiy/nyuv2.zip?dl=1"
    if not archive.exists():
        print(f"Downloading NYUv2 preprocessing archive to {archive}",flush=True)
        urllib.request.urlretrieve(url,archive)
    extract=root.parent/"nyuv2_extract"
    if extract.exists(): shutil.rmtree(extract)
    extract.mkdir()
    with zipfile.ZipFile(archive) as z: z.extractall(extract)
    candidates=[p for p in [extract,*extract.rglob("*")] if p.is_dir() and validate_nyuv2(p)]
    if not candidates:
        raise RuntimeError("NYUv2 archive extracted but expected train/val structure was not found")
    src=min(candidates,key=lambda p:len(p.parts))
    if root.exists(): shutil.rmtree(root)
    shutil.move(str(src),str(root))
    if not validate_nyuv2(root): raise RuntimeError("NYUv2 validation failed after move")
    return root

def env_snapshot(fairgrad,ny):
    import torch, numpy, scipy, cvxpy
    try:
        import torch_geometric
        pyg=torch_geometric.__version__
    except Exception: pyg=None
    try:
        import ecos
        ecos_v=getattr(ecos,"__version__",None)
    except Exception: ecos_v=None
    rc,gpus=capture(["nvidia-smi","--query-gpu=index,name,memory.total,driver_version","--format=csv,noheader"])
    return {
        "timestamp_unix":time.time(),"platform":platform.platform(),"python":sys.version,
        "torch":torch.__version__,"torch_cuda":torch.version.cuda,
        "cuda_available":torch.cuda.is_available(),"cuda_device_count":torch.cuda.device_count(),
        "numpy":numpy.__version__,"scipy":scipy.__version__,"cvxpy":cvxpy.__version__,
        "ecos":ecos_v,"torch_geometric":pyg,
        "nvidia_smi_rc":rc,"gpus":[x for x in gpus.splitlines() if x.strip()] if rc==0 else [],
        "fairgrad_revision":PINNED,"fairgrad_root":str(fairgrad),
        "nyuv2_root":str(ny) if ny else None,
    }

def preflight(fairgrad):
    tests=[
        [sys.executable,str(HERE/"test_atomicity_intervention.py")],
        [sys.executable,str(HERE/"generate_amended_manifest.py")],
        [sys.executable,str(HERE/"test_amended_manifest.py")],
    ]
    for cmd in tests: run(cmd,cwd=HERE)
    env=os.environ.copy()
    env["PYTHONPATH"]=str(fairgrad)+os.pathsep+str(REPO)+os.pathsep+env.get("PYTHONPATH","")
    for script,args in [
        ("smoke_weightmethods.py",[]),
        ("test_tier_a_gram.py",[str(fairgrad)]),
        ("test_nash_resume_state.py",[]),
    ]:
        print("+",script,*args,flush=True)
        subprocess.run([sys.executable,str(HERE/script),*args],cwd=fairgrad,env=env,check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--work-root",type=Path,default=Path("/kaggle/working") if Path("/kaggle/working").exists() else REPO.parent)
    ap.add_argument("--fairgrad-root",type=Path)
    ap.add_argument("--nyuv2-root",type=Path)
    ap.add_argument("--download-nyuv2",action="store_true")
    args=ap.parse_args()
    work=args.work_root.resolve(); work.mkdir(parents=True,exist_ok=True)
    fairgrad=(args.fairgrad_root or work/"fairgrad_v27").resolve()
    ny=(args.nyuv2_root or work/"nyuv2").resolve()
    ensure_modules()
    ensure_fairgrad(fairgrad)
    ny=ensure_nyuv2(ny,args.download_nyuv2)
    snap=env_snapshot(fairgrad,ny)
    out=work/"jmlr_v27_environment.json"
    out.write_text(json.dumps(snap,indent=2,sort_keys=True)+"\n")
    print(json.dumps(snap,indent=2,sort_keys=True))
    if not snap["cuda_available"]:
        raise SystemExit("FAIL: no CUDA device available; do not launch outcome-bearing cells")
    preflight(fairgrad)
    print(f"PASS: GPU environment + v27 preflight. Environment record: {out}")
    if ny is None:
        print("NYUv2 not installed; rerun with --download-nyuv2 or --nyuv2-root before NYUv2 compute.")

if __name__=="__main__":
    main()
