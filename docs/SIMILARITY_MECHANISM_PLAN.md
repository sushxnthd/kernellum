# Project SIMILARITY: causal mechanism experiment

Date frozen: 2026-09-20

## Background

Two independent routed corpora support the empirical relation

    Tcrit ~= 14.104 ns + 1.723 ns * sqrt(PE)

for the current regular INT8 tiled systolic RTL family.

The discovery corpus used even geometries/tile depths. The independent confirmation corpus used only unseen odd geometries and unseen K_TILE values and achieved 3.55% pooled period MAPE without coefficient refitting.

This experiment does not fit another timing law. It tests a causal mechanism.

## Mechanistic hypothesis

The sqrt(PE) timing term is caused primarily by physical signal-distribution distance/fanout in a two-dimensional compute fabric.

For roughly square arrays, linear physical extent grows as sqrt(PE). In the existing broadcast-fed structure, each row operand is distributed across a row and each column operand across a column.

### Intervention

Construct two diagnostic fabrics with identical INT8 multiply-accumulate PEs:

1. **broadcast**: one row operand source fans out to all PEs in that row and one column operand source fans out to all PEs in that column;
2. **local**: operands enter at the left/top edges and propagate through registered nearest-neighbor links before reaching each PE.

Both designs continuously execute MAC work. No workload scheduler, tile BRAM, or output reduction tree is included. Internal PEs are kept through synthesis.

If signal-distribution geometry is causal, replacing long broadcast nets with registered local transport should reduce the dependence of critical period on sqrt(PE).

## Devices and sizes

Same ECP5 family, CABGA381, speed grade 6.

25K:
- 3x3
- 5x5

45K:
- 3x3
- 5x5
- 7x7

85K:
- 3x3
- 5x5
- 7x7
- 9x9
- 11x11

Both topologies are routed for each point with nextpnr seeds:

- 1
- 2
- 3

Total planned routes: 60.

## Frozen analysis

For each device/topology/size, take the median critical period across the three seeds.

Fit the pooled fixed-effect model:

    period_ns =
        alpha_25k * I25
      + alpha_45k * I45
      + alpha_85k * I85
      + beta_broadcast * sqrt(PE)
      + delta_local
      + delta_slope * local * sqrt(PE)

where broadcast is the reference topology.

Derived slopes:

    broadcast_slope = beta_broadcast
    local_slope = beta_broadcast + delta_slope

No route is excluded except a tool-reported route failure.

## Preregistered causal gate

The signal-distribution mechanism is supported only if all hold:

1. at least 57 of 60 routes succeed;
2. every successful design maps exactly one ECP5 MULT18X18D per PE;
3. broadcast_slope >= 0.50 ns / sqrt(PE);
4. local_slope <= 0.50 * broadcast_slope;
5. on ECP5-85K at 11x11, the local topology's median critical period is at least 15% lower than broadcast;
6. median per-point seed coefficient of variation is <= 5% for both topologies;
7. the topology-by-sqrt(PE) interaction delta_slope is negative.

## Falsification

If the local topology does not materially reduce the square-root slope, the proposed broadcast-distance mechanism is rejected.

A failure cannot be reclassified as support merely because one size or device improves.

## Scientific claim boundary

If the gate passes, the supported causal claim is:

> In this controlled ECP5 INT8 MAC fabric, the observed square-root timing penalty is substantially mediated by nonlocal row/column operand distribution; converting operand transport to registered nearest-neighbor propagation suppresses the scaling term.

This is a mechanism result for a controlled FPGA fabric, not yet a universal theorem across FPGA vendors or ASIC technologies.
