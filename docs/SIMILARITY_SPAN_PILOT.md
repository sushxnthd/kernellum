# Project SIMILARITY: physical-span feasibility pilot

Date: 2026-09-20

This is a feasibility study, not a confirmatory experiment and not a breakthrough gate.

## Purpose

The logical fixed-PE diameter experiment failed, but the broadcast-vs-local intervention passed strongly. One possible reconciliation is that the relevant variable is **actual physical placement span** around ECP5 hard DSP resources, not the Verilog array's logical aspect ratio.

Before preregistering a causal physical-span experiment, verify that nextpnr can enforce substantially different DSP footprints for the same 7x7, 49-MAC netlist.

## Conditions

Device: ECP5-85K / CABGA381 / speed grade 6.

Topologies:
- broadcast;
- registered local propagation.

Placement modes:
- compact: constrain all 49 DSP cells into the minimum-Manhattan-span rectangle containing at least 49 MULT18X18D BELs;
- elongated: constrain seven groups of seven DSP cells into disjoint windows spread across a single DSP row.

Seed: 1 only.

Total pilot routes: 4.

## Pilot success conditions

This pilot is usable if:
- all four routes complete;
- all map 49 MULT18X18D cells;
- post-route placement metadata can be recovered;
- elongated DSP bounding-box Manhattan span is at least 1.5x the compact span for both topologies.

Timing is recorded but is exploratory. No pass/fail timing claim is made from this pilot.
