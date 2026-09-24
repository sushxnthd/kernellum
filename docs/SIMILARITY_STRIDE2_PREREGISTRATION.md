# Project SIMILARITY: prospective stride-two transport gate

Status: **draft until the electrical repair canary and excluded pilot are
reviewed, then frozen by the merge commit before any eligible physical route.**

## Question and scope

In the same controlled signed INT8 MAC array, can registering operand transport
every two PE positions retain most of the period benefit of registering at
every PE while reducing its standard-cell area and sequential-cell cost? Can
it improve the product of final routed period and synthesis cell area relative
to both direct broadcast and full registered-local transport on unseen array
shapes and both open ASIC platforms?

A pass supports that limited three-topology claim in the pinned flow. It does
not establish power, energy, silicon frequency, place-and-route chip area,
commercial signoff, or a predictive cross-technology law. A failure of *any*
gate below is a prospective null for this claim, with all costs and failures
published; subsets cannot be promoted into a breakthrough.

## Prior evidence and quarantine

The electrical repair canary must pass all twelve routes on the old 7x7 shape
before the 7x7 stride-two pilot is merged. The pilot, too, is exploratory and
excluded even if it wins. All ten geometries in the earlier ASIC transfer
study, both 7x7 repair and stride-two canaries, their route seeds, and all
previous ECP5 observations are permanently excluded from this gate's fitting,
confirmation and estimated effect sizes. No pilot result will set a threshold
after the first eligible route starts. The previous size-only transfer result
failed its own frozen all-required gate; this is a new intervention and claim,
not a re-analysis that rescues it.

## Frozen intervention and functional check

The three top-level RTL designs are `similarity_asic_transfer_broadcast`,
`similarity_asic_transfer_local`, and `similarity_asic_transfer_stride2`.
They share the registered activity source, signed INT8 PE arithmetic, internal
accumulator observation and digest false path. The stride-two array places an
operand register per two adjacent PEs in each axis with complementary input
edge skew; full local places one at each PE, broadcast registers the source
once. Before routing, the testbench must pass two signed GEMM transactions
including clearing and rerunning on each of the four new shapes, comparing all
three arrays. A simulation pass is a functional prerequisite only.

## Corpus and physical settings

| Split | Geometries | Platforms | Seeds | Topologies | Routes |
|---|---|---|---|---|---:|
| Discovery | 4x7, 7x4 | NanGate45, Sky130HD | 53, 71, 89 | three | 36 |
| Sealed holdout | 5x8, 8x5 | NanGate45, Sky130HD | 53, 71, 89 | three | 36 |
| Total | four fresh shapes | two | three | three | **72** |

The discovery split permits diagnostics after the merge, but no new feature,
gate, topology, threshold or retry will be selected using holdouts. This
protocol uses no fitted regression or calibration. Both platforms are
independent strata of the same frozen gate; a cross-platform law is not
estimated. In particular the two transposed holdout geometries test a shape
perturbation at equal PE count, not a fresh workload portfolio.

Use the immutable image
`openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`.
NanGate45 uses the bundled typical library, Sky130HD the bundled
`sky130_fd_sc_hd__tt_025C_1v80` corner. The clock constraint is 20 ns, core
utilization 35%, placement density 0.50, and `GPL_RANDOM_SEED` and `GRT_SEED`
both take the planned seed. `CAP_MARGIN=20` and `SLEW_MARGIN=20` are applied to
all three topologies. The comparison uses the same post-CTS repair timing
setting, native physical flow, QEMU `max` x86-64 CPU final report, disabled
auxiliary Kepler LEC, final parser and timing fields as the previous ASIC
transfer study. Neither margin nor parser can be changed after merge without
terminating this preregistration and publishing the resulting null.

The GitHub pull request performs functional and validator preflights only;
the route matrix runs only after its scientific plan, code, matrix and gates
are merged to `main`. The checkout commit SHA, hashes of RTL/config/analysis
and plan, the pinned image, each route CSV and the full all-gates JSON are
published as artifacts. CSVs retain SHA-256 of nonempty GDS, ODB, SPEF and
netlist; small route reports and logs accompany them. Large design databases
are omitted from the artifacts to limit free-tier storage use.

## Estimands and all-required gates

For each platform, geometry and seed with three electrically clean routes,
let `B`, `L` and `S` denote broadcast, full-local and stride-two final
`clk period_min` from `6_finish.rpt`; let `A_B`, `A_L`, `A_S` be their synthesis
cell areas and `D_B`, `D_L`, `D_S` their sequential-cell counts. Compute

- full-local period benefit `q_L = (B-L)/B`;
- stride-two period benefit `q_S = (B-S)/B`;
- retained benefit `(B-S)/(B-L)`, defined only when `B>L`;
- stride-two area-normalized throughput ratios
  `B*A_B/(S*A_S)` and `L*A_L/(S*A_S)`.

Geometry values are medians of seed-paired ratios, with at least two complete
seeds. Area is *synthesis cell area*, so the ratios are a proxy and cannot be
called die-area or energy efficiency. Every one of these gates must pass:

1. Signed GEMM equivalence passes at all four shapes before any route.
2. Exactly 72 planned unique platform/topology/seed/geometry attempts exist.
3. All 72 routes finish with final setup, hold, slew, fanout, capacitance and
   detailed-route DRC counts zero; every physical artifact is nonempty and
   SHA-256 recorded; cells, DFFs, area, wirelength and final period are valid.
4. Each of eight platform/geometry combinations has at least two complete
   matched three-topology seeds.
5. All eight geometry medians have `q_L > 0`, confirming the comparison's
   full-local benefit in this prospective cohort.
6. On all 24 matched triples, `D_B < D_S <= 0.90*D_L`.
7. On all 24 matched triples, `A_S < A_L`.
8. Each of four holdout platform/geometry medians has `q_S >= 0.05`.
9. Each holdout median retains at least 60% of full-local period benefit.
10. In at least three of four holdout platform/geometry medians both
    area-normalized ratios exceed 1.0.
11. At least one of those joint density wins occurs in each platform.

The gate is applied by `scripts/similarity_stride2_validate.py` with no
adaptive exclusions. A physical failure stays in its planned CSV row and
fails the all-clean gate; an interrupted shard with no CSV fails the exact
attempts gate. Seed count is not replenished. All outcomes, including nulls,
periods, DFF counts, cell area, wirelength and the complete gate vector, are
reported regardless of overall pass/fail.

## Reproduction

```bash
PYTHONPATH=. python -m pytest -q tests/test_similarity_stride2_validate.py tests/test_similarity_asic_transfer.py tests/test_similarity_asic_repair_canary.py
PYTHONPATH=. python scripts/similarity_stride2_validate.py --input results/similarity_stride2_download
```

The prospective route workflow is
`.github/workflows/similarity-stride2-study.yml`; the frozen source is the
merge commit that starts its `push` run. Related historical records are
`docs/SIMILARITY_ASIC_TRANSFER_PREREGISTRATION.md`,
`docs/SIMILARITY_ASIC_TRANSFER_REPORT.md`, and
`docs/SIMILARITY_NEXT_BREAKTHROUGH.md`.
