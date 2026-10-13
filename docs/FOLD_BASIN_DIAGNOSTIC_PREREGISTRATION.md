# Fold-basin diagnostic: development preregistration

Classification: **DISCRIMINATION / CAPABILITY-BUILDING** on already-opened development evidence. This is not confirmation and cannot establish a flagship claim.

## Active kernel

- **Question:** can a label-blind, pre-selection diagnostic computed from deterministic multi-start fold refits identify the rare paths where exact-LOO model selection depends on solver basin?
- **Frontier:** the clean-room replication agrees on 116/120 paths but disagrees on four noisy 4-D signed-Gaussian paths, with catastrophic extrapolation tails in three and a major recovery in one.
- **Objective:** rank all 60 4-D signed-Gaussian paths by fold-basin predictive dispersion.
- **Strongest alternative:** disagreements are caused by implementation details unrelated to measurable basin multiplicity; dimension/noise alone explains them as well.
- **Cheapest falsification:** compute the diagnostic without reading disagreement labels, then join the frozen labels and compare AUROC and top-10 recall against dimension/noise controls.
- **Publishable success condition:** a prospectively frozen shifted-condition study later confirms a quantitative flip boundary and a robust alternative removes catastrophic tails without ordinary-regime regression.
- **Project-relevance threshold for this development run:** AUROC >= 0.90 and all four known disagreements in the top ten scores, with score outperforming noise-only ranking.
- **Kill condition:** AUROC <= 0.60 or at least two disagreements fall outside the top ten. Intermediate results reformulate but do not validate the diagnostic.

## Frozen diagnostic

For each 4-D path, infer response sign from the median observation and fit only the signed concave exponential family. For every leave-one-out fold, use five deterministic starts derived only from the fold training data: moment start; zero-curvature affine start; half-curvature; double-curvature; and a fixed signed slope perturbation. Each start is optimized by the same bounded numerical least-squares procedure.

For held-out predictions \(\hat y_{fr}\), fold scale \(s_y\), and start objectives \(J_{fr}\), define:

1. predictive spread \(D_f=\log_{10}(1+(\max_r\hat y_{fr}-\min_r\hat y_{fr})/s_y)\);
2. objective spread \(O_f=\log_{10}((\max_r J_{fr}+10^{-12})/(\min_r J_{fr}+10^{-12}))\);
3. path score \(D=\max_f D_f\).

The primary score is \(D\). Objective spread is diagnostic only. Failed/nonfinite starts make the path score the fixed sentinel 300 (a finite representation of infinity) and are retained, not dropped. Reaching the evaluation cap with a finite iterate is retained as an observed basin rather than counted as a failure.

## Frozen population and labels

- All 60 paths with function in `{gaussian_4d, negative_gaussian_4d}` from the immutable PR #99 confirmation arrays.
- Labels are the already-recorded candidate-versus-independent winner disagreements in `independent_replication_full/records.json`.
- The score computation must complete before labels are loaded.
- No holdout or external dataset is opened.

## Frozen evaluation

- Exact rank AUROC with average ranks for ties.
- Recall of the four disagreements among the ten highest scores.
- Median score ratio, positives versus negatives.
- Baselines: noise magnitude alone and binary nonzero-noise ranking.
- Preserve all scores, failures, package versions, input hashes, and deterministic result digest.

## Consequence boundary

A development pass only authorizes freezing an unseen shifted-regime protocol. It does not authorize a scientific claim. A failure kills this diagnostic family and redirects effort toward solver-globalization or interval/certificate methods.
