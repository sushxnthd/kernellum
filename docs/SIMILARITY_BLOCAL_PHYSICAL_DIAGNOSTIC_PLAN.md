# SIMILARITY B-local physical diagnostic plan

Status: **exploratory B-local protocol fixed before physical routing**.

This is an opened-data mechanism test, not confirmation. It uses only the
previously opened 5x8 and 8x5 shapes and seeds 53, 71 and 89. No result from
this diagnostic can support a breakthrough claim.

## Evidence and intervention

The preserved selective-replica diagnostic improved descriptive timing and
area-normalized throughput, but was an all-required null: NanGate45 8x5
seeds 71 and 89 each retained one final maximum-capacitance violation, and
all three targeted maximum paths launched from still-shared B[7:3]
registers with fanouts 16, 16 and 10.

The distinct candidate preserves all eight B bits and A[7] per PE while
leaving A[6:0] and both valid streams stride-two shared. A frozen synthesis
canary established signed-GEMM equivalence and exact mapped counts of 1,979
DFFs at 5x8 and 1,972 at 8x5 on both platforms. This physical diagnostic
uses that source without modification.

Route exactly twelve rows with the pinned flow: both platforms, both opened
shapes and all three opened seeds. Compare against the published broadcast,
full-local, stride-two and merged-replica no-op rows.

## All-required continue gates

1. Signed-GEMM equivalence passes on both shapes.
2. Exactly twelve unique candidate rows exist; all twelve are complete and
   setup/hold/slew/fanout/capacitance/DRC clean; all four groups contain all
   three seeds.
3. Every 5x8 route contains exactly 1,979 DFFs and every 8x5 route exactly
   1,972, remains at or below 90% of matched full-local DFFs, and has lower
   synthesis cell area than matched full-local.
4. Every group has at least 5% median raw period benefit over broadcast and
   retains at least 70% of full-local's period benefit.
5. Median period-times-synthesis-area beats both broadcast and full-local in
   at least three of four groups, including a win on each platform.
6. NanGate45 8x5 improves median period by at least 0.04 ns versus ordinary
   stride-two and at least 0.02 ns versus the merged-replica no-op.
7. Median launch-register Q fanout across its three NanGate45 8x5 maximum
   paths is at most 10.

Any failure is published as an opened-data null and stops this intervention.
No failed seed is replaced, no row is dropped and no threshold is weakened.
A pass remains exploratory. Confirmation must use distinct source, geometries
and seeds never opened in earlier ASIC work, with all gates frozen before
routing.
