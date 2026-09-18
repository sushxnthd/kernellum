# Kernellum Evidence Dossier

**Document ID:** KRN-EVD-001  
**Version:** v0.2 evidence snapshot  
**Author:** Sushanth Dasari — Kernellum Research  
**Date:** September 2026

## Purpose

This dossier collects the public evidence supporting Kernellum's current technical claims. It keeps model results, integer-reference behavior, cycle-level behavior, generated RTL simulation, synthesis evidence, and physical-hardware evidence separate.

## Evidence hierarchy

| Level | Current status | Public evidence |
|---|---|---|
| Model / quantization | PASS | `manifest.json`, `compiler.py`, TR-001 |
| Cycle model | 450/450 exact | cycle model implementation and tests |
| Generated RTL | 32/32 golden cases | testbench + golden vectors |
| Generic synthesis | PASS; 0 CHECK problems | `run_eda.sh`, `BUILD_STATUS.md` |
| ECP5 family synthesis | PASS | `run_ecp5.sh`; 7,977 LUT4; 8 MULT18X18D |
| Place-and-route | not yet | no named-board P&R result claimed |
| Measured FPGA latency/power | not yet | no physical-board measurement claimed |

## Demonstrated workload

- Dataset: scikit-learn handwritten digits
- Network: 64 -> 32 -> 16 -> 10
- Held-out samples: 450
- Float accuracy: 96.22%
- INT8 accuracy: 96.44%
- Float/INT8 prediction agreement: 99.78%

## Architecture search

| MAC lanes | Cycles | Modeled latency @ 100 MHz | Meets <=10 us |
|---:|---:|---:|:---:|
| 1 | 2720 | 27.2 us | no |
| 2 | 1360 | 13.6 us | no |
| 4 | 680 | 6.8 us | yes — selected |
| 8 | 340 | 3.4 us | yes |
| 16 | 170 | 1.7 us | yes |

The 4-lane design is selected because it is the smallest candidate in the current search set satisfying the modeled latency target. **6.8 us is modeled, not measured.**

## Artifact map

| Claim | Artifact |
|---|---|
| 96.44% INT8 accuracy | `artifacts/digits_int8/manifest.json` |
| 450/450 cycle exact | `kernellum/compiler.py`, `tests/test_pipeline.py` |
| 32/32 RTL golden | `artifacts/digits_int8/tb_kernellum_mlp_accel.sv`, golden vectors |
| Generated accelerator | `artifacts/digits_int8/kernellum_mlp_accel.sv` |
| ECP5 mapping | `BUILD_STATUS.md`, `scripts/run_ecp5.sh` |
| Clean-room rerun | `.github/workflows/verify.yml` |
| Formal report | `research/TR-001.md` / PDF |

## Current ECP5 synthesis snapshot

- 7,977 LUT4
- 8 MULT18X18D
- 58 TRELLIS_DPR16X4
- 145 TRELLIS_FF

These are family-mapped synthesis primitive counts, not post-route board utilization.

## Unclaimed evidence

Kernellum does not yet claim named-board physical validation, place-and-route timing closure, achieved Fmax, measured board latency, measured power/energy, arbitrary ONNX coverage, ASIC readiness, or manufacturable silicon.

## Reproduce

```bash
pip install -e '.[test,onnx]'
pytest -q
python -m kernellum --out artifacts/digits_int8
bash scripts/run_eda.sh
bash scripts/run_ecp5.sh
python scripts/build_onnx_demo.py
bash scripts/run_onnx_eda.sh
```
