import json, os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import stage_d_weighted_query as sd

def main():
    target=os.environ["FAMILY"]
    root=Path(os.environ.get("ARC_TGI_ROOT","/tmp/ARC-TGI")); sys.path.insert(0,str(root))
    gens=sd.sc.core.load_generators(root)
    found=[(i,x) for i,x in enumerate(gens) if x[0]==target]
    if not found: raise RuntimeError(target)
    fi,(name,mod,cls)=found[0]
    row=sd.build_family(fi,name,mod,cls)
    out={"summary":{"split":"StageD-named-recovery","family":name,"index":fi},"families":[row]}
    Path(os.environ["OUT_FILE"]).write_text(json.dumps(out,indent=2))
    print("FAMILY_RESULT="+json.dumps({k:row.get(k) for k in ["family","index","status","n_mutants","n_classes","n_queries","acc","pass2","disagreement_n","disagreement_acc_B","disagreement_acc_W","disagreement_acc_Wd4"]},sort_keys=True))
if __name__=="__main__":main()
