# ARC Reboot Independent Transfer — Enumerative DSL Leave-One-Demo-Out

Status: PREREGISTERED BEFORE ANY TRANSFER RESULTS.

## Purpose

Test whether the Stage B counterfactual-centrality mechanism transfers beyond local AST mutants and ARC-TGI-generated tasks.

This experiment uses the public `hackos-team/arc-agi-quickstart` enumerative DSL implementation pinned at commit:

`2ea62d01162b436854b089a80715728cad2f2a3f`

and its ARC-AGI-1 public training data.

## Independent hypothesis source

Use exactly the five quickstart DSL primitives:
- tophalf
- rot90
- hmirror
- compress
- trim

Enumerate every composition of depth 1 through 6, matching the quickstart search space.

No ARC-TGI code, mutation operators, generator truth program, or Stage B candidate-generation machinery is used.

## Evaluation unit

For every public ARC-AGI-1 training task and every training demonstration j:

1. hide demonstration j completely;
2. use all remaining demonstrations as labeled evidence D_-j;
3. retain every DSL program that exactly maps every retained input to its retained output;
4. construct label-free probes only from inputs in D_-j;
5. quotient train-consistent programs by complete behavior on the frozen probe set;
6. evaluate each semantic-class representative on the held-out demonstration j only after all selectors are fixed.

A fold is usable only if:
- at least 3 semantic classes survive;
- at least 2 distinct valid held-out outputs are predicted by those classes.

No held-out output is used in candidate generation, probe generation, deduplication, centrality, or tie-breaking.

## Frozen probes

Primary probe set: the same mixed label-free family used in Stage B:
- D4 transforms of retained demonstration inputs;
- nonzero-color permutations preserving zero;
- cyclic row/column rolls;
- deterministic seed 20261028;
- cap 24 unique probes.

Secondary: D4-only, capped at 12 unique probes.

## Semantic classes and representatives

Programs are quotiented by their complete primary-probe output signature.

Within a class, the canonical representative is:
1. minimum composition depth;
2. then lexicographic program string.

Each semantic class receives equal weight for the primary analysis.

## Selectors / endpoints

For each usable fold:

- U: uniform semantic-class expected held-out correctness, i.e. fraction of classes whose representative predicts the held-out grid exactly.
- B: duplicate-invariant semantic-class plurality on the held-out input.
- D: single class with maximum primary all-probe centrality.
- D4: class with maximum D4-only centrality, secondary only.
- O: oracle whether any semantic class is correct, diagnostic.

Primary mechanism endpoint:
- macro held-out accuracy of D minus macro U across usable folds.

Primary transfer survives only if all are true:
1. >=20 usable folds from >=10 distinct ARC tasks;
2. D-U >= +0.05 absolute;
3. task-bootstrap 95% CI for D-U is not entirely below zero;
4. D beats U on the task-macro direction in >=5 distinct tasks;
5. D retains nonnegative gain on folds where semantic classes predict >=3 distinct held-out outputs.

Secondary:
- D vs B;
- D4 vs U and B;
- actual ARC test-query performance after fitting all demonstrations, reported separately and not used to rescue a failed leave-one-demo-out primary.

## Interpretation discipline

Passing this test would show that label-free counterfactual behavioral centrality transfers to an independently enumerated DSL version space.

Failure would imply the strong Stage B effect may depend materially on the local-mutant / ARC-TGI candidate construction and must be narrowed accordingly.
