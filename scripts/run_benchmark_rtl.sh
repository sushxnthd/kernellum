#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ROOT_ART="$ROOT/artifacts/benchmarks"

for dir in "$ROOT_ART"/*; do
  [[ -d "$dir" ]] || continue
  [[ -f "$dir/kernellum_dense_accel.sv" ]] || continue
  echo "=== RTL benchmark $(basename "$dir") ==="
  (
    cd "$dir"
    iverilog -g2012 -s tb_kernellum_dense_accel -o simv       kernellum_dense_accel.sv tb_kernellum_dense_accel.sv
    vvp simv | tee rtl_sim.log
    grep -q "KERNELLUM_ONNX_RTL_PASS" rtl_sim.log
  )
done

echo "All benchmark RTL simulations passed."
