# Project SIMILARITY: corrected final-route causal law

Date: 2026-09-20

Status: preregistered experiment complete; all frozen criteria passed.

## Result

The corrected post-route study completed **96/96** ECP5 implementations. Every implementation mapped exactly one `MULT18X18D` per processing element, and all **13 preregistered gates passed**.

The result supports a narrow causal claim:

> Within the tested ECP5 INT8 MAC-fabric family, nonlocal operand broadcast introduces a size-dependent final-routed timing tax relative to registered nearest-neighbor transport. A differential law learned only from square arrays predicts the tax on unseen rectangular arrays and disjoint placement seeds without refitting.

This report replaces the historical SIMILARITY routed-law coefficients. Those coefficients were based on a worst-implementation-stage timing parser that often selected a post-placement estimate. Every value below comes only from nextpnr's post-route `--report` JSON.

## Frozen design

The discovery corpus contained square arrays and seeds 17, 18 and 19. The held-out corpus contained unseen rectangular arrays and seeds 20, 21 and 22. Both direct broadcast and registered nearest-neighbor topologies were routed on ECP5-25K, 45K and 85K targets.

The discovery model was frozen as:

```text
T = alpha_device
  + beta_b * sqrt(PE)
  + LOCAL * (delta_0 + delta_1 * sqrt(PE))
```

The fitted coefficients were:

```text
beta_b =  0.450257 ns / sqrt(PE)
delta_0 = 0.501805 ns
delta_1 = -0.300915 ns / sqrt(PE)
```

Therefore:

```text
broadcast slope = 0.450257 ns / sqrt(PE)
local slope     = 0.149343 ns / sqrt(PE)
predicted tax   = -0.501805 + 0.300915 * sqrt(PE) ns
```

The local slope is **33.17%** of the broadcast slope. Discovery-model RMSE was **0.1218 ns**.

## Held-out confirmation

No held-out point participated in fitting.

| Device | Geometry | Broadcast period (ns) | Local period (ns) | Observed tax (ns) | Predicted tax (ns) | Absolute error (ns) | Local improvement |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 25K | 3x7 | 10.3320 | 9.6290 | 0.7030 | 0.8772 | 0.1742 | 6.80% |
| 45K | 3x7 | 10.9410 | 9.6480 | 1.2930 | 0.8772 | 0.4158 | 11.82% |
| 45K | 5x9 | 11.7740 | 9.9900 | 1.7840 | 1.5168 | 0.2672 | 15.15% |
| 85K | 3x7 | 10.7520 | 9.8230 | 0.9290 | 0.8772 | 0.0518 | 8.64% |
| 85K | 5x9 | 11.8550 | 9.5830 | 2.2720 | 1.5168 | 0.7552 | 19.16% |
| 85K | 7x11 | 12.7190 | 10.4210 | 2.2980 | 2.1387 | 0.1593 | 18.07% |

Held-out performance:

- positive observed broadcast tax: **6/6** pairs;
- tax MAE: **0.3039 ns**;
- tax RMSE: **0.3815 ns**;
- predicted-versus-observed correlation: **0.8921**;
- predictions within +/-1.75 ns: **6/6** pairs;
- largest held-out geometry improvement: **18.07%**;
- ECP5-85K 11x11 discovery improvement: **21.00%**.

Median seed CV remained below the frozen 6% limit in every split and topology:

| Split | Broadcast | Local |
| --- | ---: | ---: |
| Discovery | 1.57% | 1.46% |
| Holdout | 1.62% | 2.21% |

## Preregistered gate

| Criterion | Outcome |
| --- | --- |
| At least 92/96 successful routes | PASS: 96/96 |
| Exact one-DSP-per-PE mapping | PASS |
| Median seed CV at most 6% | PASS |
| Broadcast slope at least 0.15 ns / sqrt(PE) | PASS: 0.4503 |
| Local slope at most 60% of broadcast slope | PASS: 33.17% |
| Negative topology-by-size interaction | PASS: -0.3009 |
| 85K 11x11 local improvement at least 12% | PASS: 21.00% |
| Positive tax on all held-out pairs | PASS: 6/6 |
| Held-out MAE at most 1.25 ns | PASS: 0.3039 ns |
| Held-out RMSE at most 1.50 ns | PASS: 0.3815 ns |
| Held-out correlation at least 0.70 | PASS: 0.8921 |
| At least five held-out errors within 1.75 ns | PASS: 6/6 |
| Held-out 85K 7x11 improvement at least 15% | PASS: 18.07% |

## Interpretation

The intervention changes operand-distribution topology while holding PE arithmetic and the one-DSP-per-PE mapping fixed. The strong slope suppression, positive tax on every held-out pair, and accurate out-of-sample differential prediction show that the observed size effect is not merely a post-hoc correlation with PE count.

The result is useful to Kernellum because it identifies a physical-design variable that an architecture search should model explicitly. Array size alone is insufficient. Operand-distribution topology changes how routed timing scales.

## Claim boundary

This experiment establishes a final-routed timing effect, not physical-board performance. It does not establish:

- universality across FPGA vendors, process nodes or unrelated RTL families;
- a substrate-independent absolute equation;
- lower end-to-end latency after accounting for pipeline fill and workload scheduling;
- power or energy improvement;
- superiority to production systolic-array implementations;
- a complete physical explanation of the routing tax.

The paired fabrics are diagnostic research structures. The next evidence step is to integrate locality as a compiler-controlled architecture choice in the functional Kernellum GEMM engine, then test whether the predicted timing advantage survives correctness checks, complete kernel scheduling and workload-level latency accounting.

## Reproduction record

- frozen plan: `docs/SIMILARITY_ROUTED_LAW_PLAN.md`
- route driver: `scripts/similarity_routed_route.py`
- frozen validator: `scripts/similarity_routed_validate.py`
- raw 96-route table: `results/similarity_routed_law_combined.csv`
- machine-readable summary: `results/similarity_routed_law_summary.json`
- CI workflow: `.github/workflows/similarity-routed-law.yml`
- GitHub Actions run: `35498260194`

