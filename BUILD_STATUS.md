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

The ECP5 mapping reports **7,977 LUT4**, **8 MULT18X18D**, **58 TRELLIS_DPR16X4**, **145 TRELLIS_FF**, plus carry/mux primitives, with 0 Yosys CHECK problems. These are family-mapped synthesis primitives, not place-and-route utilization or timing closure on a physical board.

## v0.2 alpha

The repository includes a strict sequential ONNX `Gemm/ReLU` front-end, an explicit hardware IR, calibration-driven INT8 lowering, architecture search, a three-layer dense RTL backend and an ECP5-85F target profile.

CI now builds a real ONNX model through this path and then simulates and synthesizes the resulting RTL. Physical place-and-route, measured board power and measured end-to-end latency remain unclaimed.


## Physical FPGA bring-up

**Status: OPEN — no physical board result is claimed yet.**

The repository now includes a generic `scripts/run_pnr_ecp5.sh` scaffold plus a **ULX3S-85F reference target** (`LFE5U-85F-6BG381C`, `CABGA381`, 25 MHz) with committed LPF constraints and `scripts/run_pnr_ulx3s_85f.sh`. CI now attempts board-targeted nextpnr place-and-route and bitstream generation. This is a reproducible reference build target, not evidence that Kernellum has loaded or measured a physical ULX3S board.

Next evidence steps:

1. verify the ULX3S-85F reference P&R/bitstream CI path and archive timing/utilization evidence;
2. obtain access to a compatible physical ECP5 board;
3. load the generated bitstream and confirm the demo path;
4. measure end-to-end latency;
5. measure board power;
6. compute energy per inference with method notes.

Tracking issue: https://github.com/sushxnthd/kernellum/issues/1

Public tracker: https://sushxnthd.github.io/kernellum/hardware.html
