# Affine trend and bounded correction development protocol

Frozen before this candidate is scored, 3 October 2026. This is an exploratory
screen on the already opened 39-function cohort, not a new confirmation cohort.

Hypothesis: excluding quadratic/cubic log-response kernels and adding universal
affine-trend RBF models can preserve power-law extrapolation while removing
exponentiated polynomial tails. Universal kriging and its fast cross-validation
formula are established methods, not claimed inventions:
https://libkriging.readthedocs.io/en/latest/math/predictSimulate.html and
https://arxiv.org/abs/2101.03108. Transformed-input universal kriging also has
prior art: https://arxiv.org/abs/2307.06906.

The candidate retains the old identity-response models, log-response linear
and constant-mean RBF models, and adds affine-mean RBFs at the existing three
length scales and three ridges. Original-scale PRESS chooses the winner or six
groups with convex-simplex stacking. Rank-deficient affine trends are ineligible
by an observation-only rule; existing models remain available. Neither weights
nor eligibility use test targets. Primary is `trend_stack`; `trend` is secondary.
No method is tuned after scores are opened.

For an RBF affine-trend component, the latent prediction is
`center + scale * (beta_0 + beta^T z + sum alpha_i k(z,z_i))`.
Because `0 <= k <= 1`, the correction has absolute value at most
`scale * sum abs(alpha_i)` for every valid input. With all inputs logged, the
inverse-log response is a power-law trend times a bounded positive factor.
This is a deterministic model-growth bound, not an error bound, calibration
claim, guarantee against large coefficients, or proof of new scientific novelty.
Some partially logged models have exponential growth in the remaining physical
coordinates; identity-response polynomial models still have polynomial growth.

Use all existing 39 functions, five existing seeds and both noise levels,
192-point pool, 64 observed labels and the existing 2,048 test inputs. Restore
archived nonuniform columns so the inputs and labels match published controls.
Compare against representation winner and stack, raw winner and stack, weighted
median, adaptive stack, nonlinear-support stack, nested winner, and noise-
consistent winner. No omitted or excluded function is allowed.

The existing internal threshold is at least 20% geometric-mean error reduction,
at least 60% function wins, and no regression at either noise level against
every control. Report arithmetic means, worst case, and sensitivity removing
one function as well. A passed development threshold only permits designing
fresh confirmation; it does not establish field novelty or general superiority.

Record full source/control hashes, label IDs/values, selected models, risk scores,
weights, input arrays and truth for reproducibility. A separate arithmetic
implementation uses augmented universal-kriging systems and explicit pairwise
distances, verifies PRESS risks, weights, predictions, budgets and summary
comparisons. This is same-author verification, not external reproduction.
CI has read-only repository permissions and uploads artifacts; it never pushes.
