# Project SIMILARITY: registered relay hierarchy and minimax fanout

Date frozen: 2026-09-20

## Background

Project SIMILARITY has established and independently confirmed a positive critical-period penalty from direct row/column operand broadcast.

The confirmed differential law for the direct broadcast topology is:

    delta_T_direct ~= -1.7762 + 0.8022 * sqrt(PE) ns.

For a square N x N array, sqrt(PE)=N, which is also the direct logical fanout of each row/column source.

Simple source replication without a register boundary did not establish a clean fanout invariant.

This experiment asks whether the missing variable is **maximum unregistered distribution fanout between register boundaries**.

## Theory

Insert exactly one registered relay level between every source and its PEs.

For a row of N PEs, choose relay group width F, where F divides N.

Then:

- source -> relay fanout = N/F
- relay -> PE fanout = F

The worst fanout between register boundaries is

    M(F) = max(F, N/F).

M is minimized by balancing the two stages near F = sqrt(N).

For a square PE array P=N^2, optimal two-stage distribution gives

    M_min ~ sqrt(N) = P^(1/4),

whereas direct broadcast gives

    M_direct = N = P^(1/2).

This motivates a **hierarchical locality hypothesis**:

> adding a registered distribution level reduces the communication-induced scaling exponent by balancing the unregistered fanout carried by each timing stage.

The present experiment tests the two-stage case. It does not assume the full general hierarchy is true.

## RTL families

All designs use the same INT8 MAC accumulator PE.

1. **direct**: one row/column source directly broadcasts to all PEs;
2. **relay(F)**: source -> registered group relay -> PE;
3. **local**: registered nearest-neighbor operand propagation.

Relay fanout settings:

- N=6: F in {1,2,3,6}; minimax-optimal {2,3}
- N=8: F in {1,2,4,8}; minimax-optimal {2,4}
- N=10: F in {1,2,5,10}; minimax-optimal {2,5}

Device: ECP5-85K / CABGA381 / speed grade 6.

Seeds: 10, 11, 12.

Total routes:

- relay: 3 sizes x 4 F values x 3 seeds = 36
- direct: 3 sizes x 3 seeds = 9
- local: 3 sizes x 3 seeds = 9

Total = **54 routes**.

## Frozen analysis

Use the median critical period over seeds for each configuration.

For relay points fit:

    T_relay = alpha_6 I6 + alpha_8 I8 + alpha_10 I10 + beta * M(F).

This separates array-size baseline from the stage-fanout effect.

For every N define:

    direct_tax = T_direct - T_local
    relay_tax(F) = T_relay(F) - T_local

and

    best_relay_tax = min_F relay_tax(F).

No relay configuration is selected using individual seeds; selection uses only median points.

## Preregistered gate

The registered-relay minimax-fanout mechanism is supported only if all hold:

1. at least 52 of 54 routes succeed;
2. every successful route maps exactly one MULT18X18D per PE;
3. median per-configuration seed CV <=6%;
4. fitted beta for M(F) is positive;
5. pooled relay model RMSE <=1.25 ns;
6. for all three N, a minimum-period relay configuration belongs to the preregistered minimax-optimal F set (ties within 0.25 ns count);
7. for at least two of three N, both extreme relay choices F=1 and F=N are >=2% slower than the best minimax-optimal relay;
8. direct broadcast tax is positive for N=6,8,10;
9. for at least two of three N, the best relay removes >=40% of the direct broadcast tax relative to the local baseline;
10. at N=10, the best relay critical period is <=85% of direct broadcast period.

No failed threshold may be changed after data are opened.

## Scaling diagnostic

After the gate is evaluated, report the best-relay taxes against:

    P^(1/4) = sqrt(N).

With only three N values this is a diagnostic, not a standalone exponent claim.

If the gate passes, a larger preregistered follow-up will test the general depth law:

    communication exponent ~ 1 / (2*(L+1))

for L registered relay levels.

## Claim boundary

A pass supports a new architecture-level mechanism:

> Direct broadcast timing is limited by unregistered distribution reach between register boundaries. A single relay layer exhibits the predicted minimax fanout optimum and removes a substantial fraction of the independently confirmed broadcast tax without requiring fully local nearest-neighbor transport.
