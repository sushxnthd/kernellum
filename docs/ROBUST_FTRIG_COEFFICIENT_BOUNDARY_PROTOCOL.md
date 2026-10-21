# Frozen protocol: robust FTrig coefficient boundary

Status: frozen before generating the coefficient sweep.

## Active kernel

- **Precise question.** Can a solver-independent scalar certificate margin predict, before local solves, when the 42-basin FTrig route remains safe under coefficient drift, and can fail-closed use of that diagnostic retain the route's catastrophic-tail and ordinary-cost advantage?
- **Best-known frontier.** The interval-certified route survives affine coordinate changes, but assumes the exact published residual coefficients. Coefficient perturbation is the sharpest documented untested boundary.
- **Objective.** Replace point coefficients by independent relative intervals, compute the largest dyadic uncertainty radius at which every face-sign, Hessian, and disjointness obligation still holds, freeze perturbations on both sides of that boundary, and compare fail-closed robust routing with unconditional certified starts plus equal-budget grid, optimized Latin hypercube, and greedy-maximin controls.
- **Strongest alternative explanation.** The original margin may be numerically brittle or unrelated to realized solver failures; unconditional root starts may remain safe well after certification fails, making abstention pure overhead.
- **Cheapest decisive falsification.** No positive common uncertainty radius; disagreement between independent exact checkers; any routed instance losing a certified basin or best objective; or fail-closed routing failing to reduce catastrophic losses relative to unconditional reuse without increasing median evaluations by more than 10% on accepted cases.
- **Mechanism-derived unseen prediction.** Exact interval propagation will yield a nonzero common coefficient radius. Every perturbation contained inside it will preserve all 42 strict-minimum boxes and permit the low-cost route; outside perturbations will include both certifiable and non-certifiable cases, so the diagnostic will abstain selectively rather than act as a perturbation-size threshold.
- **Publishable threshold.** Closed-form executable interval obligations, a nonzero exact boundary bracket, independent implementation, untouched perturbations straddling the boundary, zero accepted-case safety losses, stronger matched controls, and a primary-literature priority audit.
- **Project-consequence threshold.** Runtime accepts coefficient-bearing FTrig certificates only when uncertainty-aware obligations pass; otherwise it invokes the existing generic fallback. The diagnostic must remove every observed catastrophic unconditional-reuse case while retaining at least 75% of safe low-cost routes.
- **Kill condition.** Zero robust radius, checker disagreement, any false acceptance, less than 75% safe-route retention, no catastrophic-tail reduction, or ordinary accepted-case evaluation regression above 10%.

## Frozen uncertainty model

Each of the six positive factor coefficients `A..F` varies independently in
`[c(1-rho), c(1+rho)]`. All arithmetic is exact rational interval arithmetic.
The published factor-root centers and radius-`1/200` latent boxes remain fixed;
this deliberately tests robustness of the deployed route rather than moving
centers after observing outcomes.

Search `rho = 2^-k` for integer `k=4..24` and report the largest passing grid
point plus the next larger failing point. The diagnostic is the minimum signed
certificate slack over all 42 boxes and all face/Hessian obligations.

## Frozen prospective sweep

- Seed: `20261024`.
- Draw 48 independent coefficient vectors: 16 at `0.5*rho_pass`, 16 at
  `rho_pass`, and 16 at `2*rho_pass`, storing draws before local solves.
- Budget: 42 starts per method.
- Methods: unconditional root lattice, fail-closed robust route, generic grid,
  optimized Latin hypercube, and deterministic greedy maximin.
- Catastrophe: fewer than 42 original-box basin IDs recovered or best-objective
  loss above `1e-8` relative to the best method on that instance.
- Primary endpoints: false accepts, safe-route retention, catastrophe count,
  and total/median local-solver function evaluations.

## Reporting boundary

Interval sensitivity analysis and robust nonlinear-equation certification are
prior art. A pass would support only an executable uncertainty-aware routing
law for this factor-structured family, not global completeness or unrelated-
family transfer.
