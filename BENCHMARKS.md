# Kernellum Benchmarks

Kernellum publishes benchmark results according to an evidence ladder so modeled performance is not confused with physical measurements.

## Current benchmark: digits MLP

Model/functional quality remains:

| Item | Result |
|---|---:|
| Network | 64 → 32 → 16 → 10 |
| Dataset | scikit-learn handwritten digits |
| Held-out samples | 450 |
| Float accuracy | 96.22% |
| INT8 accuracy | 96.44% |
| Float / INT8 agreement | 99.78% |
| Cycle/reference agreement | 450 / 450 |
| RTL golden vectors | 32 / 32 PASS |
| Generic Yosys synthesis | PASS |
| ECP5 family synthesis | PASS |

### ULX3S-85F physical-feedback sweep — L5 evidence

Target: LFE5U-85F-6BG381C / CABGA381 / 25 MHz.

| MAC lanes | Modeled cycles | Post-route Fmax | 25 MHz timing | Modeled core latency @25 MHz | TRELLIS_COMB | MULT18X18D |
|---:|---:|---:|:---:|---:|---:|---:|
| 1 | 2,836 | 35.96 MHz | PASS | 113.44 µs | 3,562 | 5 |
| **2** | **1,476** | **29.64 MHz** | **PASS** | **59.04 µs** | **5,727** | **6** |
| 4 | 796 | 22.12 MHz | FAIL | 31.84 µs | 10,561 | 8 |
| 8 | 456 | 16.10 MHz | FAIL | 18.24 µs | 19,652 | 12 |

**Physical-feedback selection:** 2 MAC lanes, because it has the minimum modeled cycle count among swept architectures that close the board's 25 MHz timing target.

The latency column is still modeled from cycle count and the board clock; it is not a physical-board latency measurement. The post-route Fmax and utilization values are nextpnr results for the named reference target.

Evidence record: [KRN-PNR-001](research/ULX3S_PNR_SWEEP_2026-09-18.md).

### KRN-EXT-001 — pinned third-party public ONNX model

Kernellum also completed a clean-room evaluation of the pinned `tiny-NPU/models/overlap_perf_test.onnx` graph and weights, authored outside the Kernellum repository.

Network: **64 → 64 → 64 → 32**. Target: the same ULX3S-85F / CABGA381 / 25 MHz reference board.

| MAC lanes | Modeled cycles | Post-route Fmax | 25 MHz timing | TRELLIS_COMB | MULT18X18D |
|---:|---:|---:|:---:|---:|---:|
| 1 | 10,560 | 33.51 MHz | PASS | 7,713 | 5 |
| **2** | **5,440** | **28.18 MHz** | **PASS** | **13,730** | **6** |
| 4 | 2,880 | 22.06 MHz | FAIL | 26,329 | 8 |
| 8 | 1,600 | 14.82 MHz | FAIL | 52,974 | 12 |

**Physical-feedback selection:** 2 MAC lanes. The selected bitstream SHA-256 is `50761b00fad5afda5f18c9841291bceea47a04c94155df044b5fb60ef09b2590`.

This is external **public-model** L5 evidence: the graph and weights are third-party, while deterministic synthetic inputs are used for quantization/golden verification because the upstream performance-test model does not publish a task dataset. It is not a customer-validation or application-accuracy claim.

Evidence record: [KRN-EXT-001](research/KRN-EXT-001_RESULT.md).

### Historical v0.1 baseline

TR-001 froze the earlier non-pipelined baseline at 4 MAC lanes, 680 modeled cycles and 6.8 µs at an assumed 100 MHz clock. Those numbers remain part of the historical report; the current backend adds registered requantization stages and physical-feedback selection.

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

With named-board P&R now demonstrated, the benchmark suite will expand across multiple supported dense-network shapes. The goal is to publish:

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
