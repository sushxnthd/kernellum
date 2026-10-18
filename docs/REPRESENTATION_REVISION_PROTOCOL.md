# Representation revision: external confirmation protocol

30 September 2026. Parent: published model-revision evidence in PR #90.
This protocol, implementation and external cohort are frozen before the first
comparative evaluation on that cohort. Development on the opened Feynman rows is
explicitly separate and cannot be called held-out evidence.

## Why this candidate

A new conservative aggregation screen tested four blending rules against model
selection, an RBF-only control, ordinary constrained stacking and inverse-CV
weighting. None beat ordinary stacking in aggregate. That lead was rejected.
The exact failed screen is retained in `results/conservative_revision/development`.

A second development study added logarithmic input/response representations to
the prior six-family kernel library. On the 48 already-opened Feynman rows,
representation selection had an error ratio of about 0.0313 versus original-space
model selection. Ordinary stacking of transformed models improved further; the
single-model version was about 1.198 times its error. Therefore the **frozen
primary candidate is `representation_stack`**, not the single-model selector.
These are development observations, not independent confirmation. An explicit
code fix removes a redundant identity input branch when no input column can be
logged; both development outputs and the pre-fix code commit are retained.

The broad transformation and stacking ideas are well established. This is a test
of practical performance, not a claim to invent warped regression or ensembles.

## External cohort selected without comparative results

Pinned package: **UQTestFuns 0.6.0**. Include **all 39** default test-function
instances tagged `metamodeling`, with scalar output and 2–20 input dimensions.
Use package-default parameters and probabilistic input distributions. Variable-
dimension functions use their constructor default dimension. No equations are
removed based on results. The authoritative names, dimensions, input identifiers
and upstream module hashes are in `experiments/representation_revision/spec.json`.

The cohort contains engineering simulations and mathematical test functions,
including oscillatory, polynomial and nonlinear responses. It is not physical
measurement data. It is public and was visible by metadata before the freeze,
but none of its outputs were evaluated during this candidate's development.
Some functions belong to related families; no independence-based p-value is
claimed. This is not the full UQ literature or a symbolic-discovery benchmark.

Per function: five seeds, clean and 2%-of-pool-SD Gaussian noise, a 192-point
measurement pool, and a separate 2,048-point test set from the same default
probabilistic input distribution. Query 64 points, including a common 16-point
random start, with maximin coverage in pool-normalized original coordinates.
All seven methods receive exactly the same queried labels. Record errors at
32 and 64 observations; the **64-observation result is primary**.

There are 39 × 5 × 2 = 390 unique measurement trajectories, 24,960 unique simulated
observations, 2,730 method fits/trajectories and 5,460 checkpoint scores. Counted as
independently budgeted method arms, there are 174,720 label uses; these are reused
observations, not 174,720 distinct new physical measurements.

## Predictor and controls

Input representations: identity and log(abs(x)) for columns whose entire known
pool is strictly positive or strictly negative. Mixed-sign columns stay unchanged.
Normalize each representation using pool minima/maxima. If every column is
mixed-sign, skip the redundant log-input branch. An out-of-domain logarithmic
prediction causes a reported failed trial rather than a silent exclusion.

Response representations: identity plus log(y) if all measured values are
positive, or log(-y) if all are negative. Mixed-sign observations use identity
only. No unqueried response determines eligibility. Model fitting has an
unpenalized intercept and the six kernel families and three ridge values from
`revision.py`. Compute analytic leave-one-out residuals in transformed space,
back-transform the predictions, then score **squared error in original output
units**. This is deliberately not selection by log-space error.

Select the best ridge per input/response/family group, rank by original-unit LOO
error, retain the top six groups, and fit nonnegative weights summing to one by
minimizing their LOO residual sum of squares. The six-weight convex program is
solved by exhaustive active-face enumeration. After fit/weight choice is frozen,
back-transform individual predictions and combine them in original output units.

Primary: `representation_stack`. Six comparator arms:

1. `representation`: best single model in the entire transformed library.
2. `raw`: best single model in original coordinates/output.
3. `raw_stack`: ordinary constrained stacking of original-space model families.
4. `input_only`: best model with input transformations but identity response.
5. `output_only`: best model with response transformations but original inputs.
6. `log_linear`: simple log-input/log-output linear regression, ridge selected by
   original-unit LOO; if output cannot be logged, falls back to original-space
   linear regression. This is a power-law control, not a symbolic search engine.

Selectors receive only input pools, queried indices, and observed values. They
receive no function name, formula, test responses, or clean pool responses.
The simulation evaluator holds those privileged quantities outside the selector.
LOO validation errors are correlated and also used to choose hyperparameters;
no finite-sample risk guarantee or calibrated uncertainty is asserted.

## Unchanged acceptance gate

At 64 measurements, relative to **each of all six comparators**, require:

- geometric mean NMSE ratio <=0.80;
- strictly lower equation-level geometric mean error on >=60% of functions;
- no aggregate regression within either noise condition.

Each seed/noise/function gets equal log-ratio weight. Floor NMSE at 1e-8 only
inside log ratios. Every declared comparator counts, including the transformed
single-model control. No dropped easy cases, changed error floor, or new
post-hoc endpoint will be used to convert a failed gate into success.

Passing this bounded gate would justify a promising external-benchmark result,
not by itself a field-level breakthrough, new physical law, or state of the art.
Numerical/domain/source failure aborts the study and remains in the record;
no outcome-dependent replacement function is permitted.

## Prior-art screen

- Snelson, Ghahramani, Rasmussen, *Warped Gaussian Processes*, NIPS 2003:
  https://papers.nips.cc/paper_files/paper/2003/hash/6b5754d737784b51ec5075c0dc437bf0-Abstract.html
- Breiman, *Stacked Regressions*, Machine Learning 1996:
  https://doi.org/10.1023/A:1018046112532
- van der Laan, Polley, Hubbard, *Super Learner*, 2007:
  https://doi.org/10.2202/1544-6115.1309
- Sugiyama, Krauledat, Mueller, *Covariate Shift Adaptation by Importance Weighted
  Cross Validation*, 2007: https://www.jmlr.org/papers/v8/sugiyama07a.html
- UQTestFuns upstream cohort and default models:
  https://uqtestfuns.readthedocs.io/en/stable/fundamentals/metamodeling.html
  https://joss.theoj.org/papers/10.21105/joss.05671

No full learned-warp Gaussian-process implementation, symbolic regression solver,
random forest or tuned modern AutoML suite is included. This limits all novelty
and state-of-the-art claims. The included controls test component contributions.

## Reproduction

```bash
python -m pip install numpy scipy uqtestfuns==0.6.0
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python -m unittest tests.test_representation_revision -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python experiments/representation_revision/run.py --out build/representation-confirmation
```

Source hashes, upstream function hashes, versions, exact query indices and values,
chosen representations, kernel/ridge parameters, weights, timing and errors are
preserved. Existing output paths are refused. Tests use unrelated synthetic
functions and compare transformed LOO errors to explicit refits, raw predictions
to the old implementation, exact power-law reconstruction, sign handling, and
stacking optimality conditions. No fresh-cohort outputs are used in tests.
