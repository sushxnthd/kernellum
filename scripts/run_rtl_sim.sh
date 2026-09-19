#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/k05
iverilog -g2012 -Wall -s tb_kernellum_mac_array -o build/k05/tb.out \
  rtl/kernellum_mac_array.sv rtl/tb_kernellum_mac_array.sv
vvp build/k05/tb.out | tee build/k05/simulation.log
grep -q KERNELLUM_RTL_SIM_PASS build/k05/simulation.log
