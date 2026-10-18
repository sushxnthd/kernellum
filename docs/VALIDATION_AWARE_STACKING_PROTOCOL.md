# Validation-aware robust stacking prospective protocol

## Classification

**Frozen prospective synthetic-family evaluation.** This protocol is committed before any truth-domain score is computed. No prior prospective cohort is reused for scoring or threshold selection.

## Precise question

Can deterministic out-of-fold validation construct a conservative convex aggregation of the incumbent candidate, globalized, and independently implemented fits that reduces catastrophic extrapolation tails on unseen truth families without degrading ordinary interpolation?

## Mechanism

For each dataset, partition the 32 public training observations into four interleaved folds by their fixed maximin order. On each fold:

1. fit the candidate, globalized, and independent solver banks to the other 24 observations;
2. predict the held-out eight observations;
3. normalize squared error by the held-out response variance.

Search the fixed simplex grid in increments of 0.1 subject to candidate weight at least 0.5. Choose weights minimizing, lexicographically:

1. maximum fold normalized MSE;
2. mean fold normalized MSE;
3. non-candidate weight;
4. globalized weight;
5. independent weight.

Refit all three banks on the full training set and use the fixed convex weights for all requested predictions. This is a robust action learned only from held-out training responses; it does not inspect near- or far-shell truth.

## Mechanism-derived prediction

The aggregation should help when two pre-outcome conditions hold together:

- at least 0.2 total weight is placed outside the candidate;
- RMS request-prediction disagreement among the three full-data fits exceeds 0.10 training-response standard deviations.

It should fail to improve when the fitted functions are nearly identical, and can fail under covariate shift that is not represented by the four training folds.

## Untouched cohort

Exactly 24 paths:

- truth families: `damped_chirp`, `rotated_student`, `asymmetric_ridge`;
- dimensions: 6 and 10;
- seeds: 12011 and 12017;
- noise families: `symmetric_t` and `leverage_spikes`.

Each path uses 32 maximin training points and fixed inside, near-shell, and far-shell request sets. Dataset construction, seeds, solver bank, fold partition, simplex grid, metrics, and gates are fixed in the runner before execution.

## Strong controls

- incumbent candidate;
- unconditional globalized fit;
- independent solver;
- naive minimum exact-LOO-CV fit;
- equal-weight three-solver average;
- hard validation selector using the same four-fold worst-fold objective;
- conservative validation-aware stack.

## Metrics and gates

Primary loss is geometric NMSE; catastrophe means NMSE greater than 5. The kernel passes only if all hold:

1. all 24 paths complete;
2. far-shell stack/candidate geometric-NMSE ratio is at most 0.90;
3. inside ratio is at most 1.05;
4. no domain gains catastrophes;
5. at least two far-shell candidate catastrophes exist and at least half are removed;
6. the stack beats the equal average and hard validation selector on far-shell geometric NMSE;
7. at least four paths satisfy the predicted-active condition across at least two truth families;
8. at least 75% of predicted-active paths improve over the candidate on far-shell NMSE.

## Strongest alternative explanation

Any success could be ordinary validation model averaging rather than a new instability law, or could be caused by one synthetic family. Family-level active coverage and matched equal-average/hard-selection controls distinguish these explanations but do not establish external-data transfer.

## Kill condition

If any gate fails, do not tune the simplex grid, candidate-weight floor, active thresholds, folds, or cohort. Preserve the result and kill or reformulate the kernel.

## Publishable and project-consequence threshold

A pass is only a prospective mechanism signal. It earns one external-data replication and integration as an opt-in robust selector in Kernellum evaluation. It is not a flagship claim until external transfer and a primary-literature audit survive.
