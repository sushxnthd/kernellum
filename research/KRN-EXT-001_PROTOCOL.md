# KRN-EXT-001 Protocol — Pinned Third-Party ONNX Workload

**Evidence ID:** KRN-EXT-001  
**Upstream project:** `harishsg993010/tiny-NPU`  
**Pinned upstream commit:** `8216c22b762011aa20c05fc2768423fd12dda59d`  
**Pinned upstream artifact:** `models/overlap_perf_test.onnx`  
**Expected Git blob SHA-1:** `070fb6c8f35e6f3b1d91e92143442367a25dc41b`  
**Target:** ULX3S-85F / LFE5U-85F-6BG381C / CABGA381  
**Clock target:** 25 MHz

## Why this workload

KRN-EXT-001 is Kernellum's first compiler experiment whose model graph and weights originate outside the Kernellum repository.

The upstream tiny-NPU project publishes an overlap-performance ONNX model with architecture:

```text
64 → 64 → 64 → 32
Gemm → ReLU → Gemm → ReLU → Gemm
```

That graph falls inside Kernellum's current deliberately narrow ONNX front-end, allowing an external-input test without changing or relaxing the compiler's supported-operator claim.

## Provenance rule

The upstream ONNX binary is **not vendored into Kernellum**.

The clean-room workflow downloads the model directly from the upstream repository at the pinned commit and recomputes the Git blob identity:

```text
sha1("blob " + byte_length + NUL + model_bytes)
```

Compilation aborts if the downloaded model does not equal the pinned blob.

Kernellum also records a SHA-256 digest of the retrieved binary in the generated manifest.

## Data boundary

The upstream artifact is a hardware performance-test model and does not include an application dataset for this graph.

Kernellum therefore supplies deterministic synthetic inputs only for:

- calibration of the current INT8 lowering path;
- generation of golden input/output tensors;
- exact cycle-model/reference checking;
- RTL simulation.

Seed: `20260918`.

Therefore KRN-EXT-001 is evidence of **external model ingestion and implementation**, not external application accuracy or customer validation.

## Pre-route cycle model

| MAC lanes | Modeled cycles | Modeled core latency @25 MHz |
|---:|---:|---:|
| 1 | 10,560 | 422.40 µs |
| 2 | 5,440 | 217.60 µs |
| 4 | 2,880 | 115.20 µs |
| 8 | 1,600 | 64.00 µs |

These values are compiler cycle-model values and are not physical measurements.

## Physical-feedback selection rule

Sweep 1 / 2 / 4 / 8 MAC lanes against the same ULX3S-85F package, LPF and 25 MHz clock target.

Select:

> the minimum modeled-cycle configuration whose post-route Fmax meets 25 MHz.

If none of the four candidates closes timing, report **no feasible swept architecture**.

## Required evidence

Before KRN-EXT-001 is considered complete, the clean-room workflow must produce:

- exact upstream blob verification;
- successful ONNX lowering;
- exact vector/cycle-model agreement;
- generated RTL;
- Icarus golden-vector RTL simulation PASS;
- ECP5 synthesis;
- per-candidate nextpnr result;
- post-route Fmax where routing succeeds;
- resource evidence;
- explicit timing feasibility at 25 MHz;
- physical-feedback architecture selection or explicit no-feasible result;
- selected bitstream + SHA-256 when a feasible candidate exists.

## Reference-board wrapper

The upstream model has 32 outputs while the current ULX3S demo interface exposes four class LEDs.

For place-and-route evidence, the wrapper scans all 32 outputs and drives the low four bits of the winning index to the LED pins. This is sufficient to retain the full inference/argmax path during implementation, but it is **not** presented as a complete physical user interface for the 32-way model.

Full output tensors remain covered by generated golden-vector simulation.

## Reproduce

```bash
pip install -e '.[test,onnx]'
python scripts/build_external_tiny_npu.py

sudo apt-get install -y iverilog yosys nextpnr-ecp5 fpga-trellis

cd artifacts/external_tiny_npu
iverilog -g2012 -s tb_kernellum_dense3_accel -o simv \
  kernellum_dense3_accel.sv tb_kernellum_dense3_accel.sv
vvp simv
cd ../..

bash scripts/run_external_tiny_npu_pnr.sh
```

CI workflow:

```text
.github/workflows/external-tiny-npu.yml
```

## Evidence boundary

A successful KRN-EXT-001 establishes that Kernellum can accept a pinned public ONNX model whose graph/weights were authored outside Kernellum and carry it through the supported model-to-RTL and board-targeted physical-feedback flow.

It does **not** establish:

- a customer relationship;
- confidential design-partner validation;
- application accuracy on a real dataset;
- arbitrary ONNX support;
- physical-board execution;
- measured latency, throughput, power, or energy;
- ASIC readiness.

Those remain separate evidence thresholds.
