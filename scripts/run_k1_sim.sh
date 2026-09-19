#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/k1
iverilog -g2012 -Wall -s tb_kernellum_gemm_engine -o build/k1/tb.out \
  rtl/kernellum_mac_array.sv \
  rtl/kernellum_gemm_engine.sv \
  rtl/tb_kernellum_gemm_engine.sv
vvp build/k1/tb.out | tee build/k1/simulation.log
grep -q KERNELLUM_K1_GEMM_SIM_PASS build/k1/simulation.log
