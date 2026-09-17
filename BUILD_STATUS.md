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
