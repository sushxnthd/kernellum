# KRN-EXT-001 — Completed External Public-Model Validation

**Evidence ID:** KRN-EXT-001  
**Date:** 2026-09-18  
**CI workflow run:** 35337841913  
**CI result:** PASS  
**Artifact:** `kernellum-krn-ext-001`  
**Artifact digest:** `sha256:72404f94104f2cd3ea63e5e2106581a8e0e064ead8a88407d1d747500c6fa318`

## External workload provenance

- Upstream repository: `harishsg993010/tiny-NPU`
- Pinned commit: `8216c22b762011aa20c05fc2768423fd12dda59d`
- Artifact: `models/overlap_perf_test.onnx`
- Git blob SHA-1: `070fb6c8f35e6f3b1d91e92143442367a25dc41b`
- Model SHA-256: `532bdb7ae217d557932bc70d7eea4dc3e6f1f5bc4603b2604412ea503fc775fa`
- Network: **64 → 64 → 64 → 32**
- Graph: **Gemm → ReLU → Gemm → ReLU → Gemm**
- Upstream graph/weights modified by Kernellum: **no**

The upstream model was fetched at the pinned commit and its Git blob identity was verified before compilation.

## Functional compiler evidence

The clean-room workflow completed:

- pinned upstream retrieval and integrity verification;
- ONNX lowering into Kernellum hardware IR;
- deterministic INT8 lowering using synthetic calibration inputs;
- exact cycle-model / vector-reference agreement;
- generated SystemVerilog;
- generated golden-vector testbench;
- Icarus Verilog RTL simulation: **PASS**;
- ECP5 synthesis;
- ULX3S-85F board-targeted place-and-route across 1/2/4/8 MAC lanes.

The upstream performance-test model does not publish an application dataset. Kernellum therefore uses deterministic synthetic calibration/golden inputs for implementation verification only. No application-accuracy claim is made.

## ULX3S-85F physical-feedback result

Target: **LFE5U-85F-6BG381C / CABGA381 / 25 MHz**

| MAC lanes | Modeled cycles | Post-route Fmax | 25 MHz timing | Modeled core latency @25 MHz | TRELLIS_COMB | TRELLIS_FF | TRELLIS_RAMW | MULT18X18D |
|---:|---:|---:|:---:|---:|---:|---:|---:|---:|
| 1 | 10,560 | 33.51 MHz | PASS | 422.40 µs | 7,713 | 336 | 28 | 5 |
| **2** | **5,440** | **28.18 MHz** | **PASS** | **217.60 µs** | **13,730** | **336** | **52** | **6** |
| 4 | 2,880 | 22.06 MHz | FAIL | 115.20 µs | 26,329 | 336 | 100 | 8 |
| 8 | 1,600 | 14.82 MHz | FAIL | 64.00 µs | 52,974 | 336 | 196 | 12 |

**Selected architecture: 2 MAC lanes.**

The fixed selection rule was defined before observing these post-route results:

> choose the minimum modeled-cycle configuration among 1/2/4/8 lanes whose post-route Fmax meets the 25 MHz board clock.

As with the original digits workload, cycle-only optimization would favor wider configurations, but physical timing rejects the 4- and 8-lane candidates.

## Selected bitstream

A reference ULX3S bitstream was generated for the selected 2-lane implementation.

**Bitstream SHA-256:**  
`50761b00fad5afda5f18c9841291bceea47a04c94155df044b5fb60ef09b2590`

## What KRN-EXT-001 establishes

KRN-EXT-001 establishes that Kernellum can ingest a pinned public ONNX graph and weights authored outside Kernellum, preserve provenance, lower the supported graph, verify generated RTL, run board-targeted physical design, and use physical timing to select an implementation.

## Evidence boundary

KRN-EXT-001 is **external public-model L5 evidence**.

It does **not** establish:

- a customer or design-partner relationship;
- application accuracy on a real task dataset;
- arbitrary ONNX support;
- measured physical-board latency;
- measured board power or energy;
- ASIC performance or production readiness.

Those remain separate evidence thresholds.

Protocol: [KRN-EXT-001_PROTOCOL.md](KRN-EXT-001_PROTOCOL.md)  
Physical measurement protocol: [KRN-HW-001_PROTOCOL.md](KRN-HW-001_PROTOCOL.md)
