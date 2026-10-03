# Ten-seed mechanism boundary result

Public source/protocol freeze: f6c279f962033721a70aa5e7c44b1cd7b380c748,
created before the run. 280 shared observation paths, seven methods and three
prediction domains produced all 5,880 scores. No model rule was tuned during
this experiment. These are deliberately chosen synthetic mechanism conditions,
not an unselected external benchmark or evidence of a field breakthrough.

The predicted clean inside-domain expressivity survived: add-only achieved
NMSE <=1e-8 on 10/10 seeds each for log-affine, log-quadratic, shifted Gaussian
and power law. This prediction passes. The general accuracy gate fails.

| Control | Add-only geometric error ratio | Function wins / 7 |
|---|---:|---:|
| Original | 0.126751 | 5 |
| Remove-only | 0.106524 | 6 |
| Both changes | 0.235066 | 5 |
| Adaptive stack | 5.323645 | 0 |
| Weighted median | 5.368769 | 0 |
| Nonlinear leverage support | 0.112895 | 5 |

A ratio below one favors add-only. Its improvement against the original is
mainly an extrapolation result; its inside-domain ratios at the four noise
levels are 0.9890, 0.9681, 0.9232 and 0.9891. It does not dominate the robust
controls. At noise 0.1 in the far shell its ratio to adaptive is 24,111.

Tail behavior remains unacceptable. Original worst log10 NMSE is 470.713;
add-only is 156.765; adaptive is 157.221; support is 25.553. Some far-shell truth
variances are extremely small, so enormous NMSE need not imply enormous absolute
predictions. For example the peaked log-quadratic support counterexample has
prediction magnitude 11.82 with log10 NMSE 25.55. The rational-peak add-only
counterexample has an actual prediction magnitude 5.13e77. Both must be reported.
Existing predictors retain their legacy exp(700) numerical ceiling; scoring
itself does not truncate log errors or drop large finite errors.

The sign-switch diagnosis is now especially clear. Shifted Gaussian and peaked
log-quadratic permit log-response models on all ten clean paths but on none of
the noisy paths, even at 0.002 additive noise. The noiseless function is still
positive; the measured noisy labels cross zero. Power law retains this option
on only four of ten paths at 0.1 noise; rational peak on nine. Function identity
and truth were used only to generate data and interpret outcomes.

These results justify a new development hypothesis: fit an exponential mean
directly on the measured response scale under additive noise, retaining all
negative measurements in the objective. This is established nonlinear least
squares, not a new mathematical method. A concave quadratic exponential can
retain Gaussian response geometry without permitting positive quadratic tails.
Its effectiveness, optimizer reliability and generalization need fresh testing.

Verification reconstructs the four factorial arms through separate augmented
linear systems (3,360 scores), verifies all 5,880 paired indices/observations,
and checks six aggregate comparisons. The three robust-control prediction rules
are not independently reconstructed here. Recorded simplex weights are checked
with KKT rather than refitted. This is same-author verification. Near-zero
prediction arithmetic uses the earlier audits' explicit NMSE rtol=2e-5 and
atol=1e-7; the audit reports floor-scaled discrepancies separately. An initial
stricter floor-relative audit assertion failed near machine precision, and the
final check applies the existing published tolerance rather than concealing it.
No external reproduction has occurred.
