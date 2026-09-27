# SIMILARITY flow-qualified prospective B-local replication preregistration

Status: **draft until merged to main; no eligible physical route may precede that merge**.

## Scientific role and frozen claim

This is a new prospective replication of the B-local mechanism after the
reporting, electrical-margin, antenna and runtime/headroom flow interventions
were separately qualified on opened data. It cannot rescue or reclassify any
earlier null. Architecture RTL is byte-identical to the prior B-local studies.

The claim under test is deliberately flow-specific: in this exact pinned
open-source ASIC flow, B-local staging preserves signed-GEMM behavior and, on
the sealed holdouts, retains a substantial fraction of full-local's timing
benefit while using fewer registers and less synthesis and post-route cell area
than full-local, with a jointly favorable period-times-area proxy relative to
both broadcast and full-local controls. A pass is not by itself a field-level
breakthrough, an energy result, a silicon result or an admissions guarantee.

## Frozen architecture and qualified flow

B-local preserves all eight B bits and A[7] per processing element. A[6:0]
and valid streams remain stride-two shared. Broadcast and full-local are the
controls. All three topologies use the same 20 ns constraint, 35% core
utilization, 0.50 placement density and pinned OpenROAD-flow-scripts image:

`openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`.

The physical flow is fixed at the settings qualified before this study:

- exact one-block removal of optional GUI image generation from final reports;
- exact pre-detailed-route antenna repair ratio margin of 20;
- `CAP_MARGIN=31` and `SLEW_MARGIN=25`; and
- 7200 seconds for each native-route, emulated-report and native-finish
  subprocess.

Every route is an independent Actions shard. This prevents one shape from
consuming the job budget needed by another and produces 72 independently
inspectable route artifacts.

## Frozen unopened matrix

The matrix is two platforms x three topologies x three seeds x four shapes:

- platforms: NanGate45 and Sky130HD;
- topologies: broadcast, full-local and B-local;
- discovery shapes: 6x11 and 11x6;
- sealed holdout shapes: 8x9 and 9x8; and
- seeds: 397, 421 and 449.

These shapes and seeds had not been opened by any earlier Kernellum ASIC
study when this protocol was written. The permanently excluded shapes are
3x3, 7x7, 2x4, 4x2, 3x6, 6x3, 5x5, 3x8, 8x3, 5x9, 9x5, 4x7,
7x4, 5x8, 8x5, 6x8, 8x6, 6x9, 9x6, 5x10, 10x5, 7x8, 8x7,
6x10, 10x6, 7x10 and 10x7. The permanently excluded seeds are 11, 29,
47, 53, 71, 89, 101, 131, 157, 173, 181, 211, 239, 263, 277, 293,
317, 347 and 373. The four new shapes and three new seeds become opened and
excluded as soon as this preregistration reaches main, irrespective of outcome.

## Frozen definitions

For each platform/shape/seed matched trio, let `P_b`, `P_l` and `P_c` be the
minimum clean periods for broadcast, full-local and B-local. Timing benefit is
`q=(P_b-P_x)/P_b`. Retention is `(P_b-P_c)/(P_b-P_l)` and is defined only
when full-local is faster than broadcast. A platform/shape group contains its
three seeds and uses medians.

For control `x`, the period-times-area improvement ratio is
`P_x*A_x/(P_c*A_c)`; a value of at least 1.01 is a preregistered win. The
synthesis-area and post-route-cell-area versions are independent required
gates. Wirelength is the detailed-route total. Vectorless power is recorded
descriptively only and is not workload energy, measured power or a power gate.

## All-required gates

Every gate below must pass:

1. Signed-GEMM equivalence between B-local and full-local emits the exact pass
   marker on all four unopened shapes.
2. Exactly 72 independent route artifacts contain exactly the 72 planned,
   unique, attempted rows. The functional artifact, source hashes, 72 patch
   manifests, 72 native driver logs, 72 finish reports, 72 route logs and 72
   detailed-route DRC reports are present and source-consistent.
3. Every manifest matches the pinned image and merged source SHA, both exact
   one-block flow patches, ratio margin 20, `CAP_MARGIN=31`,
   `SLEW_MARGIN=25`, the 7200-second subprocess limit, all three seeds and all
   four shapes.
4. No driver contains a timeout, SIGSEGV or `make` failure, and all 72 reach
   native finish with nonempty GDS, ODB, SPEF and netlist SHA-256 values.
5. All 72 rows have positive timing, synthesis-area, post-route-cell-area,
   wirelength and descriptive vectorless-power metrics; zero setup, hold,
   maximum-slew, maximum-fanout, maximum-capacitance and DRC violations; at
   least 2% normalized final capacitance and slew headroom; empty final DRC
   reports; and zero final antenna net and pin violations.
6. All eight platform/shape groups contain three complete matched seeds, and
   full-local has positive median timing benefit in every group.
7. In all 24 matched platform/shape/seed trios, B-local DFF count is above
   broadcast and no more than 90% of full-local. B-local synthesis cell area
   and post-route cell area are both strictly below full-local in every trio.
8. B-local is faster than broadcast in all 12 holdout seed pairs. Each of the
   four holdout groups has at least 5% median raw timing benefit and at least
   70% median retention.
9. The synthesis-area-normalized proxy wins jointly against both controls in
   at least three of four holdout groups and includes both platforms.
10. Independently, the post-route-area-normalized proxy wins jointly against
    both controls in at least three of four holdout groups and includes both
    platforms.
11. In every holdout group, B-local median detailed-route wirelength is not
    above full-local.
12. For both NanGate45 holdout shapes, the three-seed median targeted B-local
    launch-Q fanout is at most 10.

The frozen claim is supported only if all gates pass. No row may be retried,
replaced, dropped or reclassified; no seed, shape, source, margin, timeout,
threshold or statistic may change after merge. Any failure is a complete
preregistered null and must be published with all raw evidence.

## Interpretation boundary

A pass would support only this exact flow-specific replicated claim. It would
still require reconciliation with the separate primary-source/patent novelty
screen, every seed-level effect, end-to-end signed-GEMM utility, the limits of
vectorless power and period-times-area proxies, and zero-cost external
replication before any field-level breakthrough assertion. A failure cannot be
rescued by descriptive results or by a later flow change.
