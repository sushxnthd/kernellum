# Interval-certified FTrig routing result

## Decision

**The positive mechanism survives every frozen gate.** KERNELLUM can replace its cost-dominant generic FTrig fallback with factor-root starts only after an exact interval certificate proves 42 disjoint strict-minimum neighborhoods. This changes the previously falsified fleet selector from 7.87% to **51.59% aggregate evaluation savings**, with zero basin-coverage or best-objective losses.

This is the first positive selector result in the current kernel sequence that passes the preregistered portfolio-level consequence gate. It remains a narrow certified-family mechanism, not a general solver-instability law.

## Exact certificate

In latent coordinates `u=x+y`, `v=x-y`, the squared residual objective is

`Phi(u,v) = f(u) + g(v) + (10 + (u^2+v^2)/200)^2`.

Around every Cartesian pair from

- `u in {0, +/-pi, +/-2pi, +/-3pi}`;
- `v in {+/-pi/2, +/-3pi/2, +/-5pi/2}`,

the checker constructs a radius-`1/200` rational rectangle. Exact `Fraction` interval evaluation established, for all 42 boxes:

1. negative/positive `u`-gradient signs on the left/right faces;
2. negative/positive `v`-gradient signs on the lower/upper faces;
3. a positive-definite Hessian throughout the entire rectangle;
4. pairwise disjointness.

The minimum margins over all boxes were:

| Certified margin | Minimum |
|---|---:|
| inward `u` face sign | 1.00099 |
| inward `v` face sign | 0.85112 |
| `H_uu` lower bound | 200.192 |
| `H_vv` lower bound | 230.749 |
| Hessian determinant lower bound | 46,194.05 |

Poincare--Miranda supplies a stationary point in each box. Uniform positive definiteness makes the objective strongly convex on each rectangle, so that stationary point is unique there and is a strict local minimum. Disjointness proves 42 distinct strict minima. The proof does **not** assert that no additional minima exist outside these boxes.

The certificate uses only published rational coefficients, a fixed rational enclosure of `pi`, fixed factor-root hypotheses, and exact interval arithmetic before any local solver run. Invertible affine coordinate changes preserve the certified minima through Hessian congruence.

## Prospective frozen sweep

Sixteen previously unused transforms were generated from seed `20261023`. Every method received 42 starts.

| Method | Full 42-box coverage | Mean coverage | Total evaluations |
|---|---:|---:|---:|
| Certified root lattice | **16/16** | **100.0%** | **3,366** |
| Generic 7-by-6 grid | 0/16 | 66.52% | 6,947 |
| Optimized Latin hypercube | 0/16 | 69.20% | 6,308 |
| Greedy maximin | 0/16 | 52.68% | 6,641 |

The certified route used **51.55% fewer evaluations** than the frozen grid fallback, exceeding the 35% gate. It incurred zero best-objective losses. The grid missed the best certified objective in 16/16 transforms; optimized LHS missed it in 3/16 and greedy maximin in 1/16.

## Portfolio consequence

Replaying the previously frozen 36-problem, three-family portfolio changed only the FTrig route:

- selector evaluations: **2,911**;
- unchanged baseline evaluations: **6,013**;
- aggregate reduction: **51.59%**;
- coverage losses: **0**;
- best-objective losses: **0**.

This clears the original 25% fleet gate without reweighting families or lowering the threshold. Freudenstein--Roth and Himmelblau records were not regenerated or modified.

## Independent falsification

- A separate checker reimplemented all interval operations with 90-digit `Decimal` arithmetic and directed rounding; it imported neither the runner nor the `Fraction` certificate.
- Independent audit: **10/10** checks passed, including all 42 boxes, disjointness, prospective outcomes, fleet outcomes, and payload digest.
- A deliberate radius increase from `1/200` to `1/100` fails the proof, establishing that the gate is not a vacuous sign check.
- Duplicate full generation is byte-identical.

The first wide-radius unit test failed for an implementation reason: Python had captured the original radius in a default argument, so the perturbation did not reach the helper. That failed gate is preserved. The helper now resolves the radius at call time; the correction changes no frozen result byte.

## Runtime integration

`kernellum.discovery.interval_basin_router` now exposes a fail-closed route. It activates box-center starts only when the certificate uses trusted outward arithmetic, contains the expected number of uniquely identified boxes, asserts disjointness, and passes every face-sign and Hessian obligation. Missing, malformed, partial, overlapping, or failed evidence returns `generic_fallback`.

## Priority audit

- Riley, Webb, and Baker introduced the published FTrig multiple-minimum least-squares example and deflated Gauss--Newton methods: <https://arxiv.org/abs/2409.14438>.
- Interval Newton/Krawczyk inclusion methods have long certified existence and uniqueness of nonlinear-system zeros: <https://na.math.kit.edu/alefeld/download/1994_Inclusion_methods_for_system_of_nonlinear_equations_the_inteval_Newton_method_and_modifications.pdf>.
- The Poincare--Miranda theorem and its use as a multidimensional zero-existence principle are classical: <https://www.jstor.org/stable/2975081>.
- Multistart and space-filling/scatter-search initialization for nonconvex local solvers are established: <https://www.uv.es/~rmarti/paper/docs/global2.pdf>.

Accordingly, no novelty is claimed for interval arithmetic, Poincare--Miranda, polynomial roots, multistart, the benchmark, or affine invariance. The smallest defensible contribution is their objective-specific composition into a prospective, fail-closed KERNELLUM routing certificate that converts a dominant abstention into a measured portfolio win.

## Limits

- One constructed, two-dimensional external objective family; affine transforms are mechanism tests, not unrelated datasets.
- The proof certifies exactly one minimum in each of 42 boxes, not global completeness outside their union.
- Exact published coefficients and well-separated factors are assumed; noisy or learned residuals are untested.
- The portfolio replay is a consequence analysis on an already opened cohort; only the 16-transform FTrig sweep was prospective.
- Independent internal reproduction and CI are not third-party replication.

## Next external gate

Freeze the same face-sign/strong-convexity certificate on an unrelated factor-structured residual system with nontrivial coupling or coefficient perturbation. The mechanism loses flagship status if certification becomes numerically brittle or if certified starts lose matched-budget performance there.
