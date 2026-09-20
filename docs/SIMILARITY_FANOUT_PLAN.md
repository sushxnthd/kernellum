# Project SIMILARITY: orthogonal fanout law

Date frozen: 2026-09-20

## Objective

Test a mechanistic explanation for the previously confirmed square-root timing relation.

In the original row/column broadcast fabric, every processing element consumes two operands:

- an A operand with logical fanout equal to the number of columns;
- a B operand with logical fanout equal to the number of rows.

Define the **effective cross-fanout**

    G = sqrt(F_A * F_B).

For an unsplit R x C broadcast fabric,

    F_A = C
    F_B = R

and therefore

    G = sqrt(R*C) = sqrt(PE).

This exactly recovers the confirmed empirical variable while remaining invariant to aspect-ratio swaps. That makes it a plausible explanation for why the square-root law survived independent geometries while the simple max(ROWS,COLS) diameter hypothesis failed.

The experiment below changes F_A and F_B independently while holding PE count fixed.

## Controlled RTL intervention

Use a square INT8 MAC fabric on ECP5-85K.

Instead of one source register driving a whole row or column, operand sources are segmented into contiguous groups.

- A_FANOUT is the number of PEs driven by each A source.
- B_FANOUT is the number of PEs driven by each B source.
- Every PE still receives one A operand and one B operand.
- PE count, multiplier count, accumulator width and arithmetic are unchanged within each N.
- Source-register replication changes as required to implement the requested fanout, but source values are made group-distinct so synthesis cannot legally collapse the intervention.

This deliberately changes the logical distribution network without changing the number of MACs.

## Discovery and held-out arrays

Device: Lattice ECP5-85K, CABGA381, speed grade 6.

Seeds: 1, 2, 3.

Discovery arrays:

- N=6, fanouts {1,2,3,6}
- N=8, fanouts {1,2,4,8}

Held-out array:

- N=10, fanouts {1,2,5,10}

For every N, route the full Cartesian product of A_FANOUT x B_FANOUT.

Each N therefore has 16 fanout pairs.

Total planned routes:

    3 array sizes x 16 fanout pairs x 3 seeds = 144 routes.

The N=10 points are not used to fit coefficients.

## Frozen candidate variables

For every fanout pair define:

    G = sqrt(F_A * F_B)              # geometric mean / cross-fanout
    A = (F_A + F_B) / 2              # arithmetic mean
    M = max(F_A, F_B)                # maximum single-net fanout

The primary hypothesis is G.

A and M are frozen competing explanations.

## Frozen models

For each candidate z in {G, A, M}, fit only the N=6 and N=8 median points:

    period_ns = alpha + beta*N + gamma*z.

Use the median critical period across the three placement seeds for each configuration.

Freeze all coefficients before evaluating N=10.

No coefficient may be refit after the held-out N=10 data are opened.

## Additional invariance tests

### Swap symmetry

For matched pairs (F_A,F_B) and (F_B,F_A), compare median periods.

A true cross-fanout effect should not require one privileged operand orientation.

### Equal-product groups

Pairs with equal F_A*F_B have equal G even when their fanout imbalance differs.

For every product group containing at least two configurations, compute the within-group period spread.

Low spread supports G over a max-fanout explanation.

### Fanout intervention magnitude

Within each N compare:

    (F_A,F_B) = (1,1)

against

    (F_A,F_B) = (N,N).

This directly tests whether increasing distribution fanout changes timing at fixed PE count.

## Preregistered cross-fanout gate

The geometric-mean fanout mechanism is supported only if all hold:

1. at least 138 of 144 routes succeed;
2. every successful implementation maps exactly one MULT18X18D per PE;
3. median per-configuration seed CV is <= 5%;
4. the discovery G model has period MAPE <= 6%;
5. the frozen G model has held-out N=10 period MAPE <= 8%;
6. the held-out G model has lower MAPE than both frozen A and M alternatives;
7. held-out Spearman correlation between predicted and actual period is >= 0.75;
8. the fitted G coefficient gamma is positive;
9. the median absolute swap-pair period difference is <= 4%;
10. the median equal-product-group period spread is <= 6%;
11. the (N,N) configuration has median period at least 8% above (1,1) for N=6, N=8 and N=10.

No failed criterion may be removed after results are known.

## Interpretation if the gate passes

A pass supports the narrow claim:

> In this controlled ECP5 INT8 MAC family, a substantial component of routed critical-period scaling is governed by the geometric mean of the two orthogonal operand-distribution fanouts. The previously confirmed sqrt(PE) relation is then a special case of a more general cross-fanout law, not merely a PE-count correlation.

The result would still not establish a universal FPGA law. Independent RTL families, FPGA vendors and CAD flows would remain necessary replication targets.
