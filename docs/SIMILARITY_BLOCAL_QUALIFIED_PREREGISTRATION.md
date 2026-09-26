# SIMILARITY B-local: flow-qualified prospective protocol

Status: **draft until merged to main; no eligible physical route may precede that merge**.

## Exact question and quarantine

For signed INT8 MAC arrays under the qualified pinned OpenROAD flow, does the
unchanged B-local/A-sign-local transport reproduce a timing-versus-cost
advantage on four never-opened geometries and three unused seeds? Specifically,
the candidate must preserve at least 70% of full-local's median routed-period
benefit over broadcast, reduce mapped DFFs, synthesis cell area, post-route cell
area and holdout wirelength relative to full local, and beat both controls on
both synthesis-area-normalized and post-route-area-normalized throughput in at
least three of four sealed holdout groups. Every evidence, electrical, DRC,
antenna and headroom gate below is required.

This is a new prospective study, not a retry or repair of either earlier null.
The first B-local prospective study remains an evidence-completeness null. Its
distinct replication remains an electrical null. The later opened-data
electrical-margin and antenna-ratio-margin canaries qualify only the reporting
and physical flow; they do not rescue an old row or contribute an effect
estimate here.

No timing, area, power or route result from the geometries or seeds below has
been inspected. Repository-wide source search before freezing found none of the
four geometries or three seeds in any earlier SIMILARITY plan, runner,
workflow, result or test. All geometries and seeds named in earlier ASIC work
remain excluded, including canary-only seeds 173, 263 and 277. No failed row in
this study may be replaced or selectively rerun.

The explicit excluded-shape set is 3x3, 7x7, 2x4, 4x2, 3x6, 6x3, 5x5, 3x8,
8x3, 5x9, 9x5, 4x7, 7x4, 5x8, 8x5, 6x8, 8x6, 6x9, 9x6, 5x10, 10x5,
7x8 and 8x7. The explicit excluded-seed set is 11, 29, 47, 53, 71, 89, 101,
131, 157, 173, 181, 211, 239, 263 and 277. The frozen runner and tests encode
these disjointness checks.

## Frozen source, flow and cohort

The architecture is byte-identical to the prior B-local studies:

- `rtl/kernellum_blocal_mac_array.sv` SHA-256
  `7cdd3223ac401ec9c9df5a792cb41f2e754262dbd2c6fad103752fce7afdc766`;
- `rtl/similarity_asic_transfer_blocal.sv` SHA-256
  `1f6bd084dab5e368f34dee5c44fb6ca12a68860b4b26fff2f78b85277d50552a`.

Candidate B[7:0] and A[7] use distinct preserved per-PE registers. A[6:0] and
valid streams remain stride-two grouped. Broadcast and full-local controls use
the same signed arithmetic, clock and observable accumulator.

The qualified physical flow is also fixed: immutable image
`openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`,
NanGate45 typical and Sky130HD typical, 20 ns constraint, 35% core utilization,
0.50 placement density, `CAP_MARGIN=30`, `SLEW_MARGIN=25`, matching
`GPL_RANDOM_SEED`/`GRT_SEED`, the exact one-block headless final-report repair,
and pre-detailed-route `repair_antennas -ratio_margin 20`. Each shard records
both exact patch texts, counts, before/after hashes, image and source SHA.

| Split | Geometries | Platforms | Seeds | Topologies | Routes |
| --- | --- | --- | --- | --- | ---: |
| Discovery | 6x10, 10x6 (60 PE) | NanGate45, Sky130HD | 293, 317, 347 | broadcast, local, B-local | 36 |
| Sealed holdout | 7x10, 10x7 (70 PE) | NanGate45, Sky130HD | 293, 317, 347 | broadcast, local, B-local | 36 |
| Total | four never-opened shapes | two | three unused seeds | three | **72** |

The discovery pair may aid diagnosis only after all jobs finish. It cannot
change holdout gates. Signed-GEMM equivalence against full local must pass on
all four shapes before physical jobs start. These are free-CI, open-library
place-and-route experiments, not tapeout or signoff.

## Estimands

For each matched platform/shape/seed trio, let `B`, `L` and `C` be final routed
periods for broadcast, full local and B-local. Let `A^s` denote synthesis cell
area and `A^r` the final `Design area` reported after detailed routing. Define:

- candidate raw benefit: `q_C=(B-C)/B`;
- full-local raw benefit: `q_L=(B-L)/B`;
- retained benefit: `(B-C)/(B-L)` when `B>L`;
- synthesis-area-normalized throughput factors:
  `B*A_B^s/(C*A_C^s)` and `L*A_L^s/(C*A_C^s)`;
- routed-area-normalized throughput factors:
  `B*A_B^r/(C*A_C^r)` and `L*A_L^r/(C*A_C^r)`.

Each platform/geometry result is the median of three seed-paired values, never
a ratio of medians. All seeds are mandatory. A normalized win requires both
control factors to be at least 1.01. Three seeds provide repeatability and sign
consistency checks, not a confidence-interval or population claim.

The final report's vectorless total-power estimate is captured for every row so
power implications cannot be hidden. It has no workload activity file and is
therefore descriptive only: it is not an energy gate or evidence of measured
power, energy per operation, thermal behavior or battery/system efficiency.

## All-required frozen gates

Every gate must pass:

1. Signed-GEMM equivalence passes on all four shapes before routing.
2. Evidence contains exactly 18 original route shards, 18 exact two-patch
   manifests, four functional logs, 72 unique attempted rows, 72 finish
   reports, 72 native driver logs, 72 route logs and 72 DRC reports. Source and
   manifest SHAs agree.
3. Every driver reaches native finish with no signal 11 or make failure. Every
   row has nonempty hashed GDS/ODB/SPEF/netlist products and positive timing,
   synthesis area, routed cell area, wirelength and vectorless-power fields.
4. All 72 rows have zero final setup, hold, slew, fanout, capacitance and DRC
   violations, at least 2% normalized capacitance and slew headroom, zero final
   detailed-route antenna net and pin violations, and an empty DRC report.
5. All eight platform/shape groups contain three complete clean matched trios;
   full local has strictly positive median benefit over broadcast in each.
6. In all 24 trios, broadcast DFFs are below candidate DFFs, candidate DFFs are
   at most 90% of local DFFs, and candidate synthesis and post-route cell areas
   are each strictly below full local.
7. B-local is faster than broadcast in every one of the 12 holdout seed pairs.
   Each of four holdout groups has median raw benefit at least 5% and median
   retained benefit at least 70%.
8. At least three of four holdout groups, including both platforms, jointly
   beat both controls by at least 1% using synthesis-area normalization.
9. Independently, at least three of four holdout groups, including both
   platforms, jointly beat both controls by at least 1% using post-route cell
   area normalization.
10. Candidate median final wirelength is no greater than full local in all four
    holdout groups.
11. For each NanGate45 holdout shape, all three B-local maximum paths parse and
    their median launch-register Q fanout is at most 10.

The frozen evaluator is
`scripts/similarity_blocal_qualified_validate.py`. Failure of any gate is a
preregistered null for this exact claim. Preserve every row and raw artifact;
do not weaken a threshold, add or replace a seed, drop a route, round away a
negative slack, or reopen any shape as later confirmation.

## Interpretation boundary and novelty status

An all-gates pass would support a reproducible flow-specific B-local
timing-versus-routed-cost result across two open standard-cell platforms and a
third prospective cohort. It would still not establish a new accelerator
architecture, silicon performance, workload energy, deployed inference
throughput, commercial superiority or HAA admission.

The interim primary-source screen in draft PR #75 already shows that PE-local
operand reuse, bounded broadcast, systolic delivery, configurable operand
networks, timing repair and register replication are established ingredients.
The exact bit-selective implementation has not been proven novel. Any positive
study must be reconciled with the closest paper and patent precedents, every
seed-level effect, vectorless-power limitations and end-to-end signed-GEMM
utility before a field-level or breakthrough claim.
