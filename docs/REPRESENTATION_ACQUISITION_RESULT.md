# Representation-aware acquisition and noise-consistent fitting

**30 September 2026. Development evidence only. No verified breakthrough.**
The earlier representation confirmation failed its gate and exposed catastrophic
inverse-transform extrapolation. This follow-up completed two acquisition screens
and a separate noise-model screen on the **already-opened** UQ cohort. No fresh
holdout was used or represented as untouched evidence.

## Measurement selection: 13 methods, identical final predictor

All methods receive the same 192 candidate inputs and common 16-label start,
query exactly 64 distinct labels, and use the same transformed single-model
selector for final prediction. Thus predictor choice cannot explain differences
between acquisition arms. The test has all 39 prior functions, the first two
previous seeds (930101/930102), both prior noise conditions, and the prior
2,048-point test sets. Scores are final-budget geometric mean NMSE ratios with
the existing 1e-8 floor inside log ratios.

The first screen contained seven methods and **1,092 trajectories**. The second
added six methods and **936 trajectories**, reusing the first screen's controls
without counting them twice. All **2,028** outcomes and queried values/indices are
retained. These are computational simulations; each arm is charged 64 labels.

The best aggregate development candidate was `hybrid_ivr`: three output-unit
variance-reduction acquisitions followed by one maximin coverage acquisition,
repeated after the common initial design. Model selection is refreshed every four
queries. For a logarithmic response, output-unit acquisition uses the local
inverse-transform Jacobian. Between refreshes, the covariance is conditioned on
newly selected locations. This is a first-order acquisition heuristic, not an
exact transformed posterior or calibrated physical-noise model.

| Comparator | Hybrid IVR/control error ratio | Function wins | Clean ratio | Noisy ratio |
|---|---:|---:|---:|---:|
| Maximin coverage | 0.794768 | 32/39 | 0.821642 | 0.768773 |
| Random sampling | 0.542485 | 32/39 | 0.533816 | 0.551295 |
| Pure output-unit IVR | 0.813712 | 22/39 | 0.969489 | 0.682965 |
| Pure latent-unit IVR | 0.898644 | 25/39 | 0.922645 | 0.875267 |
| Original-space IVR | 0.938230 | 24/39 | 0.956972 | 0.919855 |
| Maximum output-unit variance | 0.958667 | 20/39 | 0.994288 | 0.924322 |

A **20.52% geometric-mean reduction against maximin**, with 32/39 function wins
and improvement in both noise strata, is a useful engineering lead. It is not a
confirmed generalization result. The improvement is only 4.13% versus the
variance control and 6.18% versus original-space IVR. It does not meet the broad
20%-against-every-control target.

The second screen tested matching hybrid latent/original-space controls, IDEAL
and hybrid IDEAL, and two residual-weighted variance-reduction heuristics. The
critical result is that the output-unit hybrid beats **hybrid latent IVR by only
1.004%** (ratio 0.989956; 10 wins, 11 losses, 18 ties). Thus the experiment does
not establish a substantial benefit from output-unit weighting. The coverage
schedule accounts for most of the apparent lead over maximin. None of the added
methods outperformed the original hybrid in overall geometric mean error, and no
method met the full broad target against all others.

IDEAL here uses the existing implementation of its published inverse-distance
criterion with the common revised predictor. These adaptations are not claims to
reproduce a complete published GP package or its tuned hyperparameters. The full
pairwise table is in `results/representation_acquisition/second_screen/summary.json`.

## Noise-consistent logarithmic regression

Additive noise in original output units becomes approximately heteroscedastic
under a logarithm. The candidate augments the representation library with diagonal
ridge weights proportional to `1 / abs(observed_y)^2`, with numerical caps. Three
permanently observed anchor responses define the common reference scale. They are
excluded from the validation score, so each remaining leave-one-out fit keeps
its weighting reference independent of the held-out response. Original-space and
uniform-weight models remain available.

The **matched anchor control** uses the same three-anchor validation subset but
omits the heteroscedastic models. This isolates the new weighting rule from a
change in validation rows. Unit tests compare analytic weighted LOO predictions
to complete explicit refits; output-unit rescaling and mixed-sign behavior are
also checked. The delta approximation and response-dependent training weights
can still introduce bias; this is not exact likelihood inference.

The screen completed **780 fits**: two methods on all 39 functions, all five
previous seeds, and both noise levels, using the same prior maximin measurements.

| Comparator | Noise-consistent/control error ratio | Function wins | Clean ratio | Noisy ratio |
|---|---:|---:|---:|---:|
| Matched anchor control | 0.968314 | 9/39 | 1.027504 | 0.912533 |
| Original transformed selector | 0.971076 | 12/39 | 1.024932 | 0.920051 |
| Transformed stacking | 0.895844 | 19/39 | 1.094808 | 0.733038 |

The weighting rule improves noisy results but regresses on clean data. Its
aggregate gain is about 3%, not 20%; neither win coverage nor the no-regression
condition is met. It is retained as a rejected research candidate, not promoted.

## Audit and evidence boundaries

All code, raw traces and summaries are retained under
`experiments/representation_acquisition`, `results/representation_acquisition`,
`experiments/noise_revision`, and `results/noise_revision`.

**Completed validation:** 149 tests and 24 subtests passed. The second arithmetic
implementation reproduced all 2,028 acquisition outcomes within the declared
2e-5 relative / 1e-7 absolute tolerance; its maximum scaled discrepancy was
6.014e-6. The completed machine-readable audit is in
`results/representation_acquisition/audit.json`.

The acquisition outcome auditor uses the separate augmented-system kernel
implementation from the preceding study; it imports neither the candidate
predictor nor the acquisition policy. It verifies every arm's labels, budget,
initial design, selected final model, final NMSE, and all pairwise aggregate error
ratios. It does **not** independently reimplement every adaptive acquisition score.
The full query sequences are retained for policy replay. This remains same-author
verification, not external independent reproduction. The noise screen has exact
refit unit tests but no separate full-cohort arithmetic audit.

The preceding external representation audit also passes on GitHub after a
sampling portability repair. Forty nonuniform sample arrays differed at the byte
level across platforms, with a largest column-relative difference of
9.1552e-16. The auditor checks their numerical agreement and then replays exact
original columns, still requiring all original full-input hashes. This preserved
the failed gate; it did not change scientific outcomes. The successful run is
[36737774486](https://github.com/sushxnthd/kernellum/actions/runs/36737774486).

```bash
python -m pip install numpy==2.3.5 scipy==1.17.0 uqtestfuns==0.6.0 pytest
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python -m pytest -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/audit_representation_acquisition.py
```

Development output directories are deliberately not overwritten. To rerun a
screen, change its output directory to a new path. The first development runner
is pinned to its original seven methods; the second adds only its six methods.

## Prior art and decision

Variance reduction, exploration/coverage hybrids, warped Gaussian processes and
heteroscedastic regression are established research directions. In particular:

- Kontoudis and Otte, *Adaptive Exploration-Exploitation Active Learning of Gaussian
  Processes*, IROS 2023, explicitly combine exploration with variance reduction:
  https://ottelab.com/html_stuff/pdf_files/Kontoudis.Otte.IROS23.pdf
- Jarl et al., *Correcting Boundary Bias and Observation Independence in Bayesian
  Experimental Design*, arXiv:2602.01898v2, revised 16 September 2026, separates
  acquisition from prediction and studies geometric and reconstruction-based
  corrections: https://arxiv.org/abs/2602.01898v2
- Ozbayram et al., *Active learning with heteroscedastic Gaussian Process Regression
  model*, 2026, studies noise-aware acquisitions:
  https://doi.org/10.1016/j.probengmech.2026.103975

These complete modern methods were not benchmarked here. There is no basis for a
field-wide novelty or state-of-the-art claim. The 20.52% number must not be
presented without its development-only status and stronger-control comparisons.

**Decision:** retain the hybrid as an engineering lead and reject the present
output-weighting and noise-weighting mechanisms as breakthrough candidates. A
new hypothesis needs a material gain over the matching hybrid control, stability
against inverse-transform extrapolation, and fresh frozen evidence. The unopened
28 additional UQ functions and PMLB datasets remain unused; their metadata alone
was inspected. Repeating small variations on the opened cohort would not make
this evidence independent.
