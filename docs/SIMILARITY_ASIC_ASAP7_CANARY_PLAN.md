# Project SIMILARITY: ASAP7 transfer canary

Date frozen: 2026-09-21

Status: non-scientific platform qualification; no ASAP7 result is claimed.

## Purpose

The NanGate45 canary proved that the pinned open flow can carry both diagnostic transport structures through RTL-to-GDS. The confirmation study requires a second, materially different open standard-cell platform. This stage qualifies the bundled ASAP7 predictive 7 nm platform before any scientific geometry is opened.

## Frozen configuration

- OpenROAD Flow Scripts: `3a964e13f11a4e435aac01ffa14db0a7d2853720`
- container: `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`
- platform: `asap7`
- library corner: `TC` (typical case)
- clock constraint: 10.0 ns
- core utilization: 35%
- placement density: 0.50
- geometry: fixed 3x3 broadcast and registered-local canaries

The 3x3 geometry was already opened during NanGate45 plumbing. It remains permanently excluded from discovery, transfer fitting, confirmation, effect-size estimation and publicity on every platform.

## Pass gate

The platform qualifies only if both topologies:

1. elaborate successfully;
2. retain nonzero combinational and sequential logic;
3. reach final GDS, ODB, SPEF and gate-level netlist;
4. produce parseable final-route timing;
5. report zero final setup, hold, slew, fanout and capacitance violations;
6. report zero detailed-route DRCs;
7. retain a structural topology distinction after synthesis.

Any timing, area, wirelength or power difference is inadmissible as scientific evidence. Power is additionally inadmissible because no switching-activity model is supplied.

Passing this gate authorizes preregistration, not execution, of the cross-technology experiment.
