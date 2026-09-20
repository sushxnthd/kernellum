#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/k1
iverilog -g2012 -Wall -s tb_kernellum_gemm_engine -o build/k1/tb.out \
  rtl/kernellum_mac_array.sv \
  rtl/kernellum_local_mac_array.sv \
  rtl/kernellum_gemm_engine.sv \
  rtl/tb_kernellum_gemm_engine.sv
vvp build/k1/tb.out | tee build/k1/simulation.log
grep -q KERNELLUM_K1_GEMM_SIM_PASS build/k1/simulation.log

iverilog -g2012 -Wall -s tb_kernellum_local_gemm_engine -o build/k1/tb_local.out \
  rtl/kernellum_mac_array.sv \
  rtl/kernellum_local_mac_array.sv \
  rtl/kernellum_gemm_engine.sv \
  rtl/tb_kernellum_local_gemm_engine.sv
vvp build/k1/tb_local.out | tee build/k1/simulation_local.log
grep -q KERNELLUM_K1_LOCAL_GEMM_SIM_PASS build/k1/simulation_local.log

iverilog -g2012 -Wall -s tb_kernellum_transport_equivalence \
  -o build/k1/tb_equivalence.out \
  rtl/kernellum_mac_array.sv \
  rtl/kernellum_local_mac_array.sv \
  rtl/kernellum_gemm_engine.sv \
  rtl/tb_kernellum_transport_equivalence.sv
vvp build/k1/tb_equivalence.out | tee build/k1/simulation_equivalence.log
grep -q KERNELLUM_K1_TRANSPORT_EQUIVALENCE_PASS build/k1/simulation_equivalence.log
