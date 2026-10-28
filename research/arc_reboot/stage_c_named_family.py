import json, os, sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent))
import stage_c_query_identifiability as sc

def main():
    target=os.environ["FAMILY"]
    root=Path(os.environ.get("ARC_TGI_ROOT","/tmp/ARC-TGI"))
    sys.path.insert(0,str(root))
    gens=sc.core.load_generators(root)
    found=[(i,x) for i,x in enumerate(gens) if x[0]==target]
    if not found:
        raise RuntimeError(f"family not found: {target}")
    fi,(name,mod,cls)=found[0]
    row=sc.build_family(fi,name,mod,cls)
    out={"summary":{"split":"ARC-TGI-Train-StageC-named-recovery","family":name,"index":fi,
                    "call_timeout_s":sc.CALL_TIMEOUT,"n_queries_per_usable_family":sc.N_QUERIES},
         "families":[row]}
    p=Path(os.environ.get("OUT_FILE",f"stage_c_{name}.json"))
    p.write_text(json.dumps(out,indent=2))
    print("FAMILY_RESULT="+json.dumps({k:row.get(k) for k in ["family","index","status","n_mutants","n_classes","n_queries","acc","pass2","disagreement_n","disagreement_acc_D","disagreement_acc_B"]},sort_keys=True))
if __name__=="__main__": main()
