# Robust solver-control development protocol

**Frozen:** 16 October 2026  
**Classification:** opened-cohort mechanism development; not confirmatory evidence  
**Action class:** CONTROL ELIMINATION

## Active KERNELLUM kernel

### Precise question

On the permanently opened 16-path shifted cohort, can a deterministic nine-start
solver, a basin ensemble, or a stability-penalized basin selector eliminate the
catastrophic tails that defeated single-start, cross-solver lower-CV,
sign-anchored, and three-start globalization, without materially degrading
ordinary performance?

### Frontier and strongest alternative

The current three-start globalizer repaired one same-family near-tie catastrophe
but failed aggregate tail-control and ordinary-performance gates. Multi-start
nonlinear least squares and ensembles are standard controls; the unresolved
project question is whether any such control is strong enough to justify a new
prospective Kernellum study.

The strongest alternative is that the observed failures are model
misspecification rather than basin selection. If so, larger start banks and
within-family basin aggregation will not remove tails, and this solver-centric
kernel must be killed rather than repackaged.

## Frozen cohort and methods

Use exactly the 16 opened paths produced by
`scripts/evaluate_sign_anchor_shifted.py`: two response shapes, dimensions 3
and 5, seeds 3101 and 3102, and Gaussian or Student-t noise.

For every sign/family combination, derive the usual deterministic base start.
Define the nine-start bank by multiplying the existing solver's nonlinear shape
coordinates by

`[0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00, 3.00, 4.00]`.

The affine family scales all coordinates after its intercept. The concave family
scales only coordinates after index `1+d`, matching the previous three-start
control. Duplicate starts are removed bytewise.

Compare:

1. **single:** existing base start;
2. **globalized-3:** factors `[0.50,1.00,1.50]`, minimum training SSE;
3. **globalized-9:** all nine starts, minimum training SSE;
4. **ensemble-9:** pointwise median of all successful nine-start predictions;
5. **stable-9:** among successful starts, minimize normalized training SSE plus
   `0.25` times normalized mean-squared deviation from the pointwise basin
   median on the training inputs.

For each method, reproduce exact leave-one-out fitting with the same rule and
choose the sign/family with minimum normalized LOO error. Record failed fits and
the exact number of attempted/successful optimizations.

## Objective and gates

A catastrophe is `log NMSE > 5`. All gates are required for a method to survive
to prospective testing:

1. complete all 16 paths;
2. no more catastrophes than the single-start candidate in every domain;
3. at least 50% fewer total catastrophes than single-start across the three
   domains;
4. inside-domain geometric NMSE no more than 1.10 times single-start;
5. near- and far-shell geometric NMSE no more than 1.10 times the best of
   single-start and the previous three-start control;
6. byte-identical rerun under single-threaded BLAS;
7. independent aggregation reproduces every metric and gate.

The measurable objective is lexicographic: total catastrophes, worst-domain
geometric NMSE ratio to single-start, then successful optimization count.

## Cheapest decisive falsification

If no method passes all performance gates, kill the solver-basin kernel:
catastrophic tails on this cohort are not repaired by deterministic multistart,
basin aggregation, or the frozen stability penalty. Pivot to model revision or
explicit support-aware abstention.

If one or more methods pass, select the lexicographic winner without inspecting
any unopened cohort, freeze its implementation and thresholds, then evaluate it
once on new response families, dimensions, seeds, and noise regimes.

## Publishable success and project relevance

This development study cannot establish a publishable result. Publishable
success requires the frozen winner to eliminate catastrophic tails on an
untouched cohort, remain noninferior ordinarily, survive an external dataset,
and beat matched multistart/ensemble controls at reported compute cost.

Project relevance requires a concrete Kernellum solver policy returning the
chosen control, basin count, failures, compute receipt, and an explicit
abstention when its prospective contract is not met.

## Ledgers

### SCIENCE

- **KNOWN:** single-start, sign anchoring, three-start globalization, and a
  pairwise envelope have all failed at least one frozen gate.
- **UNTESTED:** whether denser deterministic starts, basin medians, or a frozen
  stability penalty repair the opened cohort.
- **ALTERNATIVE:** model misspecification, not solver basins, drives the tails.

### CONSEQUENCE

This is a kill-or-advance screen. Passing only licenses one prospective study;
failure ends the solver-basin line and moves KERNELLUM to model revision or
support-aware abstention.
