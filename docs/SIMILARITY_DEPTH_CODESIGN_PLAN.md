# Project SIMILARITY: transport and tile-depth co-design

Date frozen: 2026-09-20

## Motivation

The preregistered functional-transfer experiment retained a null result after passing 11 of 13 gates. Its zero-shot timing law was accurate (0.8582 ns MAE, 0.9150 correlation), but the law-guided compiler chose broadcast for every candidate and delivered no workload improvement.

That failure identified a specific architectural bottleneck. Registered nearest-neighbor transport pays `ROWS + COLS - 1` drain cycles per K chunk, while every large candidate had `K_TILE <= 64`. Actual routed local timing produced three long-K crossovers, but the frozen law correctly remained conservative when the predicted clock gain did not repay frequent drains.

This follow-up tests the prospective consequence. It does not refit the law or revise the failed experiment.

## Scientific question

Can joint search over operand transport and deeper K tiles convert the existing zero-shot broadcast-tax law into a reliable, material workload-latency improvement in the functionally correct GEMM engine?

## Frozen intervention

The functional broadcast and local RTL are unchanged from the prior experiment. The compiler cycle model is unchanged. The diagnostic timing law remains frozen as:

```text
predicted_tax_ns = -0.5018052114 + 0.3009146882 * sqrt(PE)
```

Only the candidate architecture space changes: K tile depth is expanded to 128 and 256 so wavefront drain can be amortized over more MAC cycles.

## Frozen route corpus

Target: Lattice ECP5-85K, CABGA381, speed grade 6.

Architectures:

1. 8x8, K_TILE=128
2. 8x8, K_TILE=256
3. 10x12, K_TILE=128
4. 10x12, K_TILE=256
5. 12x10, K_TILE=128
6. 12x10, K_TILE=256
7. 10x14, K_TILE=256
8. 14x10, K_TILE=256

The first six are controlled depth interventions on geometries from the prior study; every architecture/K-depth tuple is new. The final two geometries and their 140-PE scale are entirely unseen.

Both transport topologies are routed with new seeds 29, 30 and 31.

Total: **48 new final-route implementations**.

## Frozen compiler evaluation

For each architecture, the law-guided compiler sees routed broadcast timing and the frozen diagnostic tax equation. It does not see routed local timing when making a choice.

Synthetic K values remain:

```text
8, 16, 32, 64, 128, 256, 512, 1024, 3072
```

Workload evaluation uses the same 12 frozen Transformer GEMMs. Baseline latency is the best broadcast-only architecture in this new corpus. Oracle latency is the best architecture/topology using routed medians.

The report will also disclose local-versus-broadcast flip-flop and block-RAM cost. These resource measurements are descriptive and cannot be removed if unfavorable.

## Preregistered gate

The co-design claim passes only if every criterion holds:

1. the existing broadcast, local and signed transport-equivalence RTL simulations pass;
2. at least 46 of 48 routes succeed;
3. every successful implementation maps exactly one `MULT18X18D` per PE;
4. maximum per-point seed CV is at most 8%;
5. at least 7 of 8 architecture pairs have positive observed broadcast tax;
6. zero-shot diagnostic-law tax MAE is at most 1.50 ns;
7. predicted-versus-observed tax correlation is at least 0.60;
8. law-guided topology-choice accuracy on the synthetic K grid is at least 85%;
9. mean law-guided topology-choice regret is at most 3%;
10. at least 6 of 8 architectures select broadcast at K <=16 and local at K >=128 using actual routed timing;
11. the law-guided compiler selects local transport on at least 10 of 12 Transformer workloads;
12. the law-guided compiler is no worse than the best broadcast-only architecture on all 12 workloads;
13. mean workload latency improvement over the best broadcast-only architecture is at least 8%;
14. mean regret versus an oracle topology-aware compiler is at most 5%;
15. K_TILE=256 local transport has lower mean workload latency than matched K_TILE=128 local transport in all three controlled geometry families.

No threshold, architecture, seed, workload, K value, equation or RTL implementation may change after results are opened.

## Interpretation

A pass supports a compiler-level co-design claim: a causal physical-design law becomes practically useful when the architecture search exposes the temporal-amortization variable that controls the intervention's cycle cost.

A failure is retained as a second null result. It would show whether timing prediction, routability, deeper-buffer timing, architecture selection or workload scheduling prevents the expected gain.

This remains final-route evidence. It does not establish physical-board performance, power, energy, ASIC transfer or vendor independence.
