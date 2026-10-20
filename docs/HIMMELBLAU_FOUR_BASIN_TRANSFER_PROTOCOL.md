# Frozen protocol: four-basin algebraic transfer

## Active KERNELLUM kernel

- **Precise question.** Does certified residual elimination retain a strict
  catastrophic-basin-coverage advantage on an unrelated external nonlinear
  least-squares system with at least four documented minima, after the earlier
  two-minimum transfer tied a simple control?
- **Best-known frontier.** The FTrig factor-root lattice covered 42 minima, but
  its first external transfer to Freudenstein--Roth tied a two-point maximin
  control and was demoted to an efficiency optimization. Algebraic equation
  elimination and the Himmelblau test function are classical.
- **External system.** Use the classical Himmelblau residual system
  `r1=x^2+y-11`, `r2=x+y^2-7` on the standard latent domain `[-5,5]^2`. Its
  objective is the sum of squared residuals and has four documented zero-valued
  minima. Source boundary: Himmelblau (1972); Jamil--Yang benchmark survey
  (2013), DOI `10.1504/IJMMNO.2013.055204`.
- **Pre-solver diagnostic.** Detect that `r1` is affine in `y`, substitute
  `y=11-x^2` into `r2`, enumerate the real roots of
  `x^4-22x^2+x+114`, lift them back to `(x,11-x^2)`, and retain only candidates
  with full-rank residual Jacobian. This is computed before any local-solver
  outcomes.
- **Exact objective.** At an equal four-start budget, compare eliminant-root
  starts against the exact four-corner maximin packing of the square, Latin
  hypercube, uniform random, and a dense-grid greedy maximin implementation.
  Measure recovery of all four independently verified strict minima, solver
  evaluations, and retention of zero residual.
- **Strongest alternative explanation.** The mechanism merely solves a tiny
  polynomial system, while maximin corners already seed all four attraction
  basins; any apparent win may also come only from placing starts at solutions.
- **Cheapest decisive falsification.** If either maximin control covers all four
  minima in every fixed regime, the catastrophic-coverage claim is killed even
  if algebraic starts use fewer evaluations.
- **Mechanism-derived unseen prediction.** The eliminant has exactly four real
  roots, all four lifted candidates have nonsingular Jacobians, and the four
  candidates recover all four minima under the identity problem and eight
  fixed affine coordinate metamorphs. Neither maximin control will attain
  universal four-minimum coverage across those nine regimes.
- **Publishable threshold.** Four certified candidates; complete structured
  coverage and zero residual in 9/9 regimes; strictly fewer catastrophes than
  both maximin controls; independent residual/Jacobian/Hessian audit; exact
  duplicate artifact; primary-literature boundary; full CI.
- **Project-consequence threshold.** KERNELLUM gains a fail-closed algebraic
  start synthesizer for two-polynomial residual systems with a certified affine
  elimination variable and simple real eliminant roots.
- **Kill condition.** Candidate-count/certificate failure, any structured basin
  miss, or universal coverage by either maximin control. No threshold retuning.

## Frozen design

- Coordinate-transform seed: `20261021`.
- Regimes: identity plus eight fixed rotations, anisotropic scales, and shifts.
- Random/LHS repetitions: 64 per regime.
- Dense greedy-maximin candidate grid: `41 x 41`, deterministic farthest-point
  selection initialized at the lexicographically first corner.
- Solver: SciPy trust-region reflective least squares with tolerances `1e-12`
  and `max_nfev=3000`.
- Recovery tolerance: latent Euclidean distance below `2e-3`.
- A catastrophe is failure to recover all four certified minima with four local
  solves.

## Holdout and claim boundary

The source benchmark and its four-minimum count are public, but solver outcomes
and affine confirmations are unopened at freeze time. The test is prospective
for mechanism transfer, not for discovery of Himmelblau's classical minima.
No novelty is claimed for the benchmark, polynomial elimination, root finding,
or multistart optimization.
