# Project SIMILARITY: ASAP7 transfer canary

Date frozen: 2026-09-21

Status: non-scientific platform qualification; no ASAP7 result is claimed.

## Purpose

The NanGate45 canary proved that the pinned open flow can carry both diagnostic transport structures through RTL-to-GDS. The confirmation study requires a second, materially different open standard-cell platform. This stage qualifies the bundled ASAP7 predictive 7 nm platform before any scientific geometry is opened.

## Frozen configuration

- OpenROAD Flow Scripts: `3a964e13f11a4e435aac01ffa14db0a7d2853720`
- container bootstrap: the ORFS repository's official
  `ghcr.io/the-openroad-project/openroad-flow-scripts/ubuntu22.04:latest`
  publication; its resolved digest must be recorded and pinned before the
  qualification run can be accepted
- platform: `asap7`
- library corner: `BC` (the ASAP7 platform default)
- clock constraint: 1,000 ps
- core utilization: 35%
- placement density: 0.50
- post-CTS repair timing: skipped with the documented ORFS architectural-exploration/CI switch
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

## Corrective rerun

The first attempt used the NanGate45 canary's numeric `10.0` clock value and
forced the non-default `TC` library corner. ASAP7 reference constraints use
picosecond-scale values (typically 300--1,000); the resulting accidental 10 ps
target generated severe setup pressure and the `TC` CTS process terminated
before routing. No scientific geometry or admissible result was opened.

The first corrective rerun used a platform-specific SDC, the platform-default
`BC` corner and a relaxed 1,000 ps clock. CTS completed and reported no setup
or hold violations, but the pinned OpenROAD binary again terminated with an
illegal instruction in the post-CTS repair/legalization block.

ORFS documents `SKIP_CTS_REPAIR_TIMING=1` as useful for architectural
exploration and CI. The next rerun freezes that switch while retaining the
requirements for parseable final-route timing, zero final timing violations
and zero detailed-route DRC. This is a disclosed toolchain workaround, not a
scientific result.

That rerun completed detailed routing with zero detailed-route violations and
then the Docker Hub binary (`OpenROAD unknown`) terminated while writing final
outputs. The checked-out ORFS revision publishes its current Ubuntu 22.04
builder at GHCR rather than Docker Hub. A bootstrap run therefore resolves and
records that official image's immutable digest. A subsequent run pinned to the
recorded digest is required before the platform qualifies.
