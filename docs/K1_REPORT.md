# Kernellum K1 Routed Architecture Validation

Date: 2026-09-19

## Result

**PASS** against the thresholds frozen in `docs/K1_PLAN.md` before the first place-and-route result was inspected.

K1 tested whether a simple fixed-frequency workload model can select accelerator architectures whose advantage survives real ECP5 synthesis and routing.

## Evidence chain

K1 now has a reproducible:

`Transformer GEMM -> architecture choice -> RTL -> functional simulation -> ECP5 synthesis -> place-and-route -> routed Fmax -> workload re-ranking`

pipeline.

The tiled GEMM engine supports packed A/B tile buffers, parameterized ROWS x COLS INT8 MAC arrays, runtime K length, controller-driven execution, and accumulation across multiple K chunks.

Functional self-checking simulation passed before routing was accepted.

## Frozen candidate set

Nine architectures were routed on an ECP5-85K / CABGA381 target.

| Architecture | PEs | K tile | Fmax (MHz) | DSP | BRAM | LUT4 | FF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4x4 | 16 | 16 | 44.04 | 16 | 2 | 175 | 597 |
| 4x8 | 32 | 32 | 42.43 | 32 | 3 | 211 | 1129 |
| 8x4 | 32 | 32 | 44.51 | 32 | 3 | 214 | 1138 |
| 8x8 | 64 | 16 | 39.61 | 64 | 4 | 243 | 2152 |
| 8x8 | 64 | 32 | 36.33 | 64 | 4 | 246 | 2173 |
| 8x8 | 64 | 64 | 33.17 | 64 | 4 | 253 | 2206 |
| 8x12 | 96 | 32 | 33.68 | 96 | 5 | 278 | 3203 |
| 12x8 | 96 | 32 | 32.63 | 96 | 5 | 281 | 3217 |
| 10x10 | 100 | 32 | 34.69 | 100 | 6 | 278 | 3336 |

All **9/9** candidates completed place-and-route.

## Predeclared gate

| Metric | Required | Observed |
| --- | ---: | ---: |
| Successful routes | >= 8 / 9 | **9 / 9** |
| DSP rank Spearman | >= 0.95 | **1.000** |
| Mean workload rank Spearman | >= 0.80 | **0.927** |
| Mean predicted-winner routed regret | <= 15% | **1.00%** |
| Predicted winners must route | yes | **yes** |

**K1 gate: PASS.**

## Physical-design effects were real

The routing results are not a trivial restatement of PE count.

Equal-PE orientation pairs produced different Fmax:

- 4x8: 42.43 MHz
- 8x4: 44.51 MHz
- 8x12: 33.68 MHz
- 12x8: 32.63 MHz

Buffer depth also changed timing with the same 8x8 array:

- K_TILE 16: 39.61 MHz
- K_TILE 32: 36.33 MHz
- K_TILE 64: 33.17 MHz

So the routed feedback genuinely contains information absent from the fixed-frequency analytical model.

## Workload-selection result

Across 12 Transformer GEMMs, the fixed-frequency architecture ranking retained a mean Spearman correlation of 0.927 with the routed-Fmax ranking.

The analytically selected winner was only 1.00% slower than the true routed winner on average.

For 8 of 12 workloads the predicted winner was also the routed winner. The four misses were small and came from the 8x12 versus 10x10 tradeoff; routed regret on each miss was about 3%.

## Target-aware ECP5 calibration

DSP prediction remained exact: one PE mapped to one MULT18X18D for the frozen INT8 design family.

The tile buffers also expose a clean ECP5 memory rule for the current depth regime. For K_TILE <= 512, each DP16KD can supply up to a 36-bit word, so:

`predicted DP16KD = ceil(ROWS*8/36) + ceil(COLS*8/36)`

This exactly matches the nine K1 synthesis results.

## What K1 establishes

1. Kernellum's first tiled GEMM engine is functionally executable.
2. The engine synthesizes and routes across multiple architecture geometries.
3. Resource scaling is predictable for the frozen design family.
4. Physical timing changes architecture ranking in measurable ways.
5. The simple analytical model remains highly correlated with routed ranking.
6. The analytically selected architecture remains near the routed optimum.

## What K1 does not establish

K1 does not establish measured board latency, power, energy, thermal behavior, end-to-end Transformer inference, ASIC performance, or commercial superiority.

## Next technical step

The next system layer is a closed-loop physical-design search:

1. fit a target-aware Fmax/resource surrogate from routed observations;
2. enumerate a larger architecture pool;
3. select the next architecture to route using predicted workload latency plus uncertainty;
4. ingest the new route;
5. refit;
6. repeat until the physical-design budget is exhausted.

That is the point where Kernellum stops merely validating an analytical search and starts learning from real physical implementation feedback.
