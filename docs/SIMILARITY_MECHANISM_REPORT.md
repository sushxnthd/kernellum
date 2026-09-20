# Project SIMILARITY: causal mechanism result

Date: 2026-09-20

## Result

The preregistered broadcast-vs-local causal mechanism gate **PASSED every criterion**.

The experiment attempted 60 routed implementations across ECP5-25K, 45K and 85K. **59/60 routes succeeded**, and every successful design mapped exactly one MULT18X18D per processing element.

## Frozen interaction model

The preregistered fixed-effect model estimated:

- broadcast slope: **1.0789 ns per sqrt(PE)**
- local registered-propagation slope: **0.2766 ns per sqrt(PE)**
- topology-by-size interaction: **-0.8022 ns per sqrt(PE)**
- model RMSE: **0.4108 ns**

Registered nearest-neighbor transport therefore suppressed the fitted size-dependent slope by approximately **74.4%** relative to broadcast.

## Large-array intervention

On ECP5-85K at 11x11:

- broadcast median critical period: **18.1882 ns**
- local median critical period: **11.4064 ns**
- period reduction: **37.29%**

The frozen threshold required at least 15%.

## Stability

Median per-point seed coefficient of variation:

- broadcast: **2.81%**
- local: **4.02%**

Both satisfy the preregistered <=5% stability threshold.

## Preregistered gate

| Criterion | Result |
| --- | --- |
| >=57/60 successful routes | PASS: 59/60 |
| one DSP per PE | PASS |
| broadcast slope >=0.50 ns/sqrt(PE) | PASS: 1.0789 |
| local slope <=50% of broadcast | PASS: 25.6% of broadcast |
| 85K 11x11 period improvement >=15% | PASS: 37.29% |
| median seed CV <=5% for both | PASS |
| negative topology-size interaction | PASS: -0.8022 |

**Overall: PASS.**

## Scientific consequence

The result supports the preregistered narrow causal claim:

> In this controlled ECP5 INT8 MAC fabric, the observed square-root timing penalty is substantially mediated by nonlocal row/column operand distribution; converting operand transport to registered nearest-neighbor propagation suppresses the scaling term.

This matters because PE count and arithmetic alone cannot explain the timing-size relationship: changing operand-distribution topology while retaining the same number and type of MAC processing elements materially changes both the slope and large-array critical period.

## Relationship to the fixed-PE diameter null result

The earlier fixed-PE experiment rejected a simple law based on `max(ROWS,COLS)`. The present pass therefore should **not** be interpreted as proof that logical array diameter itself is the sufficient variable.

Together, the experiments imply a narrower picture:

1. nonlocal broadcast-style distribution is a major mediator of the size-dependent timing penalty;
2. raw logical diameter alone does not explain the effect;
3. the deeper mechanism likely involves routed distribution topology, fanout, hard-block placement and congestion;
4. route-level critical-path decomposition is required before proposing a more specific invariant.

## Claim boundary

This result does not establish:

- a universal sqrt(PE) exponent;
- a universal FPGA timing law;
- that fanout alone is the mechanism;
- that max logical array dimension predicts timing;
- transfer to other FPGA vendors or ASIC processes.

The next mechanism study decomposes critical paths into logic and routing delay and identifies which signal classes dominate.
