# Representation revision: external confirmation and rejected repairs

**30 September 2026. The preregistered improvement gate failed. No breakthrough
or state-of-the-art result is established.** The transformed ensemble substantially
reduced geometric mean error against original-coordinate models, but lost against
its transformed single-model control and suffered a catastrophic noisy prediction.
It is not promoted as the default predictor.

## Provenance and separation of evidence

The prior model-revision study is published in [PR #90](https://github.com/sushxnthd/kernellum/pull/90).
The new protocol, implementation, exact cohort and tests were publicly frozen at
[`bdeb77d5fd192e2cfaeb414169a41c13c2063293`](https://github.com/sushxnthd/kernellum/commit/bdeb77d5fd192e2cfaeb414169a41c13c2063293)
**before evaluating any comparative outcomes on the 39-function confirmation
cohort**. This commit is an ancestor of the results publication. The local run
manifest records local commit `ab5d461`, whose frozen source contents match the
public freeze. Public and local commit IDs differ because the publication was
constructed through the GitHub API.

The [protocol](REPRESENTATION_REVISION_PROTOCOL.md) and exact
[specification](../experiments/representation_revision/spec.json) remain unchanged.
Conservative aggregation and representation development used the already-opened
48 Feynman equations. The subsequent cross-fitting and bounded-output repairs used
the now-opened UQ cohort; they are **development only**, not fresh confirmation.

## External test

All 39 default scalar UQTestFuns 0.6.0 functions tagged `metamodeling`, with 2–20
input dimensions, were included using package-default parameters/distributions.
Five seeds, clean and 2% Gaussian observation noise, 192 candidate points, 2,048
separate test points, identical maximin query sequences, 64 observations, and
checkpoints at 32/64 observations. This produced 390 unique observation
trajectories, 24,960 simulated observed labels reused by seven methods, 2,730
method trajectories and 5,460 checkpoint scores. No functions were excluded.
These are mathematical/engineering simulations, not physical measurements.

The frozen primary was `representation_stack`: choose original/log input and
response representations using original-unit leave-one-out errors, keep the best
ridge per family/representation, and convex-stack the six best groups. All methods
use only observed labels for selection. Test targets cannot enter the predictor.

At **64 measurements**, ratios are geometric mean NMSE ratios, equally weighted
by function, seed and noise, with the preregistered 1e-8 floor inside log ratios.
Below 1 favors the candidate. This is not an arithmetic-mean error reduction.

| Comparator | Candidate/control error ratio | Function wins | Clean ratio | Noisy ratio |
|---|---:|---:|---:|---:|
| Transformed single-model selector | 1.083979 | 22/39 | 0.936174 | 1.255120 |
| Original-space single selector | 0.304117 | 26/39 | 0.099832 | 0.926426 |
| Original-space stacking | 0.298351 | 22/39 | 0.097978 | 0.908505 |
| Input transformations only | 0.326402 | 26/39 | 0.108693 | 0.980176 |
| Output transformations only | 0.726292 | 23/39 | 0.515161 | 1.023951 |
| Simple power-law/log-linear control | 0.002988 | 38/39 | 0.000402 | 0.022215 |

The gate required ratio <=0.80, at least 60% function wins, and no noise-condition
regression **against every comparator**. It failed on both error and win coverage
against the transformed selector, on win coverage against original-space stacking,
and on win coverage/noisy error against output-only transformations. The same
criterion was used throughout; it was not relaxed after results were opened.

The 69.59% geometric-mean reduction against the original-space selector is a real
bounded benchmark observation. It does not establish broad reliability: the gain
is much stronger without noise, and the arithmetic-mean error is far worse.

## The tail failure matters

At budget 64, the candidate's median NMSE was 0.0007433, versus 0.0040318 for the
original-space selector. But one noisy GenzCornerPeak trial reached **8.427e16
NMSE** (seed 930105), making the candidate's arithmetic mean **2.161e14**, versus
0.1677 for the original-space selector. Exponentiating a bad log-space prediction
can overwhelm otherwise good performance. A favorable geometric mean must not
hide this failure. The transformed single selector also had a maximum NMSE of
204.8; transformation selection alone is not a complete reliability fix.

Full distribution diagnostics and the worst-case keys are in
[diagnostics.json](../results/representation_revision/confirmation/diagnostics.json).
This evidence rules out a production-reliability claim for the frozen ensemble.

## Follow-up attempts completed rather than deferred

Four research directions were evaluated during this iteration:

1. **Conservative aggregation on opened Feynman equations:** bootstrap-quantile
   blending and pair blending failed to beat ordinary stacking. The pair blend
   ratio was 1.01439 versus stacking. Rejected before the external test.
2. **Representation selection/stacking:** strong development gains motivated the
   publicly frozen external test above. The full confirmation gate failed.
3. **Nested cross-validation on the opened UQ cohort:** five-fold validation of
   complete selectors, followed by full-data refits. The best of three exploratory
   variants, `nested_winner`, achieved ratio 0.943923 against the transformed single
   selector (25/39 wins) and 0.870794 against transformed stacking (18/39 wins).
   Both noise strata improved against the single selector, but the gain was below
   20%. It does not justify a confirmatory breakthrough claim. Cross-fitted
   stacking and inverse-error weighting were weaker. All 1,170 outcomes are kept.
4. **Bounded reconstruction:** clip individual predictions to the observed output
   range expanded by 10%; critically, each LOO bound excludes its held-out label.
   This eliminated unbounded exponential outputs by construction but damaged
   accuracy. Guarded stacking had ratio **2.793964** against the transformed
   single selector and **2.577507** against its unguarded counterpart. All 1,560
   outcomes are kept. The heuristic can bias legitimate extrapolation and is
   rejected as a replacement.

The exploratory repairs were not tuned on fresh held-out data, and none met the
existing gate even on their development cohort. No additional holdout was spent
to manufacture a confirmation from a weak development result. PMLB data and other
unused function cohorts remain available for a genuinely new candidate.

## Verification and reproducibility

- **143 tests and 11 subtests pass**, including transformed LOO against explicit
  refits, stacking KKT checks, unchanged raw-model predictions, and a guarded LOO
  test proving an extreme held-out label is excluded from its prediction bound.
- A second arithmetic implementation, importing neither Kernellum nor the runner,
  recreates all samples and scores with augmented block solves and a separately
  implemented kernel distance calculation. It verifies source/upstream/output
  hashes, the exact trial grid, all query sequences/values and budgets, selected
  models, simplex optimality conditions, all 5,460 errors, and the failed gate.
- Its numeric comparisons use relative tolerance 2e-5 plus absolute tolerance
  1e-7. The large absolute discrepancy on the catastrophic 8.427e16 score is
  floating-point-scale relative error; both implementations agree it is a
  catastrophic failure. Exact discrepancies and the relevant trial are recorded
  in [audit.json](../results/representation_revision/confirmation/audit.json).
- This is **same-author verification**, not an independent external reproduction.
  A new GitHub Actions workflow reruns tests and the full evidence audit.

```bash
python -m pip install numpy==2.3.5 scipy==1.17.0 uqtestfuns==0.6.0 pytest
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python -m pytest -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python experiments/representation_revision/run.py --out build/new-representation-run
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/audit_representation_revision.py --folder results/representation_revision/confirmation --out build/representation-audit.json
```

Study outputs refuse to overwrite an existing directory. The committed traces
include observed labels, exact query indices, all model/weight choices and errors.
Exploratory scripts and their outputs live under `conservative_revision`,
`crossfit_revision`, `guarded_revision`, and `representation_revision/development`.

## What this establishes

Representations can improve prediction with the same measurements, but the current
selection and averaging rules do not reliably control extrapolation. Broad output
clipping is not an adequate repair. The next justified investigation needs a
mechanism that detects unstable inverse transformations without erasing legitimate
extrapolation, followed by a fresh frozen comparison against the strongest opened
controls. This study supplies a concrete failure case and reproducible evidence;
it does not supply that missing mechanism or a verified breakthrough.

Logarithmic/warped regression, stacking and nested cross-validation are established
ideas. Prior-art references are in the frozen protocol. Learned-warp GPs, modern
AutoML and symbolic-regression solvers were not benchmarked, so no field-wide
novelty or state-of-the-art claim is warranted.
