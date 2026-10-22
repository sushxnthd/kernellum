# Frozen protocol: phi4 orbit-certificate amortization

Status: frozen before opening the new weight regimes or solver outcomes.

## Active KERNELLUM kernel

- **Precise question.** Can the exact global sign symmetry of the coupled
  five-site phi4 residual amortize certified-start construction enough to turn
  the safe capped-solver primitive into a fleet-positive selector?
- **Best-known frontier.** The preceding route certified all 544 boxes and
  eliminated every capped catastrophe, but reduced end-to-end work by only
  20.5128% because it charged one residual and one Jacobian evaluation for all
  32 sign boxes. The frozen value gate was 25%.
- **Algebraic mechanism.** For every edge-weight vector,
  `F(-x)=-F(x)` and `J(-x)=J(x)`. Therefore the Newton map
  `N(x)=x-J(x)^(-1)F(x)` is odd: `N(-x)=-N(x)`. The 32 sign boxes form 16
  antipodal orbits, so one residual/Jacobian computation constructs both starts
  in each orbit without changing either start mathematically.
- **Scalar/vector diagnostic before outcomes.** Verify exact residual oddness,
  Jacobian evenness, sign-box antipodality, and the existing uniform face/SPD
  certificate from the rational weights. Only certified regimes may route.
- **Exact objective.** On a new disjoint 19-regime rational sweep, retain 32/32
  full and capped basin coverage with zero objective losses while reducing
  end-to-end work by at least 25% versus the strongest complete-coverage
  control. Certificate/start overhead is charged as 32 calls per regime.
- **Strongest alternative explanation.** The saving is bookkeeping: mirrored
  starts may not be numerically identical, capped convergence may change, or
  the new regimes may make tensor corners cheaper enough that halving overhead
  still misses the fleet gate.
- **Cheapest decisive falsification.** Any odd/even identity failure, any start
  mismatch beyond `1e-14`, any lost basin or objective, any capped catastrophe,
  or aggregate reduction below 25% against the best complete control.
- **Mechanism-derived unseen prediction.** Batched and unbatched certified
  routes have identical decisions, coverage, objectives, and local-solver call
  counts; only construction overhead falls from 64 to 32 calls per regime. The
  aggregate reduction crosses 25% without changing the control denominator.
- **Publishable threshold.** Exact orbit law, prospective disjoint sweep,
  unbatched ablation, tensor/LHS/maximin controls, complete accounting,
  independent exact checker, duplicate artifact, full regression and CI.
- **Project-consequence threshold.** Integrate orbit batching as the default
  certified phi4 route only if the frozen fleet gate passes.
- **Kill condition.** Any safety/coverage loss, less than 25% end-to-end
  reduction, or a stronger complete control matching the batched route.

## Frozen regimes

- Dimension: 5; 32 signs grouped canonically by first coordinate `+1` into 16
  antipodal pairs.
- Weight pool: numerators in `{1,2,3,4}` over denominator 64.
- Exclude every regime used in the predecessor experiment.
- Draw the first 19 remaining regimes after shuffling with seed `20261022`.
- Solvers, tolerances, controls, basin matching, ordinary-performance threshold,
  and end-to-end accounting are unchanged from the predecessor protocol.

## Boundary

Odd residuals with even nonsingular Jacobians admit this antipodal batching.
The law says nothing about other symmetries, asymmetric forcing, completeness of
all phi4 stationary points, or unrelated residual families. Symmetry reduction
and interval/Newton methods are classical; the candidate contribution is the
prospectively validated KERNELLUM routing mechanism and exact cost boundary.
