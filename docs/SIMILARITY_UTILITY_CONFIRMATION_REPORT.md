# Project SIMILARITY: independent compiler-utility confirmation result

Date: 2026-09-20

Status: preregistered experiment complete; independent utility gate did not pass.

## Result

All **60/60** new ECP5 routes completed, all functional simulations passed, and every design retained exact one-DSP-per-PE mapping.

The median-route confirmation was strong:

- positive broadcast tax: **10/10** architecture pairs;
- short-K/long-K crossovers: **10/10**;
- zero-shot topology-choice accuracy: **88.89%**;
- mean synthetic decision regret: **0.56%**;
- law-guided local selection: **12/12** Transformer workloads;
- mean workload improvement: **24.05%**;
- mean oracle regret: **0.00%**;
- K_TILE=384 dominated K_TILE=192 in **4/5** matched geometry families.

Even though tax magnitude was not a gate, it improved on the prior corpus: zero-shot MAE was **1.0936 ns** and predicted-versus-observed correlation was **0.9074**.

The full confirmation is nevertheless a **null result**. Seed-isolated evaluation failed two all-required criteria. Seed 33 produced only **7.05%** mean improvement, below the frozen 8% floor, and **13.02%** mean oracle regret, above the frozen 7% ceiling.

## Per-seed result

| Seed | Guided local workloads | Non-worse workloads | Mean improvement | Mean oracle regret |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 12/12 | 12/12 | 26.11% | 0.00% |
| 33 | 12/12 | 12/12 | **7.05%** | **13.02%** |
| 34 | 12/12 | 12/12 | 10.71% | 0.27% |

Seed 33 did not invalidate local transport. It exposed architecture-selection noise. The one-shot compiler selected 11x13 K192 local from that seed's broadcast routes, while actual local timing favored 13x11 K192. The selected design still beat the best broadcast-only design on all 12 workloads, but missed the improvement and oracle-regret thresholds.

## Resource cost

Across the independent corpus, local transport used on average:

- **69.63% more flip-flops**;
- **0.00% additional block RAM**;
- the same DSP population.

## Frozen gate

| Criterion | Outcome |
| --- | --- |
| All functional simulations pass | PASS |
| At least 58/60 routes succeed | PASS: 60/60 |
| Exact one-DSP-per-PE mapping | PASS |
| Positive tax in at least 9/10 pairs | PASS: 10/10 |
| Median choice accuracy at least 85% | PASS: 88.89% |
| Median mean choice regret at most 3% | PASS: 0.56% |
| At least 8/10 actual crossovers | PASS: 10/10 |
| Median compiler selects local on 12/12 workloads | PASS |
| Median compiler non-worse on 12/12 workloads | PASS |
| Median mean workload improvement at least 10% | PASS: 24.05% |
| Median mean oracle regret at most 5% | PASS: 0.00% |
| Every seed mean improvement at least 8% | **FAIL: seed 33 = 7.05%** |
| Every seed mean oracle regret at most 7% | **FAIL: seed 33 = 13.02%** |
| Every seed selects local on at least 10/12 workloads | PASS: 12/12 each |
| K384 dominates K192 in at least 4/5 families | PASS: 4/5 |

## Scientific consequence

The median result independently replicates the co-design effect on unseen geometries and depths, but one-shot architecture selection is not robust to placement-seed noise. The supported narrower observation is:

> Broadcast timing plus the causal tax law reliably identifies local transport as the winning topology, but selecting the exact geometry and tile depth from a single routing seed can be unstable. Multi-seed physical characterization is necessary before freezing the architecture.

A leakage-free follow-up should use broadcast-only discovery seeds to select one fixed architecture/topology, then evaluate that frozen choice on disjoint deployment seeds. This separates architecture selection from outcome evaluation and directly tests whether multi-seed characterization removes the failure observed here.

## Claim boundary

This remains final-route evidence on one FPGA family. It does not establish board performance, power, energy, ASIC transfer, vendor independence or area-normalized superiority. The two failed per-seed criteria remain unchanged.

## Reproduction record

- frozen plan: `docs/SIMILARITY_UTILITY_CONFIRMATION_PLAN.md`
- route driver: `scripts/similarity_utility_route.py`
- frozen validator: `scripts/similarity_utility_validate.py`
- raw routes: `results/similarity_utility_combined.csv`
- machine-readable summary: `results/similarity_utility_summary.json`
- CI workflow: `.github/workflows/similarity-utility-confirmation.yml`
- GitHub Actions run: `35523402600`
