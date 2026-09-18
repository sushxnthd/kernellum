# Kernellum build status

## v0.1 verified

The public GitHub Actions flow currently verifies:

- Python unit tests: **PASS**
- accelerator regeneration: **PASS**
- independent cycle-model / vector-INT8 agreement: **450/450**
- Icarus RTL golden-vector simulation: **32/32 PASS**
- generic Yosys synthesis: **PASS**
- Yosys final `check`: **0 problems**
- ECP5 family-mapped synthesis: **PASS**

The current regenerated 4-lane core maps to **7,756 LUT4**, **8 MULT18X18D**, **58 TRELLIS_DPR16X4**, **237 TRELLIS_FF**, plus carry/mux primitives, with 0 Yosys CHECK problems. These are family-mapped synthesis primitives; board-targeted utilization is reported separately below.

## v0.2 alpha

The repository includes a strict sequential ONNX `Gemm/ReLU` front-end, an explicit hardware IR, calibration-driven INT8 lowering, architecture search, a three-layer dense RTL backend and an ECP5-85F target profile.

CI builds a real ONNX model through this path, simulates and synthesizes the resulting RTL, and runs a ULX3S-85F physical-feedback place-and-route sweep. Physical board loading, measured board power and measured end-to-end latency remain unclaimed.


## Physical FPGA bring-up

**Status: REFERENCE P&R COMPLETE — physical board loading/measurement remains open.**

The repository includes a generic `scripts/run_pnr_ecp5.sh` flow plus a **ULX3S-85F reference target** (`LFE5U-85F-6BG381C`, `CABGA381`, 25 MHz) with committed LPF constraints. CI now completes a physical-feedback sweep across 1/2/4/8 MAC-lane variants.

| lanes | post-route Fmax | closes 25 MHz | modeled cycles |
|---:|---:|:---:|---:|
| 1 | 35.96 MHz | yes | 2,836 |
| **2** | **29.64 MHz** | **yes** | **1,476** |
| 4 | 22.12 MHz | no | 796 |
| 8 | 16.10 MHz | no | 456 |

The flow selects **2 lanes** as the lowest-cycle configuration that closes the reference board's 25 MHz clock. Selected post-route utilization includes **5,727 TRELLIS_COMB**, **333 TRELLIS_FF**, **30 TRELLIS_RAMW**, and **6 MULT18X18D**. CI generates a bitstream for this configuration.

This is reproducible **reference-board P&R evidence**, not evidence that Kernellum has loaded or measured a physical ULX3S board. Full record: `research/ULX3S_PNR_SWEEP_2026-09-18.md`.

Next evidence steps:

1. obtain access to a compatible physical ECP5 board;
2. load the generated bitstream and confirm the demo path;
3. measure end-to-end latency;
4. measure board power;
5. compute energy per inference with method notes;
6. repeat the physical-feedback loop on an external design-partner workload.

Tracking issue: https://github.com/sushxnthd/kernellum/issues/1

Public tracker: https://sushxnthd.github.io/kernellum/hardware.html
