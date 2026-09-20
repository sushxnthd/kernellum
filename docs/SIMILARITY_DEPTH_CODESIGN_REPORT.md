# Project SIMILARITY: transport and tile-depth co-design result

Date: 2026-09-20

Status: preregistered experiment complete; full co-design gate did not pass.

## Result

The experiment completed all **48/48** new final-route ECP5 implementations, and the unchanged broadcast, local and signed transport-equivalence simulations passed. Every successful design mapped exactly one `MULT18X18D` per processing element.

The architectural intervention produced the intended practical effect:

- all **8/8** architectures selected broadcast at short K and local transport at long K using actual timing;
- zero-shot topology-choice accuracy was **86.11%**;
- mean synthetic decision regret was **0.98%**;
- the law-guided compiler selected local transport on **12/12** Transformer workloads;
- it was no worse than the best broadcast-only design on **12/12** workloads;
- mean workload latency improved by **14.87%**;
- mean regret versus the routed oracle was **1.92%**;
- K_TILE=256 beat matched K_TILE=128 local transport in all **3/3** controlled geometry families.

Those results support the mechanism motivating the experiment: tile depth amortizes registered wavefront drain and converts the local topology's routed clock advantage into workload latency improvement.

The complete preregistered gate is nevertheless a **null result**. Maximum seed CV was **9.35%**, above the frozen 8% limit, and zero-shot tax MAE was **1.5703 ns**, above the frozen 1.50 ns limit. The experiment passed 13 of 15 criteria, but every criterion was required.

## Timing pairs

| Architecture | Broadcast period (ns) | Local period (ns) | Observed tax (ns) | Predicted tax (ns) | Local Fmax gain |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8x8, K128 | 19.8400 | 16.7860 | 3.0540 | 1.9055 | 18.19% |
| 8x8, K256 | 20.0100 | 17.1170 | 2.8930 | 1.9055 | 16.90% |
| 10x12, K128 | 21.8870 | 16.4550 | 5.4320 | 2.7946 | 33.01% |
| 10x12, K256 | 21.5560 | 16.9300 | 4.6260 | 2.7946 | 27.32% |
| 12x10, K128 | 21.3190 | 17.5170 | 3.8020 | 2.7946 | 21.70% |
| 12x10, K256 | 22.0650 | 16.8160 | 5.2490 | 2.7946 | 31.21% |
| 10x14, K256 | 21.3990 | 17.4690 | 3.9300 | 3.0587 | 22.50% |
| 14x10, K256 | 21.5300 | 16.8470 | 4.6830 | 3.0587 | 27.80% |

The diagnostic law remained directionally useful: broadcast tax was positive in **8/8** pairs and predicted-versus-observed correlation was **0.7260**. It was conservative, underpredicting the tax in every pair.

## Workload outcome

The law-guided compiler chose 10x14 K256 local transport for all 12 Transformer GEMMs. Per-workload improvement over the best broadcast-only architecture ranged from **14.17% to 16.93%**.

The routed oracle sometimes preferred 14x10 K256 local transport because placement outcomes differed by orientation. The law-guided choice still remained within **4.34%** of the oracle on every workload and within **1.92%** on average.

## Resource cost

Local transport used, on average:

- **69.00% more flip-flops** than matched broadcast designs;
- **0.00% additional block RAM**;
- the same one-DSP-per-PE arithmetic mapping.

The latency gain is therefore not free. Registered data movement trades sequential logic for a shorter routed critical path.

## Frozen gate

| Criterion | Outcome |
| --- | --- |
| All exact-output simulations pass | PASS |
| At least 46/48 successful routes | PASS: 48/48 |
| Exact one-DSP-per-PE mapping | PASS |
| Maximum seed CV at most 8% | **FAIL: 9.35%** |
| Positive tax in at least 7/8 pairs | PASS: 8/8 |
| Zero-shot tax MAE at most 1.50 ns | **FAIL: 1.5703 ns** |
| Tax correlation at least 0.60 | PASS: 0.7260 |
| Topology-choice accuracy at least 85% | PASS: 86.11% |
| Mean topology-choice regret at most 3% | PASS: 0.98% |
| At least 6/8 short-K/long-K crossovers | PASS: 8/8 |
| Guided compiler selects local on at least 10/12 workloads | PASS: 12/12 |
| Guided compiler non-worse on all workloads | PASS: 12/12 |
| Mean workload improvement at least 8% | PASS: 14.87% |
| Mean oracle regret at most 5% | PASS: 1.92% |
| K256 local dominates K128 local in all controlled families | PASS: 3/3 |

## Scientific consequence

The full calibration-and-stability claim failed, but every preregistered compiler-utility criterion passed. The supported observation is:

> Registered local transport and deeper K tiling are coupled architecture variables. In this functional ECP5 GEMM corpus, exposing both variables converts a zero-shot causal timing law into double-digit routed workload-latency gains, despite conservative tax-magnitude prediction.

An independent confirmation must now target this narrower decision-utility claim on new geometries, K depths and seeds. It should evaluate workload improvement separately at every route seed so the claim cannot depend on a favorable median, and it should retain the measured 69% sequential-logic cost.

## Claim boundary

This is final-route evidence on one FPGA family, not physical-board performance. It does not establish power, energy, ASIC transfer, vendor independence or superiority under an area-normalized objective. The two failed criteria are retained unchanged.

## Reproduction record

- frozen plan: `docs/SIMILARITY_DEPTH_CODESIGN_PLAN.md`
- route driver: `scripts/similarity_depth_route.py`
- frozen validator: `scripts/similarity_depth_validate.py`
- raw route table: `results/similarity_depth_combined.csv`
- machine-readable summary: `results/similarity_depth_summary.json`
- CI workflow: `.github/workflows/similarity-depth-codesign.yml`
- GitHub Actions run: `35515876774`
