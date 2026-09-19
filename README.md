# Kernellum K0

Workload-aware accelerator design-space exploration.

K0 is the first technical proof for Kernellum's reset thesis: given an AI workload and hardware constraints, search a parameterized accelerator space and return strong feasible designs plus a Pareto frontier.

Status: analytical research prototype. K0 does not claim FPGA-measured performance. The cost model is deliberately transparent and is intended to be calibrated against synthesis and hardware in K1.

## Current reproducible result

The benchmark evaluates 12 representative Transformer GEMMs. Each workload has a 24,576-point architecture space. INT8 is fixed and DSP/BRAM constraints are binding.

At 256 architecture evaluations, evolutionary search averages 0.43% latency regret relative to exhaustive search, versus 3.79% for random search. Across workload/seed trials it exactly reaches the exhaustive optimum 60.0% of the time, versus 8.3% for random search.

These are analytical-model results, not hardware measurements.

## Quick start

Install editable dependencies, then run:

    kernellum search --workload ffn_expand --seq 128 --method evolutionary --budget 256 --max-dsp 512 --max-bram 120 --precision 8

Full experiment:

    python experiments/k0_transformer/run.py

Tests:

    pytest -q

## What K0 searches

- systolic array rows and columns
- INT4 / INT8 support
- M/N/K tile sizes
- on-chip buffer size
- weight-, output-, and row-stationary dataflow proxies

## Scientific boundary

The model uses fixed frequency and bandwidth, proxy DSP packing, approximate memory traffic, and no place-and-route timing closure. K0 is useful for ranking hypotheses, not claiming real hardware speedups.

K0.5 must synthesize a stratified sample of candidates and quantify rank correlation and prediction error. K1 proceeds only if the analytical ranking remains useful after calibration.

## K0.5 synthesis-validation gate

K0.5 adds a parameterized signed MAC array, block-RAM scratchpad, self-checking matrix-multiplication simulation, and a stratified Xilinx-7 synthesis experiment. The goal is to test whether K0's coarse DSP/BRAM resource ranking survives real RTL synthesis before K1 adds a full tiled accelerator controller.

Run with an OSS CAD Suite environment:

    scripts/run_rtl_sim.sh
    PYTHONPATH=. python scripts/synthesize_k05.py

See `docs/K05_PLAN.md` for the predeclared validation thresholds. No K0.5 synthesis result should be treated as FPGA-measured latency or power.

## Repository reset

This repository intentionally replaces Kernellum's previous product/company prototype. The current project is research-first: evidence before branding.

## Licensing

No open-source license is attached at the reset point. Future public benchmark code and potentially protectable K1+ implementation/IP will be separated deliberately before licensing decisions are made.
