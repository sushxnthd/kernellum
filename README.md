# Kernellum Research

**AI-native systems for efficient computing.**

Kernellum Research is an independent research initiative exploring automated hardware–software co-design, specialized AI acceleration, and AI-assisted electronic design automation.

Its flagship project is **Kernellum Compiler v0.1**, a research prototype that takes a quantized neural workload and hardware constraints, searches a small accelerator design space, emits FPGA-oriented SystemVerilog, and generates verification artifacts.

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
RTL simulation / synthesis flow
```

### Current demonstrated workload

| Metric | Result |
|---|---:|
| Network | 64 → 32 → 16 → 10 MLP |
| Dataset | scikit-learn handwritten digits |
| Held-out samples | 450 |
| Float accuracy | **96.22%** |
| INT8 accuracy | **96.44%** |
| Float/INT8 prediction agreement | **99.78%** |
| Cycle-model / vector-INT8 match | **450 / 450** |
| Selected architecture | **4 MAC lanes** |
| Core compute cycles | **680** |
| Modeled latency @ 100 MHz | **6.8 µs** |

The 6.8 µs value is a **cycle-count estimate at an assumed 100 MHz clock**, not an FPGA timing-closure measurement. Physical FPGA resource, power, Fmax, and measured latency results are not yet claimed.

## Reproduce

```bash
python -m pip install -e '.[test]'
pytest -q
python -m kernellum --out artifacts/digits_int8
```

With Icarus Verilog and Yosys installed:

```bash
bash scripts/run_eda.sh
```

GitHub Actions repeats the Python tests, regenerates the accelerator, runs the RTL testbench, and invokes Yosys synthesis.

## Repository map

```text
kernellum/                Python research prototype
artifacts/digits_int8/    generated RTL, weights, golden vectors, report
research/TR-001.md        first technical report
scripts/                  build and EDA flows
tests/                    pipeline tests
docs/                     GitHub Pages site
.github/workflows/        clean-room verification CI
```

## Research directions

- automated hardware–software co-design
- architecture search under latency / area / power constraints
- quantized and mixed-precision accelerators
- AI-assisted RTL generation and verification
- edge AI systems
- model-to-hardware compilation

## Status

**v0.1 is a research prototype, not a production silicon compiler.** The next milestone is a named FPGA target with post-place-and-route timing/resource results and measured board-level inference.

## People

**Sushanth Dasari — Founder & Research Lead**

## Research output

- **Technical Report 001:** *Kernellum Compiler v0.1: Constraint-Driven Generation of a Quantized Neural Accelerator* — [`research/TR-001.md`](research/TR-001.md)
