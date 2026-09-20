# Project SIMILARITY: independent causal-mechanism confirmation

Date frozen: 2026-09-20

## Objective

Independently test the broadcast-distribution timing penalty found in the preregistered square-array causal intervention.

The original intervention compared broadcast operand distribution with registered nearest-neighbor transport and passed every frozen criterion.

Its fixed-effect model estimated:

    broadcast_slope = 1.0788631181 ns / sqrt(PE)
    local_intercept_shift = +1.7762324291 ns
    local_slope = 0.2766190018 ns / sqrt(PE)

Therefore the frozen **broadcast tax** is

    delta_T_pred =
        T_broadcast - T_local
      = -1.7762324291
        + 0.8022441163 * sqrt(PE)   ns

No coefficient in this equation may be refit before evaluating this confirmation corpus.

## Independent corpus

Use only rectangular geometries absent from the square-array mechanism study.

ECP5-25K:
- 3x7

ECP5-45K:
- 3x7
- 5x9

ECP5-85K:
- 3x7
- 5x9
- 7x11

For every device/geometry:
- broadcast topology;
- registered local topology;
- nextpnr seeds 4, 5 and 6.

The original causal study used seeds 1, 2 and 3.

Total planned routes:

    (1 + 2 + 3) geometries
    x 2 topologies
    x 3 new seeds
    = 36 routes.

## Frozen analysis

For each device/geometry/topology, use the median critical period across seeds 4-6.

For each matched device/geometry pair compute:

    delta_T_obs = median(T_broadcast) - median(T_local)

and

    delta_T_pred =
        -1.7762324291
        + 0.8022441163 * sqrt(ROWS*COLS).

No device-specific parameter appears in the differential prediction because the original fixed-effect device intercept cancels within matched pairs.

## Preregistered confirmation gate

The causal broadcast-tax relation is independently confirmed only if all hold:

1. at least 34 of 36 routes succeed;
2. every successful implementation maps exactly one MULT18X18D per PE;
3. median per-point seed CV is <= 6% for each topology;
4. all six matched device/geometry pairs have positive observed broadcast tax;
5. frozen broadcast-tax mean absolute error is <= 1.25 ns;
6. frozen broadcast-tax RMSE is <= 1.50 ns;
7. correlation between predicted and observed broadcast tax is >= 0.75;
8. for ECP5-85K at 7x11, local transport reduces median critical period by at least 20%;
9. at least five of six observed taxes lie within +/-1.75 ns of the frozen prediction.

No failed criterion may be removed or weakened after results are known.

## Claim boundary

A pass supports:

> The size-dependent timing penalty caused by nonlocal operand distribution transfers to unseen rectangular MAC fabrics and new placement seeds, with a frozen differential scaling relation derived from an independent square-array intervention.

A pass does not establish universality across FPGA vendors, ASIC technologies, arbitrary RTL families, or arithmetic implementations.
