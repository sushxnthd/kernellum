# Frozen protocol: basin-transition continuation selector

**Frozen before any outcome evaluation.**

## Active kernel

Can the first model/basin transition along controlled response-continuation paths
predict when the incumbent extrapolator is solver-dependent, and can routing
only those cases to the existing globalized fit suppress catastrophic tails
without degrading ordinary interpolation?

## Best-known frontier

Continuation and bifurcation methods diagnose branch loss and solver transitions;
algorithmic stability studies sensitivity to perturbations. The unresolved
project question is whether a truth-blind transition-amplitude statistic
prospectively predicts harmful model-selection instability and supports a safer
selector. No novelty is claimed for continuation itself.

## Strongest alternative explanation

Early transitions may reflect arbitrary jitter direction or numerical stiffness,
not a truth-relevant basin boundary. Globalization may then be no better, or may
harm well-behaved cases.

## Untouched prospective cohort

Sixteen deterministic paths not used by the prior consensus or perturbation
experiments:

- truth families: `oscillatory_cauchy`, `warped_laplace`;
- dimensions: 4 and 8;
- seeds: 8123 and 8129;
- noise laws: `symmetric_t`, `leverage_spikes`.

These paths become opened after the first run. No threshold may be tuned on them.

## Intervention and pre-outcome diagnostic

For each path:

1. fit the existing candidate and globalized controls on unperturbed training data;
2. generate eight deterministic, zero-mean unit-RMS response directions;
3. for amplitudes alpha in {0.00, 0.08, 0.16, 0.24, 0.32} training-response SD,
   warm conceptually from the previous amplitude but refit using the fixed
   candidate solver bank;
4. declare a path transition at the first alpha where either the selected
   sign/family changes from alpha=0 or normalized request-prediction RMS exceeds
   0.35.

Before request truth is accessed, compute:

- early-switch fraction E: directions transitioning by alpha <= 0.16;
- median first-transition amplitude A (0.40 for no transition);
- globalized/candidate request-prediction distance G;
- globalized/candidate full-training residual ratio R.

Route to the globalized fit iff E >= 0.50, A <= 0.16, G > 0.25, and R <= 1.15.
The scalar margin is min(E-0.50, 0.16-A, G-0.25, 1.15-R).

## Mechanism-derived unseen prediction

Dangerous paths should show repeated early branch changes across independent
continuation directions before outcome truth is seen. When that signature is
present, globalization should improve far-shell error; absent it, the incumbent
should remain preferable or indistinguishable.

## Controls

Candidate, independent solver, unconditional globalized fit, naive minimum-CV,
always-globalized, and the frozen continuation-routed selector. Domains are
inside, near shell, and far shell. Primary loss is geometric NMSE; catastrophe is
NMSE > 5.

## Exact objective and publishable gate

All must pass:

1. 16/16 paths complete and at least two routes fire;
2. no domain gains catastrophes;
3. catastrophes are halved in at least one domain with at least two candidate catastrophes;
4. inside geometric-NMSE ratio <= 1.05;
5. far-shell geometric-NMSE ratio <= 0.90;
6. route precision >= 0.75 on far-shell improvement;
7. duplicate output is byte-identical and an independent standard-library audit passes.

## Cheapest decisive falsification / kill condition

Kill without tuning if fewer than two routes fire, early transitions do not
repeat across directions, or any safety/performance gate fails. A failure counts
as evidence against this fixed transition diagnostic, not against continuation
methods generally.

## Project consequence threshold

Pass: integrate transition-amplitude routing into Kernellum evaluation.
Fail: retire this diagnostic and preserve exact evidence; do not tune against
the opened cohort.
