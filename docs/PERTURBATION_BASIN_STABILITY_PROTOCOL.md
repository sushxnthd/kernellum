# Frozen protocol: perturbation-basin stability selector

**Frozen before outcome evaluation.**

## Active kernel

Can controlled leave-block-out and response-jitter perturbations create genuinely
different basin observations, and can a pre-outcome basin-occupancy diagnostic
select a stable extrapolator that reduces catastrophic tails without degrading
ordinary interpolation?

## Frontier and alternative explanation

The preceding three-solver mechanism made 0/16 overrides because candidate and
globalized solvers were usually the same basin. The strongest alternative is
that perturbations either remain in that basin or create noise rather than
truth-correlated diversity; stability would then be vacuous or actively harmful.

## Untouched prospective cohort

Sixteen deterministic paths, disjoint from the opened consensus cohort:

- families: `rational_quadratic_ripple`, `anisotropic_laplace`;
- dimensions: 3 and 7;
- seeds: 7301 and 7307;
- noises: `symmetric_t`, `leverage_spikes`.

No result from these paths may change the selector, thresholds, or gates.

## Ensemble intervention

For each path, construct 12 members before accessing request truth:

1. six deterministic leave-four-out training perturbations;
2. six leave-four-out plus zero-mean response jitter interventions;
3. fit both sign hypotheses and both existing model families;
4. retain the minimum-CV fit within each intervention.

The baseline candidate is fit on the unperturbed data. Globalized,
independent, and naive minimum-CV controls are retained.

## Pre-outcome diagnostic and selector

On the request locations (without truth), normalize predictions by training
response scale and form the graph whose edges join members at RMS distance at
most 0.35. Let (C) be its largest component and let its medoid minimize mean
within-component RMS.

Diagnostic vector:

- occupancy (o=|C|/12);
- within-component medoid dispersion (s);
- candidate-to-medoid separation (d);
- full-training residual ratio (r).

The selector overrides the candidate iff:

- (|C|ge 8);
- (sle0.20);
- (d>0.45);
- (rle1.20).

Ties are lexicographic. The scalar stability margin is
(min(o-2/3,,0.20-s,,d-0.45,,1.20-r)).

## Frozen boundary sweep

Report counterfactual decisions for graph radii 0.25, 0.35, and 0.50 without
changing the primary selector. This tests whether the mechanism is a sharp
transition or threshold accident.

## Metrics and controls

Domains: inside, near shell, far shell. Metric: geometric normalized MSE;
catastrophe: NMSE > 5. Controls: candidate, independent, globalized, naive
minimum-CV, always-medoid, and abstention (candidate unless the frozen gate
fires).

## Publishable positive gate

All must hold:

1. 16/16 complete and at least two nonvacuous overrides;
2. no domain has more catastrophes than candidate;
3. at least one domain with at least two candidate catastrophes is halved;
4. inside geometric NMSE ratio <= 1.05;
5. far-shell geometric NMSE ratio <= 0.90;
6. override precision >= 0.75 (selected beats candidate on far shell);
7. independent audit and byte-identical rerun pass.

## Kill condition

Kill without tuning if fewer than two overrides occur, if perturbations do not
create multiple prediction basins, or if any safety/performance gate fails.

## Project consequence threshold

Pass: integrate the diagnostic as a guarded discovery/evaluation selector.
Fail: record whether the cause is absent diversity, unstable occupancy, or
noncausal stability; do not ship or retune on this cohort.
