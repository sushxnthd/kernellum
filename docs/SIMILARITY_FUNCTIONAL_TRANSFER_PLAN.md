# Project SIMILARITY: functional transfer and topology-aware compiler

Date frozen: 2026-09-20

## Scientific question

Does the broadcast timing tax discovered in diagnostic ECP5 MAC fabrics transfer without refitting to Kernellum's functionally correct tiled GEMM engine, and is the transferred law accurate enough to choose operand-transport topology at workload level?

## Intervention

The existing K1 engine is the broadcast arm. The local arm preserves the same signed INT8 products, accumulators, tile contents and controller semantics, but replaces direct row/column operand broadcast with registered nearest-neighbor transport.

Inputs are pre-skewed by row and column so matching K-index operands meet at every processing element. The controller drains the wavefront before asserting done. The workload cycle model charges this drain cost once per K chunk.

## Frozen route corpus

Target: Lattice ECP5-85K, CABGA381, speed grade 6.

Architectures:

1. 4x4, K_TILE=16
2. 4x8, K_TILE=32
3. 8x4, K_TILE=32
4. 8x8, K_TILE=16
5. 8x8, K_TILE=64
6. 8x12, K_TILE=32
7. 12x8, K_TILE=32
8. 10x12, K_TILE=64
9. 12x10, K_TILE=64

Both transport topologies are routed with seeds 23, 24 and 25.

Total: **54 final-route implementations**.

## Frozen zero-shot law

No functional-engine result may be used to refit the diagnostic SIMILARITY equation.

The predicted broadcast tax is frozen from the corrected diagnostic experiment:

```text
predicted_tax_ns = -0.5018052114 + 0.3009146882 * sqrt(PE)
```

For a functional broadcast period `T_b`, the law predicts:

```text
predicted_local_period = T_b - predicted_tax_ns
```

## Compiler evaluation

The law-guided compiler sees each architecture's broadcast timing and the frozen tax equation. It does not see that architecture's routed local timing when making a choice.

Synthetic K values are frozen as:

```text
8, 16, 32, 64, 128, 256, 512, 1024, 3072
```

Workload evaluation uses the existing 12 frozen Transformer GEMMs.

Broadcast cycles retain the K1 model. Local cycles add `ROWS + COLS - 1` drain cycles for every K chunk.

## Preregistered gate

The functional-transfer claim passes only if every criterion holds:

1. broadcast and local RTL simulations both pass exact-output checks;
2. at least 52 of 54 routes succeed;
3. every successful implementation maps exactly one MULT18X18D per PE;
4. maximum per-point seed CV is at most 8%;
5. at least 7 of 9 architecture pairs have positive observed broadcast tax;
6. zero-shot diagnostic-law tax MAE is at most 1.50 ns;
7. predicted-versus-observed tax correlation is at least 0.60;
8. law-guided topology-choice accuracy on the synthetic K grid is at least 85%;
9. mean law-guided topology-choice regret is at most 3%;
10. at least one architecture selects broadcast at K <=16 and local at K >=512 using actual routed timing;
11. on at least 10 of 12 Transformer workloads, the law-guided compiler is no worse than the best broadcast-only architecture;
12. mean workload latency improvement over the best broadcast-only architecture is at least 3%;
13. mean regret versus an oracle topology-aware compiler is at most 5%.

No threshold, architecture, seed, workload or K value may change after results are opened.

## Interpretation

A pass supports a compiler-level claim: a causal law learned from isolated physical-design experiments transfers zero-shot to a functional accelerator and is useful for workload-dependent architecture selection.

A failure is retained as a null result and identifies where the diagnostic law stops transferring.

This experiment remains final-route evidence. It does not establish physical-board performance, power, energy, ASIC transfer or vendor independence.
