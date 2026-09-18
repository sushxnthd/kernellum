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

## KRN-EXT-001 external public-model validation

**Status: PASS — clean-room external-model L5 evidence complete.**

Pinned upstream model: `harishsg993010/tiny-NPU` at commit `8216c22b762011aa20c05fc2768423fd12dda59d`, `models/overlap_perf_test.onnx` (64 → 64 → 64 → 32).

The clean-room workflow verifies provenance, compiles the supported ONNX graph, passes generated RTL simulation and sweeps 1/2/4/8 lanes through ULX3S-85F place-and-route.

| lanes | post-route Fmax | closes 25 MHz | modeled cycles |
|---:|---:|:---:|---:|
| 1 | 33.51 MHz | yes | 10,560 |
| **2** | **28.18 MHz** | **yes** | **5,440** |
| 4 | 22.06 MHz | no | 2,880 |
| 8 | 14.82 MHz | no | 1,600 |

The fixed physical-feedback rule selects **2 lanes**. Selected bitstream SHA-256: `50761b00fad5afda5f18c9841291bceea47a04c94155df044b5fb60ef09b2590`.

Full record: `research/KRN-EXT-001_RESULT.md`.

The remaining major technical evidence threshold is **KRN-HW-001 physical-board execution and measurement**.
