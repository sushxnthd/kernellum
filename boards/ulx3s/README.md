# ULX3S-85F physical target

Kernellum's first named-board implementation target is the **ULX3S-85F**:

- FPGA: Lattice ECP5 LFE5U-85F-6BG381C
- nextpnr device flag: `--85k`
- package: `CABGA381`
- speed grade: 6
- onboard clock: 25 MHz
- clock pin: G2

The board wrapper maps:

- BTN0 -> reset (active low)
- FIRE1 / BTN1 -> one-shot inference start
- LED[3:0] -> predicted class
- LED[4] -> completion pulse
- GP0 -> measurement start marker
- GN0 -> measurement done marker

The PMOD marker pair makes it possible to measure core inference latency with a logic analyzer without relying on software timestamps.

This directory establishes a concrete board/package/pin target. It does **not** claim that a physical board has been programmed or measured yet.
