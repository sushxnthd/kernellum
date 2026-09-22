# Project SIMILARITY: cross-technology ASIC transfer result

Date evaluated: 2026-09-22

Status: **preregistered claim rejected (16 of 18 frozen gates passed).**

## Verdict

The study does not support its all-or-nothing headline claim. All 96 planned
implementations completed, all ten RTL geometries passed signed-GEMM
equivalence, and the four unopened Sky130HD holdouts were predicted with a
mean absolute error of 0.0241 in the dimensionless timing effect. However, the
preregistered claim required every gate to pass. Two did not:

1. nine successful routes retained final capacitance and/or slew violations;
2. the six-point Sky130HD bridge rank correlation was 0.294, below the frozen
   0.60 threshold.

No threshold, geometry, seed, model or exclusion was changed after the data
were opened. The result is promising evidence for a transport-locality timing
effect, but it is not the preregistered cross-technology breakthrough claim.

## Prospective result

| Quantity | Result |
|---|---:|
| Planned / attempted / successful routes | 96 / 96 / 96 |
| Complete topology-matched seed pairs | 48 |
| Null routes | 0 |
| Median route-seed period CV | 0.949% |
| NanGate45 model intercept, alpha | 0.060714 |
| NanGate45 slope per sqrt(PE), beta | 0.007944 |
| Sky130HD calibration intercept | -0.007905 |
| Sky130HD calibration slope | 1.030300 |
| Sky130HD bridge Spearman correlation | 0.294245 |
| Holdout mean absolute error | 0.024123 |
| Frozen gates passed | 16 / 18 |

The four holdouts were not used to fit the NanGate45 law or the Sky130HD
calibration.

| Holdout | PE count | Observed local timing benefit | Predicted | Absolute error |
|---|---:|---:|---:|---:|
| 3x8 | 24 | 7.61% | 9.47% | 1.86 pp |
| 8x3 | 24 | 13.21% | 9.47% | 3.74 pp |
| 5x9 | 45 | 13.14% | 10.96% | 2.18 pp |
| 9x5 | 45 | 12.82% | 10.96% | 1.87 pp |

Every NanGate45 discovery point, every Sky130HD bridge point and every
Sky130HD holdout point had a positive median timing effect. Both 45-PE
holdouts exceeded the frozen 5% minimum by more than a factor of two. The
holdout magnitude gates passed comfortably, including the 8% MAE limit and
the 15-percentage-point per-holdout error limit.

## Failed gates

### Final electrical checks

Eighty-seven routes were clean. The following nine successful routes were
not, so the frozen requirement that every successful route have zero final
violations failed.

| Platform | Topology | Seed | Geometry | Final violation count |
|---|---|---:|---:|---|
| NanGate45 | broadcast | 29 | 6x3 | max capacitance: 1 |
| NanGate45 | broadcast | 29 | 7x7 | max capacitance: 1 |
| NanGate45 | broadcast | 47 | 7x7 | max capacitance: 1 |
| NanGate45 | local | 11 | 7x7 | max capacitance: 1 |
| NanGate45 | local | 29 | 3x6 | max capacitance: 1 |
| NanGate45 | local | 29 | 7x7 | max capacitance: 1 |
| Sky130HD | local | 11 | 7x7 | max slew: 1; max capacitance: 1 |
| Sky130HD | local | 29 | 7x7 | max slew: 39; max capacitance: 1 |
| Sky130HD | local | 47 | 7x7 | max slew: 6; max capacitance: 3 |

All 96 routes had zero final setup, hold, fanout and detailed-route DRC
violations. The failed electrical gate is not waived by that fact.

### Bridge rank transfer

The model used only sqrt(PE), so equal-PE transposes received equal
predictions. Sky130HD showed a material orientation effect in the bridge set:

| Bridge | PE count | Sky130HD observed benefit |
|---|---:|---:|
| 2x4 | 8 | 13.16% |
| 4x2 | 8 | 8.39% |
| 3x6 | 18 | 4.22% |
| 6x3 | 18 | 2.70% |
| 5x5 | 25 | 12.17% |
| 7x7 | 49 | 13.55% |

This produced a predicted-versus-observed Spearman correlation of 0.294. It
also identifies the next prospective model improvement: row/column
anisotropy must be modeled explicitly rather than inferred from PE count
alone. That hypothesis is post-result and is not counted as a finding of this
study.

## Frozen gate ledger

| Gate | Result |
|---|---|
| Functional equivalence | Pass |
| Exactly 96 unique attempts | Pass |
| At least 92 successful routes | Pass (96) |
| Every successful route electrically and DRC clean | **Fail** |
| All 16 geometry pairs have at least two complete seeds | Pass |
| Registered-local sequential structure retained | Pass |
| Median seed CV at most 6% | Pass (0.949%) |
| NanGate45 positive at least five of six | Pass (six of six) |
| NanGate45 size slope positive | Pass |
| NanGate45 7x7 effect at least 5% | Pass (11.05%) |
| Sky130HD bridge positive at least five of six | Pass (six of six) |
| Bridge Spearman at least 0.60 | **Fail (0.294)** |
| Calibration slope positive | Pass (1.030) |
| Holdout positive at least three of four | Pass (four of four) |
| Both 45-PE holdouts at least 5% | Pass (13.14%, 12.82%) |
| Holdout MAE at most 0.08 | Pass (0.0241) |
| Every holdout error at most 0.15 | Pass (maximum 0.0374) |
| Cost metrics complete | Pass |

## Provenance and evaluator recovery

- Preregistered source commit:
  `241fcda249ccc9fadf47ce880993d1fd18114607`.
- Physical study run:
  [GitHub Actions 35617268111](https://github.com/sushxnthd/kernellum/actions/runs/35617268111).
- Pinned OpenROAD Flow Scripts image:
  `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`.
- Route artifacts: IDs `10647893956`, `10648904205`, `10648966904`,
  `10649593165`, `10650070718`, `10650207065`, `10654973732`,
  `10656718843`, `10656873348`, `10657810230`, `10658510810` and
  `10658934600`; functional artifact `10646880445`.

Every physical matrix job succeeded. The original validation job failed
before evaluation because downloaded route CSVs retained an artifact-level
`results/` directory while the loader searched only its immediate input
directory. The recovery changes only file discovery from a one-level glob to
an exact-name recursive search. It does not change the frozen data,
calculations, thresholds or verdict. A dedicated evaluator-replay workflow
downloads the original run by ID and never invokes physical routing.

The committed evaluator outputs are:

| File | SHA-256 |
|---|---|
| `similarity_asic_transfer_summary.json` | `730320130729bfcc91c75f838678d97dd50540ebb18e284da5ab37f466471faf` |
| `similarity_asic_transfer_combined.csv` | `ba6394b79eea892ff6eea60c97694a953307b781b599ca60370b9676b3b81a05` |
| `similarity_asic_transfer_pairs.csv` | `e55b631412cbe093a312c7c47b1055d847e5257946558b401ceb9b5c7aa50226` |
| `similarity_asic_transfer_points.csv` | `e807e53e165dc56138c4155f494ced65e8a699ad5e0b477067c9b2976fdd62ed` |

## Claim boundary

The experiment covers functionally equivalent INT8 MAC arrays on two open
standard-cell platforms inside one pinned OpenROAD flow. It does not establish
process-node universality, foundry signoff, fabricated-silicon frequency,
voltage/temperature robustness, power, energy or workload-level superiority.
