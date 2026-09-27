# SIMILARITY runtime/headroom flow canary

Status: **draft until merged to main; no route is eligible before that merge**.

## Why this intervention is justified

The flow-qualified 72-route B-local study frozen at
`a8f24cb1825f249c43ef43457d74bbabaac31625` is a preregistered null. All 72
rows were attempted, but four Sky130HD holdout rows exhausted the fixed
3600-second native-route subprocess budget and never reached complete finish
evidence. The failures crossed B-local and full-local topologies. Raw logs show
that one route completed detailed routing and found zero antenna violations
before timing out later, one route inserted five antenna diodes and timed out
during the required second detailed route, and two stopped during detailed
routing. This is an opened-data runtime/evidence boundary, not a proven
electrical defect or a B-local-specific failure.

A fifth row, NanGate45 broadcast 7x10 seed 347, was fully routed with zero
electrical, DRC and final-antenna violations and complete product hashes. It
retained 0.5136103 fF of capacitance slack against a 26.0161991 fF limit:
1.97%, just below the separately preregistered 2% residual-headroom gate. That
is a real frozen failure. `CAP_MARGIN=31` is the smallest integer percentage
increase from the qualified value of 30 and is frozen as one conservative
qualification point; it is not claimed to be optimal or guaranteed to pass.

The canary doubles the native stage timeout from 3600 to 7200 seconds. This is
a single preregistered resource-qualification point chosen because every
observed incomplete row ended at the exact 3600-second process limit. It does
not retroactively complete or rescue any prior row.

## Frozen source, matrix and exclusions

Architecture RTL, the 20 ns clock, 35% utilization, 0.50 placement density,
pinned ORFS image, headless final reporting, `SLEW_MARGIN=25` and the
pre-detailed-route antenna ratio margin of 20 remain unchanged. The only new
settings are:

- `CAP_MARGIN=31`; and
- a 7200-second timeout for each native route/final-report/finish subprocess.

The matrix is:

- platforms: NanGate45 and Sky130HD;
- topologies: broadcast, full local and B-local;
- already-opened geometries: 7x10 and 10x7;
- one previously unused canary-only seed: 373;
- 12 routes in 12 independent platform/topology/geometry shards, so neither
  large geometry consumes the hosted-job budget needed by the other.

The canary does not rerun seeds 293, 317 or 347. Seed 373 and both geometries
are opened and excluded from all later confirmation. This canary can qualify
only the reporting/physical-flow settings; it cannot rescue prior nulls,
confirm B-local performance, establish novelty, support a breakthrough claim,
or imply an admissions outcome.

## All-required gates frozen before routing

1. Signed-GEMM equivalence between B-local and full-local RTL passes on both
   shapes.
2. Exactly 12 route shards contain exactly the 12 unique planned rows.
3. Twelve manifests certify the pinned image and source SHA, exact one-block
   headless-report patch, exact antenna-ratio-margin patch, 7200-second timeout,
   `CAP_MARGIN=31`, `SLEW_MARGIN=25`, seed 373 and both geometries.
4. All 12 driver logs reach native finish without `TIMEOUT`, SIGSEGV or `make`
   failure; all 12 finish reports, route logs and DRC reports are present.
5. Every row is attempted and complete, with positive timing, synthesis area,
   post-route cell area, wirelength and descriptive vectorless-power metrics,
   plus hashes for nonempty GDS, ODB, SPEF and netlist products.
6. Every final report has zero setup, hold, maximum-slew, maximum-fanout and
   maximum-capacitance violations and at least 2% normalized capacitance and
   slew headroom.
7. Every detailed-route DRC report is empty, every route log ends at zero DRC,
   and every final antenna check reports zero net and pin violations.
8. Every row exactly preserves the deterministic DFF count and synthesis cell
   area published for the same platform/topology/shape in the frozen qualified
   study.

Every gate is required. No failed route may be retried, replaced, dropped or
reclassified, and no threshold, seed, shape, timeout or margin may change after
merge. A failure is published as the complete opened-data canary null and stops
this intervention. A pass is flow-qualification evidence only.

If the canary passes, any later architecture experiment must be frozen before
routing on genuinely unopened shapes and seeds with all functional, evidence,
electrical, DFF, synthesis-area, post-route-area, timing-retention,
area-normalized, wirelength and fanout gates fixed. Primary prior-art, practical
utility and independent-replication audits remain separate requirements before
any field-level claim.
