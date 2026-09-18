# Kernellum FPGA Bring-up Protocol

**Document ID:** KRN-HW-001  
**Version:** v0.1  
**Author:** Sushanth Dasari — Kernellum Research  
**Date:** September 2026

## Purpose

This protocol defines the evidence required before Kernellum may claim physical FPGA implementation, achieved timing, measured inference latency, board power, or energy per inference.

## Starting point

The repository currently has:
- an ECP5-85F family target profile;
- passing Yosys `synth_ecp5` family mapping;
- a board-explicit `scripts/run_pnr_ecp5.sh` scaffold.

It does **not** yet have a validated physical board.

## Board record

Record the exact:
- board model;
- FPGA device;
- package;
- oscillator frequency;
- programming path;
- supply/power measurement method.

## Place-and-route

```bash
PACKAGE=<exact-package> \
LPF=<board.lpf> \
FREQ_MHZ=<target-clock> \
bash scripts/run_pnr_ecp5.sh
```

The script intentionally refuses to invent package, LPF, or target clock values.

Preserve:
- nextpnr version;
- complete nextpnr log;
- target frequency;
- worst slack;
- achieved/max frequency;
- utilization summary.

Do not substitute the compiler's assumed 100 MHz modeling clock for achieved hardware timing.

## Board execution

1. Generate a board-compatible bitstream.
2. Program the actual board and record the tool/command.
3. Use the committed demo top or an equally documented host wrapper.
4. Confirm known inputs produce expected outputs.
5. Repeat after cold reset.

## Latency measurement

Preferred method: expose start and done markers to GPIO or a logic-analyzer-visible signal.

Report:
- clock frequency;
- number of repeated inferences;
- min/median/max latency;
- core-only vs end-to-end definition;
- exact measurement endpoints.

## Power and energy

Record:
- instrument;
- supply voltage;
- idle power;
- active power;
- inference window;
- energy/inference calculation or integration method.

## Publication threshold

Before publishing physical claims:
- named board/device/package documented;
- real constraint file committed;
- place-and-route log preserved;
- timing closure status reported;
- bitstream demonstrated;
- latency method documented;
- power/energy method documented;
- `BUILD_STATUS.md`, Evidence Explorer, Hardware Tracker, and next technical report updated from the same record.
