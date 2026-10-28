# ARC Reboot Independent Transfer II — Rich Typed DSL, Fixed 20k Program Budget

Status: PREREGISTERED BEFORE ANY RESULTS.

## Purpose

The first independent quickstart transfer was coverage-inconclusive because its 5-primitive DSL produced only 3 usable leave-one-demo-out folds across 400 ARC-AGI-1 training tasks.

This second transfer tests the same counterfactual-centrality mechanism using a substantially richer and independently implemented typed DSL/search system on ARC-AGI-2.

Source repository:
`sirPhoebus/challenge-ARC-AGI`

Pinned commit:
`15c39778f9c36e511053b00fe69658bb3dc5be4d`

## Independent bounded hypothesis pool

Use the repository's unmodified:
- `state/config.yaml`
- `app.search.enumerator.enumerate_programs`
- `app.dsl.interpreter.run_tokens`
- token registry and enabled operation set.

The pinned config specifies:
- DSL max depth: 4
- enabled ops: MAP_COLOR, FILTER_EQ, ROTATE, REFLECT, CROP, PAD, COMPOSE
- numeric enumeration values: 0..9
- 10 colors, 4 rotations, 5 reflections
- search.max_nodes: 20,000

For every task, materialize the **first 20,000 programs yielded deterministically by the repository enumerator** and no others.

This is explicitly a bounded search pool, not a complete version space.

No ARC-TGI mutation code, true generator program, quickstart DSL, LLM, learned policy, or test labels are used.

## Dataset

Use every JSON task in the pinned repository's `data/training/` directory.

## Leave-one-demonstration-out protocol

For every task and every training demonstration j:

1. hide demonstration j completely;
2. retain programs from the fixed 20k pool that exactly solve every other training pair;
3. generate label-free probes only from retained demonstration inputs;
4. quotient consistent programs by complete behavior on the frozen mixed probe set;
5. choose class representatives and selectors without the held-out output;
6. evaluate against held-out demonstration j.

A fold is usable if:
- >=3 semantic classes remain;
- >=2 distinct valid held-out outputs are predicted by class representatives.

Folds with oracle=0 remain in the preregistered primary because selection cannot create an unexpressed answer; oracle-positive results are additionally reported as a diagnostic subset.

## Frozen probes

Primary mixed probes, exactly as the prior mechanism:
- D4 transforms;
- nonzero-color permutations preserving zero;
- cyclic row/column rolls;
- seed 20261028;
- cap 24 unique probes.

Secondary:
- D4-only, cap 12.

## Semantic quotient and tie rules

Semantic classes are complete primary-probe output signatures.

Canonical representative:
1. minimum token-sequence length;
2. lexicographically smallest token tuple.

Centrality ties:
1. canonical representative token length;
2. lexicographic token tuple.

Plurality grid ties:
- canonical serialized grid order.

Invalid/nonrectangular/empty/>30x30 outputs are valid "invalid behavior" in signatures but cannot be selected as held-out outputs.

## Endpoints

For every usable fold:

- U: fraction of semantic classes whose canonical representative exactly solves the held-out demonstration (uniform-class expected correctness).
- B: duplicate-invariant semantic-class plurality on the held-out input.
- D: class whose representative has maximum mixed-probe centrality.
- D4: class with maximum D4-only centrality, secondary.
- O: whether any semantic class solves the held-out demonstration.

Primary endpoint:
- macro D-U across usable folds.

Task-level bootstrap resamples ARC task IDs, preserving all folds from a task.

## Frozen transfer survival rule

The mechanism transfers only if every condition holds:

1. >=20 usable folds;
2. >=10 distinct tasks;
3. D-U >= +0.05 absolute;
4. task-bootstrap 95% CI for D-U is not entirely below zero;
5. positive task-macro D-U direction in >=5 distinct tasks;
6. D-U is nonnegative on folds with >=3 distinct held-out outputs.

Secondary:
- D-B;
- D4-U;
- oracle-positive subset D-U;
- coverage/oracle rate.

A failed coverage gate is **inconclusive**, not evidence against centrality.
A covered test that fails effect gates is a transfer failure and narrows the Stage B claim to its original candidate construction.
