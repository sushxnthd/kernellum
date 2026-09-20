# SIMILARITY geometric timing model

Date written: 2026-09-20

This note states the mechanistic model being tested by Project SIMILARITY. It is intentionally written before the broadcast-vs-local causal gate is evaluated.

## 1. Physical abstraction

Consider a regular two-dimensional processing-element fabric with:

- R rows;
- C columns;
- P = R*C processing elements;
- identical registered PE arithmetic;
- a clock period limited by the slowest register-to-register combinational path.

Let D denote the largest physical communication span, expressed in units proportional to PE pitch.

For a broadcast-fed row/column fabric, an operand source must reach sinks across a row or column. To first order,

    D_broadcast = Theta(max(R, C)).

For a roughly square fabric,

    R ~= C ~= sqrt(P),

so

    D_broadcast = Theta(sqrt(P)).

## 2. First-order delay model

For a fixed FPGA family and PE microarchitecture, decompose critical period as

    Tcrit = Tlocal + Tcomm + epsilon,

where:

- Tlocal is local register/arithmetic delay;
- Tcomm is the delay contribution of operand/control distribution;
- epsilon contains placement/routing variation and secondary effects.

Over a bounded range of routed spans, approximate communication delay by

    Tcomm ~= k * D.

Then

    Tcrit ~= a + k * max(R, C)

for broadcast-dominated rectangular fabrics.

For near-square fabrics this reduces to

    Tcrit ~= a + b * sqrt(P).

This gives a geometric interpretation of the empirically confirmed square-root law.

## 3. Local-propagation intervention

Now replace nonlocal broadcast with registered nearest-neighbor propagation.

Each operand travels through a sequence of registered links. The number of cycles required to traverse the array grows with distance, but the **combinational distance crossed in a single clock period** is bounded by one local hop.

Under the idealized model,

    D_local,clock = O(1),

therefore

    Tcrit_local ~= a_local + O(1)

with respect to array dimension, until secondary congestion/placement effects dominate.

This predicts:

1. broadcast critical period has a positive slope versus linear array dimension;
2. local registered propagation has a much smaller slope;
3. the slope difference grows in importance at large arrays;
4. local propagation can improve Fmax even though it adds pipeline latency;
5. at fixed PE count, elongated broadcast arrays should be slower than compact arrays if max(R,C) changes;
6. the corresponding aspect-ratio sensitivity should be substantially weaker with local propagation.

## 4. Relationship to the confirmed empirical law

The independently confirmed relation

    Tcrit ~= 14.104 + 1.723 * sqrt(P) ns

was obtained for a particular regular INT8 tiled ECP5 design family.

The geometric model does **not** assert that the numerical intercept or slope are universal constants.

The proposed invariant is the scaling structure:

    local arithmetic cost
    +
    communication-distance-dependent cost.

The square-root form is a special case created by two-dimensional near-square scaling.

## 5. Falsifiable consequences

The model is rejected or materially weakened if any of the following occur:

- local registered propagation retains essentially the same sqrt(P) slope as broadcast;
- fixed-PE aspect-ratio changes do not affect broadcast timing;
- communication span fails to predict timing better than PE count in deliberately elongated arrays;
- the effect disappears when arithmetic implementation changes while communication geometry is held fixed.

These consequences motivate the causal, arithmetic-backend, and future aspect-ratio experiments.

## 6. Claim boundary

This is a first-order physical model, not a transistor-level theorem.

FPGA routing delay is discrete, architecture-dependent and affected by congestion, dedicated hard-block placement, fanout buffering, clocking and CAD heuristics.

A successful experiment supports a geometric mechanism within the tested regime. It does not prove exact asymptotic behavior for arbitrary FPGA families or ASIC technologies.
