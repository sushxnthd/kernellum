# Paired noise-regime diagnosis

This is a retrospective discrimination experiment on the opened 39-function
cohort, based on affine-trend evidence frozen at
`283d846852113e5128fdbc05f55981b4e3be74e2`. It neither evaluates a new predictor
nor creates fresh confirmation evidence. No completed outcome is rerun or
replaced. The original general-performance gates remain unchanged.

Question: does the clean/noisy reversal support a broadly useful robustness
mechanism, or does repairing one extreme inverse-transform failure dominate
the reported benefit?

Before computing this diagnosis, fix these analyses:

1. Require exactly 39 functions × five seeds × two noise levels for each
   predictor. Check paired queried indices, input hashes, and observed labels.
2. Recompute every published trend comparison from immutable final scores
   using a separate standard-library implementation and the existing 1e-8 floor.
3. Report clean/noisy ratios separately against all nine controls, both with
   and without GenzCornerPeak. Exclusion is sensitivity analysis only.
4. For each function compute the geometric mean paired noisy/clean change
   in the trend-to-control error ratio. Report medians, function wins, and
   leave-one-function-out ranges. Analyze raw positive errors separately to
   expose floor dependence; do not change the primary metric.
5. Report weight on removed exponential polynomial components in the original
   stack, weight on affine components in the candidate, and clean/noisy loss
   of response-transform availability. These associations are descriptive,
   not causal attribution.
6. Resample whole functions (20,000 samples; seed 20261003) for descriptive
   uncertainty of aggregate log ratios. Functions share source families;
   these intervals do not establish population coverage or independent
   replication. Also report equal-source-family-weighted sensitivity.

Decision: retain a noisy-regime foothold only if it remains directionally
positive against the original and adaptive stacks after deleting the known
catastrophe, with benefit on a majority of functions. This diagnostic rule
is not the original breakthrough gate and cannot promote a predictor.
Otherwise target generalization/model-selection reliability rather than
another noise-specialized predictor patch. Preserve all rows and report
contrary cases. Any later mechanism test needs a separate frozen protocol.
