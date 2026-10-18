# Fold-basin dispersion diagnostic: decisive development failure

Status: **FAIL**. The preregistered diagnostic does not reliably identify solver-dependent exact-LOO selection and performs worse than noise magnitude alone.

## Decisive table

| Frozen criterion | Required | Observed | Gate |
|---|---:|---:|---|
| AUROC over all 60 four-dimensional paths | >= 0.90 | **0.7500** | FAIL |
| Known failures recovered in top 10 | 4/4 | **2/4** | FAIL |
| Beat noise-magnitude ranking | > 0.7679 | **0.7500** | FAIL |
| Sequential replay of top 10 plus all positives | exact | **12/12 exact** | PASS |

Positive paths had 2.78x higher median score than negatives, so fold dispersion carries some signal. It is not discriminating enough for prospective routing.

## What was tested

The label-blind score measured the maximum leave-one-out held-point prediction spread across five deterministic starts of the signed concave-exponential model. All 60 scores were written and hashed before the four already-known candidate-versus-independent disagreements were joined. The experiment used only opened development evidence; no holdout was touched.

The highest-ranked failure was Gaussian seed 104206/noise 0.1, and Gaussian seed 104203/noise 0.01 ranked ninth. The other two failures ranked outside the top ten:

| Missed path | Frozen score | Mechanism clue |
|---|---:|---|
| Gaussian 104209, noise 0.1 | 1.4928 | Independent selection flips from affine-positive to concave-negative; a correct-sign concave-only score cannot represent the failure. |
| Negative Gaussian 104207, noise 0.1 | 1.2481 | Candidate missed a strong concave-negative fit despite low within-sign fold spread; maximum fold dispersion is not the relevant failure signal. |

This falsifies the working explanation that all four disagreements are instances of one measurable within-model fold-basin mechanism. At least two phenomena are present: within-model fold dispersion and cross-family/sign selection instability. The latter may also include full-fit initialization failure.

## Two ledgers

### SCIENCE

- **KNOWN:** the score is deterministic; 12 sequential recomputations, covering the top ten and every positive, matched exactly.
- **FALSIFIED:** one correct-sign concave fold-dispersion statistic predicts the known solver-dependent selection failures strongly enough for routing.
- **CONFLICTING:** positive median dispersion is 2.78x higher, but AUROC is only 0.75 and lower than noise magnitude's 0.7679.
- **ANOMALOUS:** the two missed failures correspond to different selection transitions, indicating the original failure class was heterogeneous.
- **UNTESTED:** a model-bank stability object combining within-model basin occupancy, sign/family margin, and full-fit restart occupancy predicts solver dependence prospectively.

### CONSEQUENCE

- Do not add this scalar diagnostic to Kernellum's model-selection pipeline.
- Do not route expensive multi-start optimization based on maximum correct-sign fold spread alone.
- Reformulate the active kernel around a **selection stability matrix**, not a scalar: restart × fold × family × sign, with separate within-model dispersion and cross-model margin components.
- The cheapest next decisive experiment is an opened-data ablation asking whether either component is necessary; only then freeze a shifted-condition evaluation. If a two-component diagnostic cannot recover all four failures without excessive false positives, kill prospective prediction and move directly to solver-globalized/certified selection.

## Reproduction and provenance

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python scripts/run_fold_basin_parallel.py \
  --workers 6 \
  --unlabeled /tmp/fold-basin-unlabeled.json \
  --output /tmp/fold-basin-result.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python scripts/audit_fold_basin_diagnostic.py \
  /tmp/fold-basin-result.json \
  --output /tmp/fold-basin-audit.json
```

- Result canonical SHA-256: `650dc90f12670e2f124a63bf78c14df050816b6896cb54c10e5c80c22e6a6a40`
- Label-free scores SHA-256: `3b5b284c8f6a41806057466b17454ad2514ac7571f7b997e400d57e9a8c7bdd7`
- Audit canonical SHA-256: `fd2f6e41c35cccf15ddcf07768206573b2a53f7c792f90acb4ff231dba47a0a0`
- Frozen runner correction commit: `822aced46f9a0580e140d1ce42926b58b31b953d`
- Candidate source evidence: `949d69b1de5284a106d6ce99ab6bc95f71bb2ab6`

## Claim boundary

This is a high-value negative result on opened synthetic signed-Gaussian evidence. It does not establish a general taxonomy of nonlinear solver instability, a new diagnostic, or a robust alternative. No prior-art novelty claim is made. The Kernellum breakthrough gate remains **INCONCLUSIVE**.
