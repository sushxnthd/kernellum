# Kernellum K2 Board-Ready Build Report

Date: 2026-09-20

## Status

**BOARD-READY. NOT PHYSICALLY VALIDATED.**

The cleaned K2 implementation has passed the entire software/toolchain gate:

- Python host tests: PASS
- UART RTL simulation: PASS
- Yosys synthesis: PASS
- ECP5-85K place-and-route: PASS
- 12 MHz board timing target: PASS
- ecppack bitstream generation: PASS
- all three frozen architectures: PASS

No physical FPGA board measurement is claimed in this report.

## Final cleanup result

The first K2 board wrapper used a variable result-address multiplication that caused one extra DSP to appear in the two non-power-of-two variants.

That protocol-side multiplication was replaced with a logic mux and the complete build was rerun.

Final DSP counts now exactly match compute-array PE counts:

| Variant | Expected compute DSPs | Final mapped DSPs |
| --- | ---: | ---: |
| 8x8 K32 | 64 | **64** |
| 10x12 K32 | 120 | **120** |
| 8x14 K64 | 112 | **112** |

The measurement/control shell therefore adds **zero DSPs** to the accelerator count in the final build.

## Final board images

| Variant | DSP | BRAM | LUT4 | FF | Post-route Fmax | 12 MHz target |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline 8x8 K32 | 64 | 4 | 8,928 | 2,551 | **48.98 MHz** | PASS |
| active 10x12 K32 | 120 | 6 | 11,898 | 4,439 | **39.93 MHz** | PASS |
| active 8x14 K64 | 112 | 6 | 15,055 | 4,188 | **41.72 MHz** | PASS |

The reported Fmax values are the final post-route nextpnr timing reports. K2 intentionally operates at the board's fixed 12 MHz bring-up clock, so these are implementation timing margins rather than measured board maximum frequencies.

## Bitstream integrity

### baseline_r08_c08_k32

SHA-256:

`e8c59c3f6772d076d783c271275089a28f077dc5d2d513edb6de691196966fbf`

Size: 455,852 bytes.

### active_r10_c12_k32

SHA-256:

`9a8609df56802cc2cb4adf3e1e5f92b1f6c27d3709393a7a9061c51ac1cbe05c`

Size: 567,650 bytes.

### active_r08_c14_k64

SHA-256:

`807ceec7f918bd254b3882f87a103bc816e267d765720a6e0950eecea0e8a00d`

Size: 567,633 bytes.

## UART simulation

The board-level serial path completed the self-checking protocol simulation and emitted:

`KERNELLUM_K2_UART_SIM_PASS`

This validates the simulated PING/INFO transport path before physical-board use.

## Physical next step

Program each image into SRAM on the real ECP5 EVN board and run the preregistered 100-trial benchmark described in `docs/K2_PLAN.md` and `docs/K2_BOARD_SETUP.md`.

Only after those raw physical JSON logs exist may the project status change from:

**K2 board-ready**

to:

**K2 physically validated**.
