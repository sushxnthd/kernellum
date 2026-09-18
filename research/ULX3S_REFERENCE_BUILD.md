# ULX3S-85F Reference Build Validation

This note exists to validate the board-targeted CI path introduced for Kernellum's first named ECP5 reference target.

Target:
- Board family: ULX3S 85F
- FPGA: LFE5U-85F-6BG381C
- nextpnr package: CABGA381
- Clock: 25 MHz
- Constraints: `boards/ulx3s_85f/kernellum_demo.lpf`

A successful CI run establishes reproducible **place-and-route and bitstream-generation evidence only**.

It does not establish:
- physical board loading;
- measured Fmax on hardware;
- measured inference latency;
- measured power or energy/inference.

The corresponding logs and bitstream are emitted by the `verify` workflow.
