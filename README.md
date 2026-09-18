# Kernellum Research

**AI-native systems for efficient computing.**

![Kernellum Research](docs/og-card.svg)

Kernellum Research is an independent research initiative exploring automated hardware-software co-design, specialized AI acceleration, and AI-assisted electronic design automation.

Its flagship project is **Kernellum Compiler**, a research prototype for mapping neural workloads and hardware constraints into accelerator architectures, RTL and verification evidence.

## Explore Kernellum

- **Site:** https://sushxnthd.github.io/kernellum/
- **Build log:** https://sushxnthd.github.io/kernellum/log.html
- **Evidence explorer:** https://sushxnthd.github.io/kernellum/evidence.html
- **FPGA bring-up tracker:** https://sushxnthd.github.io/kernellum/hardware.html
- **Launch/share copy:** [`LAUNCH.md`](LAUNCH.md)
- **Technical Report 001:** https://sushxnthd.github.io/kernellum/TR-001.pdf

[![verify](https://github.com/sushxnthd/kernellum/actions/workflows/verify.yml/badge.svg)](https://github.com/sushxnthd/kernellum/actions/workflows/verify.yml)

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
