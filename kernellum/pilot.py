"""Bounded K1 workload-to-route pilot and frozen policy benchmark. No APIs."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import shutil
import subprocess
import time
from pathlib import Path

from kernellum.k1.closed_loop import RoutedObservation, predict_fmax
from kernellum.k1.ecp5 import predicted_dp16kd
from kernellum.k1.model import K1Architecture, predicted_cycles
from kernellum.k1.routed_timing import post_route_fmax_mhz
from kernellum.route_review import review, positive_int

ROOT = Path(__file__).resolve().parents[1]
RTL = ["kernellum_mac_array.sv", "kernellum_local_mac_array.sv",
       "kernellum_gemm_engine.sv", "kernellum_k1_pnr_top.sv"]
PYTHON_SOURCES = ["kernellum/pilot.py", "kernellum/k1/model.py", "kernellum/k1/closed_loop.py",
                  "kernellum/k1/ecp5.py", "kernellum/k1/routed_timing.py", "kernellum/route_review.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def load_spec(path):
    s = json.loads(Path(path).read_text())
    if s["target"] != "ecp5-85k-CABGA381" or s["frequency_mhz"] != 25:
        raise ValueError("this backend supports only ECP5-85K CABGA381 at a 25 MHz routing constraint")
    pool = []
    for c in s["candidates"]:
        r, col, kt = (positive_int(c[k]) for k in ("rows", "cols", "k_tile"))
        if max(r, col) > 32 or kt not in (8, 16, 32, 64, 128, 256, 512):
            raise ValueError("candidate outside bounded K1 backend")
        a = K1Architecture(f"r{r:02d}_c{col:02d}_k{kt:03d}", r, col, kt)
        if a.pe_count > s["limits"]["dsp"] or predicted_dp16kd(a) > s["limits"]["bram"]:
            raise ValueError("candidate exceeds predicted resource limits")
        pool.append(a)
    if not pool or len({a.name for a in pool}) != len(pool):
        raise ValueError("candidate set must be nonempty and unique")
    if positive_int(s["budget"]) > len(pool):
        raise ValueError("budget exceeds candidate set")
    if not s["seeds"] or len(set(s["seeds"])) != len(s["seeds"]):
        raise ValueError("seeds must be nonempty and unique")
    for seed in s["seeds"]:
        positive_int(seed)
    for w in s["workloads"]:
        for d in ("m", "n", "k"):
            positive_int(w[d])
    if not s["workloads"] or len({w["name"] for w in s["workloads"]}) != len(s["workloads"]):
        raise ValueError("workload names must be nonempty and unique")
    for value in s["limits"].values():
        positive_int(value)
    return s, pool


def prior(s):
    r = review([ROOT / p for p in s["prior_files"]], m=1, n=1, k=1,
               baseline="unused", max_resources=s["limits"])
    if r["rejected"] or not r["ranking"]:
        raise ValueError("prior observations are invalid or empty")
    return [RoutedObservation(K1Architecture(x["name"], x["rows"], x["cols"], x["k_tile"]),
                              x["worst_observed_fmax_mhz"]) for x in r["ranking"]]


def latency(w, arch, fmax):
    return predicted_cycles(w["m"], w["n"], w["k"], arch) / (fmax * 1000)


def choose(pool, observations, w, policy):
    if policy not in ("analytic", "static", "adaptive"):
        raise ValueError("unknown policy")
    def score(a):
        fmax = 1.0 if policy == "analytic" else predict_fmax(a, observations)[0]
        return latency(w, a, fmax), a.name
    return min(pool, key=score)


def simulate_policy(pool, initial, w, policy, budget, evaluate):
    """Only the callback sees hidden timings; a policy sees its own observations."""
    remaining, observed, trace = list(pool), list(initial), []
    for _ in range(budget):
        a = choose(remaining, observed if policy == "adaptive" else initial, w, policy)
        remaining.remove(a)
        result = evaluate(a)
        value = result.get("fmax_mhz")
        ok = result.get("eligible") is True and isinstance(value, (int, float)) and math.isfinite(value) and value > 0
        trace.append({"candidate": a.name, "eligible": ok,
                      "latency_ms": latency(w, a, value) if ok else None})
        if ok:
            observed.append(RoutedObservation(a, value))
    values = [x["latency_ms"] for x in trace if x["latency_ms"] is not None]
    return {"trace": trace, "best_ms": min(values) if values else None, "route_calls": len(trace)}


def testbench(a):
    return f'''`timescale 1ns/1ps
module tb;
localparam R={a.rows}, C={a.cols}, K={a.k_tile}, AW=$clog2(K), LW=$clog2(K+1);
reg clk=0,rst=1,a_we=0,b_we=0,start=0,clear_before=1;
reg [AW-1:0] a_waddr=0,b_waddr=0;
reg [R*8-1:0] a_wdata=0; reg [C*8-1:0] b_wdata=0;
reg [LW-1:0] k_len=0; wire busy,done; wire [R*C*32-1:0] acc_flat;
reg signed [31:0] expected [0:R*C-1];
integer trial,t,r,c,len;
kernellum_gemm_engine #(.ROWS(R),.COLS(C),.K_TILE(K),.ACC_WIDTH(32)) dut(.*);
always #5 clk=~clk;
function integer av(input integer x,y,z);
begin av=((x*37+y*13+z*59)%256)-128; end endfunction
function integer bv(input integer x,y,z);
begin bv=((x*71+y*29+z*17)%256)-128; end endfunction
initial begin #1000000; $fatal(1,"TIMEOUT"); end
initial begin
 repeat(3) @(negedge clk); rst=0;
 for(trial=0;trial<3;trial=trial+1) begin
  len=(trial==0)?K:((trial==1)?7:1);
  clear_before=(trial!=1);
  if(clear_before) for(r=0;r<R*C;r=r+1) expected[r]=0;
  for(t=0;t<len;t=t+1) begin
   @(negedge clk); a_we=1; b_we=1; a_waddr=t; b_waddr=t;
   for(r=0;r<R;r=r+1) a_wdata[r*8+:8]=av(t,r,trial);
   for(c=0;c<C;c=c+1) b_wdata[c*8+:8]=bv(t,c,trial);
   for(r=0;r<R;r=r+1) for(c=0;c<C;c=c+1)
    expected[r*C+c]=expected[r*C+c]+av(t,r,trial)*bv(t,c,trial);
  end
  @(negedge clk); a_we=0; b_we=0; k_len=len; start=1;
  @(negedge clk); start=0;
  wait(done===1'b1); @(negedge clk);
  for(r=0;r<R*C;r=r+1)
   if($signed(acc_flat[r*32+:32]) !== expected[r]) $fatal(1,"MISMATCH trial=%0d cell=%0d",trial,r);
 end
 $display("KERNELLUM_PILOT_SIM_PASS"); $finish;
end
endmodule
'''


def run_command(cmd, cwd, label, timeout=600):
    started = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        text, rc = p.stdout + "\n" + p.stderr, p.returncode
    except subprocess.TimeoutExpired as exc:
        text, rc = str(exc.stdout or "") + "\n" + str(exc.stderr or "") + "\nTIMEOUT", 124
    (cwd / (label + ".log")).write_text(text)
    return {"command": cmd, "returncode": rc, "wall_seconds": time.monotonic()-started}, text


def route(a, seed, s, spec_sha, out):
    out = Path(out).resolve() / f"s{seed}" / a.name
    if out.exists():
        raise ValueError(f"refusing to overwrite route evidence: {out}")
    missing = [t for t in ("iverilog", "vvp", "yosys", "nextpnr-ecp5") if not shutil.which(t)]
    if missing:
        raise ValueError("missing toolchain: " + ", ".join(missing))
    out.mkdir(parents=True)
    hashes = {}
    for f in RTL:
        shutil.copy2(ROOT / "rtl" / f, out / f)
        hashes[f] = digest(out / f)
    (out / "tb.sv").write_text(testbench(a))
    record = {"name": a.name, "rows": a.rows, "cols": a.cols, "k_tile": a.k_tile,
              "seed": seed, "spec_sha256": spec_sha, "source_hashes": hashes,
              "runner_sha256": digest(__file__), "functional_ok": False,
              "dependency_hashes": {p:digest(ROOT/p) for p in PYTHON_SOURCES+s["prior_files"]},
              "synth_ok": False, "route_ok": False, "eligible": False,
              "fmax_mhz": None, "commands": [], "tool_versions": {}}
    for tool in ("yosys", "nextpnr-ecp5"):
        p = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=20)
        record["tool_versions"][tool] = (p.stdout + p.stderr).strip()
    def execute(cmd, label):
        info, text = run_command(cmd, out, label)
        record["commands"].append(info)
        return info["returncode"], text
    try:
        rc, _ = execute(["iverilog", "-g2012", "-s", "tb", "-o", "sim", *RTL, "tb.sv"], "compile")
        if rc:
            raise ValueError("functional compilation failed")
        rc, text = execute(["vvp", "sim"], "functional")
        record["functional_ok"] = rc == 0 and "KERNELLUM_PILOT_SIM_PASS" in text
        if not record["functional_ok"]:
            raise ValueError("functional simulation failed")
        script = ("read_verilog -sv " + " ".join(RTL) + "; "
                  f"chparam -set ROWS {a.rows} -set COLS {a.cols} -set K_TILE {a.k_tile} kernellum_k1_pnr_top; "
                  "hierarchy -check -top kernellum_k1_pnr_top; "
                  "synth_ecp5 -top kernellum_k1_pnr_top -json design.json; stat")
        rc, text = execute(["yosys", "-p", script], "synthesis")
        record["synth_ok"] = rc == 0 and (out / "design.json").exists()
        if not record["synth_ok"]:
            raise ValueError("synthesis failed")
        cells = {m.group(1):int(m.group(2)) for m in re.finditer(r"^\s+([A-Za-z_$][A-Za-z0-9_$]*)\s+(\d+)\s*$", text, re.M)}
        resources = {r:cells.get(cell, 0) for r,cell in zip(("dsp","bram","lut4","ff"), ("MULT18X18D","DP16KD","LUT4","TRELLIS_FF"))}
        record["resources"] = resources
        if resources["dsp"] != a.pe_count or resources["bram"] <= 0 or resources["ff"] <= 0:
            raise ValueError("synthesis did not preserve expected architecture resources")
        if any(resources[r] > s["limits"][r] for r in resources):
            raise ValueError("synthesis resource limit exceeded")
        rc, _ = execute(["nextpnr-ecp5", "--85k", "--package", "CABGA381", "--json", "design.json",
                         "--textcfg", "design.config", "--report", "timing.json", "--freq", "25",
                         "--seed", str(seed), "--timing-allow-fail"], "route")
        if rc or not (out / "design.config").exists():
            raise ValueError("routing failed")
        fmax = post_route_fmax_mhz(out / "timing.json")
        if not math.isfinite(fmax) or fmax <= 0:
            raise ValueError("invalid final route Fmax")
        record.update(route_ok=True, eligible=True, fmax_mhz=fmax, timing_metric="post_route_report_json")
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        record["error"] = str(exc)
    record["file_sha256"] = {p.name:digest(p) for p in out.iterdir() if p.is_file()}
    dump(out / "result.json", record)
    return record


def audit(spec_path, inputs, output):
    s, pool = load_spec(spec_path)
    expected = {(seed,a.name) for seed in s["seeds"] for a in pool}
    records, errors = {}, []
    for path in sorted(Path(inputs).rglob("result.json")):
        r = json.loads(path.read_text())
        key = (r["seed"],r["name"])
        if key in records or key not in expected:
            errors.append(f"duplicate or unexpected result {key}")
        records[key] = r
        if r["spec_sha256"] != digest(spec_path) or r["runner_sha256"] != digest(__file__):
            errors.append(f"source/spec mismatch {key}")
        if r.get("dependency_hashes") != {p:digest(ROOT/p) for p in PYTHON_SOURCES+s["prior_files"]}:
            errors.append(f"dependency/prior mismatch {key}")
        for name, sha in r["file_sha256"].items():
            p = path.parent / name
            if Path(name).name != name or not p.is_file() or digest(p) != sha:
                errors.append(f"artifact hash mismatch {key}/{name}")
        for name in RTL:
            if r["source_hashes"].get(name) != digest(ROOT / "rtl" / name):
                errors.append(f"RTL mismatch {key}/{name}")
        if r["eligible"]:
            a = next((a for a in pool if a.name == r["name"]), None)
            if a is None or (r["rows"],r["cols"],r["k_tile"]) != (a.rows,a.cols,a.k_tile):
                errors.append(f"geometry mismatch {key}")
            try:
                actual = post_route_fmax_mhz(path.parent / "timing.json")
                if actual != r["fmax_mhz"] or not math.isfinite(actual) or actual <= 0:
                    errors.append(f"timing mismatch {key}")
            except (ValueError,OSError,KeyError,TypeError):
                errors.append(f"unreadable final timing {key}")
            if not r["functional_ok"] or not r["synth_ok"] or not r["route_ok"]:
                errors.append(f"false eligibility {key}")
            if len(r["commands"]) != 4 or any(c["returncode"] != 0 for c in r["commands"]):
                errors.append(f"failed or missing command {key}")
            if any(r["resources"].get(x,math.inf)>s["limits"][x] for x in s["limits"]):
                errors.append(f"resource excess {key}")
    missing = sorted(expected - records.keys())
    complete = not missing and not errors and all(r["eligible"] for r in records.values())
    versions = {json.dumps(r["tool_versions"],sort_keys=True) for r in records.values()}
    complete = complete and len(versions) == 1
    report = {"spec_sha256":digest(spec_path), "expected_routes":len(expected),
              "received_routes":len(records),"missing":missing,"integrity_errors":errors,
              "complete_and_eligible":complete,"tool_versions_consistent":len(versions)==1,
              "cases":[],"claim_supported":False,
              "boundary":"Prospective software-flow benchmark on one ECP5 family. Modeled kernel latency from routed Fmax; no board, power, customer, novel architecture or investor outcome claim. Exhaustive benchmark cost includes every route; two-call policy cost is simulated by controlled replay."}
    if complete:
        initial = prior(s)
        for seed,w in itertools.product(s["seeds"],s["workloads"]):
            values = {a.name:latency(w,a,records[seed,a.name]["fmax_mhz"]) for a in pool}
            oracle = min(values.values())
            case = {"seed":seed,"workload":w["name"],"oracle_ms":oracle,"policies":{}}
            for policy in ("analytic","static","adaptive"):
                result = simulate_policy(pool, initial, w, policy, s["budget"], lambda a:records[seed,a.name])
                result["oracle_regret_pct"] = 100*(result["best_ms"]/oracle-1)
                case["policies"][policy]=result
            random_values = [min(values[a.name] for a in subset) for subset in itertools.combinations(pool,s["budget"])]
            case["expected_random_best_ms"] = sum(random_values)/len(random_values)
            case["random_subsets"] = len(random_values)
            report["cases"].append(case)
        cases = report["cases"]
        mean = lambda xs:sum(xs)/len(xs)
        gains = {p:mean([100*(1-c["policies"]["adaptive"]["best_ms"]/(c["expected_random_best_ms"] if p=="random" else c["policies"][p]["best_ms"])) for c in cases]) for p in ("analytic","static","random")}
        regret = mean([c["policies"]["adaptive"]["oracle_regret_pct"] for c in cases])
        flags = {"mean_regret":regret<=s["gate"]["max_mean_regret_pct"],
                 **{f"gain_vs_{p}":gains[p]>=s["gate"][f"min_gain_vs_{p}_pct"] for p in gains},
                 "never_worse_than_analytic":all(c["policies"]["adaptive"]["best_ms"]<=c["policies"]["analytic"]["best_ms"]+1e-12 for c in cases)}
        report.update(mean_adaptive_regret_pct=regret,mean_gain_pct=gains,flags=flags,claim_supported=all(flags.values()))
    dump(output,report)
    print(json.dumps(report,indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run","benchmark-route","audit"))
    p.add_argument("--spec",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--seed",type=int,default=1103)
    p.add_argument("--workload",default="expand")
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--shards",type=int,default=1)
    p.add_argument("--inputs",type=Path)
    args=p.parse_args()
    try:
        s,pool=load_spec(args.spec)
        if args.mode=="audit":
            if args.inputs is None: raise ValueError("--inputs required")
            r=audit(args.spec,args.inputs,args.out)
            return 0 if r["complete_and_eligible"] else 2
        if args.seed not in s["seeds"]: raise ValueError("seed must be frozen in spec")
        if args.mode=="benchmark-route":
            if args.shards<1 or not 0<=args.shard<args.shards: raise ValueError("invalid shard")
            records=[route(a,args.seed,s,digest(args.spec),args.out) for i,a in enumerate(pool) if i%args.shards==args.shard]
            return 0 if records and all(r["eligible"] for r in records) else 2
        w=next((w for w in s["workloads"] if w["name"]==args.workload),None)
        if w is None: raise ValueError("unknown workload")
        obs=prior(s)
        if args.mode=="plan":
            first=choose(pool,obs,w,"adaptive")
            result={"spec_sha256":digest(args.spec),"workload":w,"budget":s["budget"],
                    "first_candidate":first.name,"candidate_count":len(pool),
                    "prior_hashes":{f:digest(ROOT/f) for f in s["prior_files"]},
                    "status":"plan_only_no_routes_executed"}
            dump(args.out,result); print(json.dumps(result,indent=2)); return 0
        result=simulate_policy(pool,obs,w,"adaptive",s["budget"],
                               lambda a:route(a,args.seed,s,digest(args.spec),args.out))
        result.update(workload=w,spec_sha256=digest(args.spec),
                      boundary="Modeled K1 kernel cycles divided by final routed Fmax; no board latency or novel architecture claim.")
        dump(args.out/"selection.json",result); print(json.dumps(result,indent=2))
        return 0 if result["best_ms"] is not None else 2
    except (ValueError,OSError,KeyError,TypeError) as exc:
        p.error(str(exc))


if __name__=="__main__":
    raise SystemExit(main())
