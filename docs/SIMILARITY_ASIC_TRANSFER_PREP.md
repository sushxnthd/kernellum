# Project SIMILARITY: preparation for cross-technology transfer

Date: 2026-09-21

Status: toolchain preparation only; no ASIC scientific result is claimed.

## Why this is the next breakthrough target

The confirmed ECP5 result shows that a two-candidate portfolio built from broadcast-only characterization can absorb route-seed variability and recover low-regret workload choices. Its largest remaining limitation is external validity: every causal and utility experiment uses one FPGA family and one place-and-route flow.

The next high-attention claim must remove that limitation rather than add another favorable ECP5 corpus.

The target question is:

> Does the communication-topology mechanism identified on an FPGA survive complete standard-cell ASIC physical design, and can the same bounded portfolio principle recover low-regret workload choices across technology and backend-flow variation?

## Novelty boundary

Physical-design-driven accelerator search is not itself new. Prior work has combined backend ASIC place-and-route data, learned PPA models and automated accelerator design-space exploration:

- H. Esmaeilzadeh et al., “An Open-Source ML-Based Full-Stack Optimization Framework for Machine Learning Accelerators,” arXiv:2308.12120.
- The OpenROAD project provides an autonomous, open RTL-to-GDSII flow for architecture exploration and physical implementation.

Kernellum must therefore not claim to invent physical-design-aware DSE.

The intended contribution is narrower and more falsifiable:

1. a causal intervention on operand-transport topology, not only a black-box PPA predictor;
2. a prospective test of whether the intervention's direction and geometry dependence transfer from FPGA routing to standard-cell ASIC routing;
3. a bounded two-candidate compiler policy that is evaluated against a full routed oracle;
4. complete public RTL, constraints, layouts, raw metrics and null retention.

## Free toolchain

The preparation uses OpenROAD Flow Scripts because the official flow integrates:

- Yosys logic synthesis;
- OpenROAD floorplanning, placement, clock-tree synthesis and detailed routing;
- KLayout finishing and public-platform checks;
- machine-readable quality-of-results metrics.

The first canary uses the bundled NanGate45 platform. A later independent transfer gate should use a second bundled open platform such as ASAP7 if the canary establishes a deterministic and auditable flow.

No fabricated chip, commercial PDK, paid EDA license, cloud credit or external hardware is required.

## Stage 0: non-scientific canary

The canary routes fixed 3x3 broadcast and registered-local fabrics through the complete NanGate45 flow. It exists only to verify:

- SystemVerilog elaboration;
- clock and I/O constraints;
- placement, clock-tree synthesis and detailed routing;
- artifact retention;
- parseable timing, area and routing reports.

The canary geometries and metrics are permanently excluded from any later discovery or confirmation corpus. No comparison between its broadcast and local results may be promoted as scientific evidence.

## Intended staged experiment

After the canary passes:

1. freeze a small ASIC discovery corpus on NanGate45;
2. measure post-route timing, standard-cell area, register count, wirelength and routing violations for matched broadcast/local pairs;
3. fit only dimensionless or technology-normalized quantities that can transfer across process libraries;
4. preregister an unseen-geometry confirmation on a disjoint platform and backend seeds;
5. evaluate both the causal topology claim and the two-candidate workload policy;
6. retain any failure without changing thresholds or omitting PPA costs.

Power and energy will not be claimed unless the flow produces a documented, reproducible activity model. Timing-only results will be labelled timing-only.

## Stop conditions

The cross-technology study is not opened if:

- the canary cannot complete detailed routing reproducibly;
- the flow silently optimizes away the intended topology distinction;
- timing extraction is not based on a documented post-route endpoint;
- broadcast and local RTL are not functionally equivalent under their pipeline alignment;
- the chosen open platforms cannot produce comparable normalized metrics.

Passing the canary authorizes experiment design, not a positive scientific claim.
