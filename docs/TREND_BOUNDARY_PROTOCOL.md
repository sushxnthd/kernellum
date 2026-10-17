# Curvature, noise and support boundary experiment

Freeze the protocol, generator and runner before producing comparative scores.
This is an untouched set of synthetic mechanism conditions, deliberately chosen
after the opened cohort diagnosed lost log-quadratic expressivity. It is not an
unselected external benchmark and cannot alone establish general accuracy.

Use seven explicitly defined two-variable response families, ten predetermined
seeds, four noise levels, and three test domains. Pool points are uniform in
[-1,1]^2. For the power-law family exponentiate these coordinates before both
coverage selection and fitting. Select 64 labels using the existing common
label-independent maximin procedure, starting with 16 points. Every method
receives exactly those observed labels and the unlabeled pool.

Response families in latent coordinates z=(u,v):

- log_affine: exp(.5+.8u-.35v)
- log_quadratic: exp(.5-.7u²-1.1v²+.3uv)
- peaked_log_quadratic: exp(.3-8u²-12v²+3uv)
- shifted_gaussian: exp(-5((u-.4)²+(.5v+.2)²))
- rational_peak: 1/(1+10(u+.5)²+6(v-.2)²)
- signed_cubic: u+.2v+.4uv+.3u³
- power_law: 3x1^1.7/x2^.8, x=exp(z)

Noise is independent additive Gaussian, with standard deviation equal to the
specified fraction of the clean response standard deviation over the pool.
Predetermined seed offsets fix input generation and shared perturbations.
No labels, test responses or function identities enter any predictor. Test
coordinates enter prediction only; truth enters scoring only.

Domain samples: 512 uniform points inside [-1,1]^2; 256 points in [-1.5,1.5]^2
outside [-1,1]^2; 256 points in [-3,3]^2 outside [-1.5,1.5]^2. Rejection sampling
changes coordinates, not response-based selection. Preserve exact arrays.

Seven arms: original, remove-only, add-only and both from the fixed factorial
definition, plus the existing adaptive, weighted-median and nonlinear-leverage
support controls. No new prediction rule or threshold is tuned here.

Predictions to test before outcomes:

1. Add-only retains exact clean log-affine, log-quadratic, shifted-Gaussian and
   power-law accuracy (NMSE <=1e-8) inside the measured domain on at least 9/10
   seeds per named family. Removal need not retain quadratic-log expressivity.
2. The add-only general gate is tested unchanged: <=0.8 geometric error ratio
   against every control, >=60% function wins, and no noise/domain stratum
   regression. This is a demanding synthetic-domain gate, not proof of SOTA.
3. Log-response availability can change under additive noise. Record all
   observed sign transitions and whether losses track that discrete switch.
4. A good inside-domain PRESS risk is not sufficient evidence of stable
   extrapolation; explicitly record prediction magnitudes and tail errors.

Report every 280 observation path × seven methods × three domains = 5,880
scores. Compute errors in log space to avoid silently clipping or excluding
overflow-sized scores. NMSE may be null when its finite log-NMSE is larger than
floating point can represent. Nonfinite predictions are explicit failures,
retained in the trace and disqualifying the general gate. Preserve unchanged
1e-8 flooring for comparative metrics, and separately report raw log errors.
No geometric aggregate may substitute for tail-error reporting.
An exactly zero residual is flagged explicitly; its log error uses -10000 as
a finite serialization sentinel, below the fixed comparison floor. Overflowing
ratios are null alongside their finite log ratios; gate decisions use log ratios.
Prediction arithmetic exceptions are retained as failures rather than omitted.

Verification: source/data hashes, paired indices and observed values, explicit
scalar arithmetic reductions, and separate reconstruction of kernel prediction
arithmetic where feasible. Classification is PASS/FAIL/INCONCLUSIVE for each
specific prediction. Search prior art before promoting any law or mechanism.

Relevant established work includes Fischer and Proppe, Enhanced Universal
Kriging for Transformed Input Parameter Spaces (arXiv:2307.06906); Deutsch,
Correcting for negative weights in ordinary kriging (1996),
doi:10.1016/0098-3004(96)00005-2; and Foster et al., Stable and Efficient Gaussian
Process Calculations (JMLR 10, 2009). These prevent novelty claims based merely
on transformed kriging, weight correction or improved linear algebra.
