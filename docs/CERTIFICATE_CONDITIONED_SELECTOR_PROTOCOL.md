# Frozen protocol: certificate-conditioned structural-start selector

Frozen before generating the prospective transform outcomes.

## Active KERNELLUM kernel

- **Precise question.** Can a pre-solver, fail-closed certificate select
  structural starts only where their basin completeness is proved, reducing
  solver evaluations across heterogeneous external residual systems without
  any loss of certified basin coverage or ordinary best-objective performance?
- **Best-known frontier.** Structural starts were much cheaper on
  Freudenstein--Roth and Himmelblau, but their coverage matched optimized
  maximin controls. FTrig showed a coverage win but lacks a complete algebraic
  stationary-point certificate. The positive opportunity is therefore safe
  routing, not another universal superiority claim.
- **Diagnostic before outcomes.** `profile_complete` requires exact elimination
  of an affine variable, enumeration of every real critical root of the
  resulting univariate polynomial, positive second derivative at retained
  roots, and distinct lifted candidates. `zero_set_complete` requires exact
  affine elimination, enumeration of every real eliminant root, zero residual,
  nonsingular residual Jacobian, and distinct lifts. Anything else is
  uncertified.
- **Policy.** Use the certified structural candidate set when either certificate
  passes; otherwise use the fixed strongest maximin baseline. No solver outcome
  participates in routing.
- **External families.** Freudenstein--Roth (profile-complete), Himmelblau
  (zero-set-complete), and FTrig (expected abstention because its factor-root
  lattice does not certify completeness for the regularized objective).
- **Exact objective.** Compare the selector with always-maximin at equal
  family-specific start budgets on 12 unopened affine transforms per family.
  Require identical full-coverage counts and best-objective success, while
  reducing aggregate local-solver evaluations by at least 25%.
- **Strongest alternative explanation.** The rule only dispatches already-known
  special solvers and the savings vanish outside the two easy polynomial
  families; the certificate may also misclassify FTrig or silently omit a
  stationary basin.
- **Cheapest decisive falsification.** Any selector coverage loss, best-objective
  loss, false FTrig activation, certificate mismatch, or aggregate evaluation
  reduction below 25% kills the kernel without threshold tuning.
- **Mechanism-derived unseen prediction.** The selector activates on all 12
  Freudenstein--Roth and all 12 Himmelblau transforms, abstains on all 12 FTrig
  transforms, exactly matches always-maximin coverage and best-objective
  success, and reduces aggregate evaluations by more than 35%.
- **Publishable threshold.** Frozen prospective transforms, strongest matched
  controls, exact certificate checks, independent audit, duplicate artifact,
  primary-literature boundary, and green repository CI.
- **Project-consequence threshold.** KERNELLUM receives an executable router
  whose default is the strongest generic plan and whose specialized path can
  only activate with a machine-checkable completeness certificate.
- **Kill condition.** Any decisive-gate failure above, or evidence that routing
  uses post-solver outcomes.

## Frozen design

- Transform seed: `20261022`; 12 transforms per family, none used in prior
  experiments.
- Solver: SciPy trust-region reflective least squares; `xtol=ftol=gtol=1e-12`,
  `max_nfev=3000`.
- Recovery tolerance: latent Euclidean distance below `2e-3`.
- Freudenstein--Roth budget: two starts; maximin endpoints are unchanged.
- Himmelblau budget: four starts; exact-corner maximin is unchanged.
- FTrig budget: 42 starts; the generic `7 x 6` grid is the frozen fallback.
- Best-objective success uses the same family-specific boundary as the source
  experiment; no new empirical threshold is fitted.

## Claim boundary

The three benchmarks, polynomial elimination, profile reduction, affine
metamorphic testing, and maximin starts are classical. The intended claim is a
KERNELLUM system law and fail-closed selector with prospective evidence, not a
new theorem of nonlinear optimization. Because two eligible families were
previously opened, the new evidence tests routing and affine transfer rather
than rediscovering their known landscape.
