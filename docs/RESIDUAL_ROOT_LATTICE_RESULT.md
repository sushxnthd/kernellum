# KERNELLUM residual-root lattice result

## Decision

**The benchmark-specific positive mechanism survives.** On the externally published FTrig nonlinear least-squares objective, a pre-solver residual-factor certificate generated 42 starts that recovered all 42 strict minima in every trial. Keep this as a guarded discovery-system capability and advance the active kernel to unrelated external factorable residual systems. Do **not** call this a general solver-instability breakthrough yet.

## Frozen result

The source residuals factor along `u=x+y` and `v=x-y`. Their real factor roots give 7 `u` hypotheses and 6 `v` hypotheses, predicting a 42-start Cartesian lattice before local-solver outcomes are observed.

| Equal-budget method | Trials | Full 42-minimum coverage | Mean coverage | Mean function evaluations |
|---|---:|---:|---:|---:|
| Residual-root lattice | 9 | 9 | 100.0% | 218.6 |
| Generic 7-by-6 grid | 9 | 0 | 66.4% | 431.8 |
| Latin hypercube | 9 | 0 | 63.5% | 391.8 |
| Uniform random | 9 | 0 | 59.8% | 390.3 |
| All controls | 27 | 0 | 63.2% | 404.6 |

The identity objective was development. The frozen prediction then survived eight fixed rotation/translation/anisotropic-scaling metamorphs. The transformations changed optimizer conditioning but not the underlying minima, so this is a mechanism/invariance test rather than eight independent scientific datasets.

Selection behavior also changed:

- the lattice found the lowest observed objective (`100.246682897`) in 9/9 trials;
- the generic grid missed it in 9/9 trials (`101.236732026` best);
- uniform random missed it in 1/9 trials (`103.232284628` in that trial);
- Latin hypercube found it in 9/9 trials but never covered all 42 basins.

Thus the structured start set removed the observed best-solution tail without sacrificing ordinary best-objective performance, while uniquely giving complete basin coverage at the same 42-start budget.

## Independent checks

The independent checker does not import the runner. It:

1. recomputes the scalar FTrig objective from the pinned rational coefficients;
2. verifies all 378 root-lattice centers are finite;
3. verifies every center has a positive-definite finite-difference Hessian;
4. recomputes trial and budget invariants from the raw JSON.

Duplicate generation is required to be byte-identical. The result payload records its own canonical SHA-256.

## SCIENCE ledger

**Supported:** for this published residual-product objective, the real-factor Cartesian lattice is a sufficient prospective basin-coverage mechanism. It predicts the exact basin count and dominates matched generic starts in complete coverage and solver evaluations.

**Not supported:** factor-root seeding is not yet shown to work on unrelated objectives, noisy residuals, approximate factors, coupled factors, high dimensions, or model-selection/LOO tasks. Affine metamorphs are not external replication. Polynomial root seeding, separability, multistart, deflation, and continuation are prior art; no broad mathematical novelty is claimed.

**Strongest alternative explanation:** FTrig was deliberately constructed from visible factors, so the result may expose benchmark structure rather than a general law. That alternative remains live and defines the next falsification.

## CONSEQUENCE ledger

KERNELLUM should add a fail-closed pre-solver stage:

1. certify low-dimensional residual coordinates and real factor roots;
2. synthesize the Cartesian start lattice only when the certificate passes;
3. run the ordinary local solver from those starts;
4. fall back to generic globalized controls when the certificate fails.

The system claim is narrow but real: on certified residual-product problems, start placement can be derived from residual geometry rather than solver transcripts, eliminating a basin-coverage tail on FTrig at lower evaluation cost.

## External provenance and priority boundary

- Alban Bloor Riley, Marcus Webb, and Christopher T. Baker, *Deflation Techniques for Finding Multiple Local Minima of a Nonlinear Least Squares Problem*, arXiv:2409.14438 (2024).
- Public source repository: `AlbanBloorRiley/DeflatedGaussNewton`, commit `615c185f3d61f044eab7cfd27f97f698ff341d8f`.
- `PaperFigures.m` blob `0083087a71d2314d6c49c5ba152297e72d75fad8` supplies FTrig and reports the 42-minimum comparison.

The paper's deflated Gauss-Newton method and 300-start MultiStart comparison are the relevant frontier. This experiment evaluates a separate 42-start structural shortcut; it does not supersede deflation.

## Next decisive gate

Find two unrelated externally sourced nonlinear least-squares systems whose residuals admit certified low-dimensional factor/root hypotheses. Freeze the certificate and coverage prediction before solver outcomes. Kill the general mechanism if either external system loses coverage against a 42-equivalent evaluation budget or if approximate/noisy factors make the certificate unstable.
