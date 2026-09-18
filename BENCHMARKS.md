# Kernellum Benchmarks

Kernellum publishes benchmark results according to an evidence ladder so modeled performance is not confused with physical measurements.

## Current benchmark: digits MLP

| Item | Result |
|---|---:|
| Network | 64 → 32 → 16 → 10 |
| Dataset | scikit-learn handwritten digits |
| Held-out samples | 450 |
| Float accuracy | 96.22% |
| INT8 accuracy | 96.44% |
| Float / INT8 agreement | 99.78% |
| Cycle model agreement | 450 / 450 |
| RTL golden vectors | 32 / 32 PASS |
| Selected parallelism | 4 MAC lanes |
| Core compute cycles | 680 |
| Modeled latency @ 100 MHz | 6.8 µs |
| Generic Yosys synthesis | PASS |
| ECP5 family synthesis | PASS |
| Physical FPGA P&R | pending |
| Measured board latency | pending |
| Measured board power | pending |

The 6.8 µs number is derived from 680 modeled cycles at an assumed 100 MHz clock. It is not an achieved Fmax or measured latency.

## Evidence levels

**L0 — Model:** accuracy / quantization behavior.

**L1 — Functional reference:** integer/vector behavior.

**L2 — Cycle model:** cycle-exact architecture behavior.

**L3 — RTL simulation:** generated RTL against golden vectors.

**L4 — Family synthesis:** technology-family mapping, without board placement.

**L5 — Place-and-route:** named device/package constraints, timing and utilization.

**L6 — Physical measurement:** loaded hardware, measured latency, throughput, power and energy.

Kernellum will label every benchmark with the highest evidence level it actually reaches.

## Next benchmark pack

After the first physical FPGA bring-up, the benchmark suite will expand across multiple supported dense-network shapes. The goal is to publish:

- compiler-selected architecture;
- generated RTL size;
- synthesis / P&R utilization;
- achieved Fmax;
- end-to-end latency;
- throughput;
- board power;
- energy per inference;
- quantization delta;
- reproducible commands and artifacts.

## Benchmark contribution

Teams with a compact, non-confidential inference workload can propose it through the [Design Partner Program](DESIGN_PARTNERS.md).
