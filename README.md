# Kernellum Research

**AI-native systems for efficient computing.**

![Kernellum Research](docs/og-card.svg)

**Kernellum is building an AI-native compiler for workload-specific accelerators.**

Given a trained model and deployment constraints, **Kernellum Compiler** lowers the workload into a hardware IR, searches candidate accelerator architectures, emits inspectable SystemVerilog, and generates verification evidence.

The current system is a research-stage prototype—not a production silicon compiler—but the model-to-RTL path is public and reproducible. Kernellum now also runs a board-targeted physical-feedback search on a ULX3S-85F reference target: the latest sweep selected a 2-lane accelerator after place-and-route timing rejected faster cycle-only candidates.

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
- **Public diligence index:** [`DILIGENCE.md`](DILIGENCE.md)
- **Investor brief:** [`INVESTOR_BRIEF.md`](INVESTOR_BRIEF.md)
- **Design partner program:** [`DESIGN_PARTNERS.md`](DESIGN_PARTNERS.md)
- **Benchmark policy:** [`BENCHMARKS.md`](BENCHMARKS.md)
- **ULX3S P&R evidence:** [`research/ULX3S_PNR_SWEEP_2026-09-18.md`](research/ULX3S_PNR_SWEEP_2026-09-18.md)
- **KRN-EXT-001 result:** [`research/KRN-EXT-001_RESULT.md`](research/KRN-EXT-001_RESULT.md)
- **KRN-BENCH-001 result:** [`research/KRN-BENCH-001_RESULT.md`](research/KRN-BENCH-001_RESULT.md)
- **External workload protocol:** [`research/KRN-EXT-001_PROTOCOL.md`](research/KRN-EXT-001_PROTOCOL.md)
- **Physical measurement protocol:** [`research/KRN-HW-001_PROTOCOL.md`](research/KRN-HW-001_PROTOCOL.md)
- **ULX3S hardware-access call:** [Issue #9](https://github.com/sushxnthd/kernellum/issues/9)
- **Document index:** [`DOCUMENTS.md`](DOCUMENTS.md)

[![verify](https://github.com/sushxnthd/kernellum/actions/workflows/verify.yml/badge.svg)](https://github.com/sushxnthd/kernellum/actions/workflows/verify.yml)
[![reference-pnr](https://github.com/sushxnthd/kernellum/actions/workflows/reference-pnr.yml/badge.svg)](https://github.com/sushxnthd/kernellum/actions/workflows/reference-pnr.yml)
[![benchmark-pnr](https://github.com/sushxnthd/kernellum/actions/workflows/benchmark-pnr.yml/badge.svg)](https://github.com/sushxnthd/kernellum/actions/workflows/benchmark-pnr.yml)

## Why Kernellum

Most AI deployment treats hardware as fixed. Kernellum treats the workload, latency target, precision, memory budget and deployment constraints as inputs to the hardware-design process.

The intended long-term interface is:

```text
model + constraints → hardware IR → architecture search → verified RTL → FPGA / ASIC
```

The goal is not an LLM that merely writes Verilog. The goal is a compiler-like co-design system whose outputs are constrained by the workload, verification chain and, over time, physical PPA feedback.

**Interested in evaluating a real workload?** See the [Design Partner Program](DESIGN_PARTNERS.md).  
**Evaluating Kernellum as a deep-tech venture?** See the [Investor Brief](INVESTOR_BRIEF.md).

## Kernellum Compiler v0.1 — frozen baseline

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

TR-001 freezes the first complete compiler baseline. The numbers below remain historical v0.1 evidence rather than being rewritten after later backend changes.

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

The 6.8 µs value is a **cycle-count estimate at an assumed 100 MHz clock**, not a physical timing-closure measurement. For this frozen v0.1 record, the generated RTL is verified through simulation and synthesis only; the newer v0.2 flow below carries the current board-targeted P&R/Fmax/resource evidence. Physical-board power, energy and measured latency remain future work.

## Reproduce v0.1

```bash
python -m pip install -e '.[test]'
pytest -q
python -m kernellum --out artifacts/digits_int8
bash scripts/run_eda.sh
```

## v0.2 alpha — physical feedback enters the loop

The current compiler slice introduces:

- validated ONNX lowering for a narrow sequential `Gemm/ReLU` subset;
- an explicit hardware IR;
- calibration-driven INT8 conversion;
- architecture search from the lowered graph;
- RTL/golden-vector emission for three-layer dense networks;
- a named **Lattice ECP5-85F** FPGA target profile for family-mapped synthesis;
- a **ULX3S-85F reference board target** with real package/clock/pin constraints;
- registered requantization stages reflected in cycle accounting;
- a board-targeted lane sweep that feeds post-route Fmax back into architecture selection;
- reproducible bitstream generation for the selected reference-board configuration.

### Physical-feedback result

| MAC lanes | Modeled cycles | Post-route Fmax | 25 MHz target | Modeled core latency @ 25 MHz |
|---:|---:|---:|:---:|---:|
| 1 | 2,836 | 35.96 MHz | PASS | 113.44 µs |
| **2** | **1,476** | **29.64 MHz** | **PASS** | **59.04 µs** |
| 4 | 796 | 22.12 MHz | FAIL | 31.84 µs |
| 8 | 456 | 16.10 MHz | FAIL | 18.24 µs |

**Selected for the ULX3S-85F 25 MHz reference target: 2 MAC lanes.** The selection rule chooses the lowest modeled cycle count among configurations whose post-route Fmax meets the board clock.

This is **Level-5 place-and-route evidence**, not a physical-board measurement. A bitstream was generated in CI; board programming, measured latency, power and energy remain unclaimed.

Full record: [KRN-PNR-001](research/ULX3S_PNR_SWEEP_2026-09-18.md).

### Multi-workload physical-feedback result

KRN-BENCH-001 repeats the same 1/2/4/8-lane ULX3S-85F search across three deterministic dense-network shapes. The clean-room workflow completed successfully and selected **2 lanes for all three workloads** after the 4- and 8-lane candidates missed the 25 MHz target.

| Shape | Selected lanes | Selected post-route Fmax | Modeled cycles @ 25 MHz |
|---|---:|---:|---:|
| 32 → 16 → 8 → 4 | 2 | 31.55 MHz | 392 |
| 64 → 32 → 16 → 10 | 2 | 29.76 MHz | 1,476 |
| 128 → 64 → 32 → 8 | 2 | 28.10 MHz | 5,456 |

This establishes multi-shape L5 place-and-route evidence, not customer validation or physical-board measurement. Full record: [KRN-BENCH-001](research/KRN-BENCH-001_RESULT.md).

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

**Kernellum Compiler is a research prototype, not a production silicon compiler.** The ULX3S-85F reference flow completes board-targeted place-and-route, physical-feedback architecture selection and bitstream generation in CI. KRN-BENCH-001 now demonstrates that the same timing-constrained selection loop executes across three dense-network shapes, and KRN-EXT-001 completes the clean-room L5 path on a pinned third-party tiny-NPU model. In every completed sweep, physical timing rejects the cycle-faster 4/8-lane candidates and selects 2 lanes for the 25 MHz target. KRN-HW-001 provides the frozen programming, raw-data and analysis path for the next threshold: physical-board correctness, latency, power and energy measurements. Physical execution remains tracked in [Issue #1](https://github.com/sushxnthd/kernellum/issues/1), with compatible-board access requested in [Issue #9](https://github.com/sushxnthd/kernellum/issues/9).

## People

**Sushanth Dasari — Founder & Research Lead**

## Research output

- **Technical Report 001:** *Kernellum Compiler v0.1: Constraint-Driven Generation of a Quantized Neural Accelerator* — [`PDF`](research/TR-001.pdf) · [`source`](research/TR-001.md)

## Site

**https://sushxnthd.github.io/kernellum/**
