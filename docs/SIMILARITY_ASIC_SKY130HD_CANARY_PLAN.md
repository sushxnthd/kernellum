# Project SIMILARITY: Sky130HD transfer canary

Date frozen: 2026-09-21

Status: non-scientific platform qualification; no Sky130HD result is claimed.

## Purpose

The NanGate45 canary proved that the pinned open flow can carry both diagnostic
transport structures through RTL-to-GDS. The confirmation study requires a
second, materially different standard-cell stack. This stage qualifies the
open Sky130HD 130 nm platform before any scientific geometry is opened.

ASAP7 was attempted first. Both canary topologies could reach clean detailed
routing, but the pinned OpenROAD executable repeatedly terminated with an
illegal instruction during final-output serialization. Since that stack could
not meet the complete-artifact gate on public runners, it is excluded from the
confirmation study rather than weakened into a partial-route claim.

## Frozen configuration

- flow source, tools and platform files: bundled contents of
  `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`
- platform: `sky130hd`
- library: `sky130_fd_sc_hd__tt_025C_1v80`
- clock constraint: 10.0 ns
- core utilization: 35%
- placement density: 0.50
- post-CTS repair timing: skipped with the documented ORFS CI switch because
  the pinned binary's repair/legalization block is not portable across the
  heterogeneous public-runner CPU pool
- final timing report: the same pinned OpenROAD executable runs through QEMU's
  deterministic `max` x86-64 CPU model; all physical-design stages remain
  native, and the final report remains the mandatory acceptance endpoint
- geometry: fixed 3x3 broadcast and registered-local canaries

The 3x3 geometry was opened only for plumbing. It remains permanently excluded
from discovery, transfer fitting, confirmation, effect-size estimation and
publicity on every platform.

## Pass gate

The platform qualifies only if both topologies:

1. elaborate successfully;
2. retain nonzero combinational and sequential logic;
3. reach final GDS, ODB, SPEF and gate-level netlist;
4. produce parseable final-route timing;
5. report zero final setup, hold, slew, fanout and capacitance violations;
6. report zero detailed-route DRCs;
7. retain a structural topology distinction after synthesis.

Any timing, area, wirelength or power difference is inadmissible as scientific
evidence. Power is additionally inadmissible because no switching-activity
model is supplied. Passing this gate authorizes preregistration, not execution,
of the cross-technology experiment.

The workaround cannot convert a timing failure into a pass: the validator
still rejects any nonzero final setup, hold, slew, fanout or capacitance count.
