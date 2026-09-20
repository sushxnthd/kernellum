# Project SIMILARITY: functional-transfer result

Date: 2026-09-20

Status: preregistered experiment complete; functional-transfer gate did not pass.

## Result

The functional experiment completed all **54/54** final-route ECP5 implementations. Broadcast and registered nearest-neighbor engines produced bit-exact signed INT8 results, including negative outputs, edge values and accumulation without clearing. Every route mapped exactly one `MULT18X18D` per processing element.

The diagnostic timing law transferred accurately to the functional GEMM engine:

- positive observed broadcast tax: **9/9** architecture pairs;
- zero-shot tax MAE: **0.8582 ns**;
- zero-shot tax RMSE: **0.9559 ns**;
- predicted-versus-observed tax correlation: **0.9150**;
- maximum per-point seed CV: **5.08%**.

However, the full compiler-level claim is a **null result**. The frozen law-guided policy selected broadcast for all 81 architecture/K cases. Actual routed timing produced local-transport winners in 18 cases, so choice accuracy was **77.78%**, below the preregistered 85% requirement. On the 12 Transformer GEMMs, the law-guided compiler matched the broadcast-only baseline and delivered **0.00%** mean improvement, below the required 3%.

The experiment passed 11 of 13 criteria. Because every criterion was required, the functional-transfer gate failed.

## Functional timing pairs

| Architecture | Broadcast period (ns) | Local period (ns) | Observed tax (ns) | Predicted tax (ns) | Local Fmax gain |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4x4, K16 | 17.5860 | 16.0770 | 1.5090 | 0.7019 | 9.39% |
| 4x8, K32 | 18.4920 | 16.8780 | 1.6140 | 1.2004 | 9.56% |
| 8x4, K32 | 18.4170 | 16.7180 | 1.6990 | 1.2004 | 10.16% |
| 8x8, K16 | 20.2540 | 17.2070 | 3.0470 | 1.9055 | 17.71% |
| 8x8, K64 | 19.9030 | 17.3700 | 2.5330 | 1.9055 | 14.58% |
| 8x12, K32 | 20.6260 | 17.5220 | 3.1040 | 2.4465 | 17.71% |
| 12x8, K32 | 21.3280 | 17.0030 | 4.3250 | 2.4465 | 25.44% |
| 10x12, K64 | 21.1480 | 17.6630 | 3.4850 | 2.7946 | 19.73% |
| 12x10, K64 | 21.2170 | 17.4130 | 3.8040 | 2.7946 | 21.85% |

## Frozen gate

| Criterion | Outcome |
| --- | --- |
| Exact-output broadcast and local simulations | PASS |
| At least 52/54 successful routes | PASS: 54/54 |
| Exact one-DSP-per-PE mapping | PASS |
| Maximum seed CV at most 8% | PASS: 5.08% |
| Positive tax in at least 7/9 pairs | PASS: 9/9 |
| Zero-shot tax MAE at most 1.50 ns | PASS: 0.8582 ns |
| Tax correlation at least 0.60 | PASS: 0.9150 |
| Topology-choice accuracy at least 85% | **FAIL: 77.78%** |
| Mean topology-choice regret at most 3% | PASS: 0.83% |
| At least one short-K/long-K crossover | PASS: 3 architectures |
| Guided compiler non-worse on at least 10/12 workloads | PASS: 12/12 |
| Mean workload improvement at least 3% | **FAIL: 0.00%** |
| Mean oracle regret at most 5% | PASS: 2.91% |

## What failed

The timing law was useful but conservative. It underpredicted the functional broadcast tax in every tested pair. More importantly, the candidate architecture space coupled the largest arrays to `K_TILE=64`. For those designs, local transport pays `ROWS + COLS - 1` drain cycles per 64-wide K chunk.

The frozen equation therefore predicted that the clock gain would not repay the wavefront cost and chose broadcast in all 81 synthetic cases. Actual timing was stronger than predicted and made local transport win for `K >= 64` on the 8x8 K64, 10x12 K64 and 12x10 K64 designs. Those 18 misses account for the entire policy-accuracy failure.

For the Transformer suite, the oracle selected the 10x12 K64 local design on all 12 workloads, but its mean advantage over the best broadcast design was only about 2.91%. The law-guided compiler retained broadcast, producing zero gain and the same 2.91% mean oracle regret.

## Scientific consequence

The experiment supports a narrower result than the preregistered claim:

> A causal broadcast-tax law learned from diagnostic routed fabrics transfers zero-shot to a functionally correct GEMM engine with sub-nanosecond mean error and strong correlation, but timing prediction alone does not guarantee useful topology choices when wavefront drain is not jointly amortized by tile depth.

The next defensible experiment is not a coefficient refit. It is a new preregistered architecture intervention: hold the timing law and functional transport RTL fixed, increase K tile depth on unseen geometries and seeds, and test whether joint topology/tile-depth search converts the predicted clock advantage into held-out workload latency improvement.

## Claim boundary

This remains final-route evidence on one FPGA family and does not establish board performance, power, energy, ASIC transfer or vendor independence. The two failed criteria are retained as a null result; no threshold or result is revised.

## Reproduction record

- frozen plan: `docs/SIMILARITY_FUNCTIONAL_TRANSFER_PLAN.md`
- functional local array: `rtl/kernellum_local_mac_array.sv`
- route driver: `scripts/similarity_functional_route.py`
- frozen validator: `scripts/similarity_functional_validate.py`
- raw route table: `results/similarity_functional_combined.csv`
- machine-readable summary: `results/similarity_functional_summary.json`
- CI workflow: `.github/workflows/similarity-functional-transfer.yml`
- GitHub Actions run: `35514955683`
