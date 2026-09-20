# Project SIMILARITY: registered relay hierarchy result

Date: 2026-09-20

## Result

The preregistered registered-relay hierarchy gate **FAILED**.

All **54/54 routes succeeded**, every successful implementation mapped exactly one MULT18X18D per PE, and median seed CV was **4.22%**. The null result is therefore not explained by routing failures or an unstable intervention.

## Frozen mechanism test

The relay model used the maximum unregistered stage fanout

    M(F) = max(F, N/F)

where F is relay-to-PE group width.

The fitted model was:

    T_relay = alpha_N + beta * M(F)

with:

- beta = **0.01925 ns per unit M**
- RMSE = **0.3581 ns**

The coefficient was positive and the model fit relay points compactly, but reducing M did not reproduce the benefit of nearest-neighbor transport.

## Matched topology results

| N | Direct period (ns) | Local period (ns) | Direct tax (ns) | Best minimax relay (ns) | Relay tax (ns) | Direct tax removed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 13.5667 | 11.1669 | 2.3997 | 13.8064 | 2.6395 | **-9.99%** |
| 8 | 14.8876 | 10.4471 | 4.4405 | 15.4871 | 5.0399 | **-13.50%** |
| 10 | 16.9262 | 11.4064 | 5.5198 | 18.0083 | 6.6019 | **-19.60%** |

A negative "tax removed" value means the relay topology was worse than direct broadcast relative to the same local baseline.

## Frozen gate failures

The following preregistered criteria failed:

- extreme relay choices were >=2% slower than the minimax relay in only **1/3** sizes, not >=2/3;
- the best relay removed >=40% of the direct broadcast tax in **0/3** sizes;
- at N=10 the best relay period was not <=85% of direct broadcast period.

The minima did fall inside the preregistered minimax-optimal fanout sets for all three sizes, but this small within-relay effect is insufficient to explain the large direct-vs-local timing gap.

## Scientific consequence

This experiment rejects a strong candidate mechanism:

> The independently confirmed broadcast timing tax is not explained by maximum logical fanout between register boundaries alone, and adding one balanced registered relay level does not recover the timing benefit of a physically local nearest-neighbor graph.

This is an important constraint on the mechanism. Direct broadcast, bounded relay broadcast, and local propagation differ not only in fanout and register depth, but also in how their communication graphs can be embedded into the FPGA routing fabric.

The next experiment therefore matches fanout at exactly one and matches PE/register resources while changing only the spatial communication graph.
