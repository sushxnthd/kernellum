# SIMILARITY B-local replica-preservation synthesis canary

Status: **synthesis-only B-local repair protocol fixed before results**.

The preserved selective physical diagnostic is permanently closed as an
opened-data null. Ten of twelve routes were electrically clean. Its
NanGate45 maximum paths moved from replicated A[7]/B[2:0] bits to still-
shared B[7:3] registers, with targeted median launch-Q fanout 16.

This distinct intervention keeps A[6:0] and both valid streams stride-two
shared, while preserving per-PE A[7] and all eight B bits. Lane-diverse
invalid reset values prevent synthesis from merging adjacent data replicas;
shared valid resets low, so invalid reset data is never accumulated. Signed-
GEMM equivalence must pass on the already-opened 5x8 and 8x5 shapes.

The pinned flow performs synthesis only, without placement or routing. Every
platform/shape row must match the structural counts predicted before results:

| Shape | Ordinary stride-two DFFs | Required B-local DFFs | Full-local DFFs | Fraction of local |
|---|---:|---:|---:|---:|
| 5x8 | 1,831 | **1,979** | 2,284 | 86.65% |
| 8x5 | 1,796 | **1,972** | 2,232 | 88.35% |

All four synthesis rows must exactly match and remain at or below 90% of
full-local DFFs. This canary establishes implementation fidelity only. A
failure stops the intervention. A pass permits designing a separately frozen
opened-data physical diagnostic; it is not timing evidence, confirmation or
a breakthrough.
