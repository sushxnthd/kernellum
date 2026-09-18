# Kernellum Reproducibility Guide

**Version:** v0.2  
**Author:** Sushanth Dasari — Kernellum Research  
**Date:** September 2026

This guide describes the clean-room path for reproducing the current public compiler, verification, and synthesis evidence.

## Environment

Recommended:
- Python 3.11
- current pip
- Icarus Verilog
- Yosys
- project ONNX extras

## Clone and install

```bash
git clone https://github.com/sushxnthd/kernellum.git
cd kernellum
python -m pip install -e '.[test,onnx]'
```

## Run Python verification

```bash
pytest -q
```

If a test fails, preserve the commit SHA, tool versions, dependency versions, and traceback before changing the environment.

## Regenerate v0.1

```bash
python -m kernellum --out artifacts/digits_int8
```

Expected public values:
- held-out samples: 450
- float accuracy: 96.22%
- INT8 accuracy: 96.44%
- prediction agreement: 99.78%
- selected architecture: 4 MAC lanes
- core cycles: 680
- modeled latency: 6.8 us at an assumed 100 MHz

## RTL simulation and generic synthesis

```bash
bash scripts/run_eda.sh
```

Current public expectation: 32/32 golden-vector RTL cases pass and Yosys finishes with 0 CHECK problems.

## ECP5 family synthesis

```bash
bash scripts/run_ecp5.sh
```

Current public family-mapped synthesis reports 7,977 LUT4 and 8 MULT18X18D primitives. This is not board-specific place-and-route.

## v0.2 alpha ONNX path

```bash
python scripts/build_onnx_demo.py
bash scripts/run_onnx_eda.sh
```

The front-end intentionally supports a narrow sequential Gemm/ReLU subset and should explicitly reject unsupported graphs.

## Independent reproduction record

Record:
1. exact Git commit SHA;
2. Python, Icarus Verilog and Yosys versions;
3. pytest and EDA logs;
4. manifest differences, if any;
5. any dependency/tool-version deviations.

Do not reinterpret the modeled 100 MHz latency as achieved hardware timing.

For board-specific physical work, use the FPGA Bring-up Protocol and GitHub Issue #1.
