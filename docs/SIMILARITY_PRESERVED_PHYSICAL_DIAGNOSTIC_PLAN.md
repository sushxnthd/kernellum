# SIMILARITY preserved-replica physical diagnostic plan

Status: **exploratory repair protocol fixed before physical routing**.

This is an opened-data mechanism test, not confirmation. The 5x8 and 8x5
geometries and seeds 53, 71 and 89 were opened previously. No result from
this diagnostic can support a breakthrough claim.

## Rationale and fixed intervention

The first selective A[7]/B[2:0] diagnostic was a null. Although all twelve
routes were clean, synthesis merged every intended replica: DFF totals were
identical to ordinary stride-two and critical launch fanout remained 14 to
18. A separately frozen synthesis canary then established that lane-diverse
reset values, applied only while shared valid is low, preserve exactly the
intended registers without changing the signed-GEMM result. Both platforms
mapped 1,899 DFFs at 5x8 and 1,872 at 8x5.

This diagnostic routes that fixed preserved implementation. It uses the
same pinned OpenROAD-flow-scripts image, platform settings and parsers as
the earlier studies. Candidate results are compared with the published
broadcast, full-local and stride-two rows and with the published merged-
replica no-op diagnostic. There are exactly twelve candidate routes: two
platforms, two shapes and three seeds.

## All-required continue gates

The intervention warrants a fresh-geometry prospective study only if every
gate passes:

1. Signed-GEMM equivalence passes on both opened shapes.
2. Exactly twelve unique candidate rows exist; all twelve are complete and
   setup/hold/slew/fanout/capacitance/DRC clean; every group has all seeds.
3. Every 5x8 route contains exactly 1,899 DFFs and every 8x5 route exactly
   1,872, remains at or below 90% of matched full-local DFFs, and has lower
   synthesis cell area than matched full-local.
4. Every platform/shape group has at least 5% median raw period benefit over
   broadcast and retains at least 70% of full-local's period benefit.
5. Median period-times-synthesis-area beats both broadcast and full-local in
   at least three of four groups, including a win on each platform.
6. The targeted NanGate45 8x5 median period is at least 0.04 ns better than
   ordinary stride-two and at least 0.02 ns better than the prior merged-
   replica no-op candidate. The second condition makes the required gain
   larger than the improvement observed when no replicas survived.
7. The median launch-register Q fanout across the three targeted NanGate45
   8x5 maximum paths is at most 10, compared with 15 in all three prior
   merged-replica routes.

Any failure is published as an opened-data null and stops this intervention.
No seed is replenished, no row is dropped, and no threshold is weakened. A
pass remains exploratory: any confirmation must freeze distinct source,
geometries and seeds never opened by prior ASIC work, plus all electrical,
timing, DFF, synthesis-area and area-normalized gates, before routing.
