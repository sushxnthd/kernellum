# Model revision before measurement selection

30 September 2026. This protocol and implementation are frozen in git before any
comparative outcomes on the new cohort are generated. Parent evidence is
`d607358` / PR #89. The older experiment failed; it is not reclassified here.

## Hypotheses and decision rules

The previous quadratic-only predictor was the main diagnosed limitation. This
study tests two **separate** claims, in a fixed order:

1. **Acquisition:** a committee covariance that includes model disagreement,
   combined with integrated variance reduction (IVR), reduces prediction error
   at equal measurement budget relative to every included baseline.
2. **Model revision:** cross-validated choice among polynomial and RBF models
   improves the existing system even with the same maximin query sequence.
   This secondary comparison is an engineering advance, not evidence for a new
   acquisition algorithm or a field-level discovery.

For either claim, every listed comparator must have candidate/comparator geometric
mean NMSE ratio <=0.80, at least 60% equation-level wins, and ratio <=1 in each
noise condition. These are descriptive acceptance gates, not significance tests.
No parameter changes or outcome-dependent exclusions follow the comparative run.
All outcomes and failures will be retained. A failed acquisition gate means the
candidate cannot be called a breakthrough even if model revision improves greatly.

## Fresh cohort and access boundary

All 48 nonempty rows with 4–9 variables from the pinned Feynman metadata are used.
The earlier 52-equation study used only 1–3 variables. Equation rows are unused
by that earlier experiment, but published, visible to the experiment designer,
and sometimes algebraically related to older equations. This is **not a secret
benchmark** or proof of broad distributional generalization.

The machine receives only normalized input coordinates and labels it queries.
It receives no formula, equation name, dimension labels, test data, or clean
unqueried responses. Reuse the earlier restricted formula interpreter and
uniform sampling protocol. These are simulated observations of existing equations,
not new physical experiments or equation recovery. Both old and new metadata use
published bounds, which are not necessarily realistic experimental distributions.

Spec: 192 pool points, 2,048 separate test points, 16 identical random initial
measurements, 64 total observations, three fresh seeds (93001–93003), clean and
2%-of-pool-SD Gaussian noise. All arms share indexed responses. Outcomes at
16, 32, 64 measurements are computed only after a trajectory is complete.
Invalid formula domains abort the study; they are not silently removed.
Total: 48 × 3 × 2 × 9 = 2,592 trajectories and 165,888 simulated label calls.

## Model library and candidate

Six kernel families: degree-1, -2, -3 polynomial kernels and RBF lengths
sqrt(d) × {0.4, 0.8, 1.6}. Each kernel is scaled to unit mean pool diagonal.
Three ridge values {1e-6, 1e-3, 1e-1} are compared by exact leave-one-out (LOO)
squared error on **observed** labels. Every model has an unpenalized intercept.
Labels are standardized using observed labels only; analytic LOO accounts for
refitting the intercept. Final predictions use the minimum-LOO model.
This library and its hyperparameter range are fixed before cohort outcomes.

Let C=K+lambda I, u=C^-1 1, P=C^-1-u u^T/(1^T u).
The LOO residual vector is (P y)/diag(P). These are standard kernel ridge and
universal-kriging identities, not novel mathematical results.

For acquisition, take the best ridge from each family and the three families with
lowest LOO errors e_j. Weights are proportional to max(e_j,1e-8)^-2. If m_j and
S_j are the fitted means and posterior covariances, construct

    m = sum_j w_j m_j
    S = sum_j w_j [S_j + (m_j-m)(m_j-m)^T].

Select point i maximizing mean_z S[z,i]^2 / (S[i,i]+sum_j w_j lambda_j).
Refit models every four measured responses; between refits update covariance with
a rank-one Gaussian conditioning step. The mixture and frozen-weight conditioning
are **heuristics**: weights are not posterior model probabilities and this is not
exact Bayesian experimental design. We do not claim calibrated uncertainty.

## Controls

All flexible arms use exactly the same LOO-selected final predictor:

- `mixture_ivr`: primary method above.
- `winner_ivr`: IVR using only the best-LOO model, removing mixture disagreement.
- `maximin`: farthest-point coverage.
- `random`: uniform random unused point.
- `variance`: maximum mixture marginal variance, with the same batch conditioning.
- `ideal`: IDEAL acquisition equations 9b, 11, 12, 14, delta=1 and no density term;
  standardized labels, common random initialization, predictor refreshed every 4
  labels. This is the published rule under shared initialization/model settings,
  **not the original complete benchmark configuration**. New labels enter IDW at
  every step even between model refreshes.
- `committee`: weighted disagreement among the same three models. Model refresh
  every four labels; no covariance-conditioning correction to disagreement.
- `quadratic_maximin`: the original fixed quadratic ridge predictor, same coverage
  trace as `maximin`, to isolate the effect of revising model class.
- `rbf_maximin`: LOO selection restricted to the three RBF kernels and all ridge
  values, same coverage trace, to test against an ordinary flexible predictor.

Error floor 1e-8 only inside log ratios. Equal weight per seed/noise/equation.
Raw NMSE, all query indices/values, model choices, source hashes, and runtime are
saved. Runtime includes post-trajectory checkpoint evaluation; no claims of
real laboratory time or cost savings follow from simulated budgets.

## Prior art and limits on novelty

- Bemporad, *Active Learning for Regression by Inverse Distance Weighting*,
  https://arxiv.org/abs/2204.07177 (2022 preprint; Information Sciences 2023).
  IDEAL is included as the precisely specified acquisition-rule control above.
- Tang, Sloman, Kaski, *Representative, Informative, and De-Amplifying*, AISTATS
  2026, https://proceedings.mlr.press/v300/tang26d.html. It directly addresses
  misspecification and error amplification. R-IDeA is **not** implemented here.
- Cohn, Ghahramani, Jordan, *Active Learning with Statistical Models* (1996),
  https://arxiv.org/abs/cs/9603104, is prior work on variance-reduction acquisition.
- The Feynman equations originate from Udrescu and Tegmark,
  https://arxiv.org/abs/1905.11481; pinned mirror provenance and license remain
  in the parent `DISCOVERY_DESIGN_PROTOCOL.md` and vendor directory.

Model selection, model mixtures and IVR are established ideas. This experiment
can test this implementation's usefulness, not establish priority for those ideas.
No state-of-the-art claim without R-IDeA/EMCM and broader modern baselines; no
external reproduction, physical validation, symbolic recovery, or investor claim.

## Reproduction

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python -m unittest tests.test_model_revision -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. python experiments/model_revision/run.py --out build/model-revision
```

The runner refuses existing output paths. Source hashes and exact git commit are
recorded before execution. Tests use unrelated synthetic functions and check
LOO against explicit refits, covariance against augmented-system solves, IVR
against explicit trace reduction, IDEAL against scalar equations, and budget and
common-start boundaries. No new-cohort outcomes are used for development.
