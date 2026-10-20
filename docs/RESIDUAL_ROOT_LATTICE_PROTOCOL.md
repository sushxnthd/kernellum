# Residual-root lattice protocol (frozen)

## Active KERNELLUM kernel

**Question.** On an external nonlinear least-squares objective with independently documented multiple minima, can a computable pre-solver structural diagnostic generate a fixed-budget start set that covers solver basins more reliably than random, Latin-hypercube, or generic-grid multistart?

**Frontier.** Riley, Webb, and Baker (arXiv:2409.14438) introduce deflated Gauss-Newton methods and publish FTrig as a 42-minimum example. Their public figure code compares deflation against 300-start MATLAB MultiStart. This run tests a distinct and narrower mechanism: factor-root seeding at an equal 42-start budget. It does not claim deflation, multistart, polynomial roots, or separability as new.

**Diagnostic before outcomes.** The source residuals factor along `u=x+y` and `v=x-y`. They have 7 and 6 distinct real zero hypotheses respectively, so the diagnostic predicts a 42-cell basin lattice before any local solve completes.

**Objective.** Recover 42 distinct converged minima with exactly 42 starts on the source objective and eight fixed affine metamorphs. Compare with 42-start random, Latin-hypercube, and 7-by-6 generic-grid controls.

**Strongest alternative explanation.** Any coverage gain is merely good placement on a handcrafted polynomial, not a general solver-instability mechanism. The affine confirmations test coordinate robustness but do not establish transfer to unrelated objectives.

**Cheapest decisive falsification.** Kill if any root-lattice trial finds fewer than 42 minima, or if a matched simple control also achieves full coverage in every confirmation regime.

**Prediction.** All 9 root-lattice trials recover 42 minima. The exact prediction was fixed before running the confirmation transforms. Transform seed: `20261020`.

**Publishable threshold.** A broader result requires prospective success on at least two unrelated externally sourced residual-factor benchmarks plus a complexity/coverage statement. This single benchmark cannot meet that threshold.

**Project consequence threshold.** If the prediction survives while controls fail, add residual-factor diagnostics and structured start synthesis as a discovery-system capability, guarded by a fail-closed applicability certificate.

**Kill condition.** One failed root-lattice confirmation, universal control success, or evidence that discovered stationary points are not distinct minima.

## Provenance and holdout discipline

- External repository commit: `615c185f3d61f044eab7cfd27f97f698ff341d8f`.
- `PaperFigures.m` blob: `0083087a71d2314d6c49c5ba152297e72d75fad8`.
- Identity transform is development. Eight generated transforms are confirmation and are not used for tuning.
- No threshold may be changed after results are generated.

## Ledgers

**SCIENCE.** Determine whether real-root product structure is a sufficient prospective basin-coverage mechanism on this published objective.

**CONSEQUENCE.** Decide whether KERNELLUM should detect certified residual factorization and synthesize structure-aware starts before using generic solver ensembles.
