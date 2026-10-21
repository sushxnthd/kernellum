# Frozen protocol: interval-certified FTrig routing

Status: frozen before the prospective transform sweep.

## Active kernel

- **Precise question.** Can a solver-independent interval certificate prove that the 42 FTrig factor-root neighborhoods each contain exactly one strict local minimum, allowing the fail-closed portfolio to activate the low-cost root lattice instead of its dominant generic fallback?
- **Best-known frontier.** The root lattice empirically covered all 42 FTrig basins, but the prior selector correctly abstained because the factor intersections are not zero-residual stationary points. Classical interval methods can certify zeros and local uniqueness; this run tests a specific objective-derived certificate and its routing consequence.
- **Objective.** Certify 42 disjoint boxes using exact rational interval arithmetic; freeze a new affine sweep; compare equal-budget root-lattice routing against generic grid, optimized Latin hypercube, and deterministic greedy-maximin controls; then recompute the three-family fleet gate.
- **Strongest alternative explanation.** The certificate may merely formalize a bespoke constructed benchmark and may not reduce solver work after conditioning changes. Generic space-filling designs may match its coverage or evaluation cost.
- **Cheapest decisive falsification.** Any box lacking inward gradient signs or a positive-definite interval Hessian; overlapping boxes; fewer than 42 independently verified minima; any prospective coverage or best-objective loss; or less than 25% aggregate fleet savings.
- **Mechanism-derived unseen prediction.** With latent coordinates `u=x+y`, `v=x-y`, every Cartesian factor-root point has a disjoint radius-`1/200` box on which the objective is strongly convex and the gradient points inward on opposite faces. Therefore each box contains exactly one strict minimum. The certificate is preserved by every invertible affine coordinate transform. Root-lattice starts will recover all 42 minima on every frozen transform and reduce FTrig evaluations by at least 35% versus the 42-start grid fallback.
- **Publishable threshold.** Exact certificate with independent implementation; 42/42 strict-minimum verification; zero losses on the untouched transform sweep; stronger matched controls; deterministic reproduction; primary-literature audit; and a portfolio-level savings pass.
- **Project-consequence threshold.** Replace FTrig abstention with an `interval_box_complete` route only when all boxes certify. The existing generic fallback remains mandatory on any certificate failure.
- **Kill condition.** Any certificate/checker disagreement, any prospective basin or objective loss, FTrig savings below 35%, fleet savings below 25%, or evidence that the result requires solver outcomes to issue the certificate.

## Frozen certificate

Write the squared residual objective in latent coordinates as

`Phi(u,v) = f(u) + g(v) + (10 + (u^2+v^2)/200)^2`,

where `f(u)=100 u^2 Π_{a in {A,B,C}}(a u^2-1)^2` and `g(v)=100 Π_{d in {D,E,F}}(d v^2-1)^2` with the published rational coefficients.

For each `u` root in `{0, +/-pi, +/-2pi, +/-3pi}` and each `v` root in `{+/-pi/2, +/-3pi/2, +/-5pi/2}`, form the radius-`1/200` rectangle using a fixed rational enclosure of `pi`. Certify:

1. the `u` gradient interval is negative on the left face and positive on the right;
2. the `v` gradient interval is negative on the lower face and positive on the upper;
3. throughout the box, both Hessian diagonal lower bounds are positive and their product exceeds the squared maximum cross-term;
4. all 42 boxes are pairwise disjoint.

Poincare--Miranda gives a stationary point in every box. Uniform positive definiteness makes the objective strongly convex on the box, so the point is unique and is a strict local minimum. Disjointness yields at least 42 distinct strict minima. The certificate is computed only from residual coefficients, fixed root hypotheses, and rational arithmetic before local solves.

## Frozen prospective evaluation

- Transform seed: `20261023`.
- Transform count: 16; rotations, translations, and positive anisotropic scales are sampled once and stored in the result.
- Budget: 42 starts for every method.
- Methods: certified root lattice, generic `7 x 6` grid, optimized Latin hypercube, and greedy maximin over a fixed dense candidate mesh.
- Primary safety endpoints: all 42 certified boxes recovered; no loss in best objective.
- Efficiency endpoint: total local-solver function evaluations.
- FTrig pass: 16/16 full coverage, zero objective losses, and at least 35% fewer evaluations than grid.
- Fleet pass: substitute the certified FTrig route into the already-frozen 12-transform selector portfolio without changing Freudenstein--Roth or Himmelblau records; require zero losses and at least 25% aggregate savings.

## Reporting boundary

The interval existence/uniqueness ingredients, polynomial factorization, multistart optimization, and benchmark are prior art. Even a pass supports only a KERNELLUM certificate-and-routing mechanism on this objective family, not a general global-optimization theorem.
