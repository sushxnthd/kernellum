#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/k2
iverilog -g2012 -Wall -s tb_kernellum_k2_uart -o build/k2/tb_uart.out \
  rtl/kernellum_mac_array.sv \
  rtl/kernellum_gemm_engine.sv \
  rtl/kernellum_uart_rx.sv \
  rtl/kernellum_uart_tx.sv \
  rtl/kernellum_k2_board_top.sv \
  rtl/tb_kernellum_k2_uart.sv
vvp build/k2/tb_uart.out | tee build/k2/uart_simulation.log
grep -q KERNELLUM_K2_UART_SIM_PASS build/k2/uart_simulation.log
