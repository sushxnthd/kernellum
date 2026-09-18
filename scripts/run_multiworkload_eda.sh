#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$ROOT/artifacts/multiworkload"

if [ ! -d "$BASE" ]; then
  echo "multi-workload artifacts missing; run scripts/run_multiworkload_bench.py first" >&2
  exit 1
fi

count=0
for ART in "$BASE"/*; do
  [ -d "$ART" ] || continue
  [ -f "$ART/kernellum_dense3_accel.sv" ] || continue

  name="$(basename "$ART")"
  echo "=== KERNELLUM EDA: $name ==="
  cd "$ART"

  iverilog -g2012 -s tb_kernellum_dense3_accel -o simv     kernellum_dense3_accel.sv tb_kernellum_dense3_accel.sv
  vvp simv | tee rtl_sim.log
  grep -q "KERNELLUM_ONNX_RTL_PASS" rtl_sim.log

  yosys -p 'read_verilog -sv kernellum_dense3_accel.sv; synth -top kernellum_dense3_accel; stat; check'     | tee yosys_stat.log
  grep -q "Found and reported 0 problems" yosys_stat.log

  yosys -p 'read_verilog -sv kernellum_dense3_accel.sv; synth_ecp5 -top kernellum_dense3_accel; stat; check'     | tee yosys_ecp5_stat.log
  grep -q "Found and reported 0 problems" yosys_ecp5_stat.log

  echo "KERNELLUM_MULTIWORKLOAD_EDA_PASS name=$name"
  count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
  echo "no generated workloads were found" >&2
  exit 1
fi

echo "KERNELLUM_MULTIWORKLOAD_EDA_SUITE_PASS workloads=$count"
