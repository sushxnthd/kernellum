# K1 final-route timing correction report

Date: 2026-09-20

Status: complete; both unchanged gates passed.

## Audit finding

The original K1 routing scripts retained the minimum of all nextpnr console Fmax lines. Because nextpnr reports timing after placement and again after routing, the stored value was a reproducible worst-implementation-stage metric rather than an authoritative final-route metric.

The correction was frozen in `docs/K1_FINAL_ROUTE_CORRECTION_PLAN.md` before opening the new results. Architecture sets, workloads, target, package, placement seed, active budget, random seed and every gate threshold remained unchanged. Only the timing source changed to nextpnr's final `--report` JSON.

Functional simulation, synthesis, resource counts and route-success evidence were not invalidated by the audit. Timing-derived rankings, latency estimates, surrogate error and closed-loop comparisons were rerun.

## Corrected K1 result

All nine frozen architectures completed final-route measurement.

| Metric | Required | Corrected result |
| --- | ---: | ---: |
| Successful routes | at least 8/9 | **9/9** |
| DSP rank Spearman | at least 0.95 | **1.000** |
| Mean workload rank Spearman | at least 0.80 | **0.9441** |
| Mean predicted-winner regret | at most 15% | **0.5828%** |
| Every predicted winner routed | yes | **yes** |

The corrected K1 gate passed. The fixed-frequency predictor selected the final-route winner on 8/12 Transformer GEMMs. Its four misses each had 1.7485% regret.

The final-route Fmax range was 45.83 to 54.06 MHz across the nine architectures. Every route row records `timing_metric=post_route_report_json`.

## Corrected closed-loop result

The selector rebuilt its nine-observation baseline from corrected timing before choosing any new architecture.

Active choices:

- 10x12, K_TILE=64;
- 10x12, K_TILE=32;
- 12x10, K_TILE=64;
- 8x14, K_TILE=64.

The equal-budget random arm retained seed 20260919 and selected the same four random controls as the original experiment.

| Metric | Required | Corrected result |
| --- | ---: | ---: |
| New routes successful | at least 7/8 | **8/8** |
| Observed design-space fraction | at most 10% | **9.88%** |
| Surrogate final-route-Fmax MAPE | at most 20% | **6.4750%** |
| Active mean final-best latency | no worse than random | **16.7398 ms vs 19.4428 ms** |
| Workloads improved by active | at least random | **12 vs 0** |

The corrected closed-loop gate passed. The active arm's mean final-best latency was **13.90% lower** than the random arm's under the same four-route budget.

## What changed scientifically

The correction strengthens, rather than merely preserves, the main K1 conclusions:

- workload-ranking correlation increased from the historical 0.9274 to **0.9441**;
- mean predicted-winner regret decreased from 1.00% to **0.5828%**;
- closed-loop surrogate MAPE decreased from 11.95% to **6.4750%**;
- active search still improved all 12 workloads while random improved none.

Absolute latency values changed because final routed Fmax is higher than the historical worst-stage value. Historical absolute timing numbers and timing-derived comparisons are superseded by the corrected files committed with this report.

## Claim boundary

The corrected result establishes that the frozen analytical ranking and equal-budget active selector remain useful under final-route ECP5 timing for this design family. It does not establish physical-board latency, power, energy, thermal behavior, full Transformer inference, ASIC transfer, cross-vendor generality or superiority to commercial EDA systems.

## Evidence

- correction plan: `docs/K1_FINAL_ROUTE_CORRECTION_PLAN.md`
- corrected K1 routes: `results/k1_routes.csv`
- corrected workload rankings: `results/k1_workload_rankings.csv`
- corrected K1 gate: `results/k1_validation.json`
- corrected proposals: `results/k1_closed_loop_proposals.json`
- corrected new routes: `results/k1_closed_loop_routes.csv`
- corrected closed-loop gate: `results/k1_closed_loop_validation.json`
- K1 workflow run: `35508660108`
- closed-loop workflow run: `35508660102`

