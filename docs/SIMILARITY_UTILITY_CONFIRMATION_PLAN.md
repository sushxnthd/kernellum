# Project SIMILARITY: independent compiler-utility confirmation

Date frozen: 2026-09-20

## Prior evidence and claim selection

The functional-transfer study passed 11/13 gates but failed topology-choice accuracy and workload improvement. The subsequent depth co-design study passed 13/15 gates but failed maximum seed CV and absolute tax MAE by narrow margins.

Crucially, every preregistered compiler-utility criterion in the depth study passed: 86.11% choice accuracy, 0.98% mean synthetic regret, 8/8 crossovers, local selection on 12/12 workloads, 14.87% mean workload improvement and 1.92% mean oracle regret.

This experiment independently tests that narrower result. It does not reopen either null, refit the diagnostic timing law, or claim precise tax-magnitude calibration.

## Scientific question

Does the zero-shot law-guided compiler reproduce its topology decisions and double-digit workload-latency benefit on entirely unseen array geometries, unseen K tile depths and unseen routing seeds?

## Frozen intervention and law

Functional RTL, cycle accounting, workloads and compiler decision logic are unchanged.

The timing law remains:

```text
predicted_tax_ns = -0.5018052114 + 0.3009146882 * sqrt(PE)
```

The compiler sees each candidate's routed broadcast timing and the frozen equation. It does not see local routed timing when selecting an architecture/topology.

## Frozen independent corpus

Target: Lattice ECP5-85K, CABGA381, speed grade 6.

Architectures:

1. 9x9, K_TILE=192
2. 9x9, K_TILE=384
3. 9x13, K_TILE=192
4. 9x13, K_TILE=384
5. 13x9, K_TILE=192
6. 13x9, K_TILE=384
7. 11x13, K_TILE=192
8. 11x13, K_TILE=384
9. 13x11, K_TILE=192
10. 13x11, K_TILE=384

Every geometry and K-depth value is absent from the earlier functional corpora. Both transport topologies are routed with new seeds 32, 33 and 34.

Total: **60 new final-route implementations**.

## Frozen evaluation

Synthetic K values remain:

```text
8, 16, 32, 64, 128, 256, 512, 1024, 3072
```

The existing 12 Transformer GEMMs remain frozen.

Two compiler evaluations are required:

1. **Median-route evaluation:** architecture selection uses median broadcast timing and is scored against median actual timing.
2. **Per-seed replication:** for each seed independently, selection uses that seed's broadcast timing and is scored against that seed's actual broadcast/local timing. No route from another seed participates.

The best broadcast-only design within the same corpus and seed is the baseline. The best design using actual broadcast/local timing is the oracle.

Flip-flop and block-RAM overhead remain mandatory descriptive outputs.

## Preregistered gate

The independent compiler-utility claim passes only if every criterion holds:

1. the existing broadcast, local and signed transport-equivalence simulations pass;
2. at least 58 of 60 routes succeed;
3. every successful implementation maps exactly one `MULT18X18D` per PE;
4. at least 9 of 10 architecture pairs have positive median observed broadcast tax;
5. median-route topology-choice accuracy on the synthetic K grid is at least 85%;
6. median-route mean topology-choice regret is at most 3%;
7. at least 8 of 10 architectures select broadcast at K <=16 and local at K >=128 using actual median timing;
8. the median-route compiler selects local transport on all 12 Transformer workloads;
9. the median-route compiler is no worse than the best broadcast-only architecture on all 12 workloads;
10. median-route mean workload improvement is at least 10%;
11. median-route mean oracle regret is at most 5%;
12. each of seeds 32, 33 and 34 independently produces at least 8% mean workload improvement;
13. each seed independently has mean oracle regret at most 7%;
14. every seed independently selects local transport on at least 10 of 12 workloads;
15. K_TILE=384 local transport has lower median mean workload latency than matched K_TILE=192 local transport in at least 4 of 5 geometry families.

Tax MAE, tax correlation and seed CV are still reported, but they are not gates because this experiment tests decision utility rather than precise magnitude calibration or absolute placement stability. Per-seed end-to-end improvement gates directly test whether placement variation can overturn the claimed benefit.

No threshold, architecture, seed, workload, K value, equation, decision rule or RTL implementation may change after results are opened.

## Interpretation

A pass supports an independent compiler-level result:

> A zero-shot causal timing law can guide joint transport/tile-depth selection to reproducible double-digit routed workload gains on unseen functional accelerator architectures, even when its absolute tax magnitude is conservative.

A failure is retained as a null and identifies whether the earlier utility result depended on its geometry set, K depths, median aggregation or route seeds.

This remains final-route evidence on one FPGA family. It does not establish physical-board performance, power, energy, ASIC transfer, vendor independence or area-normalized superiority.
