#!/usr/bin/env python3
"""Execute exactly one frozen validation-aware stacking path."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from evaluate_validation_aware_stacking import FAMILIES, DIMS, SEEDS, NOISES, evaluate_path

def canonical(obj):
    return json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--index",type=int,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    keys=[(f,d,s,n) for f in FAMILIES for d in DIMS for s in SEEDS for n in NOISES]
    if not 0 <= a.index < len(keys):
        raise SystemExit(f"index must be in [0,{len(keys)-1}]")
    decision,record=evaluate_path(keys[a.index])
    payload={"schema":"kernellum.validation-aware-stacking-shard.v1","index":a.index,
             "key":list(keys[a.index]),"decision":decision,"record":record}
    payload["canonical_sha256"]=hashlib.sha256(canonical(payload).encode()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(canonical(payload))
    print(json.dumps({"index":a.index,"key":payload["key"],"canonical_sha256":payload["canonical_sha256"],
                      "predicted_active":decision["predicted_active"]},sort_keys=True),flush=True)
if __name__=="__main__": main()
