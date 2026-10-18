# Validation-aware stacking prospective result

## Verdict

**KILL — conservative out-of-fold stacking improved aggregate loss but failed the frozen predictive and catastrophe-control gates.**

This is a prospective evaluation on 24 previously untouched synthetic-family paths. No threshold, fold, simplex constraint, cohort member, metric, or gate was changed after outcomes were opened.

## Exact result

| Quantity | Candidate | Stack | Strongest matched control |
|---|---:|---:|---:|
| Inside geometric NMSE | 0.7519 | **0.6607** | naive minimum-CV: 0.5986 |
| Near-shell geometric NMSE | 1.8725 | **1.5876** | naive minimum-CV: 1.4102 |
| Far-shell geometric NMSE | 8.0837 | **6.9378** | naive minimum-CV: 3.5626 |
| Far-shell catastrophes | 4 | **3** | naive minimum-CV: 2 |

The stack/candidate far-shell ratio was **0.8582**, a 14.2% aggregate improvement. Inside performance also improved, with ratio **0.8787**, and no domain gained catastrophes.

However, the mechanism failed three mandatory gates:

- catastrophe halving: **4 → 3**, not the required at most 2;
- matched hard-validation control: stack/hard-validation far ratio **1.2667**;
- mechanism-derived active prediction: only **4/10 = 40%** of predicted-active paths improved, versus the required 75%.

The active set did cover all three truth families, so the low precision cannot be dismissed as missing family coverage. Equal averaging was worse than the stack, but this does not rescue the failure against hard selection and the catastrophe gate.

## SCIENCE ledger

Candidate-anchored robust stacking can improve average interpolation and extrapolation on an unseen synthetic cohort, but the chosen pre-outcome signal—non-candidate validation weight plus request-prediction disagreement—does not identify where that improvement occurs. Large disagreement and nontrivial secondary weight were not reliable win predictors.

The result separates two claims that would otherwise be conflated:

1. convex aggregation can reduce aggregate loss;
2. validation/disagreement can prospectively identify solver-instability cases and suppress catastrophic tails.

Only the first received support, and it is established model-averaging behavior rather than a new Kernellum mechanism.

The naive minimum-CV control was strongest on this cohort, including 4 → 2 far catastrophes. This is an anomaly, not a positive mechanism claim: prior frozen evidence contains catastrophic near-tie CV failures, and this cohort was not designed as a clean revalidation of naive selection.

## CONSEQUENCE ledger

Do not deploy the stack or its active flag as a Kernellum solver-instability guardrail. Do not tune the weight floor, disagreement threshold, fold assignment, or simplex grid on this cohort.

The current synthetic solver-routing line has now produced repeated family-sensitive or non-predictive mechanisms. The next kernel should reformulate around an external nonlinear least-squares benchmark and a directly actionable intervention with a safety constraint, rather than another synthetic telemetry-derived router.

## Reproducibility

- frozen protocol commit: `748e7a43bdb7a28c2370c70607d67de3e79dc900`;
- sharded executor commit: `8373d42cea11a7edc85663ab9f4b2442f71462dc`;
- 24/24 shard manifests passed digest and key-binding verification;
- independent standard-library audit passed **10/10** checks;
- a second merge was byte-identical;
- decision SHA-256: `096c704c1eb3dac111d1144923f1bb4b7020f7d8c348a2e715cdbb430866e4de`;
- result SHA-256: `863ceae78db09997ad34575ad6bcbef811a2931622866a12e31f784db3d56b99`.

## Smallest supported claim

On the frozen 24-path unseen synthetic-family cohort, conservative four-fold worst-case validation stacking improved candidate aggregate NMSE but did not halve far-shell catastrophes, did not beat hard validation selection, and its predeclared active diagnostic achieved only 40% precision.

## Limitations

- The cohort is synthetic; no external dataset was opened.
- The result falsifies this fixed stack and diagnostic, not model averaging generally.
- Solver-bank diversity remains limited by the three existing implementations.
- The naive-control anomaly requires a separately frozen question before reuse.
