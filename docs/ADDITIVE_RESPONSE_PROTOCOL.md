# Additive response means: prospective mechanism confirmation

Freeze the predictor, generator and protocol publicly before producing any
comparative confirmation score. The preceding single-seed opened development
results suggested that negative additive-noise measurements wrongly erase an
otherwise appropriate exponential mean from the existing bank. They are not
confirmation evidence. No existing default predictor is modified.

The candidate appends four established nonlinear least-squares model families
per available input representation: signed exponential affine means and signed
exponential concave-quadratic means. The latter is
s A exp(a + b^T z - ||L^T z||²), where s is independently +1 or -1 and L is
lower triangular with nonnegative diagonal. This covers Gaussian shapes and
prevents positive quadratic curvature in that model. It does not certify the
whole ensemble against extrapolation or optimizer failure.

Fit squared residuals directly on every measured response, including negative
measurements of positive means. No log transform is applied to the response
objective. Logs of floored positive targets are used only for initialization.
All model scores use explicit leave-one-out refits: each fold reinitializes and
rescales from its own training data. Held-out labels never initialize the fold.
The full fit and each fold must report optimizer success; failed families are
recorded and unavailable to selection. This is numerical convergence, not proof
of a global optimum. No observation is discarded.

Optimization is deterministic scipy least_squares with analytic derivatives,
max_nfev=300 and ftol=xtol=gtol=1e-10. Positive curvature from the initializing
quadratic is projected away. A training-step exp(40) ceiling prevents overflow;
a fitted model reaching it is rejected. Prediction uses the existing bank's
exp(700) numerical ceiling, not the training ceiling. Thus the training ceiling
cannot artificially bound a model's reported far-domain prediction at exp(40).
The predictor itself receives no noise level, truth, function identity or
family parameters. It uses only the common unlabeled input pool and 64 labels.

Selection and adaptive aggregation reuse the existing representation and
AdaptiveStack rules unchanged. Test augmented winner and augmented adaptive;
the latter is the frozen primary. Controls are original stack, add-only stack,
original adaptive, original weighted median, nonlinear-leverage support, and
exponential-only winner (raw winner fallback if all exponential fits fail).
This last control directly tests whether the integration adds value beyond
ordinary nonlinear exponential regression. The augmented winner is also a
control for the primary. Exact LOO model scores do not imply unbiased selected
ensemble error; confirmation responses remain separate from fitting.

Data: nine response families × dimensions 2 and 4 × ten predetermined seeds
104201..104210 × three additive-noise fractions (0, .01, .1) = 540 shared
observation paths. Families: Gaussian, negative Gaussian, exponential affine,
power law, convex exponential, rational peak, sine, signed cubic, and Gaussian
mixture. Parameters (centers, rotated positive curvature, slopes, amplitudes)
are drawn deterministically and saved. Gaussian-mixture, sine, rational and
convex-exponential cases deliberately violate the new concave single-peak
model assumption. Positive and negative Gaussian cases share input conditions;
these are paired sign tests, not independent function identities. There are
nine functional forms rather than eighteen unrelated physical systems.

For each path draw 256 unlabeled pool points uniform in latent [-1,1]^d; apply
exp to input coordinates only for the power-law case. Select 64 common labels
with the existing coverage procedure. Additive Gaussian perturbations scale
with the clean pool standard deviation and are shared across methods. Test
512 inside points, 256 near-shell points and 256 far-shell points as in the
previous boundary protocol, generalized to d dimensions. Preserve exact arrays
and function parameters. All 12,960 scores must be retained; nonfinite
predictions disqualify a comparison, and failed fits do not erase a path.

Two separate frozen claims:

1. **Scoped mechanism:** on the positive/negative Gaussian cases at nonzero
   noise, the primary's floored geometric NMSE ratio to the original adaptive
   control is <=.25 across dimensions and domains; it wins at least 80% of
   inside-domain seed/noise trials; at least 90% of clean Gaussian inside trials
   retain NMSE <=1e-8. These conditions collectively decide PASS/FAIL. Also
   report every dimension/noise/domain ratio, sign crossings and optimizer
   failures. This can support a restricted mechanism, not general superiority.
2. **General synthetic gate:** unchanged <=.8 geometric ratio to every control,
   >=60% wins across the eighteen family/dimension groups, and no
   noise/domain-stratum regression. Failures remain failures even if scoped
   claim 1 passes. Scores retain the existing 1e-8 comparison floor and raw
   log errors; extreme predictions and tail NMSE are separately reported.

Verify analytic derivatives against finite differences and known clean fits
before outcomes. Then independently aggregate all paired traces and recheck
selected nonlinear fits with a distinct optimizer where feasible. Numerical
verification by the same author is explicitly not external reproduction.
No new thresholds may be tuned from these confirmation results.

Nonlinear exponential fitting and additive-error least squares are established
prior art: NIST, Nonlinear Least Squares Regression,
https://www.itl.nist.gov/div898/handbook/pmd/section1/pmd142.htm; Rust (2002),
Fitting Nature's Basic Functions Part III: Exponentials, Sinusoids and Nonlinear
Least Squares, https://www.nist.gov/publications/fitting-natures-basic-functions-part-iii-exponentials-sinusoids-and-nonlinear-least.
A positive scoped result is a Kernellum capability candidate, not a claim to have
invented nonlinear regression or achieved a field-defining breakthrough.
