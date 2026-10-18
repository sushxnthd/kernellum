# Separate the two affine-trend interventions

3 October 2026. Retrospective mechanism discrimination on the already-opened
39-function cohort. No new holdout, performance claim, or label acquisition.
Freeze this protocol and runner locally before reading ablation outcomes.

The earlier candidate simultaneously removed quadratic/cubic kernels under
exponentiation and added an affine mean to RBF kernels. Its outcome cannot
attribute improvement or regression to either change alone.

Fit four arms on identical archived 64-label paths: original; remove
exponential polynomial components only; add affine RBF components only;
both (the existing trend stack). Keep all other model fitting, six-group
selection, ridge candidates, original-unit PRESS scores, and simplex weights
unchanged. Predictors receive observed labels and the pool only. Test inputs
enter prediction, and test targets enter scoring only.

Competing explanations and predictions:

- Lost expressivity: removing exponential polynomial components causes
  clean regressions on McLainS2/S3/S4 and Franke4/5; adding affine components
  alone retains their original clean accuracy.
- Affine-model selection instability: adding affine components alone causes
  those regressions even with the original models retained.
- Genuine general affine benefit: adding affine alone improves against both
  original and adaptive stacks across the cohort, not just GenzCornerPeak.

Report all 390 paths × four arms, geometric ratios using the unchanged 1e-8
floor, both noise strata, function wins, all nine prior controls, and deletion
sensitivity for GenzCornerPeak. Preserve raw scores and selected model metadata.
Require original and both arms to match their archived scores within the
existing numerical tolerances. Independently recompute summary arithmetic
from traces using standard-library log reductions. No default promotion.

The named-function predictions follow from opened evidence and are explanatory
ablations, not unseen predictions. Even a positive result must later survive
fresh mechanism-derived predictions and a frozen external confirmation.
