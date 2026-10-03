# Additive-response capability: supported mechanism, limited transfer

A response-scale exponential model recovers a useful capability lost by the
current observed-sign gate. On fresh noisy positive/negative Gaussian cases,
augmented adaptive has 97.23% lower inside-domain geometric NMSE than original
adaptive. The frozen scoped mechanism gate passes. The general synthetic gate
and the targeted external NIST transfer gate fail. This is a useful research
foothold, not a verified scientific breakthrough or novel nonlinear regression.

## Decisive comparison

Ratios below one favor augmented adaptive. The comparison floor is unchanged
at 1e-8. The intervals are post-outcome descriptive seed-block bootstrap
percentile intervals, not new acceptance rules.

| Condition versus original adaptive | Geometric NMSE ratio | 95% seed-block interval | Relevant frozen decision |
|---|---:|---:|---|
| Noisy Gaussian, inside measured domain | 0.027675 | [0.015696, 0.053037] | Part of scoped PASS |
| Noisy Gaussian, all three domains | 0.0001775 | [0.00007344, 0.0004654] | Scoped mechanism PASS |
| All selected synthetic cases | 0.190634 | [0.162788, 0.221790] | General gate FAIL |
| Six external NIST datasets | 0.961834 | [0.871574, 1.044435] | Transfer gate FAIL |

The scoped claim additionally requires inside-domain wins and clean exactness:
70/80 noisy seed/sign/dimension trials won (87.5%), and all 40 clean Gaussian
inside trials retained NMSE <=1e-8. Its predeclared thresholds were 80% and 90%.
Do not describe eighty paired trials as eighty independent physical systems.
All-domain Gaussian ratios are especially affected by baseline extrapolation
errors and tiny far-domain truth variances; the inside-domain effect is reported
separately to make that limitation visible.

## What changed and why

The boundary experiment showed that additive noise disables log-response
families as soon as measurements of both signs are present. For peaked Gaussian
responses, even tiny absolute noise changes the available hypothesis class.
The newly appended means fit signed exponential affine and concave-quadratic
functions directly to measured responses, retaining negative measurements in a
positive-mean additive-error objective. Explicit leave-one-out refits score them
on the original response scale. Selection and adaptive aggregation are reused.

Concave quadratic exponential means cover Gaussian shapes without positive
quadratic tails. This restriction is specific to the appended model; the whole
ensemble still contains other models and is not certified stable outside the
measured region. The hypothesis predicts recovery of this lost model class,
not universal accuracy or a new physical law. Direct nonlinear exponential
least squares is established NIST-documented regression methodology.

Two public freezes precede comparative outcomes:

- Synthetic predictor/protocol: f606378c8c474d40b803330af322491956b313c9.
- NIST transfer/certified-fit protocol: c9b01ccaf7208daafc6dc964269a8b5c96e77ce0;
  the predictor is unchanged from the first freeze.

The synthetic run contains nine functional forms, two dimensions (2 and 4),
ten new seeds and three noise levels: 540 shared observation paths, eight methods
and three domains, all 12,960 scores retained. Positive/negative cases are paired;
random function parameters and exact input/response arrays are saved. Mixture,
oscillatory, rational and convex-exponential cases challenge the Gaussian model.
These forms were selected after the mechanism diagnosis and are not an
unselected external benchmark.

## Why broad promotion remains unsupported

Against original adaptive the overall synthetic ratio is 0.190634 with 12/18
family/dimension wins and no noise/domain aggregate regression. Nevertheless,
the general gate requires every strong control. Against augmented winner the
ratio is 1.292861 (29.3% higher error), with only 9/18 wins. Against exponential-
only regression it wins only 8/18 groups. Original-stack clean inside ratio
1.014877 and weighted-median clean far-shell ratio 1.318415 also violate the
unchanged no-regression requirement. Gate FAIL must not be rescued by choosing
only the favorable baselines.

On NIST, the gain over adaptive is 3.82% overall, concentrated in Eckerle4
(17.48% lower error) and Lanczos3 (4.05% lower). Gauss1, Gauss2, Hahn1 and Bennett5
have unchanged predictions against adaptive. The predeclared transfer rule
required <=.8 ratio and at least 4/6 dataset wins; neither was met. The split-
variation bootstrap includes one. Repeated splits overlap and these intervals
do not establish transfer to a population of physical systems.

A separate full-data Eckerle4 numerical check reproduces NIST's certified RSS
0.0014635887487 with relative error 1.879e-11. The maximum parameter relative
error is 4.984e-9. This checks a known numerical solution using observed
transmittance data; it is isolated from all prediction splits and is not
held-out evidence, a novel law or an external replication.

Optimizer failures remain material: 302 nonlinear families failed on 223/540
synthetic paths. Failed families are excluded from selection, but their paths
and failure reasons remain present and the original bank remains available.
A reported solver success does not prove a global optimum. Inference preserves
the legacy exp(700) ceiling; optimization's exp(40) step ceiling does not cap
reported test predictions at exp(40). No nonfinite prediction scores occurred.
The primary still has worst log10 NMSE 39.215, equal to the adaptive control's
worst case. Better geometric error does not eliminate catastrophic tails.

## Verification and reproducibility

Twenty focused tests passed, including analytic derivatives against finite
differences in dimensions 1, 2 and 4, clean fits, and exact fold-only prediction
agreement with negative measured responses. Separate closed-form evaluation of
saved parameters verifies all 720 pool/test truth and domain arrays.

The audit checks all 13,440 pairings and 14 aggregate comparisons, reconstructs
11,760 prediction scores through augmented kernel systems and separate
exponential/ensemble arithmetic, and verifies stored simplex weights by KKT.
Support routing predictions are not separately reconstructed. Nonlinear LOO
coefficient optimization reuses the candidate fit_exp primitive; thus this is
partial same-author algorithm verification, not a clean independent nonlinear
implementation or external reproduction.

A different optimizer (L-BFGS-B) checks 687 selected full nonlinear fits, starting
at recorded parameters. Five reported unsuccessful termination; the largest
observed relative objective improvement was 7.324e-9. This tests local
stationarity and is not a global-optimality certificate. Independent arithmetic
uses the preceding audits' explicit NMSE rtol=2e-5, atol=1e-7. Maximum floor-scaled
score discrepancy is 0.000240 on synthetic data and 0.00000331 on NIST. The
second calculation also retains all 40 clean exact Gaussian trials.

Reproduction uses Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, single BLAS/OMP
threads (exact environment versions are in manifests). Use a fresh output path
so the saved evidence remains intact:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/additive_response/run.py --out /tmp/kernellum-additive-replay --public-freeze f606378c8c474d40b803330af322491956b313c9
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/additive_response/nist.py --out /tmp/kernellum-nist-replay --public-freeze c9b01ccaf7208daafc6dc964269a8b5c96e77ce0
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/audit_additive_response.py
python scripts/check_additive_data.py
python scripts/summarize_additive_uncertainty.py
```

The last three commands verify/analyze the saved canonical results. To audit
fresh outputs, import audit from scripts/audit_additive_response.py and call
it with the new folder and kind 'synthetic' or 'nist'. NIST source CSVs are
exact numeric extraction from official pages; their provenance manifest records
that source text is a web extraction, not original downloaded .dat bytes.

## Claim state and next decisive action

KNOWN: the old sign-gated log model class disappears under noisy Gaussian
measurements; direct measured-scale exponential means recover the predicted
capability on untouched conditions. FALSIFIED: general superiority of augmented
adaptive under the unchanged synthetic gate; strong transfer under the NIST
gate. UNTESTED: a clean independent nonlinear implementation, broad physical
transfer, and any defensible novelty beyond established regression/stacking.

Keep this foothold active. The next decisive action is a clean implementation
from the written specification using an independent optimizer and fold setup,
followed by a newly frozen external test that separates noise likelihood from
model-family matching. Preserve the frozen positive mechanism claim and all
negative gates. Do not tune on these opened outcomes or replace the baseline to
manufacture a field-level result.
