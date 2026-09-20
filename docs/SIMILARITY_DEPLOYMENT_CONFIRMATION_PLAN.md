# Project SIMILARITY: leakage-free selection and deployment confirmation

Date frozen: 2026-09-20

## Motivation

The independent utility study retained a 13/15-gate null because one-shot selection on route seed 33 chose the wrong orientation/depth. Its median-route compiler still reproduced a 24.05% mean workload gain with zero oracle regret. A forensic calculation showed that the architecture chosen from multi-seed broadcast timing remained beneficial on each individual local route seed, but that calculation was post hoc and cannot establish the claim.

This experiment tests the implied protocol prospectively with disjoint selection and deployment routes.

## Scientific question

Can broadcast-only multi-seed characterization plus the frozen causal timing law select accelerator configurations that retain material workload gains on completely unseen deployment-routing seeds?

## Frozen law, RTL and compiler

Functional RTL, cycle accounting, workloads and the equation remain unchanged:

```text
predicted_tax_ns = -0.5018052114 + 0.3009146882 * sqrt(PE)
```

For each workload, the compiler selects an architecture/topology using only median broadcast timing from selection seeds 35, 36 and 37. No local timing and no deployment seed participates in selection.

The resulting workload-to-configuration mapping is evaluated unchanged on deployment seeds 38, 39 and 40.

## Frozen unseen corpus

Target: Lattice ECP5-85K, CABGA381, speed grade 6.

Architectures:

1. 8x11, K_TILE=320
2. 8x11, K_TILE=448
3. 11x8, K_TILE=320
4. 11x8, K_TILE=448
5. 10x13, K_TILE=320
6. 10x13, K_TILE=448
7. 13x10, K_TILE=320
8. 13x10, K_TILE=448

Every geometry and K depth is absent from prior functional corpora.

Routes:

- selection: broadcast only, 8 architectures x 3 seeds = 24;
- deployment: broadcast and local, 8 architectures x 3 seeds = 48.

Total: **72 new final-route implementations**.

## Preregistered gate

The leakage-free deployment claim passes only if every criterion holds:

1. all existing functional transport simulations pass;
2. at least 70 of 72 routes succeed;
3. every successful route maps exactly one `MULT18X18D` per PE;
4. the selection compiler chooses local transport for all 12 workloads;
5. at least 7 of 8 architecture pairs have positive median deployment broadcast tax;
6. on each deployment seed, the frozen selection mapping is no worse than the best broadcast-only architecture on all 12 workloads;
7. on each deployment seed, mean workload improvement is at least 8%;
8. across all 36 deployment workload/seed cases, mean improvement is at least 10%;
9. on each deployment seed, mean oracle regret is at most 7%;
10. across all deployment cases, mean oracle regret is at most 5%;
11. all three K=1200 feed-forward contraction workloads select K_TILE=448;
12. mean local flip-flop and block-RAM overhead are reported without suppression.

Tax MAE, tax correlation and route CV remain descriptive. The scientific test is fully held-out deployment utility.

No threshold, architecture, seed, workload, equation, decision rule or RTL implementation may change after results are opened.

## Interpretation

A pass supports the result:

> Multi-seed broadcast-only physical characterization, combined with a causal topology law and explicit wavefront accounting, selects functional accelerator configurations that deliver reproducible held-out routed workload gains without observing local timing during selection.

A failure is retained as a null. This remains final-route evidence on one FPGA family and does not establish board performance, power, energy, ASIC transfer, vendor independence or area-normalized superiority.
