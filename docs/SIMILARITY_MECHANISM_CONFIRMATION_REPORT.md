# Project SIMILARITY: independent causal-mechanism confirmation

Date: 2026-09-20

## Result

The preregistered independent confirmation **PASSED every frozen criterion**.

The confirmation used only unseen rectangular geometries and new nextpnr seeds 4, 5 and 6. The original causal intervention used square arrays and seeds 1, 2 and 3.

All **36/36 routes succeeded** and every successful implementation mapped exactly one MULT18X18D per PE.

## Frozen equation

Before opening the confirmation corpus, the differential timing law was frozen from the independent square-array intervention:

    delta_T_ns =
        T_broadcast - T_local
      = -1.7762324291
        + 0.8022441163 * sqrt(PE)

No coefficient was refit.

## Held-out performance

Across six device/geometry pairs:

- mean absolute error: **0.5952 ns**
- RMSE: **0.7343 ns**
- predicted-vs-observed correlation: **0.9004**
- pairs within +/-1.75 ns: **6/6**
- positive observed broadcast tax: **6/6**

Median seed CV:

- broadcast: **2.51%**
- local: **4.21%**

For the largest unseen geometry, ECP5-85K 7x11:

- broadcast median period: **17.0474 ns**
- local median period: **11.6469 ns**
- observed broadcast tax: **5.4005 ns**
- frozen predicted tax: **5.2634 ns**
- absolute prediction error: **0.1371 ns**
- local-topology period improvement: **31.68%**

## Pairwise results

| Device | Geometry | Observed tax (ns) | Frozen prediction (ns) | Abs. error (ns) |
| --- | --- | ---: | ---: | ---: |
| 25K | 3x7 | 1.5590 | 1.9001 | 0.3411 |
| 45K | 3x7 | 2.7598 | 1.9001 | 0.8597 |
| 45K | 5x9 | 4.4405 | 3.6054 | 0.8351 |
| 85K | 3x7 | 3.1848 | 1.9001 | 1.2846 |
| 85K | 5x9 | 3.7192 | 3.6054 | 0.1138 |
| 85K | 7x11 | 5.4005 | 5.2634 | 0.1371 |

## Scientific consequence

The causal observation is now independently replicated:

> In these controlled ECP5 INT8 MAC fabrics, nonlocal broadcast operand distribution introduces a positive size-dependent critical-period penalty that transfers from square discovery arrays to unseen rectangular geometries and new placement seeds. A differential equation frozen before confirmation predicts that penalty with sub-nanosecond mean absolute error across ECP5-25K, 45K and 85K.

This is materially stronger than a post-hoc PE-count correlation because:

1. topology is experimentally intervened on;
2. the effect is measured within matched PE populations;
3. the differential model is frozen before the confirmation corpus;
4. the confirmation geometries and seeds are disjoint from discovery;
5. all preregistered confirmation criteria pass.

## Claim boundary

The result establishes a reproducible causal **broadcast timing tax** inside this ECP5 MAC-fabric family. It does not yet establish the physical latent variable that creates the tax, nor universality across FPGA vendors, arithmetic backends, or unrelated RTL families.
