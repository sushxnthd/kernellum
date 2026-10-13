# Selection-stability matrix: opened-development preregistration

Classification: **DISCRIMINATION** on already-opened evidence. This cannot establish a scientific claim.

## Active kernel

- **Question:** are the four candidate-versus-independent model-selection disagreements prospectively detectable from a factorized stability representation, or should Kernellum abandon predictive routing and globalize selection?
- **Frontier:** the scalar within-family fold-basin score failed (AUROC 0.75; 2/4 positives in the top ten). Inspection identified heterogeneous mechanisms: within-family prediction dispersion, a cross-family/sign near-tie, and a full-fit miss with low same-sign dispersion.
- **Objective:** rank all 60 opened 4-D signed-Gaussian paths with one frozen, label-blind score.
- **Strongest alternative:** the four disagreements are idiosyncratic optimizer events that no cheap pre-selection diagnostic can separate without unacceptable false positives.
- **Cheapest decisive falsification:** freeze four label-blind components and an equal-weight aggregation, materialize and hash the unlabeled matrix, then join the existing labels exactly once.
- **Project-relevance threshold:** AUROC >= 0.90, all four positives in the top ten, and false-positive rate <= 0.25 at the threshold covering all positives.
- **Publishable success condition:** a later untouched shifted-regime protocol confirms a quantitative flip boundary and routed globalization removes catastrophic tails without ordinary-regime regression.
- **Kill condition:** failure of any project-relevance gate kills cheap predictive routing for this kernel. Kernellum then uses globalized/certified selection rather than another post-hoc scalar.

## Frozen matrix

For every path, compute without labels:

1. existing within-family maximum held-out predictive dispersion;
2. existing within-family maximum restart-objective dispersion;
3. signed-pair asymmetry: absolute difference of `log10(1 + dispersion)` between the positive and negative response built from the same seed/noise;
4. cross-model margin risk: `min(-log10(g + 1e-12), 12)`, where `g=(CV2-CV1)/(|CV1|+|CV2|+1e-12)` for the two best candidate family/sign models.

Convert each component to its average-rank percentile over all 60 paths. The primary score is the equal-weight L4 norm of the four percentiles. No coefficients, thresholds, or components may change after labels are loaded. Report leave-one-component-out AUROC and top-ten recall as mechanism diagnostics, not tuning opportunities.

## Consequence boundary

A pass only authorizes freezing a new external/shifted-condition study. A fail is a decisive system result: remove diagnostic routing from the Kernellum roadmap and globalize/certify model selection. All opened paths remain permanently ineligible as confirmation.
