# Kernellum Build Log — September 2026

**Document ID:** KRN-LOG-2026-09  
**Author:** Sushanth Dasari — Kernellum Research

This is a curated technical log. Routine styling and housekeeping commits are intentionally excluded.

## 17 September 2026 — Kernellum Compiler v0.1

Commit: `63e4a54d4c046862d90a2d7ff98e3791a194160e`

First public end-to-end path: model training, INT8 quantization, architecture search, independent cycle execution, generated SystemVerilog, weights, vectors, and verification collateral.

## 17 September 2026 — synthesis safety

Commits:
- `7a5913072338988f7bc4382bca5489a32d1ba92e`
- `af74d7a9d9ee243df63ac293582d2efd7bf73381`

Generated RTL was patched for synthesis safety before synthesis evidence was treated as valid.

## 17 September 2026 — TR-001 and v0.2 alpha

Commit: `b4ce966793a95c5cfbb6bda0ed20eb0fb6e91ffb`

TR-001 froze the v0.1 evidence record. v0.2 alpha introduced a deliberately narrow ONNX Gemm/ReLU front-end and explicit hardware IR.

## 17 September 2026 — ONNX-generated RTL + ECP5 mapping

Commit: `0bf4867c1477b04c6b6342241b9a2cf309cbf7f3`

CI began building a real ONNX model through the compiler path and simulating/synthesizing its generated RTL. ECP5 family synthesis evidence was exposed publicly.

## 18 September 2026 — public evidence surfaces

The site gained a curated Build Log, claim-to-artifact Evidence Explorer, and FPGA Bring-up Tracker.

## Current threshold

The next substantive milestone is physical FPGA evidence:
- named board;
- real package/constraints;
- place-and-route;
- achieved timing;
- programmed bitstream;
- measured inference latency;
- measured power/energy.

Tracking issue: https://github.com/sushxnthd/kernellum/issues/1
