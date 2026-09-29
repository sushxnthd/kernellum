# Scientific Discovery: experiment selection under model error

Date: 29 September 2026. Status: protocol written before the comparative run.

## Question and candidate

Can a flexible provisional model choose measurements that improve a simpler,
interpretable model more efficiently than uncertainty-driven acquisition?
This addresses a component of Kernellum's broader Scientific Discovery and
Machine Reasoning programs. It is **not a complete autonomous scientist**.

The candidate, `teacher_risk`, fits a quadratic ridge response surface and three
RBF kernel ridge teachers to observed measurements. For each possible next query,
it computes the exact one-step change in integrated squared error of the response
surface against each teacher, and averages the changes. It selects the greatest
predicted error reduction. Every fourth acquisition uses farthest-point coverage.
`teacher_risk_pure` removes that coverage step as an ablation. Teacher predictions
are provisional estimates: an incorrect teacher can make acquisition worse.

For features Phi, A = Phi_observed.T Phi_observed + lambda I, current coefficients
b, and candidate feature vector p, let v = A^-1 p / (1 + p.T A^-1 p).
For teacher h, residual r = h(x) - p.T b, the hypothetical updated coefficients
are b + v r. The integrated proxy-risk change is

    2 r (Phi b - h).T Phi v / N + r^2 v.T (Phi.T Phi / N) v.

This is the ordinary rank-one ridge update, not a new theorem. A numerical test
checks the expression against separately refitting every hypothetical candidate.
The study tests the utility of this acquisition recipe, not mathematical novelty.

## Cohort and controls

`experiments/discovery_design/spec.json` is authoritative. Include **all 52**
nonempty one-, two-, or three-variable rows from the external Feynman equation
metadata. No equations are removed after inspecting comparative outcomes.
The mirror is pinned to commit `22cd4b3362dea302e82b91db45cc1516c95f184d` of
[prescriptiveanalytics/FeynmanEquations-Python](https://github.com/prescriptiveanalytics/FeynmanEquations-Python).
The original benchmark is from [Udrescu and Tegmark](https://arxiv.org/abs/1905.11481).
The metadata and mirror's MIT notice are preserved in `vendor/`.

We generate **new numerical samples from published formulas and bounds**; we do
not claim to have run the original full SRBench protocol or used physical data.
All inputs use independent uniform sampling within the metadata bounds. This is
not necessarily a realistic physical experimental distribution. Repeated or
algebraically related equations remain in the cohort and are not independent
scientific discoveries. No inferential p-value is asserted from equation counts.

Each equation has three fixed random seeds, two noise levels (0 and 2% of clean
pool standard deviation), a 256-point query pool, and a separate 2,048-point test
set. All methods share initial 12 points and the same indexed noisy responses.
They spend 40 total measurements, including initialization; metrics at 12, 24,
and 40 are computed **after selection ends**. Test labels never select a query.
The primary endpoint is 40-measurement normalized test MSE of the same quadratic
model. This is prediction quality, **not equation recovery or explanation truth**.

Eight arms: uniform random; farthest-point coverage; quadratic leverage
(pointwise variance); integrated quadratic variance reduction; disagreement among
the three RBF teachers; improved greedy sampling (minimum product of squared
input distance and squared predicted-output distance to an observed point);
`teacher_risk`; and its no-coverage ablation. Both committee and risk methods use
identical teachers. All methods refit the same final quadratic model; they do not
receive formulas or latent noiseless outputs. Teacher fitting overhead is counted.

The primary candidate passes only if it achieves all of:

- At least 20% lower geometric mean normalized test MSE than **each** of the six
  baselines, averaging log ratios equally across seeds, noise levels and equations.
- Lower equation-level geometric mean error on at least 60% of the 52 equations
  against each baseline.
- No aggregate regression against any baseline within either noise level.

A floor of 1e-8 is applied only to errors inside log-ratio computations, so nearly
exact quadratic fits do not dominate ratios through floating-point noise. Raw
errors are retained. All outcomes are reported; no tuning follows opened results.
Passing these gates establishes only a promising result in this bounded setup.
It cannot by itself establish field-level novelty or a venture-scale advantage.

## Prior-art screen and claim boundary

The broad idea is already established:

- [Sugiyama (2005), Active Learning for Misspecified Models](https://proceedings.neurips.cc/paper_files/paper/2005/hash/0c1c995b77ea7312f887ddd9f9d35de5-Abstract.html).
- [Cai et al. (2013), Expected Model Change Maximization](https://ieeexplore.ieee.org/document/6729489/).
- [Wu et al. (2018), Active Learning for Regression Using Greedy Sampling](https://arxiv.org/abs/1808.04245), the source of the iGS comparison.
- [Murari et al. (2019), Model Falsification for Experimental Design](https://pmc.ncbi.nlm.nih.gov/articles/PMC6884580/).
- [Bemporad (2022), IDEAL](https://arxiv.org/abs/2204.07177).
- [Tang, Sloman and Kaski (2026), R-IDeA](https://proceedings.mlr.press/v300/tang26d.html), particularly close work on representativeness, informativeness and error amplification.

This small study does not implement full published IDEAL, EMCM, or R-IDeA and
cannot claim superiority over them. A positive result would need those comparisons,
independent reproduction, realistic distributions, more model classes, and a
clear novelty argument. This literature screen already rules out claiming that
falsification, model misspecification, or teacher-guided acquisition itself is new.

## Reproduction

From the repository root, with Python and NumPy installed:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python -m unittest tests.test_discovery_design -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python experiments/discovery_design/run.py --out build/discovery-design
```

The runner refuses existing output directories. It records source SHA-256 hashes,
versions, queried row indices and observations, every checkpoint error, wall time,
and a summary. There are 52 x 3 x 2 x 8 = **2,496 runs** and 99,840 accounted
measurement calls across all arms; this is a simulated label budget, not paid or
physical experiments. No API keys, GPUs, or external hardware are required.
