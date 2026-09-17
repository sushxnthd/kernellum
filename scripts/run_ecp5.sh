#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ART="$ROOT/artifacts/digits_int8"
cd "$ART"
echo "Kernellum FPGA target profile: Lattice ECP5-85F (family-mapped synthesis only)"
yosys -p 'read_verilog -sv kernellum_mlp_accel.sv; synth_ecp5 -top kernellum_mlp_accel; stat; check' | tee yosys_ecp5_stat.log
