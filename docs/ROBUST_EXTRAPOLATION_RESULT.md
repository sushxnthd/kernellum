# Robust extrapolation follow-up

**1 October 2026 — development evidence only. No verified breakthrough.**

The representation experiment exposed a useful failure mode: a transformed
model can fit its observed labels well while producing a catastrophic inverse
transform outside the observed region. The known Genz Corner Peak case reached
`8.427168e16` NMSE for the original representation stack.

## Support routing

Six fixed, observation-only routing variants were evaluated on the already-opened
39-function UQ cohort: five seeds, two noise levels, 192 candidate inputs, 64
labels, and the existing 2,048-point test sets. The variants route a transformed
component to the existing raw selector when its input is outside measured bounds,
when its latent kernel variance exceeds the largest leave-one-out variance, or
when that rule is applied only to nonlinear families.

The best variant, `support_nonlinear_leverage_stack`, repaired the known failure
(Genz Corner Peak, seed 930105, noise 0.02) to 0.101 NMSE. It nevertheless
regressed on clean cases: 1.141× the original representation stack overall,
1.631× at zero noise and 0.797× at 0.02 noise, with only 10/39 function wins.
It therefore fails the preregistered 0.8 ratio, 60%-wins, and no-noise-regression
requirements. The support audit independently recomputed all 2,340 outcomes,
with maximum scaled discrepancy `4.904e-6`.

## Robust aggregation

Three fixed aggregators were screened over the same cohort: weighted component
median, weighted signed geometric mean when all components share a sign, and an
observed-label LOO selector among those two and the original weighted mean.
The weighted median was the strongest: 0.891× the original representation
stack error, with 18/39 function wins. It repaired the catastrophic Genz case to
0.045 NMSE, but did not reach the 0.8 ratio / 60%-wins gate. The geometric mean
and LOO selector were weaker (0.899× and 0.911× respectively).

The same-author second arithmetic implementation passed in CI (job
110502038012), recomputing all 1,170 robust outcomes. Maximum scaled NMSE
discrepancy was `4.904e-6`; 16 aggregation-choice numerical ties were accepted
within the reported score tolerance. This is not external reproduction, and
the benchmark remains development-only.

These results are retained as a reproducible negative result and a practical
diagnostic: robust aggregation is materially safer than the original stack, but
not yet a general predictor. None of the routing or aggregation variants is
promoted as a default.

All methods use only observed labels for fitting, selection, and routing. The
test responses are used only for development scoring. No untouched holdout was
used, and no claim of field-level generalization is made.
