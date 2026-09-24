# SIMILARITY replica-preservation synthesis canary

Status: **synthesis-only repair protocol fixed before results**.

The opened critical-bit physical diagnostic is permanently closed as a null.
Its intended replica registers were merged by the pinned synthesis flow:
post-synthesis DFF counts exactly equalled ordinary stride-two, and maximum
launch fanout remained 14 to 18. No physical route is repeated here.

This distinct implementation assigns lane-diverse reset values to data bits
while their shared valid bit is reset low. Invalid pipeline data is therefore
different across replicas during reset/clear but never accumulated. Once
valid data enters, the replicas carry the same operand value. The existing
two-transaction signed GEMM test must pass on the already-opened 5x8 and 8x5
shapes.

The pinned OpenROAD-flow-scripts synthesis is run without placement or
routing for both open platforms and both opened shapes. A pass requires the
exact structural counts predicted before synthesis:

| Shape | Prior stride-two DFFs | Required preserved DFFs | Full-local DFFs |
|---|---:|---:|---:|
| 5x8 | 1,831 | **1,899** | 2,284 |
| 8x5 | 1,796 | **1,872** | 2,232 |

All four synthesis rows must match the required DFF count and remain at or
below 90% of full-local. Source hashes, logs, synthesis metrics and functional
logs are artifacts. This canary establishes implementation fidelity only.
It cannot establish timing, area-normalized throughput, novelty, practical
utility or a scientific claim. A failure stops this repair. A pass permits
designing a separately frozen opened-data physical diagnostic; it does not
permit reusing any opened geometry or seed as confirmation.
