# KRN-BENCH-001 — Multi-Workload Physical-Feedback Result

**Evidence ID:** KRN-BENCH-001  
**Status:** PASS  
**Evidence level:** L5 — named-board place-and-route  
**Target:** ULX3S-85F / LFE5U-85F-6BG381C / CABGA381  
**Board clock target:** 25 MHz  
**Completed:** 18 September 2026

## Provenance

- Source workflow: [benchmark-pnr run 35336911649](https://github.com/sushxnthd/kernellum/actions/runs/35336911649)
- Source commit: [`435555d738af8511487704b632273beea1521060`](https://github.com/sushxnthd/kernellum/commit/435555d738af8511487704b632273beea1521060)
- Workflow artifact ID: `10544618641`
- Workflow artifact digest: `sha256:8f46b9b3582591a06d765bb5b03113f56eeb2fa460cc0f7425ac7677999caaee`
- Synthesis tool recorded in logs: Yosys 0.33 (`2584903a060`)

## Research question

Does Kernellum's architecture choice remain physically constrained when the same compiler/backend is applied to multiple supported dense-network shapes, rather than one hand-selected demonstration?

## Method

Three deterministic three-layer dense ONNX graphs were lowered through the supported `Gemm → ReLU → Gemm → ReLU → Gemm` path. For every workload, Kernellum generated RTL and swept 1/2/4/8 MAC-lane candidates through Yosys and nextpnr using the same ULX3S-85F package, LPF constraints and 25 MHz clock target.

The frozen selection rule was applied independently to every workload:

> choose the minimum modeled cycle count among swept configurations whose post-route Fmax meets 25 MHz.

If no candidate met timing, the workflow would record no feasible selection.

## Headline result

| Workload | Shape | Selected lanes | Post-route Fmax | Modeled cycles | Modeled core latency @ 25 MHz | TRELLIS_COMB | TRELLIS_FF | TRELLIS_RAMW | MULT18X18D |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| compact | 32 → 16 → 8 → 4 | **2** | **31.55 MHz** | 392 | 15.68 µs | 3,135 | 330 | 18 | 6 |
| reference | 64 → 32 → 16 → 10 | **2** | **29.76 MHz** | 1,476 | 59.04 µs | 5,704 | 338 | 30 | 6 |
| wide | 128 → 64 → 32 → 8 | **2** | **28.10 MHz** | 5,456 | 218.24 µs | 14,739 | 335 | 58 | 6 |

All three workloads selected 2 lanes. In every case, the 4- and 8-lane candidates reduced modeled cycle count but failed the physical 25 MHz timing constraint.

## Full sweep

| Shape | Lanes | Modeled cycles | Modeled latency @ 25 MHz | Post-route Fmax | 25 MHz timing | TRELLIS_COMB | MULT18X18D |
|---|---:|---:|---:|---:|:---:|---:|---:|
| 32 → 16 → 8 → 4 | 1 | 728 | 29.12 µs | 36.74 MHz | PASS | 2,194 | 5 |
| 32 → 16 → 8 → 4 | **2** | **392** | **15.68 µs** | **31.55 MHz** | **PASS / selected** | **3,135** | **6** |
| 32 → 16 → 8 → 4 | 4 | 224 | 8.96 µs | 22.49 MHz | FAIL | 5,573 | 8 |
| 32 → 16 → 8 → 4 | 8 | 140 | 5.60 µs | 16.09 MHz | FAIL | 10,190 | 12 |
| 64 → 32 → 16 → 10 | 1 | 2,836 | 113.44 µs | 35.83 MHz | PASS | 3,451 | 5 |
| 64 → 32 → 16 → 10 | **2** | **1,476** | **59.04 µs** | **29.76 MHz** | **PASS / selected** | **5,704** | **6** |
| 64 → 32 → 16 → 10 | 4 | 796 | 31.84 µs | 22.04 MHz | FAIL | 10,330 | 8 |
| 64 → 32 → 16 → 10 | 8 | 456 | 18.24 µs | 15.98 MHz | FAIL | 19,947 | 12 |
| 128 → 64 → 32 → 8 | 1 | 10,704 | 428.16 µs | 34.87 MHz | PASS | 7,935 | 5 |
| 128 → 64 → 32 → 8 | **2** | **5,456** | **218.24 µs** | **28.10 MHz** | **PASS / selected** | **14,739** | **6** |
| 128 → 64 → 32 → 8 | 4 | 2,832 | 113.28 µs | 20.59 MHz | FAIL | 28,394 | 8 |
| 128 → 64 → 32 → 8 | 8 | 1,520 | 60.80 µs | 14.84 MHz | FAIL | 55,504 | 12 |

## Selected bitstream identities

| Workload | SHA-256 |
|---|---|
| compact | `333df9830e7df9d1f35bfbdecccfa4b2c6e31988ca6e2ef8511caeaf241261a7` |
| reference | `04505e9dde10478373efd515b9eb2a96be90814bb21b1543350fed88a1bdd76e` |
| wide | `0c21831c71b4b2d085ce926df09a9fab487c8f19dc7284f714add8be631b1f3e` |

The hashes above were recomputed from the downloaded clean-room artifact and matched its generated summary.

## Interpretation

The result strengthens the physical-feedback claim beyond the original reference shape. More lanes monotonically reduce the compiler's modeled cycle count, but they also increase routed logic and reduce achievable clock frequency. Across all three tested shapes, the fastest cycle-only candidates were physically infeasible at the board clock and the timing-aware rule selected the 2-lane design.

This is evidence that the implemented search loop responds to physical timing across multiple supported shapes. It is not evidence that 2 lanes is universally optimal outside this target, workload class, toolchain or sweep space.

## Reproduce

```bash
pip install -e '.[test,onnx]'
python scripts/build_benchmark_matrix.py
bash scripts/run_benchmark_pnr_sweep_ulx3s_85f.sh
```

Clean-room workflow: `.github/workflows/benchmark-pnr.yml`.

The exact machine-readable promoted record is [`KRN-BENCH-001_RESULT.json`](KRN-BENCH-001_RESULT.json).

## Evidence boundary

The workloads are deterministic synthetic dense graphs selected to test compiler-shape and physical-feedback behavior. This record establishes named-board P&R, post-route timing, utilization, architecture selection and bitstream generation.

It does **not** establish:

- application-level accuracy;
- an external customer or design-partner workload;
- physical-board execution;
- measured end-to-end latency or throughput;
- measured board power or energy;
- ASIC PPA.
