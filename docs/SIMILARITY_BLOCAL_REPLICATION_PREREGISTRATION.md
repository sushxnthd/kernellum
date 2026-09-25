# SIMILARITY B-local transport: prospective replication protocol

Status: **draft until merged to main; no eligible physical route may precede that merge**.

## Exact question and prior-data quarantine

For signed INT8 MAC arrays under the pinned OpenROAD flow, does
B-local/A-sign-local operand transport on new 56-PE geometries preserve at
least 70% of the median full-local routed-period benefit over broadcast while
retaining a DFF and synthesis-cell-area reduction, with at least 1% median
period-times-synthesis-area improvement over both broadcast and full local on
at least three of four platform/geometry sealed-holdout groups?

This is a prospective replication after a reporting-pipeline repair. The
first 72-route prospective B-local study remains a preregistered null because
71 rather than 72 routes supplied complete final evidence. Its four holdout
groups were descriptively positive but cannot be reused. The opened-geometry
final-report canary subsequently showed that removing the optional GUI image
block allows the mandatory final report and products to finish. That canary is
implementation-fidelity evidence only.

No route, timing value or synthesis result from the geometries or seeds below
has been inspected before this protocol. All previously opened ASIC shapes
are excluded: 3x3, 7x7, 2x4, 4x2, 3x6, 6x3, 5x5, 3x8, 8x3, 5x9, 9x5,
4x7, 7x4, 5x8, 8x5, 6x8, 8x6, 6x9 and 9x6. All earlier ASIC route seeds,
including 11, 29, 47, 53, 71, 89, 101, 131, 157 and canary-only 173, are
excluded. Opened observations may inform this protocol's rationale but are
not part of its effect estimates or gates.

## Frozen source, repair and cohort

The architecture is unchanged from the first prospective study:

- `rtl/kernellum_blocal_mac_array.sv` SHA-256
  `7cdd3223ac401ec9c9df5a792cb41f2e754262dbd2c6fad103752fce7afdc766`
- `rtl/similarity_asic_transfer_blocal.sv` SHA-256
  `1f6bd084dab5e368f34dee5c44fb6ca12a68860b4b26fff2f78b85277d50552a`
- headless patch implementation `scripts/similarity_final_report_canary.py`
  SHA-256
  `5fb440ce9037a2efbf75be6ba82d366f184a53b858daca9e1ff97f582847ec17`

Candidate B bits and A[7] use distinct preserved per-PE registers. A[6:0]
and valid streams remain stride-two grouped. Broadcast and full-local controls
use the same clock, signed INT8 arithmetic and observable accumulator. The
only reporting-flow change relative to the null study is the canary-tested
replacement of exactly one optional GUI image block in `final_outputs.tcl`.
Every route shard records a patch manifest with the exact removed text,
replacement count, image digest, source SHA and before/after file hashes.

| Split | Geometries | Platforms | Seeds | Topologies | Routes |
| --- | --- | --- | --- | --- | ---: |
| Discovery | 5x10, 10x5 (50 PE) | NanGate45, Sky130HD | 181, 211, 239 | broadcast, local, blocal | 36 |
| Sealed holdout | 7x8, 8x7 (56 PE) | NanGate45, Sky130HD | 181, 211, 239 | broadcast, local, blocal | 36 |
| Total | 4 unopened shapes | 2 | 3 unused seeds | 3 | **72** |

The moderately elongated 50-PE discovery pair and near-square 56-PE sealed
holdout pair test both orientation and scale without exceeding the free-CI
route envelope already exercised by 54-PE arrays. Discovery observations can
aid diagnosis only after the cohort is complete. They cannot change sealed
holdout gates. No failed seed may be replaced and no selected route may be
rerun.

Signed-GEMM equivalence against full local must pass on all four shapes before
the physical jobs begin. The immutable OpenROAD-flow-scripts image is
`openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`.
The platforms are NanGate45 typical and Sky130HD typical
(`sky130_fd_sc_hd__tt_025C_1v80`). All topologies use a 20 ns clock, core
utilization 35%, placement density 0.50, `CAP_MARGIN=20`, `SLEW_MARGIN=20`,
the same post-CTS timing-repair setting, QEMU `max` final report and matching
`GPL_RANDOM_SEED=GRT_SEED` values. These are open PDK/library experiments on
free CI, not tapeout or signoff.

## Exact estimands

For each platform, geometry and seed, let `B`, `L` and `C` denote the final
routed `period_min` values for broadcast, full local and B-local. Let `A_B`,
`A_L`, `A_C` be their synthesis cell areas and `D_B`, `D_L`, `D_C` their
mapped DFF counts.

- Full-local benefit: `q_L=(B-L)/B`
- Candidate benefit: `q_C=(B-C)/B`
- Retained benefit: `(B-C)/(B-L)` when `B>L`
- Area-normalized throughput ratios: `B*A_B/(C*A_C)` and
  `L*A_L/(C*A_C)`

Each platform/geometry result is the median of the three seed-paired ratios,
not a ratio of medians. All three seeds are mandatory. The 1% density hurdle
requires each median ratio to be at least 1.01. Three seeds do not support a
confidence-interval claim.

## All-required gates

Every gate must pass:

1. Signed-GEMM equivalence passes on all four shapes before routing.
2. The evidence contains exactly 18 original route shards, 18 exact headless
   patch manifests, four functional logs, 72 unique attempted CSV rows, 72
   final critical-path reports and 72 driver logs. The recorded functional
   and manifest source SHAs must agree.
3. Every manifest proves exactly one replacement of the frozen optional GUI
   block in the pinned image, with valid and distinct before/after SHA-256
   values. Every driver reaches `native finish` with no signal 11 or `make`
   failure.
4. All 72 rows have zero final setup, hold, maximum-slew, maximum-fanout,
   maximum-capacitance and detailed-route DRC counts. Period, cells, DFFs,
   synthesis area and wirelength are positive. GDS, ODB, SPEF and netlist
   hashes are valid lowercase SHA-256 values. A successful process exit alone
   is insufficient.
5. All eight platform/shape groups contain three fully matched clean topology
   trios. Full local has strictly positive median period benefit over broadcast
   in every group.
6. In all 24 matched trios, `D_B < D_C <= 0.90*D_L` and `A_C < A_L`.
   Missing structural evidence or a dropped route fails this gate.
7. Each of the four sealed-holdout groups has median `q_C >= 0.05` and median
   retained benefit `>=0.70`.
8. At least three of four sealed-holdout groups have both median
   area-normalized throughput ratios `>=1.01`, including at least one group on
   each platform.
9. For each NanGate45 sealed-holdout shape, the median launch-register Q
   fanout across all three B-local maximum paths is `<=10`. Every maximum path
   must be parseable.

The frozen evaluator is
`scripts/similarity_blocal_replication_validate.py`. Failure of any gate is a
preregistered null for this exact claim. Preserve every artifact and report
every failed gate. Do not weaken thresholds, add or replace seeds, drop rows,
retry selected outcomes or reclassify an opened geometry as future
confirmation.

## Interpretation boundary

A pass would establish a reproducible, flow-specific comparison for this RTL
across two open standard-cell platforms and a second unseen cohort. It would
not by itself prove architectural novelty, silicon performance, energy saving
or workload-level utility. Local operand reuse and spatial dataflow are
established in Eyeriss, MAERI and TPU-style systolic architectures. Any later
scientific claim must first survive an audit of primary prior literature,
reproducibility and practical utility. No HAA admission or funding outcome is
promised.
