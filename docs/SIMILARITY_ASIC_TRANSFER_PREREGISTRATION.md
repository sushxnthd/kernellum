# Project SIMILARITY: cross-technology ASIC transfer preregistration

Date frozen: 2026-09-21

Status: **frozen before any eligible physical-design result is opened.**

## Question and claim target

Does the timing benefit of registered nearest-neighbor operand transport grow
with array geometry in one standard-cell technology, and can a dimensionless
law learned there predict unseen geometries in an independent open technology?

If every gate below passes, the supported claim is:

> In this controlled family of functionally equivalent INT8 MAC arrays, a
> dimensionless operand-transport timing law discovered in an open 45 nm
> standard-cell flow, then calibrated on six bridge geometries, predicted the
> sign and magnitude of the effect on unopened geometries in an independent
> open 130 nm flow.

This is the full claim. The experiment does not test power, energy, fabricated
silicon, commercial signoff, end-to-end inference or a workload portfolio.

## Scientific firewall

The pull-request workflow runs only functional simulation and synthetic
validator tests. Physical routes are enabled only by a push to `main`, so the
plan, RTL, analysis code, geometries, seeds and thresholds must merge before
eligible data can exist.

The fixed 3x3 NanGate45 and Sky130HD canaries were opened only to qualify the
flow. They are permanently excluded from fitting, calibration, confirmation,
effect-size estimation and publicity. No 3x3 value appears in this study.

## Causal intervention

The matched designs use the production Kernellum arithmetic arrays:

- broadcast: `kernellum_mac_array` distributes one registered row operand and
  one registered column operand directly to every consuming PE;
- registered-local: `kernellum_local_mac_array` propagates the same operands
  through registered nearest-neighbor links.

`rtl/similarity_asic_transfer_top.sv` supplies identical registered activity to
both arrays. A combinational XOR fold observes every accumulator so synthesis
cannot discard PEs; the digest output is declared a false timing path. Only
internal register-to-register timing enters the estimand.

Before routing, `rtl/tb_similarity_asic_transport_equivalence.sv` must compare
both `kernellum_gemm_engine` transports against the same software-computed
signed GEMM result at all ten geometries. It tests both cleared execution and
accumulation without clearing.

## Frozen technologies and flow

| Role | ORFS platform | Library corner | Geometries |
|---|---|---|---|
| Discovery | NanGate45 | `NangateOpenCellLibrary_typical` | six bridge geometries |
| Calibration + confirmation | Sky130HD | `sky130_fd_sc_hd__tt_025C_1v80` | six bridge + four holdouts |

Both use OpenROAD Flow Scripts and platform files bundled with the immutable
container:

`openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`

Frozen physical settings:

- clock constraint: 20.0 ns;
- core utilization: 35%;
- placement density: 0.50;
- seeds: 11, 29 and 47, applied to the supported ORFS perturbation controls
  `GPL_RANDOM_SEED` and `GRT_SEED`;
- post-CTS repair timing: skipped with the documented ORFS CI switch because
  that block is not portable across the public-runner CPU pool;
- synthesis, floorplanning, placement, CTS, routing and finishing: native;
- final `report_checks`: the same pinned OpenROAD executable under QEMU's
  deterministic `max` x86-64 CPU model;
- auxiliary Kepler LEC: disabled because its pinned Naja library raises SIGILL
  on part of the public-runner CPU pool even under QEMU 8.2. The frozen signed
  GEMM equivalence simulation at all ten geometries is authoritative.

Final setup, hold, slew, fanout, capacitance and detailed-route DRC counts remain
mandatory. Emulation changes instruction execution, not the routed database or
the timing executable.

## Frozen corpus

Bridge geometries, used in both technologies:

- 2x4
- 4x2
- 3x6
- 6x3
- 5x5
- 7x7

Sky130HD holdouts, never used for fitting or calibration:

- 3x8
- 8x3
- 5x9
- 9x5

Route count:

| Corpus | Calculation | Routes |
|---|---:|---:|
| NanGate45 discovery | 6 geometries x 2 topologies x 3 seeds | 36 |
| Sky130HD bridge | 6 geometries x 2 topologies x 3 seeds | 36 |
| Sky130HD holdout | 4 geometries x 2 topologies x 3 seeds | 24 |
| Total |  | **96** |

## Authoritative timing and estimand

The authoritative timing value is `clk period_min` from ORFS's final
`6_finish.rpt`. Console timing, pre-route timing and the reported raw data-path
delay are not substituted.

For a complete matched seed pair:

\[
q = \frac{T_{broadcast}-T_{local}}{T_{broadcast}}.
\]

The geometry value is the median of its complete-seed \(q\) values. At least
two complete seeds are required for every geometry in both technologies.

## Frozen model and transfer rule

Fit the six NanGate45 geometry medians by ordinary least squares:

\[
q_{NG} = \alpha + \beta\sqrt{PE}.
\]

Use that model to predict the six matching Sky130HD bridge geometries. Fit one
affine technology calibration on those six points:

\[
q_{SKY} = c + d\,\widehat{q}_{NG}.
\]

Then predict the four Sky130HD holdouts without changing \(\alpha\), \(\beta\),
\(c\), \(d\), the corpus or any threshold.

## Frozen all-or-nothing gate

The transfer claim is supported only if every criterion passes:

1. functional equivalence passes at all ten geometries;
2. exactly 96 unique routes are attempted and at least 92 succeed;
3. every successful route has zero final setup, hold, slew, fanout,
   capacitance and detailed-route DRC violations;
4. all 16 platform/geometry pairs retain at least two complete topology-matched
   seeds;
5. registered-local sequential-cell count exceeds broadcast for every complete
   seed pair;
6. the median period CV across platform/topology/geometry seed groups is at
   most 6%;
7. NanGate45 median \(q\) is positive for at least five of six geometries;
8. NanGate45 \(\beta > 0\);
9. NanGate45 7x7 median \(q \ge 0.05\);
10. Sky130HD bridge median \(q\) is positive for at least five of six
    geometries;
11. bridge predicted-versus-observed Spearman rank correlation is at least
    0.60;
12. calibration slope \(d > 0\);
13. at least three of four Sky130HD holdouts have positive median \(q\);
14. both 45-PE holdouts, 5x9 and 9x5, have median \(q \ge 0.05\);
15. holdout mean absolute prediction error is at most 0.08 in \(q\);
16. every holdout absolute prediction error is at most 0.15 in \(q\);
17. standard-cell count, sequential-cell count, cell area and routed
    wirelength are present for every successful implementation.

No subset can be relabelled as a pass. A failed criterion remains a negative or
inconclusive result under this preregistration.

## Nulls, failures and costs

Every planned key is written to CSV even when a route fails. Failed routes keep
their stage and remain null; they are never silently dropped or replaced. No
new seed, geometry, platform, clock or retry is added after results open.

The report must publish all routed nulls and, for both topologies, cell count,
sequential count, cell area and routed wirelength. Those costs are descriptive
and cannot be traded against a failed timing gate. Power and energy are
inadmissible because the study has no switching-activity model.

## Claim boundary

A pass would establish prospective transfer across two open/academic
standard-cell platforms inside one pinned ORFS toolchain. It would not
establish process-node universality, foundry signoff, silicon frequency,
voltage or temperature robustness, power, energy, or superiority for all
accelerator architectures.
