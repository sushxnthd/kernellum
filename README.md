# Kernellum Research

**AI-native systems for efficient computing.**

![Kernellum Research](docs/og-card.svg)

**Kernellum is building an AI-native compiler for workload-specific accelerators.**

Given a trained model and deployment constraints, **Kernellum Compiler** lowers the workload into a hardware IR, searches candidate accelerator architectures, emits inspectable SystemVerilog, and generates verification evidence.

The current system is a research-stage prototype—not a production silicon compiler—but the model-to-RTL path is public, reproducible, and being pushed toward physical FPGA validation.

## Explore Kernellum

- **Site:** https://sushxnthd.github.io/kernellum/
- **Build log:** https://sushxnthd.github.io/kernellum/log.html
- **Evidence explorer:** https://sushxnthd.github.io/kernellum/evidence.html
- **FPGA bring-up tracker:** https://sushxnthd.github.io/kernellum/hardware.html
- **Launch/share copy:** [`LAUNCH.md`](LAUNCH.md)
- **Technical Report 001:** https://sushxnthd.github.io/kernellum/TR-001.pdf
- **Evidence Dossier v0.2:** https://sushxnthd.github.io/kernellum/Kernellum_Evidence_Dossier_v0.2.pdf
- **Reproducibility Guide v0.2:** https://sushxnthd.github.io/kernellum/Kernellum_Reproducibility_Guide_v0.2.pdf
- **FPGA Bring-up Protocol v0.1:** https://sushxnthd.github.io/kernellum/Kernellum_FPGA_Bringup_Protocol_v0.1.pdf
- **Build Log (Sep 2026):** https://sushxnthd.github.io/kernellum/Kernellum_Build_Log_2026-09.pdf
- **Investor brief:** [`INVESTOR_BRIEF.md`](INVESTOR_BRIEF.md)
- **Design partner program:** [`DESIGN_PARTNERS.md`](DESIGN_PARTNERS.md)
- **Benchmark policy:** [`BENCHMARKS.md`](BENCHMARKS.md)
- **Document index:** [`DOCUMENTS.md`](DOCUMENTS.md)

[![verify](https://github.com/sushxnthd/kernellum/actions/workflows/verify.yml/badge.svg)](https://github.com/sushxnthd/kernellum/actions/workflows/verify.yml)

## Why Kernellum

Most AI deployment treats hardware as fixed. Kernellum treats the workload, latency target, precision, memory budget and deployment constraints as inputs to the hardware-design process.

The intended long-term interface is:

```text
model + constraints → hardware IR → architecture search → verified RTL → FPGA / ASIC
```

The goal is not an LLM that merely writes Verilog. The goal is a compiler-like co-design system whose outputs are constrained by the workload, verification chain and, over time, physical PPA feedback.

**Interested in evaluating a real workload?** See the [Design Partner Program](DESIGN_PARTNERS.md).  
**Evaluating Kernellum as a deep-tech venture?** See the [Investor Brief](INVESTOR_BRIEF.md).

## Kernellum Compiler v0.1

```text
trained neural network
        ↓
INT8 quantization
        ↓
hardware constraint
        ↓
architecture search
        ↓
selected accelerator
        ↓
SystemVerilog + weights
        ↓
cycle-accurate verification
        ↓
RTL simulation + Yosys synthesis
```

### Demonstrated workload

| Metric | Result |
|---|---:|
| Network | 64 → 32 → 16 → 10 MLP |
| Dataset | scikit-learn handwritten digits |
| Held-out samples | 450 |
| Float accuracy | **96.22%** |
| INT8 accuracy | **96.44%** |
| Float/INT8 prediction agreement | **99.78%** |
| Cycle-model / vector-INT8 match | **450 / 450** |
| RTL golden-vector simulation | **32 / 32 PASS** |
| Selected architecture | **4 MAC lanes** |
| Core compute cycles | **680** |
| Modeled latency @ 100 MHz | **6.8 µs** |
| Generic Yosys synthesis | **PASS, 0 CHECK problems** |

The 6.8 µs value is a **cycle-count estimate at an assumed 100 MHz clock**, not a physical timing-closure measurement. The latest CI run proves the generated RTL simulates and synthesizes under Icarus Verilog + Yosys; physical FPGA resource, power, Fmax and measured latency results remain future work.

## Reproduce v0.1

```bash
python -m pip install -e '.[test]'
pytest -q
python -m kernellum --out artifacts/digits_int8
bash scripts/run_eda.sh
```

## v0.2 alpha

The next compiler slice introduces:

- validated ONNX lowering for a narrow sequential `Gemm/ReLU` subset;
- an explicit hardware IR;
- calibration-driven INT8 conversion;
- architecture search from the lowered graph;
- RTL/golden-vector emission for three-layer dense networks;
- a named **Lattice ECP5-85F** FPGA target profile for family-mapped synthesis.

This is intentionally a constrained front-end, not a claim of arbitrary ONNX support.

## Repository map

```text
kernellum/                Python compiler and hardware IR
artifacts/digits_int8/    generated v0.1 RTL, weights and golden vectors
research/TR-001.md        report source
research/TR-001.pdf       publication-style Technical Report 001
scripts/                  EDA and FPGA-family mapping flows
tests/                    pipeline and ONNX-front-end tests
docs/                     GitHub Pages site
.github/workflows/        clean-room verification CI
```

## Research directions

- automated hardware-software co-design
- architecture search under latency / area / power constraints
- quantized and mixed-precision accelerators
- AI-assisted RTL generation and verification
- edge AI systems
- model-to-hardware compilation

## Status

**Kernellum Compiler is a research prototype, not a production silicon compiler.** The next major evidence threshold is a named FPGA implementation with place-and-route timing/resource results and measured board-level inference. The physical bring-up is tracked in [Issue #1](https://github.com/sushxnthd/kernellum/issues/1), and `scripts/run_pnr_ecp5.sh` now provides a board-explicit nextpnr scaffold that refuses to invent package/clock constraints.

## People

**Sushanth Dasari — Founder & Research Lead**

## Research output

- **Technical Report 001:** *Kernellum Compiler v0.1: Constraint-Driven Generation of a Quantized Neural Accelerator* — [`PDF`](research/TR-001.pdf) · [`source`](research/TR-001.md)

## Site

**https://sushxnthd.github.io/kernellum/**
