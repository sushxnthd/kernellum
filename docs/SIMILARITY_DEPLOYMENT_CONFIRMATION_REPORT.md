# Project SIMILARITY: leakage-free deployment confirmation result

Date: 2026-09-20

Status: preregistered experiment complete; leakage-free deployment gate did not pass.

## Result

All **72/72** new final-route ECP5 implementations completed, all functional simulations passed, and every design retained exact one-DSP-per-PE mapping. The compiler selected configurations from median broadcast-only timing on seeds 35, 36 and 37, then deployed that frozen mapping on disjoint seeds 38, 39 and 40 without observing local timing or deployment-seed timing during selection.

The held-out deployment result was strong:

- local transport selected for **12/12** workloads;
- positive median broadcast tax in **8/8** architecture pairs;
- frozen selections were no worse than the best broadcast-only design in **36/36** deployment cases;
- mean held-out workload improvement: **21.54%**;
- overall mean oracle regret: **3.90%**;
- every deployment seed exceeded the frozen **8%** mean-improvement floor;
- all resource and exact-DSP checks passed.

The complete confirmation is nevertheless a **null result** because every preregistered criterion was required. Seed 38 produced **8.18%** mean oracle regret, above the frozen 7% per-seed ceiling. In addition, only **2/3** K=1200 feed-forward contraction workloads selected K_TILE=448; the sequence-64 contraction selected K_TILE=320.

## Per-seed deployment result

| Deployment seed | Non-worse workloads | Mean improvement | Mean oracle regret |
| ---: | ---: | ---: | ---: |
| 38 | 12/12 | 14.74% | **8.18%** |
| 39 | 12/12 | 25.02% | 2.92% |
| 40 | 12/12 | 24.86% | 0.59% |

The seed-38 miss was not a topology failure: the frozen local selections still beat the best broadcast-only option for every workload. It was an exact-architecture miss. Selection chose 13x10 K320 for most workloads, while seed 38's routed local oracle favored 13x10 K448, yielding roughly 9.23% regret on those cases.

## Frozen selection mapping

| Workload class | Selected configuration |
| --- | --- |
| All QKV, attention-output and FFN-expand workloads | 13x10, K_TILE=320, local |
| Sequence-64 FFN-contract | 13x10, K_TILE=320, local |
| Sequence-128 and sequence-256 FFN-contract | 10x13, K_TILE=448, local |

The deep-selection gate failed because the short sequence-64 FFN contraction did not amortize K_TILE=448 under the frozen compiler objective. That criterion remains unchanged.

## Resource cost

Across the held-out corpus, local transport used on average:

- **69.51% more flip-flops**;
- **0.00% additional block RAM**;
- the same DSP population.

## Frozen gate

| Criterion | Outcome |
| --- | --- |
| All functional simulations pass | PASS |
| At least 70/72 routes succeed | PASS: 72/72 |
| Exact one-DSP-per-PE mapping | PASS |
| Selection compiler chooses local on 12/12 workloads | PASS |
| Positive tax in at least 7/8 pairs | PASS: 8/8 |
| Every deployment seed is non-worse on 12/12 workloads | PASS |
| Every deployment seed mean improvement at least 8% | PASS: minimum 14.74% |
| Overall mean improvement at least 10% | PASS: 21.54% |
| Every deployment seed mean oracle regret at most 7% | **FAIL: seed 38 = 8.18%** |
| Overall mean oracle regret at most 5% | PASS: 3.90% |
| All three K=1200 FFN contractions choose K448 | **FAIL: 2/3** |
| Resource overhead reported | PASS |

## Scientific consequence

This prospective experiment removes the leakage concern from the earlier post-hoc observation. Broadcast-only characterization on three routes selected local configurations that delivered double-digit average gains on three entirely disjoint deployment routes, and all 36 deployed workload cases beat their broadcast-only baselines.

It does **not** establish the full preregistered claim. Exact architecture/depth selection remains sensitive enough to placement that one deployment seed exceeded the per-seed oracle-regret bound, and the universal deep-FFN selection prediction was false for the shortest sequence.

The supported narrower observation is:

> Multi-seed broadcast-only physical characterization plus the causal topology law selects functional local-transport accelerator configurations that reproducibly outperform broadcast-only designs on unseen routes, but it does not yet select the routed local oracle within 7% on every seed.

## Claim boundary

This is final-route evidence on one FPGA family. It does not establish board performance, power, energy, ASIC transfer, vendor independence or area-normalized superiority. The two failed criteria remain recorded without threshold or analysis changes.

## Reproduction record

- frozen plan: `docs/SIMILARITY_DEPLOYMENT_CONFIRMATION_PLAN.md`
- route driver: `scripts/similarity_deployment_route.py`
- frozen validator: `scripts/similarity_deployment_validate.py`
- raw routes: `results/similarity_deployment_combined.csv`
- frozen selections: `results/similarity_deployment_selections.csv`
- per-seed outcomes: `results/similarity_deployment_seed_summary.csv`
- workload outcomes: `results/similarity_deployment_workloads.csv`
- architecture pairs: `results/similarity_deployment_pairs.csv`
- machine-readable summary: `results/similarity_deployment_summary.json`
- CI workflow: `.github/workflows/similarity-deployment-confirmation.yml`
- GitHub Actions run: `35524429889`
