# Kernellum K0.5 Synthesis Validation Report

Date: 2026-09-19

## Result

**PASS** against the validation thresholds declared in `docs/K05_PLAN.md` before the synthesis results were observed.

K0.5 asked one narrow question: does K0's coarse FPGA resource model preserve useful architecture rankings after real RTL elaboration and Xilinx-7 technology mapping?

The answer for the sampled K0.5 architecture family is yes.

## Toolchain

- Yosys 0.33 (git sha1 2584903a060)
- Icarus Verilog 12.0 stable
- GitHub Actions Ubuntu runner
- Xilinx-7 technology mapping via `synth_xilinx -family xc7`

The exact machine-readable evidence is committed under `results/k05_validation.json` and `results/k05_synthesis.csv`.

## Functional RTL validation

The parameterized MAC array was simulated with Icarus Verilog.

The self-checking test computes:

`[[1,2,3],[4,5,6]] x [[7,8],[9,10],[11,12]]`

and verifies the expected output:

`[[58,64],[139,154]]`

The same simulation separately checks scratchpad write/read behavior.

**Functional simulation: PASS.**

## Synthesis sample

Nine stratified configurations were synthesized:

- arrays from 4x4 through 32x16 / 16x32;
- 16 to 512 processing elements;
- 64, 128 and 256 KB scratchpads;
- INT8 MACs.

## Predeclared gate versus result

| Metric | Required | Observed |
| --- | ---: | ---: |
| DSP rank Spearman | >= 0.90 | **1.000** |
| BRAM rank Spearman | >= 0.90 | **1.000** |
| Mean BRAM relative error | <= 20% | **11.21%** |
| Generic multiplier preservation | >= 99% | **100%** |
| Mean mapped-DSP / predicted-DSP ratio | >= 0.80 | **1.000** |

**Resource-model gate: PASS.**

## DSP result

Every sampled processing element survived generic synthesis as one multiplier and mapped to one DSP48:

- 4x4 array: predicted 16 DSP, synthesized 16;
- 8x8: 64 vs 64;
- 16x16: 256 vs 256;
- 16x32 / 32x16: 512 vs 512.

This is the strongest K0.5 result: for this RTL structure and synthesis flow, K0's DSP-equivalent ordering and absolute count both survived technology mapping exactly.

## BRAM result and calibration

BRAM ordering was also perfectly preserved, but K0 systematically underestimated absolute mapped BRAM use.

| Scratchpad | K0 prediction (BRAM18 eq.) | Synthesized | Error |
| --- | ---: | ---: | ---: |
| 64 KB | 29 | 32 | 10.34% |
| 128 KB | 57 | 64 | 12.28% |
| 256 KB | 114 | 128 | 12.28% |

The cause is architectural granularity rather than random model error. The scratchpad is 32 bits wide and Yosys maps it to RAMB36 blocks. A RAMB36 used as a 32-bit memory contributes 4096 data bytes, so the observed mapping follows:

`RAMB36 = ceil(buffer_bytes / 4096)`

or, in BRAM18-equivalents:

`BRAM18eq = 2 * ceil(buffer_bytes / 4096)`.

K1 should therefore use a target-aware memory model rather than K0's ideal bit-capacity approximation.

## What K0.5 establishes

1. The first Kernellum RTL datapath is functionally executable.
2. K0's DSP scaling survives real synthesis for the sampled architecture family.
3. K0's BRAM ordering survives real synthesis.
4. The BRAM model has a measurable and explainable target-specific bias that can be calibrated.
5. The project now has a reproducible analytical -> RTL -> simulation -> synthesis evidence chain.

## What K0.5 does not establish

K0.5 does **not** establish:

- routed maximum clock frequency;
- place-and-route feasibility at the largest configurations;
- measured FPGA latency;
- measured power or energy;
- model-quality impact from INT8 quantization;
- superiority to mature accelerator generators;
- novelty or patentability of the current MAC-array structure.

## K1 gate

K1 should now add:

1. a tiled GEMM controller that turns the MAC array into a complete scheduled matrix engine;
2. a target-aware BRAM resource model using K0.5 calibration;
3. place-and-route feedback for achievable Fmax and device utilization;
4. predicted-versus-routed latency ranking;
5. synthesis/P&R ingestion back into the search loop;
6. only after those pass, physical FPGA measurement.

The K1 claim should remain narrow: **can Kernellum automatically choose a workload-specific architecture whose predicted ranking remains useful after synthesis and routing?**
