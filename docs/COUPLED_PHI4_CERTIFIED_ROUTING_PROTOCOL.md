# Coupled phi4 certified-routing protocol

Status: frozen before any solver outcomes.

## Active KERNELLUM kernel

- **Precise question.** Can a pre-solver interval/monotonicity certificate on
  an unrelated coupled factor-structured residual family synthesize starts
  that eliminate capped local-solver coverage tails and reduce total work?
- **Best-known frontier.** The FTrig route certified 42 boxes and saved 51.6%
  of work, but its coefficient-radius diagnostic was non-predictive. Two
  low-dimensional external transfers were cheaper but did not beat maximin
  coverage. No prospective coupled-family transfer exists.
- **External family.** Use the stationary residual of a five-site open-chain
  discrete phi4 lattice,

  `F_i(x)=x_i^3-x_i + w_(i-1)(x_i-x_(i-1)) + w_i(x_i-x_(i+1))`,

  omitting nonexistent boundary terms. Discrete phi4 lattices are classical
  coupled nonlinear systems; this family is unrelated to FTrig and is not
  fitted to solver outcomes.
- **Scalar/vector diagnostic before outcomes.** For every sign vector
  `s in {-1,+1}^5`, certify the box `s_i*x_i in [3/4,5/4]`. Face-sign margins
  plus strict positive definiteness of the sign-transformed Jacobian certify
  one unique zero in each box. A deterministic interval-Newton refinement
  supplies the start and a residual/Jacobian receipt.
- **Exact objective.** Across the identity weights and 16 unopened rational
  edge-weight vectors, certify all 32 boxes, recover all 32 distinct strict
  zero-residual minima, and reduce capped-solver catastrophes and total
  residual evaluations against tensor corners, optimized LHS, and greedy
  maximin at the same 32-start budget.
- **Strongest alternative explanation.** The boxes merely encode one start
  per orthant; a tensor-corner design may achieve identical coverage, and
  Newton refinement may only shift computation outside the counted solver.
- **Cheapest decisive falsification.** Any failed box certificate, duplicate
  certified root, non-positive Hessian, missed structured basin, or tensor-
  corner control matching both capped coverage and end-to-end work.
- **Mechanism-derived unseen prediction.** For positive edge weights at most
  `1/16`, every sign box is invariantly certified. The certified route has no
  capped coverage failures at `max_nfev=4`; at least one strongest control has
  a positive failure rate, and end-to-end evaluations (including certificate
  refinement residual/Jacobian calls) fall by at least 25% versus the best
  control that preserves complete coverage.
- **Publishable threshold.** Exact box theorem, frozen rational sweep,
  strongest matched controls, end-to-end accounting, independent Decimal or
  Fraction checker, duplicate artifact, full tests/CI, and priority audit.
- **Project-consequence threshold.** Add a fail-closed coupled-lattice route
  keyed only by certificate data; otherwise retain generic solver routing.
- **Kill condition.** Any structural/certificate error; any structured
  catastrophe; no control tail improvement; or less than 25% end-to-end work
  reduction against the strongest complete-coverage control.

## Frozen regimes and controls

- Dimension: 5; 32 sign boxes and 32 starts per method.
- Edge weights: identity `(1/32)^4` plus 16 rational vectors sampled without
  replacement from `{1/64,2/64,3/64,4/64}` using seed `20261021`.
- Local solver: SciPy `least_squares`, analytic Jacobian, tolerances `1e-11`,
  frozen full run and capped replay at `max_nfev=4`.
- Controls: outer tensor corners at magnitude `5/4`, optimized 32-point Latin
  hypercube (128 fixed candidates), and greedy maximin from a frozen 4096-point
  Sobol pool. All controls are generated before local outcomes.
- Basin match: infinity distance `<=1e-6` to an independently reconstructed
  certified root; complete coverage requires all 32 roots.
- Ordinary performance: best objective `<=1e-20` and no loss relative to the
  strongest control.
- End-to-end work counts every residual and Jacobian call in certificate
  refinement plus every local-solver evaluation.

## Theorem boundary

For `|x_i| in [3/4,5/4]`, the uncoupled face values have inner magnitude
`21/64` and outer magnitude `45/64`. With degree at most two and
`w<=1/16`, the coupling magnitude is at most `5/16`, leaving a strict inner
margin `1/64`. Poincare--Miranda gives a zero in every sign box. After the sign
change, the Jacobian is symmetric with diagonal
`3x_i^2-1+sum_j w_ij` and off-diagonal magnitudes `w_ij`; strict diagonal
dominance gives positive definiteness and uniqueness. At a zero, the squared-
residual Hessian is `2 J^T J`, hence positive definite.

These are classical interval, monotonicity, and discrete-lattice ingredients.
Even a pass supports a KERNELLUM certificate-conditioned routing mechanism,
not a new general theorem about phi4 lattices or nonlinear least squares.
