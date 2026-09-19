# Kernellum K1 Closed-Loop Physical-Design Search

Date: 2026-09-19

## Result

**PASS** against the criteria frozen in `docs/K1_CLOSED_LOOP_PLAN.md` before the eight new routes were executed.

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
- 8x14, K_TILE=64
- 10x12, K_TILE=16

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
| Surrogate Fmax MAPE | <= 20% | **11.95%** |
| Active final mean latency vs random | <= random | **24.01 ms vs 26.61 ms** |
| Active workload improvements | >= random | **12 vs 0** |

**Closed-loop gate: PASS.**

## What the selector discovered

The active arm improved the best routed latency over the initial nine-design set on **all 12 Transformer GEMMs**.

The random arm improved the initial optimum on **0 of 12**.

Examples:

| Workload | Initial best | Active final best | Improvement |
| --- | ---: | ---: | ---: |
| s64 qkv | 12.154 ms | 10.529 ms | 13.4% |
| s128 qkv | 23.108 ms | 21.059 ms | 8.9% |
| s256 qkv | 46.217 ms | 42.118 ms | 8.9% |
| s128 FFN expand | 29.500 ms | 27.031 ms | 8.4% |
| s256 FFN contract | 60.343 ms | 54.132 ms | 10.3% |

These are routed-cycle/Fmax estimates from the same K1 kernel model, not physical-board measurements.

## Physical feedback mattered

The active candidates were not simply "largest array wins."

The 10x12 designs used 120 DSPs, but K_TILE changed routed timing substantially:

- K_TILE 16: 29.95 MHz
- K_TILE 32: 31.42 MHz
- K_TILE 64: 28.80 MHz

The 8x14 K_TILE=64 design reached 32.63 MHz with 112 DSPs.

The surrogate's new-candidate Fmax MAPE was 11.95%, good enough to guide the acquisition but clearly imperfect. That uncertainty is precisely why Kernellum keeps routing selected designs and feeding the results back.

## What K1 now is

K1 is no longer only an analytical design-space search.

It now implements this loop:

`workload -> analytical candidates -> routed-Fmax surrogate -> acquisition -> RTL -> synthesis -> place-and-route -> measured physical-design feedback -> updated search`

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
