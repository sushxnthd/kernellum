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

## Verification

- cycle-level model vs vectorized INT8 reference: **450/450 exact**
- Icarus Verilog generated-RTL simulation: **32/32 golden samples PASS**
- Yosys 0.33 generic synthesis: **PASS**
- final Yosys `check`: **0 problems**

## Claim boundary

The 6.8 µs figure is modeled, not measured. v0.1 does not yet claim named-device LUT/FF/DSP/BRAM use, place-and-route timing closure, Fmax, board power or measured end-to-end latency.
