# Project SIMILARITY: fixed-PE communication-diameter stress test

Date: 2026-09-20

## Result

The preregistered **communication-diameter gate FAILED**.

This is a clean falsification of the simple hypothesis that the confirmed square-root timing relation is explained primarily by

`D = max(ROWS, COLS)`

when PE count is held fixed.

All **66/66** routes succeeded and every successful implementation mapped exactly one ECP5 MULT18X18D per PE, so the null result is not caused by missing data or resource-mapping failures.

## Frozen-model result

The preregistered fixed-effect model estimated:

- broadcast span slope: **0.0341 ns per unit D**
- local span slope: **0.00930 ns per unit D**
- topology interaction: **-0.0248 ns per unit D**
- model RMSE: **0.474 ns**

The required broadcast slope was at least 0.15 ns per unit D. It did not pass.

## Rank tests

Broadcast Spearman correlation between critical period and D:

- P=64: **0.865**
- P=96: **0.061**

The P=96 group decisively rejects a monotonic diameter-only explanation.

## Compact versus elongated arrays

### P=64

Broadcast:

- compact 8x8: 15.246 ns
- elongated 2x32: 16.926 ns
- penalty: **11.02%**

The frozen threshold was 15%.

Local:

- compact 8x8: 10.567 ns
- elongated 2x32: 10.447 ns
- penalty: **-1.14%**

### P=96

Broadcast:

- compact 8x12: 17.406 ns
- elongated 4x24: 17.167 ns
- penalty: **-1.37%**

Local:

- compact 8x12: 10.567 ns
- elongated 4x24: 11.406 ns
- penalty: **7.94%**

The P=96 result has the opposite sign from the simple diameter prediction.

## Stability

Median seed coefficient of variation:

- broadcast: **1.85%**
- local: **3.82%**

The measurements are stable enough that placement-seed noise is not a plausible explanation for the failed diameter gate.

## Scientific consequence

The confirmed square-root law should **not** be described as a direct communication-diameter law.

For square broadcast arrays, several physical quantities grow together with array side length:

- driver fanout per operand net;
- number and spatial distribution of high-fanout nets;
- routing competition around hard DSP resources;
- physical span;
- placement constraints.

The fixed-PE experiment separates PE count from logical aspect ratio and shows that `max(ROWS,COLS)` alone is insufficient.

The next causal target is therefore **broadcast fanout / distribution structure**, not raw geometric diameter.

## Claim boundary

Supported:

> The original square-root timing relation is robust across device capacities and independent geometries, but a simple max-dimension communication-span model does not explain it.

Rejected:

> Critical period is generally affine in max(ROWS,COLS) at fixed PE count.

This null result is retained as part of the Project SIMILARITY evidence chain.
