# Project SIMILARITY: corrected final-route causal law

Date frozen: 2026-09-20

## Measurement correction

A timing audit established that historical SIMILARITY scripts took the minimum of every nextpnr primary-clock Fmax line. nextpnr reports timing after placement and again after routing, so the historical metric often selected the post-placement estimate.

This experiment starts a corrected measurement chain.

**Only nextpnr's post-route `--report` JSON is used.**

No console-regex timing value enters the analysis.

## Scientific question

Does nonlocal row/column operand broadcast cause a size-dependent **final routed** timing penalty relative to registered nearest-neighbor transport, and does a relation learned only from square arrays transfer to unseen rectangular arrays?

## RTL intervention

Use the already-audited matched diagnostic fabrics:

- `similarity_broadcast_fabric`: direct row/column operand distribution;
- `similarity_local_fabric`: registered nearest-neighbor operand propagation.

Every successful design must map exactly one ECP5 MULT18X18D per PE.

## Discovery corpus

Square arrays, seeds 17, 18, 19.

ECP5-25K:
- 3x3
- 5x5

ECP5-45K:
- 3x3
- 5x5
- 7x7

ECP5-85K:
- 3x3
- 5x5
- 7x7
- 9x9
- 11x11

Both topologies are routed.

Discovery routes: 60.

## Held-out confirmation corpus

Rectangular geometries absent from discovery, seeds 20, 21, 22.

ECP5-25K:
- 3x7

ECP5-45K:
- 3x7
- 5x9

ECP5-85K:
- 3x7
- 5x9
- 7x11

Both topologies are routed.

Held-out routes: 36.

Total: **96 final-route implementations**.

## Frozen discovery model

For each device/topology/geometry take the median post-route critical period across the three seeds.

Fit only square discovery points:

    T =
        alpha_25 * I25
      + alpha_45 * I45
      + alpha_85 * I85
      + beta_b * sqrt(PE)
      + delta_0 * LOCAL
      + delta_1 * LOCAL * sqrt(PE)

Derived:

    broadcast_slope = beta_b
    local_slope = beta_b + delta_1

and the learned broadcast tax is

    tax_pred(sqrtPE)
      = T_broadcast - T_local
      = -delta_0 - delta_1 * sqrt(PE).

No held-out rectangular point participates in fitting.

## Held-out evaluation

For each rectangular device/geometry pair:

    tax_obs = median(T_broadcast) - median(T_local)

Use the discovery-frozen equation above to predict the tax.

No coefficient is refit.

## Preregistered routed-law gate

The corrected final-route causal law is supported only if all criteria hold:

1. at least 92 of 96 routes succeed;
2. every successful implementation maps exactly one MULT18X18D per PE;
3. median per-point seed CV <=6% for both topologies in discovery and holdout;
4. discovery broadcast slope is positive and >=0.15 ns / sqrt(PE);
5. discovery local slope <=60% of the broadcast slope;
6. discovery topology-by-size interaction delta_1 is negative;
7. on ECP5-85K 11x11, local median routed period is at least 12% below broadcast;
8. all six held-out rectangular pairs have positive observed broadcast tax;
9. held-out frozen-tax MAE <=1.25 ns;
10. held-out frozen-tax RMSE <=1.50 ns;
11. predicted-vs-observed held-out tax correlation >=0.70;
12. at least five of six held-out taxes are within +/-1.75 ns of prediction;
13. on held-out ECP5-85K 7x11, local routed period is at least 15% below broadcast.

No criterion may be changed after results are opened.

## Interpretation

A pass supports:

> Under a corrected post-route timing definition, nonlocal operand broadcast causally introduces a size-dependent timing tax in this ECP5 INT8 MAC family. A differential law learned only from square arrays transfers without refitting to unseen rectangular geometries and new placement seeds.

This would replace, not merely supplement, the historical worst-stage timing equation.

It would still not establish a vendor-independent universal law.
