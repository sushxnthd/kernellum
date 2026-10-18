#!/usr/bin/env python3
import argparse, hashlib, json, math
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--result",type=Path,required=True)
ap.add_argument("--output",type=Path,required=True)
a=ap.parse_args()
d=json.loads(a.result.read_text())
raw=dict(d); claimed=raw.pop("canonical_sha256")
canonical=lambda x: json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n"
topo=d["topology_operating_points"]; static=d["static_operating_points"]
checks={
 "opened_classification":d["classification"]=="OPENED_COHORT_LEAVE_ONE_FAMILY_OUT_DEVELOPMENT",
 "forty_paths":d["paths"]==40,
 "five_family_folds":len(d["families"])==5,
 "threshold_grid":[x["threshold"] for x in topo]==[.1,.15,.2,.25,.3],
 "topology_has_no_passing_point":not any(x["passes"] for x in topo),
 "topology_precision_below_gate":all(x["precision"]<.75 for x in topo if x["routes"]>=8),
 "topology_tail_gain_present":any(x["far_geometric_ratio"]<.90 for x in topo),
 "static_viable_point_exists":any(x["routes"]>=8 and x["precision"]>=.75 and x["far_geometric_ratio"]<=.90 and x["catastrophes_removed"]>=2 for x in static),
 "status_kills_kernel":d["status"]=="KILL_TOPOLOGY_NO_TRANSFER_GATE",
 "prediction_counts":len(d["topology_predictions"])==40 and len(d["static_predictions"])==40,
 "canonical_hash":hashlib.sha256(canonical(raw).encode()).hexdigest()==claimed,
}
out={"schema":"kernellum.continuous-transition-topology-development.audit.v1",
     "checks":checks,"passed":sum(bool(v) for v in checks.values()),"total":len(checks),
     "all_pass":all(checks.values()),"result_sha256":hashlib.sha256(a.result.read_bytes()).hexdigest()}
a.output.write_text(canonical(out))
print(canonical(out),end="")
raise SystemExit(0 if out["all_pass"] else 1)
