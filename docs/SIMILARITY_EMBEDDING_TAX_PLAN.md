# Project SIMILARITY: topology-embedding tax under matched fanout

Date frozen: 2026-09-20

## Motivation

Project SIMILARITY has established three facts:

1. direct broadcast has a reproducible size-dependent timing tax relative to registered nearest-neighbor transport;
2. a simple geometric-mean fanout invariant fails;
3. early registered-relay data show that reducing fanout without enforcing spatial locality does not reproduce the nearest-neighbor timing benefit.

This suggests that the important variable may be **physical embeddability of the communication graph**, rather than logical fanout itself.

## Causal intervention

Compare two registered operand-propagation fabrics with:

- exactly one INT8 MAC per PE;
- one A register and one B register per PE;
- fanout exactly one for every inter-PE operand-propagation edge;
- the same number of propagation stages;
- the same edge-source register counts;
- the same accumulator logic.

The only intervention is the communication graph.

### LOCAL

A operands advance to the next PE in the same row.

B operands advance to the next PE in the same column.

This is the conventional nearest-neighbor mesh and has an obvious low-wirelength embedding.

### SHUFFLE

Every stage remains a one-to-one permutation, so fanout is still one.

For A at column c>0, PE (r,c) receives from row

    (r + c) mod N

in column c-1.

For B at row r>0, PE (r,c) receives from column

    (c + 2*r) mod N

in row r-1.

Each stage mapping is bijective. No value is broadcast and every inter-PE propagation register drives exactly one successor, but the two independent stage permutations create a graph that is not the ordinary row/column mesh.

This intervention is designed to distinguish **degree/fanout locality** from **spatial graph locality**.

## Experiment

Device: ECP5-85K, CABGA381, speed grade 6.

Odd square sizes:

- 5x5
- 7x7
- 9x9
- 11x11

Seeds:

- 13
- 14
- 15

Total:

    4 sizes x 2 topologies x 3 seeds = 24 routes.

Use median period across seeds.

N=5,7,9 are discovery sizes.

N=11 is completely held out from the embedding-tax fit.

## Frozen model

Define

    embedding_tax(N) =
        T_shuffle(N) - T_local(N).

Fit only N=5,7,9:

    embedding_tax = alpha + beta*N.

Freeze alpha and beta, then predict N=11.

The model is secondary to the paired causal intervention but provides a held-out scaling check.

## Preregistered embedding gate

The topology-embedding mechanism is supported only if all hold:

1. at least 23/24 routes succeed;
2. every successful route maps exactly one MULT18X18D per PE;
3. for each N, LOCAL and SHUFFLE synthesize to identical DSP and FF counts;
4. median per-configuration seed CV <=6% for both topologies;
5. SHUFFLE median critical period is higher than LOCAL for all four N;
6. SHUFFLE is at least 12% slower than LOCAL at N=11;
7. fitted discovery beta is positive;
8. frozen N=11 embedding-tax prediction has absolute error <=1.50 ns;
9. the embedding tax at N=11 is at least 1.5x the tax at N=5;
10. local N=11 period remains <=13 ns, ensuring the comparison is not driven by failure of the local baseline.

No criterion may be weakened after results are known.

## Scientific interpretation

A pass supports:

> Communication fanout and register depth are insufficient to explain FPGA timing scaling. Two degree-one registered communication graphs with identical compute and register resources can exhibit systematically different critical periods solely because one graph admits a local mesh embedding and the other imposes shuffled cross-fabric connectivity.

This would identify **spatial graph embeddability** as a causal latent variable behind the previously confirmed broadcast timing tax.

The experiment does not yet provide a vendor-independent graph metric. A pass would motivate a follow-up relating timing tax to routed wirelength, cutwidth or graph-layout measures.
