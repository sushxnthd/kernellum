# Kernellum Press Kit

## One-line description

**Kernellum is building an AI-native compiler that maps supported neural workloads and deployment constraints into workload-specific accelerator architectures, RTL and verification evidence.**

## 50-word description

Kernellum is a research-stage AI-hardware venture exploring model-to-hardware compilation. Its compiler lowers supported neural workloads into a hardware IR, searches accelerator configurations under deployment constraints, emits inspectable SystemVerilog, and produces verification evidence. The next technical threshold is physical FPGA place-and-route and measured board-level performance.

## Current public evidence

- 96.22% float held-out accuracy on the demonstrated digits workload.
- 96.44% INT8 held-out accuracy.
- 99.78% float/INT8 prediction agreement.
- 450/450 cycle-model / vector-INT8 agreement.
- 32/32 generated RTL golden-vector cases PASS.
- Generic Yosys synthesis PASS with 0 CHECK problems.
- ECP5 family mapping: 7,977 LUT4 and 8 MULT18X18D.

### Important measurement boundary

The 680-cycle / 6.8 µs figure is modeled at an assumed 100 MHz clock. It is **not** an achieved physical Fmax or measured board latency. Physical FPGA P&R, latency, power and energy/inference remain pending.

## Founder

**Sushanth Dasari — Founder & Research Lead**

GitHub: https://github.com/sushxnthd

## Canonical links

- Project: https://sushxnthd.github.io/kernellum/
- Compiler: https://sushxnthd.github.io/kernellum/compiler.html
- Evidence explorer: https://sushxnthd.github.io/kernellum/evidence.html
- FPGA tracker: https://sushxnthd.github.io/kernellum/hardware.html
- Work with Kernellum: https://sushxnthd.github.io/kernellum/partner.html
- Repository: https://github.com/sushxnthd/kernellum
- TR-001: https://sushxnthd.github.io/kernellum/TR-001.pdf
- Investor brief: https://github.com/sushxnthd/kernellum/blob/main/INVESTOR_BRIEF.md

## Visual assets

- Primary mark: `docs/kernellum-mark.svg`
- Social / Open Graph card: `docs/og-card.svg`

## What Kernellum does not currently claim

Kernellum does not currently claim arbitrary ONNX coverage, production ASIC readiness, tapeout, measured FPGA performance, production safety certification, or guaranteed speedups on external workloads.

For factual reporting, please distinguish modeled results, family synthesis, post-route results and physical measurements.
