#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,tempfile,torch

here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    audit=td/"nyu__ls__released__0__coarse.audit.ep0.pt"
    torch.save({
        "epoch":0,
        "semantic_losses":torch.tensor([1.2,0.7,2.0],dtype=torch.float64),
        "semantic_gram":torch.tensor([[2.0,-0.2,0.3],[-0.2,1.4,0.1],[0.3,0.1,1.0]],dtype=torch.float64),
        "run_id":"nyu__ls__released__0__coarse",
        "arm":"coarse","parent":0,"k":4,
    },audit)
    out=td/"out.jsonl"
    fg=Path(sys.argv[1]).resolve()
    subprocess.run([sys.executable,str(here/"analyze_tier_a_gram.py"),"--audit",str(audit),"--fairgrad-root",str(fg),"--output",str(out)],check=True)
    rows=[x for x in out.read_text().splitlines() if x.strip()]
    assert len(rows)==6*3*3*2, len(rows)
print("PASS: Tier-A Gram analyzer synthetic census")
