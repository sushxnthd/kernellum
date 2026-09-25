# SIMILARITY antenna-ratio-margin flow canary

Status: **draft until merged to main; no route is eligible before that merge**.

## Why this is distinct and justified

The opened-data electrical-margin canary at frozen SHA
`bb9a8887be5411247afe59404652676d293d1cc8` passed every preregistered gate:
18/18 routes were complete and electrically/DRC clean, preserved exact
structure, and retained at least 23.22% capacitance and 16.17% slew headroom.
That result qualifies `CAP_MARGIN=30` and `SLEW_MARGIN=25` for their stated
scope only.

Independent inspection of all raw route logs found a separate, non-frozen
integrity issue. Sky130HD B-local 10x5 seed 263 ended with one antenna net and
one antenna pin violation after post-detailed-route repair reduced an initial
22 violations to one. The same residue persisted through every allowed repair
iteration and the log emitted `GRT-0243`.

[OpenROAD's global-router documentation](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html#repair-antennas)
states that `GRT-0243` is emitted when constant
`ANTENNADIFFSIDEAREARATIO` technology rules make additional diode insertion
ineffective. It also documents `repair_antennas -ratio_margin` as the control
that adds margin to antenna ratios. The pinned flow's global-route repair can
insert routing jumpers before detailed routes exist; its later post-route
repair is limited by the observed diode condition. This canary therefore
tests a **pre-detailed-route 20% antenna-ratio margin**, not more repetitions
of the ineffective post-route operation. The 20% setting is a single
conservative qualification point, not an optimized result, and the canary is
allowed to fail.

## Frozen source, matrix and exclusions

The architecture RTL, 20 ns clock, 35% utilization, 0.50 placement density,
pinned ORFS image, exact headless final-report patch, CAP_MARGIN=30 and
SLEW_MARGIN=25 remain unchanged. The only new flow change is an exact
replacement of the global-route antenna command to add `-ratio_margin 20`.

The fixed matrix is:

- platforms: NanGate45 and Sky130HD;
- topologies: broadcast, full local and B-local;
- already-opened geometry: 10x5 only;
- previously unused canary-only seed: 277;
- six planned routes in six independent shards.

Geometry 10x5 and seed 277 are excluded from every later architectural
confirmation. This canary cannot rescue a prior null, confirm B-local
performance, establish novelty or support a breakthrough claim.

## All-required gates frozen before routing

1. Signed 10x5 GEMM equivalence between B-local and full-local RTL passes.
2. Exactly six shards contain the six unique planned rows. Six manifests
   certify the pinned image, merged source SHA, exact headless patch and exact
   single replacement that adds `-ratio_margin 20`.
3. All six native drivers reach finish without SIGSEGV or `make` failure.
4. Every row is attempted and complete, with positive timing/area/wire
   metrics, valid hashes, and zero final setup, hold, maximum-slew,
   maximum-fanout, maximum-capacitance and detailed-route DRC violations.
5. Every finish report retains at least 2% normalized cap and slew headroom.
6. Every detailed-route log ends at zero detailed-route DRC violations and
   its final antenna check reports exactly zero net and zero pin violations.
7. Every row exactly preserves the deterministic DFF count and synthesis cell
   area from the published electrical-margin canary for the same
   platform/topology/shape.

Every gate is required. No failed route may be retried, replaced or dropped;
no threshold, seed, margin or classification may change after merge. A pass
qualifies this exact opened-data flow setting only. A failure is published as
a complete canary null and stops this intervention. No new architecture
confirmation may route until antenna-flow integrity has a frozen pass.
