# Project SIMILARITY: fixed-PE communication-diameter stress test

Date frozen: 2026-09-20

## Objective

Distinguish a true communication-diameter mechanism from a simple PE-count correlation.

The previously confirmed square-root law was observed over varying PE counts. For square arrays, sqrt(PE) and array side length are the same quantity. This experiment holds PE count fixed while changing physical aspect ratio.

## Device

Lattice ECP5-85K, CABGA381, speed grade 6.

Use the same two controlled INT8 MAC fabrics as the causal mechanism experiment:

- broadcast row/column operand distribution;
- registered nearest-neighbor local propagation.

Placement seeds:

- 1
- 2
- 3.

## Fixed-PE geometry groups

### P = 64

- 2x32
- 4x16
- 8x8
- 16x4
- 32x2

### P = 96

- 4x24
- 6x16
- 8x12
- 12x8
- 16x6
- 24x4

Every design within a group has exactly the same PE count and arithmetic.

Define communication span proxy

    D = max(ROWS, COLS).

Total planned routes:

11 geometries x 2 topologies x 3 seeds = **66 routes**.

## Frozen analysis

For each geometry/topology, use the median critical period over three seeds.

Fit the pooled fixed-effect model

    period_ns =
        alpha_64 * I(P=64)
      + alpha_96 * I(P=96)
      + beta_broadcast * D
      + delta_local
      + delta_slope * local * D.

Derived slopes:

    broadcast_span_slope = beta_broadcast
    local_span_slope = beta_broadcast + delta_slope.

For each PE group, also compute Spearman correlation between median period and D separately for broadcast and local.

## Preregistered diameter gate

The communication-diameter mechanism is supported only if all hold:

1. at least 63 of 66 routes succeed;
2. every successful design maps exactly one MULT18X18D per PE;
3. broadcast_span_slope >= 0.15 ns per unit D;
4. local_span_slope <= 0.50 * broadcast_span_slope;
5. delta_slope < 0;
6. broadcast Spearman(period,D) >= 0.75 in both P=64 and P=96 groups;
7. for each PE group, the most elongated broadcast geometry has median period at least 15% above the most compact geometry;
8. for each PE group, the elongated-minus-compact period penalty under local propagation is <= 50% of the corresponding broadcast penalty;
9. median per-geometry seed coefficient of variation <= 5% for both topologies.

## Why this is discriminative

Within P=64, both PE count and sqrt(PE) are constant.

Within P=96, both PE count and sqrt(PE) are constant.

Therefore any systematic timing change with D cannot be explained by PE count or the original square-root variable alone.

A positive result would refine the empirical square-root law into a geometric communication-diameter principle.

## Falsification

If fixed-PE aspect ratio does not produce the predicted broadcast timing penalty, communication diameter is not sufficient to explain the original scaling relation and the geometric model must be revised.

## Claim boundary

A pass supports communication span as a causal timing variable in these controlled ECP5 fabrics. It does not establish a universal physical law across FPGA vendors, arbitrary placement tools, or ASIC processes.
