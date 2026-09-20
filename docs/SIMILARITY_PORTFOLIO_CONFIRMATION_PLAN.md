# Project SIMILARITY: two-candidate physical-feedback confirmation

Date frozen: 2026-09-20

## Motivation

The leakage-free single-choice deployment study retained a 10/12-gate null. Its frozen choices beat the broadcast-only baseline in all 36 held-out workload/seed cases, but one deployment seed had 8.18% mean oracle regret against a frozen 7% ceiling.

A post-hoc feasibility analysis found that no fixed workload-to-architecture mapping could satisfy that ceiling on the opened deployment corpus: even a hindsight minimax mapping had 8.64% mean regret on the failing seed. This shows that the failed criterion cannot be repaired merely by changing the broadcast-only ranking statistic.

The same post-hoc analysis suggested a different, operationally explicit protocol: retain the two best candidates selected from broadcast-only characterization, route those two local designs, and resolve the pair using only their own final-route timing. On the opened corpus that diagnostic would have reduced overall regret from 3.90% to 0.89%. That number is motivation only and is not confirmation evidence.

This experiment prospectively tests the two-candidate protocol on entirely unseen geometries, depths and route seeds.

## Scientific question

Can a two-candidate portfolio selected using only multi-seed broadcast timing and the frozen causal topology law absorb place-and-route variability, while using local final-route timing for only those two candidates, and deliver low-regret workload choices on unseen deployment routes?

## Frozen policy

Functional RTL, cycle accounting, workloads and the causal equation remain unchanged:

```text
predicted_tax_ns = -0.5018052114 + 0.3009146882 * sqrt(PE)
```

For each workload:

1. obtain median broadcast timing from selection seeds 41, 42 and 43;
2. predict local timing for every candidate with the frozen equation;
3. retain the two distinct architectures with the lowest predicted local workload latency;
4. on a deployment seed, inspect final-route local timing only for those two portfolio members;
5. choose the member with lower cycle-model latency at its observed local Fmax.

No local selection timing and no deployment timing participates in portfolio construction. Timing from non-portfolio deployment candidates is used only after the choice is frozen to compute the independent oracle.

The prior claim that every K=1200 FFN contraction must choose the deeper tile was falsified and is not repeated here.

## Frozen unseen corpus

Target: Lattice ECP5-85K, CABGA381, speed grade 6.

Architectures:

1. 9x12, K_TILE=352
2. 9x12, K_TILE=480
3. 12x9, K_TILE=352
4. 12x9, K_TILE=480
5. 10x15, K_TILE=352
6. 10x15, K_TILE=480
7. 15x10, K_TILE=352
8. 15x10, K_TILE=480

Every geometry, PE count, K depth and seed is absent from the prior utility corpora.

Routes:

- selection: broadcast only, 8 architectures x 3 seeds = 24;
- deployment validation: broadcast and local, 8 architectures x 3 seeds = 48.

Total: **72 new final-route implementations**.

The validation sweep routes all candidates so an oracle can be measured. The tested policy may inspect local timing for only the two portfolio members per workload.

## Preregistered gate

The two-candidate confirmation passes only if every criterion holds:

1. all existing functional transport simulations pass;
2. at least 70 of 72 routes succeed;
3. every successful route maps exactly one `MULT18X18D` per PE;
4. every workload portfolio contains exactly two distinct local architectures;
5. at least 7 of 8 architecture pairs have positive median deployment broadcast tax;
6. on each deployment seed, the portfolio choice is no worse than the best broadcast-only architecture on all 12 workloads;
7. on each deployment seed, mean workload improvement is at least 8%;
8. across all 36 deployment workload/seed cases, mean improvement is at least 10%;
9. on each deployment seed, mean oracle regret is at most 5%;
10. across all deployment cases, mean oracle regret is at most 3%;
11. the second-ranked portfolio member is selected in at least one deployment case;
12. the portfolio reduces overall mean oracle regret by at least 1.0 percentage point versus using its first-ranked member alone;
13. mean local flip-flop and block-RAM overhead are reported without suppression.

Tax magnitude error and route variation remain descriptive. No threshold, architecture, seed, workload, equation, policy or RTL implementation may change after results are opened.

## Interpretation

A pass supports the result:

> A two-candidate architecture portfolio constructed from broadcast-only characterization converts a causal topology law into route-seed-robust workload choices: bounded local physical feedback resolves CAD variability while retaining material gains over broadcast-only designs.

A failure is retained as a null. This remains final-route evidence on one FPGA family and does not establish board performance, power, energy, ASIC transfer, vendor independence or area-normalized superiority.
