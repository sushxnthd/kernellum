# Build status — Kernellum Compiler v0.1

## Reproduced in the release build environment

- Python tests: **3/3 PASS**
- Float held-out accuracy: **96.22%**
- INT8 held-out accuracy: **96.44%**
- Float/INT8 prediction agreement: **99.78%**
- Cycle-accurate software model vs vector INT8 reference: **exact on 450/450 samples**
- Architecture search: **4 MAC lanes selected / 680 modeled core cycles**
- Generated weights, biases, golden vectors, RTL, manifest and technical report: **PASS**

## Pending independent EDA evidence

The release environment used to assemble this repository does not contain Icarus Verilog or Yosys, so local HDL simulation and synthesis are not claimed here. The GitHub Actions workflow installs both tools and runs:

1. Python regression tests
2. artifact regeneration
3. Icarus SystemVerilog compilation
4. 32-sample end-to-end RTL golden-vector simulation
5. Yosys synthesis/statistics

Physical FPGA timing closure, LUT/FF/DSP/BRAM use, board power and measured inference latency remain future work.
