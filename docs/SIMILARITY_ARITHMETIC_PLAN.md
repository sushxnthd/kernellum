# Project SIMILARITY: arithmetic-backend replication

Date frozen: 2026-09-20

## Objective

Test whether the observed linear-dimension timing structure is specific to ECP5 hard DSP placement or persists when the same 2-D broadcast MAC fabric is implemented in LUT logic.

This experiment is independent of the causal broadcast-vs-local intervention.

## Matched implementations

Use the same square broadcast-fed INT8 MAC fabric and identical RTL parameters.

Two synthesis backends:

1. **DSP**: normal `synth_ecp5`, allowing each 8-bit multiplier to map to MULT18X18D.
2. **LUT**: `synth_ecp5 -nodsp`, forcing the same 8-bit multipliers into programmable logic.

The communication topology, accumulator width, operand generators, reset behavior, nextpnr settings and placement seeds are otherwise unchanged.

## Devices and array sizes

ECP5 CABGA381, speed grade 6.

25K:
- 3x3
- 5x5

45K:
- 3x3
- 5x5
- 7x7

85K:
- 3x3
- 5x5
- 7x7
- 9x9

Seeds:
- 1
- 2
- 3

Total planned routes:

2 backends x (2 + 3 + 4 sizes) x 3 seeds = **54 routes**.

## Frozen analysis

For each device/backend/size, use the median critical period over three placement seeds.

For each backend separately fit, using only the 45K median points:

### Square-root model

    period = alpha + beta * sqrt(PE)

### Linear-PE model

    period = alpha + beta * PE

The 25K and 85K data are held out from coefficient fitting.

No coefficient may be refit after the held-out devices are opened.

## Preregistered replication gate

The geometric scaling form is considered replicated across arithmetic backends only if all hold:

1. at least 52 of 54 routes succeed;
2. every successful DSP implementation maps exactly one MULT18X18D per PE;
3. every successful LUT implementation maps zero MULT18X18D cells;
4. on held-out 85K, the frozen square-root model has period MAPE <= 10% for both DSP and LUT backends;
5. on held-out 25K, the frozen square-root model has period MAPE <= 12% for both backends;
6. for each backend, the square-root model has lower combined held-out MAPE than its frozen linear-PE alternative;
7. mean signed held-out bias magnitude <= 6% for each backend;
8. median seed coefficient of variation <= 6% for each backend.

## Exponent diagnostic

Only after the frozen pass/fail gate is evaluated, fit

    period = a + b * PE^p

to all median points separately for DSP and LUT backends.

This is exploratory. A best-fit exponent near 0.5 in both backends would strengthen the geometric interpretation but cannot rescue a failed preregistered gate.

## Scientific interpretation

If the gate passes, the supported claim is:

> The approximately linear-in-array-dimension critical-period structure is not solely an artifact of ECP5 hard DSP placement. It persists when identical MAC arithmetic is forced into LUT fabric, with backend-dependent coefficients but the same square-root model class transferring across device capacities.

This still does not imply universality across FPGA vendors or CAD toolchains.
