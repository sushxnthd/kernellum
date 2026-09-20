# Project SIMILARITY: compute-backend invariance of the broadcast timing tax

Date frozen: 2026-09-20

## Motivation

Two preregistered studies have established and independently confirmed a causal timing penalty from nonlocal row/column operand distribution in DSP-backed ECP5 INT8 MAC fabrics.

The differential relation was frozen before independent confirmation:

    delta_T_ns =
        T_broadcast - T_local
      = -1.7762324291
        + 0.8022441163 * sqrt(PE)

and then confirmed on unseen rectangular geometries and new seeds with 0.595 ns MAE.

The open question is whether this is fundamentally a **communication-topology tax** or an artifact of ECP5 DSP placement.

A stronger invariant should survive when the arithmetic implementation changes completely.

## Intervention

Use identical broadcast and registered-local RTL fabrics, but synthesize each with two arithmetic backends:

- DSP: ordinary `synth_ecp5`, requiring one MULT18X18D per PE;
- LUT: `synth_ecp5 -nodsp`, requiring zero MULT18X18D cells.

All other RTL is unchanged.

Device: ECP5-85K, CABGA381, speed grade 6.

Square sizes:

- 3x3
- 5x5
- 7x7
- 9x9

Placement seeds:

- 7
- 8
- 9

These seeds were not used by the original mechanism discovery (1-3) or rectangular confirmation (4-6).

Total planned routes:

    4 sizes x 2 topologies x 2 arithmetic backends x 3 seeds = 48.

## Frozen prediction

For every size and both arithmetic backends, predict:

    delta_T_pred =
        -1.7762324291
        + 0.8022441163 * sqrt(PE).

No coefficient may be refit before evaluating the LUT-backed results.

The DSP results in this study are a contemporaneous positive control.

## Primary preregistered gate

The broadcast-tax relation is supported as compute-backend invariant only if all criteria pass:

1. at least 46 of 48 routes succeed;
2. every successful DSP design maps exactly one MULT18X18D per PE;
3. every successful LUT design maps zero MULT18X18D cells;
4. median per-configuration seed CV is <=7% separately for all four topology/backend combinations;
5. observed broadcast tax is positive for all eight size/backend pairs;
6. for the LUT backend, frozen-equation MAE is <=1.75 ns;
7. for the LUT backend, frozen-equation RMSE is <=2.25 ns;
8. LUT predicted-vs-observed tax correlation is >=0.70;
9. at 9x9, registered-local transport improves LUT critical period by at least 15%;
10. at least three of four LUT observed taxes lie within +/-2.25 ns of the frozen DSP-derived prediction.

The gate is intentionally looser than the same-backend confirmation because forcing multiplication into LUTs materially changes placement density and critical-path structure.

No threshold may be weakened after results are known.

## Secondary descriptive analysis

After the primary gate is evaluated, fit

    delta_T = alpha + beta * sqrt(PE)

separately for DSP and LUT observations and report their coefficients.

This fit is descriptive only and cannot rescue a failed primary gate.

## Interpretation

A pass supports:

> In this controlled ECP5 INT8 MAC family, the critical-period cost of nonlocal operand distribution is primarily a communication-topology phenomenon rather than a DSP-specific artifact: a differential timing equation derived entirely from DSP-backed arrays transfers to LUT-multiplier arrays without coefficient refitting.

This still would not establish cross-vendor universality.
