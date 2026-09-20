# Project SIMILARITY Confirmation: square-root critical-period law

Date frozen: 2026-09-20

## Background

The first preregistered SIMILARITY study rejected the broad universal-optimum hypothesis.

A post-hoc diagnostic on the already-open 45K discovery corpus exposed a much simpler relation:

    period_ns = 14.104151375868376
                + 1.722605870482421 * sqrt(PE_count)

This reduced relation is now frozen before any independent confirmation route is generated.

## Confirmation question

Does post-route critical period for the Kernellum INT8 tiled systolic fabric scale approximately with the linear dimension of the 2-D compute fabric, represented by sqrt(PE count), across unseen array geometries, unseen tile depths, and multiple ECP5 device capacities?

## Independent architecture corpus

The confirmation corpus uses only dimensions absent from the first corpus.

ROWS/COLS use odd values.

Shared low-capacity geometries:

- 3x3
- 3x5, 5x3
- 3x7, 7x3
- 5x5

Additional 45K/85K geometries:

- 5x7, 7x5
- 5x9, 9x5
- 7x7
- 5x11, 11x5
- 7x9, 9x7

Additional 85K geometries:

- 7x11, 11x7
- 9x9
- 7x13, 13x7
- 9x11, 11x9
- 9x13, 13x9

Tile depths are also unseen:

- K_TILE = 12
- K_TILE = 24
- K_TILE = 48

The same Yosys + nextpnr-ecp5 flow, CABGA381 package, speed grade 6, seed 1 is used.

## Frozen comparison laws

All coefficients are frozen from the original 45K corpus before confirmation.

### Hsqrt

    period_ns = 14.104151375868376
                + 1.722605870482421 * sqrt(PE)

### Hlinear

    period_ns = 18.602356969344182
                + 0.14970963713526794 * PE

### Hperimeter

    period_ns = 14.456684505987951
                + 0.7273119635481695 * (ROWS + COLS)

No coefficient may be refit on the confirmation corpus.

## Confirmation criteria

The square-root law is considered independently confirmed only if all hold:

1. successful-route period MAPE <= 7% on each of 25K, 45K, and 85K;
2. pooled period MAPE <= 5.5%;
3. Hsqrt pooled MAPE is lower than both Hlinear and Hperimeter;
4. Hsqrt has lower MAPE than Hlinear on at least 2 of 3 devices;
5. mean signed percentage bias magnitude <= 3% on each device;
6. for orientation pairs R x C versus C x R, the median absolute timing difference is <= 8%, showing the law is not merely fitting one preferred orientation;
7. at least 90% of successful routes have absolute percentage error <= 10%.

## Exponent diagnostic

After the confirmation gate is evaluated, an exploratory exponent scan may fit

    period = a + b * PE^p

on the confirmation data only.

This scan is diagnostic, not part of the pass/fail gate.

A physically compelling result would place the best-fit exponent near 0.5, but the frozen square-root law must pass without using that scan.

## Scientific interpretation

If the frozen square-root relation passes this independent corpus, the supported claim is narrow:

> For this regular INT8 tiled systolic RTL family on ECP5, post-route critical period is approximately affine in the linear dimension of the compute fabric, sqrt(PE count), and this relation transfers across device capacities and unseen array geometries.

This is not yet a universal FPGA law. A second-family or second-toolchain replication would still be required before broader universality language.
