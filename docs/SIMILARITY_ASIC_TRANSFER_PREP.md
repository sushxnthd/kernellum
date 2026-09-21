# Project SIMILARITY: preparation for cross-technology transfer

Date: 2026-09-21

Status: stage-0 toolchain canary passed; no ASIC scientific result is claimed.

## Why this is the next breakthrough target

The confirmed ECP5 result shows that a two-candidate portfolio built from broadcast-only characterization can absorb route-seed variability and recover low-regret workload choices. Its largest remaining limitation is external validity: every causal and utility experiment uses one FPGA family and one place-and-route flow.

The next high-attention claim must remove that limitation rather than add another favorable ECP5 corpus.

The target question is:

> Can a dimensionless operand-transport timing law discovered in one open
> standard-cell technology predict unseen geometries in an independent open
> technology after a frozen six-point calibration?

## Novelty boundary

Physical-design-driven accelerator search is not itself new. Prior work has combined backend ASIC place-and-route data, learned PPA models and automated accelerator design-space exploration:

- H. Esmaeilzadeh et al., “An Open-Source ML-Based Full-Stack Optimization Framework for Machine Learning Accelerators,” arXiv:2308.12120.
- The OpenROAD project provides an autonomous, open RTL-to-GDSII flow for architecture exploration and physical implementation.

Kernellum must therefore not claim to invent physical-design-aware DSE.

The intended contribution is narrower and more falsifiable:

1. a causal intervention on operand-transport topology, not only a black-box PPA predictor;
2. a prospective discovery/bridge/holdout test across NanGate45 and Sky130HD;
3. a dimensionless effect and frozen affine technology calibration;
4. complete public RTL, constraints, layouts, raw metrics and null retention.

## Free toolchain

The preparation uses OpenROAD Flow Scripts because the official flow integrates:

- Yosys logic synthesis;
- OpenROAD floorplanning, placement, clock-tree synthesis and detailed routing;
- KLayout finishing and public-platform checks;
- machine-readable quality-of-results metrics.

The first canary uses the bundled NanGate45 platform. The independent transfer
gate uses Sky130HD. ASAP7 was attempted and excluded after a reproducible
final-output serialization failure on public runners.

No fabricated chip, commercial PDK, paid EDA license, cloud credit or external hardware is required.

## Stage 0: non-scientific canary

The canary routes fixed 3x3 broadcast and registered-local fabrics through the complete NanGate45 flow. It exists only to verify:

- SystemVerilog elaboration;
- clock and I/O constraints;
- placement, clock-tree synthesis and detailed routing;
- artifact retention;
- parseable timing, area and routing reports.

The canary geometries and metrics are permanently excluded from any later discovery or confirmation corpus. No comparison between its broadcast and local results may be promoted as scientific evidence.

## Frozen experiment

The canaries passed and the eligible study is now frozen separately in
`docs/SIMILARITY_ASIC_TRANSFER_PREREGISTRATION.md`. It will:

1. route six matched geometries on NanGate45;
2. calibrate on the same six geometries in Sky130HD;
3. predict four unopened Sky130HD geometries;
4. retain every null and report cell, register, area and wirelength costs;
5. evaluate one all-or-nothing 17-criterion gate.

Power and energy will not be claimed unless the flow produces a documented, reproducible activity model. Timing-only results will be labelled timing-only.

## Stop conditions

The cross-technology study is not opened if:

- the canary cannot complete detailed routing reproducibly;
- the flow silently optimizes away the intended topology distinction;
- timing extraction is not based on a documented post-route endpoint;
- broadcast and local RTL are not functionally equivalent under their pipeline alignment;
- the chosen open platforms cannot produce comparable normalized metrics.

Passing the canary authorizes experiment design, not a positive scientific claim.

## Stage-0 outcome

The audited canary completed on 2026-09-21. Both fixed 3x3 designs reached final GDS and passed the artifact, final-timing, detailed-route DRC and structural-retention gates. The decision record is in `docs/SIMILARITY_ASIC_CANARY_REPORT.md`.

The workflows are pinned to one immutable ORFS container digest, and
`scripts/similarity_asic_canary_validate.py` emits machine-readable audit
records. All 3x3 measurements remain excluded from science.
