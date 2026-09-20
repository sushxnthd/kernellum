# Project SIMILARITY: critical-path decomposition diagnostic

Date: 2026-09-20

## Purpose

The confirmed square-root critical-period relation is a statement about the worst routed register-to-register path. Before assigning a mechanism to fanout, geometry, or congestion, identify what that path actually contains.

This diagnostic deliberately does **not** define a breakthrough gate. It is a mechanism-discovery study used to choose the next preregistered causal experiment.

## Design

Use the existing controlled DSP-backed square broadcast MAC fabric:

- `rtl/similarity_arithmetic_broadcast.sv`
- ECP5-85K / CABGA381 / speed grade 6
- N in {3,5,7,9,11}
- placement seeds {1,2,3,4,5}

Total: **25 routed implementations**.

## Extracted observables

From each nextpnr timing report:

- achieved Fmax and critical period;
- critical-path logic delay;
- critical-path routing delay;
- routing fraction of critical period;
- number of routed net arcs printed on the critical path;
- maximum and summed Manhattan displacement of those printed arcs;
- lexical path-class indicators for operand-source, accumulator, and counter/control nets.

Cell counts are recorded to verify one DSP per PE.

## Questions

1. Does critical-period growth with N arise primarily from routing delay while logic delay stays roughly stable?
2. Do critical paths actually traverse operand broadcast nets?
3. Are accumulator-feedback paths dominant?
4. Does routed path displacement grow with N?
5. Is placement-seed variability concentrated in routing rather than logic?

A strong answer to these questions determines the next causal intervention. No universal claim is made from this diagnostic alone.
