# Frozen protocol: quintic equivariance transfer

Status: frozen before opening the disjoint holdout regimes or their solver outcomes.

## Pilot disclosure

A 20-regime calibration pilot (seed `20261023`, denominator 96) was used only to choose the unrelated family, tolerances, cost accounting, and holdout gate. It is opened and excluded from every prospective claim. The pilot produced complete certified coverage and motivated the stricter holdout below.

## Active question

Does KERNELLUM's pre-outcome equivariance diagnostic transport the symmetry-amortized selector from the coupled phi4 family to an unrelated coupled quintic residual, while correctly abstaining under symmetry-breaking forcing?

The five-dimensional residual is

[
F_i(x)=x_i^5-x_i+sum_{jsim i} w_{ij}(x_i-x_j).
]

This changes the local polynomial degree, curvature, root locations, Newton dynamics, and certified face margins relative to the phi4 experiment.

## Exact pre-outcome diagnostic

For every regime, require all of:

1. exact odd residual: (F(-x)=-F(x));
2. exact even Jacobian: (J(-x)=J(x));
3. complete antipodal pairing of all 32 sign boxes;
4. face margin at least (1063/3072);
5. strong-monotonicity margin at least (149/256);
6. one certified root in every box ([3/4,5/4]) or its negative coordinate interval.

The face bound uses (x^5-x=-525/1024) at (x=3/4), while the maximum adverse coupling is (1/6). The Jacobian is a positive diagonal with minimum (149/256) plus a positive-semidefinite weighted path Laplacian. Poincare-Miranda gives existence and strict monotonicity gives uniqueness inside each box.

Only regimes satisfying this vector diagnostic may use orbit batching. Any nonzero forcing breaks oddness and must cause abstention before residual/Jacobian evaluation.

## Frozen holdout

- Weight pool: four path-edge numerators in `{1,2,3,4}` over denominator 96.
- Exclude all 20 pilot regimes.
- Shuffle remaining regimes with seed `20261024`; take the first 23.
- Negative controls: eight forced variants with nonzero first-coordinate forcing `1/1000,...,8/1000`.
- Thirty-two starts and the same full/capped Newton budgets as the pilot.
- Methods: orbit-batched certified, unbatched certified ablation, tensor corners, optimized Latin hypercube, greedy maximin.

## Frozen predictions and gates

The mechanism predicts:

- 23/23 exact 32-root box certificates;
- orbit-batched and unbatched starts identical to (10^{-14});
- identical solver decisions, coverage, and objectives;
- 23/23 full and capped coverage with zero capped catastrophes;
- at least 35% total-work reduction versus the strongest full-complete simple baseline;
- no ordinary-performance loss;
- all eight forced negative controls abstain with zero construction calls.

Kill or narrow the transfer claim on any certificate failure, holdout overlap, start/decision mismatch, lost basin, objective loss, forced activation, or reduction below 35%.

## Strongest alternative explanations

The phi4 win may be family-specific; quintic curvature may make the one-step starts unreliable, tensor corners may become cheaper, or the symmetry check may be merely descriptive and fail to predict forced abstention.

## Completion gate

Require raw per-regime outcomes, the unbatched ablation, strongest simple controls, exact certificate derivation, a structurally independent checker, duplicate reproduction, focused and full regression, CI, explicit novelty limits, and integration into the real selector.

## Novelty boundary

Equivariance, symmetry reduction, Poincare-Miranda, monotone maps, and Newton iteration are established. The candidate contribution is a prospectively falsifiable KERNELLUM diagnostic that predicts when certificate transport is operationally safe and fleet-positive across residual families, plus a fail-closed boundary when it is not.
