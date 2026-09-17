# Kernellum build status

## v0.1 verified

The public GitHub Actions flow currently passes end-to-end:

- Python unit tests: **PASS**
- accelerator regeneration: **PASS**
- independent cycle-model / vector-INT8 agreement: **450/450**
- Icarus RTL golden-vector simulation: **32/32 PASS**
- generic Yosys synthesis: **PASS**
- Yosys final `check`: **0 problems**

The latest generic synthesis evidence reports 38,170 post-synthesis generic cells. This is not a device-specific FPGA utilization figure.

## v0.2 alpha in progress

The repository now includes an ONNX front-end for a deliberately narrow sequential `Gemm/ReLU` subset, a hardware IR, calibration-driven INT8 lowering, dense3 RTL emission and an ECP5-85F target profile.

Physical place-and-route, timing closure, measured board power and measured end-to-end latency are not yet claimed.
