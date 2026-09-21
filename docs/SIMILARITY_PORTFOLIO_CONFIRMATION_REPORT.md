# Project SIMILARITY: two-candidate physical-feedback confirmation result

Date: 2026-09-21

Status: preregistered experiment complete; **all 13 confirmation criteria passed**.

## Result

The experiment completed **72/72** new final-route ECP5 implementations. All functional simulations passed, and every implementation retained exact one-DSP-per-PE mapping.

The portfolio was constructed using only median broadcast timing from selection seeds 41, 42 and 43 plus the unchanged causal topology law. For each workload it retained two local candidates. On disjoint deployment seeds 44, 45 and 46, the policy inspected final-route local timing for only those two members and selected the faster workload implementation. All other deployment routes were hidden from the choice and used only to measure the oracle afterward.

The prospective result passed every frozen gate:

- frozen portfolio choices beat the best broadcast-only implementation in **36/36** deployment workload/seed cases;
- overall mean improvement over the best broadcast-only architecture was **23.56%**;
- overall mean regret versus the full routed oracle was **1.44%**;
- per-seed mean oracle regret was at most **3.58%**, below the 5% ceiling;
- the second-ranked member was selected in **21/36** deployment cases;
- the portfolio reduced mean oracle regret by **2.15 percentage points** versus using rank 1 alone;
- all **8/8** architecture pairs had positive median broadcast tax.

This is an independent confirmation on geometries, PE counts, K depths and route seeds absent from the prior utility studies.

## Per-seed deployment result

| Deployment seed | Non-worse workloads | Mean improvement | Mean oracle regret | Rank-2 choices |
| ---: | ---: | ---: | ---: | ---: |
| 44 | 12/12 | 20.00% | 3.58% | 3/12 |
| 45 | 12/12 | 20.16% | 0.43% | 9/12 |
| 46 | 12/12 | 30.54% | 0.30% | 9/12 |

Across individual workload/seed cases, improvement ranged from **15.45% to 33.90%**. Maximum individual oracle regret was **6.54%**. The preregistered regret gates apply to per-seed and overall means, both of which passed.

## Portfolio effect

The rank-1-only policy already produced a substantial result:

- mean improvement: **21.12%**;
- mean oracle regret: **3.58%**.

Resolving the frozen two-member portfolios with their own local route timing improved those outcomes to:

- mean improvement: **23.56%**;
- mean oracle regret: **1.44%**.

The second member was not decorative. It won 21 cases, including 9/12 workloads on each of seeds 45 and 46. The result therefore supports the proposed mechanism: a small physical-feedback budget absorbs placement-and-routing variation that a single fixed architecture cannot.

## Resource cost

Across the independent corpus, local transport used on average:

- **70.57% more flip-flops**;
- **0.00% additional block RAM**;
- the same DSP population.

The latency gain is not area-free. Registered local movement trades sequential logic for a shorter routed critical path.

## Frozen gate

| Criterion | Outcome |
| --- | --- |
| All functional simulations pass | PASS |
| At least 70/72 routes succeed | PASS: 72/72 |
| Exact one-DSP-per-PE mapping | PASS |
| Every workload has two distinct local candidates | PASS: 12/12 |
| Positive tax in at least 7/8 architecture pairs | PASS: 8/8 |
| Every deployment seed is non-worse on 12/12 workloads | PASS |
| Every deployment seed mean improvement at least 8% | PASS: minimum 20.00% |
| Overall mean improvement at least 10% | PASS: 23.56% |
| Every deployment seed mean oracle regret at most 5% | PASS: maximum 3.58% |
| Overall mean oracle regret at most 3% | PASS: 1.44% |
| Rank-2 member selected at least once | PASS: 21/36 cases |
| Regret reduction versus rank 1 at least 1.0 percentage point | PASS: 2.15 points |
| Resource overhead reported | PASS |

## Supported claim

The prospectively supported result is:

> In this functional ECP5 INT8 GEMM family, a two-candidate architecture portfolio constructed from broadcast-only multi-seed characterization and a frozen causal topology law converts bounded local physical feedback into route-seed-robust workload choices. Across 36 unseen deployment cases, it delivered 23.56% mean latency improvement over the best broadcast-only architecture at 1.44% mean regret to the full routed oracle.

This is stronger than the preceding single-choice result because it tests and confirms the operational response to irreducible CAD variability rather than silently averaging it away.

## Claim boundary

This is final-route evidence on one FPGA family. Latency is derived from the functional cycle model and final-routed Fmax, not measured on a physical board. The result does not establish power, energy, ASIC transfer, vendor independence, end-to-end model inference or area-normalized superiority.

Within that boundary, this is a successful independent, preregistered confirmation of a new architecture-selection protocol.

## Reproduction record

- frozen plan: `docs/SIMILARITY_PORTFOLIO_CONFIRMATION_PLAN.md`
- route driver: `scripts/similarity_portfolio_route.py`
- frozen validator: `scripts/similarity_portfolio_validate.py`
- raw routes: `results/similarity_portfolio_combined.csv`
- frozen portfolios: `results/similarity_portfolio_selections.csv`
- per-seed outcomes: `results/similarity_portfolio_seed_summary.csv`
- workload outcomes: `results/similarity_portfolio_workloads.csv`
- architecture pairs: `results/similarity_portfolio_pairs.csv`
- machine-readable summary: `results/similarity_portfolio_summary.json`
- CI workflow: `.github/workflows/similarity-portfolio-confirmation.yml`
- GitHub Actions run: `35525687973`
