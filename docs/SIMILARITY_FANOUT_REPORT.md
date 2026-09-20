# Project SIMILARITY: orthogonal fanout-law result

Date: 2026-09-20

## Result

The preregistered geometric-mean cross-fanout gate **FAILED**.

All 144 planned routes completed successfully and every implementation retained exactly one DSP multiplier per PE. The intervention was stable enough to analyze:

- median seed CV: **4.95%**
- median absolute A/B swap difference: **3.53%**
- median equal-product spread: **3.84%**

The geometric-mean model was useful but not sufficient:

- discovery MAPE: **3.09%**
- held-out N=10 MAPE: **5.94%**
- held-out Spearman rank correlation: **0.401**

The preregistered held-out rank threshold was 0.75, so that criterion failed.

The intervention-magnitude criterion also failed because the N=6 full-fanout penalty was only **6.52%**, below the frozen 8% minimum. The corresponding penalties were 8.16% at N=8 and 11.39% at N=10.

## Competing models

Held-out N=10 MAPE:

- geometric-mean fanout: **5.94%**
- arithmetic-mean fanout: **6.10%**
- maximum fanout: **6.30%**

Geometric mean therefore slightly outperformed the frozen alternatives in average error, but it failed to rank the held-out configurations reliably and the causal gate did not pass.

## Scientific consequence

The result rejects the strong claim that

    sqrt(F_A * F_B)

is the sufficient hidden invariant behind Project SIMILARITY.

Logical fanout matters, but the independently replicated broadcast timing tax cannot be reduced to this simple two-number fanout summary. The remaining mechanism must incorporate additional structure such as register boundaries, physical placement, routed topology, or congestion.

This null result is retained because it materially narrows the search space.
