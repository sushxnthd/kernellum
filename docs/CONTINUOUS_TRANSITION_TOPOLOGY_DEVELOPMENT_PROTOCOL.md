# Continuous transition-topology development falsification

## Classification

**Opened-cohort development audit. Not prospective evidence and not a breakthrough claim.**

## Precise question

Does the full controlled-continuation transition curve add enough family-transfer information beyond two static pre-outcome quantities—candidate/globalized request disagreement and their training-residual ratio—to support a positive solver-routing mechanism?

## Inputs

Only the two already-opened deterministic archives are used:

- 16-path basin-transition continuation cohort;
- 24-path basin-transition confirmatory cohort.

Together they contain 40 paths across five truth families. No frozen or external holdout is opened.

## Representation

For each path, before using request truth, construct:

- switch fractions by amplitudes 0.08, 0.16, 0.24, 0.32;
- mean normalized request-prediction distances at those amplitudes;
- candidate/globalized request-prediction distance;
- log candidate/globalized training-residual ratio.

The **topology model** uses all ten coordinates. The matched **static ablation** uses only the final two.

Target on the opened archive is clipped far-shell log-NMSE gain:

`clip(logNMSE(candidate) - logNMSE(globalized), -2, 2)`.

Both models use the same standardized ridge regression with lambda 10. Evaluation is leave-one-truth-family-out. Family identity is never a feature.

## Frozen decision grid and positive-mechanism gate

Evaluate thresholds {0.10, 0.15, 0.20, 0.25, 0.30}. A viable topology rule must have:

1. at least eight routes;
2. routed precision at least 0.75;
3. far-shell geometric-NMSE ratio at most 0.90;
4. no increase in catastrophes (NMSE > 5);
5. at least two catastrophes removed;
6. and a topology operating point that is not dominated by a static operating point with route count within two (static has at least its precision and no worse aggregate ratio).

## Strongest alternative explanation

Any apparent gain may come entirely from candidate/globalized disagreement or training fit, while continuation-curve features add noise and family sensitivity. The matched static ridge is the decisive control.

## Kill condition

Kill the continuous transition-topology kernel if no topology operating point passes every gate. Do not open a new cohort and do not tune a larger representation after seeing this result.

## Consequence threshold

Pass: freeze coefficients and one threshold for a new untouched three-family evaluation.

Fail: retain continuation traces as telemetry only and pivot the positive-mechanism search to a different intervention, such as validation-aware robust aggregation or direct model averaging with an externally interpretable safety constraint.
