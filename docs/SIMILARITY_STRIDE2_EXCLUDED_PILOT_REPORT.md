# SIMILARITY stride-two excluded 7x7 pilot

Result checked: 2026-09-24. Both excluded pilot routes are **electrically
clean**. This pilot is not a scientific confirmation.

The pilot reuses the already opened 7x7 geometry at seed 29 on NanGate45 and
Sky130HD. Both baseline topologies use the electrically qualified repair
settings; stride two uses the same clock, density, utilization, repair margins
and pinned ORFS image. The three implementations differ in operand transport.
These prior-geometry observations are **permanently excluded** from discovery,
threshold fitting, confirmation and effect-size estimation in the prospective
new-geometry study.

| Platform | Transport | Final period (ns) | Synthesis cell area (µm²) | DFF cells | Routed wire (µm) | Final violations |
|---|---|---:|---:|---:|---:|---:|
| NanGate45 | Broadcast | 1.73 | 64,235.808 | 1,650 | 428,873 | 0 |
| NanGate45 | Full local | 1.53 | 70,919.324 | 2,743 | 475,013 | 0 |
| NanGate45 | Stride two | 1.62 | 67,532.878 | 2,229 | 434,394 | 0 |
| Sky130HD | Broadcast | 8.29 | 304,852.3776 | 1,650 | 876,594 | 0 |
| Sky130HD | Full local | 7.20 | 330,998.704 | 2,743 | 989,204 | 0 |
| Sky130HD | Stride two | 7.79 | 318,975.9232 | 2,229 | 921,361 | 0 |

Both stride-two rows have six final electrical/DRC counts zero and four
64-digit artifact hashes. Each reduces DFF count 18.74% relative to full
local; synthesis cell area falls 4.78% on NanGate45 and 3.63% on Sky130HD.

| Platform | Stride-two period benefit vs broadcast | Benefit retained vs full local | Area-normalized throughput vs broadcast | Area-normalized throughput vs full local |
|---|---:|---:|---:|---:|
| NanGate45 | +6.36% | 55.0% | +1.58% | **−0.82%** |
| Sky130HD | +6.03% | 45.9% | +1.71% | **−4.09%** |

The area-normalized ratios use `(baseline_period * baseline_cell_area) /
(stride2_period * stride2_cell_area)`. They are synthesis-cell-area proxies,
not measured die area, power or energy. On the old shape, stride two saves
registers and area and beats broadcast on this proxy, but **full local remains
better on the same proxy on both platforms**. The critical stride-two path on
both platforms begins at a group operand register and ends at a PE
accumulator. The NanGate45 area-normalized loss to full local corresponds to
13.3 ps of stride-two period at the observed area. These signs and effect
sizes are descriptive only; a single old geometry and seed cannot settle a
later multi-seed, unopened-geometry hypothesis. In particular these pilot
retention percentages do not meet the proposed 60% fresh-holdout gate; that
gate is not redefined or claimed satisfied from the pilot.

The [pilot workflow](https://github.com/sushxnthd/kernellum/actions/runs/36011235219)
was triggered by merge commit `1084128368e81dde782c9b3afff47e41457bb8c9`.
Both unmodified route CSVs are checked in as
`results/similarity_stride2_pilot_{nangate45,sky130hd}.csv`, preserving the
full raw costs, final violation counts and physical-artifact hashes beyond
the workflow's 30-day retention period.
The [separate repair canary report](SIMILARITY_ASIC_REPAIR_CANARY_REPORT.md)
records the matched broadcast/full-local baselines and twelve-route electrical
qualification.
