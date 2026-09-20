# Kernellum K1 Closed-Loop Physical-Design Search

Date: 2026-09-19

## Result

**PASS** against the criteria frozen in `docs/K1_CLOSED_LOOP_PLAN.md` before the eight new routes were executed.

Timing status: corrected on 2026-09-20 after rebuilding the nine-route baseline from nextpnr final post-route report JSON. The values below supersede the historical worst-implementation-stage timing results. See `docs/K1_FINAL_ROUTE_CORRECTION_REPORT.md`.

Kernellum used only the original nine routed K1 observations to choose four new architectures. A fixed-seed random arm received the same four-route budget.

## Budget

The frozen space contains **172** architectures.

- initial routed observations: 9
- active acquisitions: 4
- random controls: 4
- total physical implementations attempted: **17 / 172 = 9.88%**

The experiment therefore stayed below the preregistered 10% physical-design budget.

## Active choices

The routed-feedback selector chose:

- 10x12, K_TILE=64
- 10x12, K_TILE=32
- 12x10, K_TILE=64
- 8x14, K_TILE=64

All four synthesized and routed successfully.

## Random controls

With seed 20260919, the equal-budget random arm routed:

- 2x14, K_TILE=16
- 8x6, K_TILE=8
- 4x6, K_TILE=8
- 8x4, K_TILE=8

All four synthesized and routed successfully.

## Predeclared gate

| Metric | Required | Observed |
| --- | ---: | ---: |
| New routes successful | >= 7 / 8 | **8 / 8** |
| Physically attempted fraction | <= 10% | **9.88%** |
| Surrogate Fmax MAPE | <= 20% | **6.475%** |
| Active final mean latency vs random | <= random | **16.74 ms vs 19.44 ms** |
| Active workload improvements | >= random | **12 vs 0** |

**Closed-loop gate: PASS.**

## What the selector discovered

The active arm improved the best routed latency over the initial nine-design set on **all 12 Transformer GEMMs**.

The random arm improved the initial optimum on **0 of 12**.

Examples:

| Workload | Initial best | Active final best | Improvement |
| --- | ---: | ---: | ---: |
| s64 qkv | 8.790 ms | 7.506 ms | 14.6% |
| s128 qkv | 16.918 ms | 14.662 ms | 13.3% |
| s256 qkv | 33.835 ms | 29.324 ms | 13.3% |
| s128 FFN expand | 21.597 ms | 18.797 ms | 13.0% |
| s256 FFN contract | 44.177 ms | 37.489 ms | 15.1% |

These are cycle/final-route-Fmax estimates from the same K1 kernel model, not physical-board measurements.

## Physical feedback mattered

The active candidates were not simply "largest array wins."

The 10x12 designs used 120 DSPs, but K_TILE changed final-routed timing substantially:

- K_TILE 32: 45.37 MHz
- K_TILE 64: 41.95 MHz

Orientation also mattered at identical PE count and buffer depth: 10x12 K_TILE=64 reached 41.95 MHz, while 12x10 K_TILE=64 reached 44.80 MHz. The 8x14 K_TILE=64 design reached 45.77 MHz with 112 DSPs.

The surrogate's new-candidate final-route-Fmax MAPE was 6.475%, good enough to guide the acquisition but still imperfect. That uncertainty is precisely why Kernellum keeps routing selected designs and feeding the results back.

## What K1 now is

K1 is no longer only an analytical design-space search.

It now implements this loop:

`workload -> analytical candidates -> final-route-Fmax surrogate -> acquisition -> RTL -> synthesis -> place-and-route -> measured physical-design feedback -> updated search`

That loop is the core technical asset of the current Kernellum direction.

## Boundaries

This does not establish:

- board-measured latency;
- power or energy;
- thermal behavior;
- full Transformer end-to-end inference;
- ASIC transfer;
- novelty or patentability;
- superiority over mature commercial EDA systems.

## Next gate

The next meaningful step is **K2 / physical execution**: take one selected architecture to an actual FPGA board, measure clocked kernel latency and power, and compare those measurements against routed predictions. Only after that should Kernellum make hardware-performance claims.
