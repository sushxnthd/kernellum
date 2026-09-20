# Project SIMILARITY: independent confirmation

Date: 2026-09-20

## Result

The independently frozen square-root critical-period law **PASSED every preregistered confirmation criterion**.

The frozen law was:

`Tcrit_ns = 14.104151375868376 + 1.722605870482421 * sqrt(PE_count)`

No coefficient was refit before evaluating the confirmation corpus.

## Independent confirmation corpus

The confirmation set used only architecture parameters absent from the discovery corpus:

- odd ROWS/COLS only;
- K_TILE in {12, 24, 48}, while discovery used {8,16,32,64};
- three ECP5 capacities: 25K, 45K, 85K;
- 135 attempted routes;
- 135 successful routes.

## Preregistered results

| Device | Routes | sqrt(PE) MAPE | Linear-PE MAPE | Perimeter MAPE | sqrt signed bias |
| --- | ---: | ---: | ---: | ---: | ---: |
| 25K | 18 | **4.31%** | 3.55% | 3.82% | +1.85% |
| 45K | 45 | **3.38%** | 3.98% | 5.29% | -0.96% |
| 85K | 72 | **3.46%** | 4.53% | 4.17% | +1.26% |
| pooled | 135 | **3.55%** | 4.22% | 4.49% | +0.60% |

The sqrt(PE) law beat the frozen linear-PE law on 45K and 85K and beat both alternative laws on the pooled corpus.

97.04% of successful routes fell within 10% absolute period error.

## Orientation robustness

Across 30 matched R x C / C x R pairs:

- median absolute period difference: **2.47%**
- mean absolute period difference: **3.35%**

The effect therefore is not explained by one preferred array orientation.

## Exponent diagnostic

After the frozen pass/fail evaluation, an exploratory fit of

`period = a + b * PE^p`

on the independent confirmation corpus selected:

`p = 0.57`

with 3.47% MAPE.

This diagnostic was not used to pass the confirmation gate. Its proximity to 1/2 is consistent with the frozen square-root hypothesis.

## Scientific claim boundary

The supported claim is narrow:

> For the regular INT8 tiled systolic RTL family studied here, under Yosys + nextpnr-ecp5, post-route critical period is approximately affine in the linear dimension of the two-dimensional compute fabric, represented by sqrt(PE count), and this relation transfers across ECP5 device capacities and unseen array geometries/tile depths.

This is **not yet claimed as a universal FPGA law**.

## Why this matters

The original accelerator search problem appears high-dimensional: ROWS, COLS, tile depth, device capacity, and other architectural choices all vary.

For post-route timing in this controlled family, most of that complexity collapses to a one-dimensional geometric scale.

The next experiment must test mechanism rather than fit another curve. The working causal hypothesis is that distributed interconnect/fanout across the two-dimensional PE fabric creates a characteristic physical distance proportional to its linear dimension.

A causal intervention that changes signal-distribution geometry should therefore change the square-root slope in a predictable direction.
