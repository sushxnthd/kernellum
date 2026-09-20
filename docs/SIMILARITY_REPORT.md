# Project SIMILARITY: first preregistered study

Date: 2026-09-20

## Outcome

The broad preregistered similarity-breakthrough gate **FAILED**.

This is a scientific null result, not a reason to change the thresholds after the fact.

The experiment routed:

- 172 attempted architectures on ECP5-45K for discovery;
- 172 architectures on held-out ECP5-85K;
- 100 attempted low-capacity architectures on ECP5-25K.

The 45K discovery corpus had 128 successful routes. The 25K replication corpus had 64 successful routes because larger designs exceeded the device's physical DSP capacity.

## Frozen timing model

The discovery procedure selected:

`period_ns = 14.329300 + 1.721724*sqrt(PE) - 0.045177*log2(K_TILE) - 0.018825*anisotropy`

using only the 45K discovery data.

Discovery leave-one-out period MAPE:

**3.98%**

Held-out results:

| Device | Period MAPE | Fmax MAPE | Fmax R2 | Fmax Spearman |
| --- | ---: | ---: | ---: | ---: |
| ECP5-85K | **4.31%** | **4.14%** | **0.910** | **0.961** |
| ECP5-25K | **5.37%** | **5.03%** | 0.152 | 0.818 |

The compact normalized model beat the frozen raw-coordinate ROWS/COLS/K_TILE baseline on both held-out devices.

## Why the broad breakthrough gate failed

The timing law transferred surprisingly well in absolute error, but the preregistered universal-design claim did not survive.

Failures:

1. The 25K rank correlation was below the frozen 0.90 threshold.
2. On 144 held-out GEMM shapes, the law's architecture-family accuracy was only 16.7%.
3. A largest-array heuristic achieved 83.3% family accuracy.
4. Law-guided mean routed-latency regret was 5.32%, above the frozen 5% threshold.

Therefore:

**No universal accelerator-optimum similarity law is claimed from this experiment.**

## Emergent observation

The selected model's K_TILE and anisotropy coefficients are extremely small. A reduced post-hoc diagnostic fitted only to the already-open 45K discovery corpus gives:

`period_ns ~= 14.104151 + 1.722606*sqrt(PE)`

Diagnostic MAPE:

- 45K discovery: 3.87%
- 85K held-out: 4.31%
- 25K held-out: 5.36%

This reduced square-root relation was **not** the original preregistered breakthrough claim, so it is not promoted to a law from this dataset.

It motivates a new independent confirmation experiment using geometries and tile depths absent from the first corpus.

## Interpretation

The failed workload-optimum hypothesis suggests that most workload-level optimum variation in the present RTL family is governed by coarse PE capacity and tile-edge effects.

The more scientifically interesting observation is physical:

> post-route critical period appears to grow approximately with the linear dimension of a 2-D compute fabric, represented by sqrt(PE count), and this absolute timing relation transfers across three ECP5 capacities far better than raw architecture coordinates.

The next experiment is designed specifically to falsify that narrower claim.
