# Stability-certified abstention: frozen development protocol

**Classification:** OPENED DEVELOPMENT DISCRIMINATION  
**Active kernel:** replace failed predictive routing with a directly checkable
solver-invariance certificate.

## Question

Can Kernellum safely treat cross-solver exact-LOO scores as an ordering only
when two independently implemented solvers agree on model identity, the CV
margin exceeds a fixed numerical-equivalence band, and their predictions agree
on the actual requested inputs?

This protocol is frozen before the evaluator joins any generated truth values
to the certificate decisions. The 16 shifted paths are permanently opened and
cannot provide confirmation.

## Certificate

Fit the candidate and independent implementations exactly as in the frozen
shifted study. Let `c` and `i` be their winning models. On the union of the
inside, near-shell, and far-shell request inputs, define

```
relative_cv_margin = abs(CV_c - CV_i) / (1 + min(CV_c, CV_i))
prediction_rms = rms(pred_c - pred_i) / max(std(y_train), 1e-12)
prediction_max = max(abs(pred_c - pred_i)) / max(std(y_train), 1e-12)
```

The arbitration certificate accepts iff all conditions hold:

1. sign and model family agree;
2. `relative_cv_margin >= 1e-3`;
3. `prediction_rms <= 0.5`;
4. `prediction_max <= 4.0`.

If accepted, choose the lower-CV implementation. Otherwise abstain. Thresholds
are engineering constants frozen without label access; no threshold sweep is
permitted in this run.

## Preregistered gates

The development certificate passes only if all hold:

1. all 16 paths complete and decisions are hashed before label join;
2. every harmful naive switch is rejected, where harmful means the independent
   lower-CV choice is worse than candidate by `ln(10)` in any domain;
3. no accepted arbitration is worse than candidate by `ln(2)` in any domain;
4. at least 4/16 paths are accepted (non-vacuous coverage);
5. accepted aggregate geometric NMSE is no worse than 1.10x candidate in every
   domain;
6. rerun and independent aggregation reproduce every decision and gate.

Failure kills this fixed certificate. Passing only earns a fresh prospective
shifted study; it is not a breakthrough or external validation.

## Strongest alternative explanation

The rule may only detect obvious numerical disagreement, abstain too often, or
appear safe because candidate happens to be the better solver on this small
opened cohort. Agreement between two solvers does not certify scientific model
correctness.

## Consequence boundary

- **Pass:** add an experimental fail-closed certificate interface and freeze a
  genuinely new shifted/external study.
- **Fail:** retire pairwise arbitration certificates at these fixed thresholds;
  require a globalized optimizer with an objective/optimality certificate or
  expose unresolved model-selection uncertainty to the caller.

