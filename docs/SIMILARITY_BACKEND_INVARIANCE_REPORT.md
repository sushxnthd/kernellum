# Project SIMILARITY: compute-backend invariance result

Date: 2026-09-20

## Result

The preregistered compute-backend invariance gate **FAILED**.

All **48/48 routes succeeded**. DSP designs mapped exactly one MULT18X18D per PE and LUT-forced designs mapped zero DSP cells, so the arithmetic-backend intervention worked as intended.

The direction of the causal effect survived every test point: broadcast critical period was higher than registered-local period for all eight size/backend pairs.

However, the absolute DSP-derived differential equation did not transfer to LUT arithmetic.

## Frozen equation

The equation frozen from the independently confirmed DSP-backed studies was:

    delta_T =
      -1.7762324291
      + 0.8022441163 * sqrt(PE) ns.

### DSP contemporaneous control

| N | Observed tax (ns) | Frozen prediction (ns) | Error (ns) |
| --- | ---: | ---: | ---: |
| 3 | 0.2399 | 0.6305 | 0.3906 |
| 5 | 2.3999 | 2.2350 | 0.1650 |
| 7 | 4.3206 | 3.8395 | 0.4812 |
| 9 | 4.5606 | 5.4440 | 0.8834 |

### LUT-forced arithmetic

| N | Observed tax (ns) | Frozen prediction (ns) | Error (ns) |
| --- | ---: | ---: | ---: |
| 3 | 3.2238 | 0.6305 | 2.5933 |
| 5 | 6.1404 | 2.2350 | 3.9054 |
| 7 | 6.0760 | 3.8395 | 2.2365 |
| 9 | 9.7696 | 5.4440 | 4.3257 |

LUT frozen-equation metrics:

- MAE: **3.2652 ns**
- RMSE: **3.3797 ns**
- predicted-vs-observed correlation: **0.9422**
- points within +/-2.25 ns: **1/4**

Median seed CV:

- DSP broadcast: **1.20%**
- DSP local: **6.19%**
- LUT broadcast: **8.20%**
- LUT local: **4.96%**

The frozen seed-stability criterion therefore also failed for LUT broadcast.

## Descriptive post-gate fits

After the gate was scored, separate descriptive linear fits gave:

DSP:
    delta_T ~= -1.5845 + 0.7441 * sqrt(PE)

LUT:
    delta_T ~=  0.4305 + 0.9787 * sqrt(PE)

These are diagnostic only and cannot rescue the failed primary gate.

## Scientific consequence

The experiment rejects the strong claim that one additive DSP-derived broadcast-tax equation is invariant to the arithmetic substrate.

At the same time, it establishes a useful boundary condition:

> The *direction and size trend* of the communication-topology penalty survive a complete replacement of DSP multipliers by LUT multipliers, but its absolute magnitude is amplified and shifted by the implementation substrate.

The high LUT tax correlation (**0.942**) with the frozen size trend suggests that communication scaling and physical implementation load interact rather than acting as completely unrelated effects.

The next model must therefore allow the implementation substrate or congestion state to modulate the topology penalty.
