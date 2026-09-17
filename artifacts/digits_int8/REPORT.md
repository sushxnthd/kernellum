# Kernellum Compiler v0.1 — Technical Evidence Report

## Demonstrated workload

- Dataset: **scikit-learn handwritten digits**
- Network: **64 → 32 → 16 → 10**, ReLU hidden layers
- Quantization: **signed INT8 weights and activations**, 32-bit accumulators
- Held-out samples: **450**
- Floating-point accuracy: **96.22%**
- Integer pipeline accuracy: **96.44%**
- Float/INT8 prediction agreement: **99.78%**

## Architecture search

Constraint: ≤10 µs modeled core latency at a 100 MHz clock assumption, minimizing MAC-lane count.

| MAC lanes | Core cycles | Modeled latency (µs) | Meets target |
|---:|---:|---:|:---:|
| 1 | 2720 | 27.2 | no |
| 2 | 1360 | 13.6 | no |
| 4 | 680 | 6.8 | yes |
| 8 | 340 | 3.4 | yes |
| 16 | 170 | 1.7 | yes |

Selected architecture: **4 lanes**, **680 core cycles**, **6.8 µs** at the 100 MHz assumption.

## Hardware-semantics verification

A separate cycle-accurate software model follows the same lane grouping, output-neuron scheduling, integer accumulation, requantization, ReLU, saturation and layer transitions as the generated RTL.

- Compared against the vectorized INT8 reference on **450** held-out samples.
- Exact output-tensor match: **PASS**.
- Generated HDL testbench contains **32** held-out golden samples for HDL simulation.

## Generated hardware

- `kernellum_mlp_accel.sv` — synthesizable inference engine
- `kernellum_demo_top.sv` — simple FPGA demo wrapper
- `weights/*.hex` — network weights, biases and golden vectors
- `tb_kernellum_mlp_accel.sv` — end-to-end RTL testbench
- `scripts/run_eda.sh` — Icarus simulation + Yosys synthesis
- `.github/workflows/verify.yml` — CI reproduction

## Claim boundary

The repository build environment used to prepare this release does not include Icarus Verilog or Yosys. Therefore **no FPGA timing closure, resource utilization, power, Fmax, or physical-silicon claim is made here**.

The modeled latency is a cycle-count calculation at an assumed 100 MHz clock; it is **not** a measured FPGA latency.
