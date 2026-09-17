#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/digits_int8"
cd "$ART"

iverilog -g2012 -o simv kernellum_mlp_accel.sv tb_kernellum_mlp_accel.sv
vvp simv | tee rtl_sim.log
grep -q "KERNELLUM_RTL_PASS" rtl_sim.log

yosys -p 'read_verilog -sv kernellum_mlp_accel.sv; synth -top kernellum_mlp_accel; stat' | tee yosys_stat.log

echo "EDA flow completed successfully."
