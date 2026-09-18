#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/onnx_digits"
cd "$ART"

iverilog -g2012 -s tb_kernellum_dense_accel -o simv \
  kernellum_dense_accel.sv tb_kernellum_dense_accel.sv
vvp simv | tee rtl_sim.log
grep -q "KERNELLUM_ONNX_RTL_PASS" rtl_sim.log

yosys -p 'read_verilog -sv kernellum_dense_accel.sv; synth -top kernellum_dense_accel; stat; check' \
  | tee yosys_stat.log
grep -q "Found and reported 0 problems" yosys_stat.log

yosys -p 'read_verilog -sv kernellum_dense_accel.sv; synth_ecp5 -top kernellum_dense_accel; stat; check' \
  | tee yosys_ecp5_stat.log
grep -q "Found and reported 0 problems" yosys_ecp5_stat.log
