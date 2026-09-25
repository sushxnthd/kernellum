# SIMILARITY B-local transport: prospective confirmation protocol

Status: **draft until merged to main; no eligible physical route may precede that merge**.

## Exact claim and prior-data quarantine

For signed INT8 MAC arrays under the pinned OpenROAD flow, does B-local/A-sign-local operand transport on new 54-PE geometries preserve at least 70% of the median full-local routed-period benefit over broadcast while retaining a DFF and synthesis-cell-area reduction, with at least 1% median period-times-synthesis-area improvement over both broadcast and full local on at least three of four platform/geometry holdout groups? All electrical and evidence gates below are required. The result would be a bounded comparison of this RTL/flow, not a claim of a new accelerator architecture, silicon measurement, energy saving or HAA admission.

The 72-route original stride-two prospective study was an all-required null, faithfully published in `docs/SIMILARITY_STRIDE2_PROSPECTIVE_REPORT.md`. The published B-local physical diagnostic passed on **already opened** 5x8 and 8x5 geometries and seeds 53, 71, 89; its raw evidence and independent audit are in `docs/SIMILARITY_BLOCAL_PHYSICAL_DIAGNOSTIC_REPORT.md`. All previous studies on 7x7, 2x4, 4x2, 3x6, 6x3, 5x5, 3x8, 8x3, 5x9, 9x5, 4x7, 7x4, 5x8 and 8x5 and all their seeds are permanently excluded from confirmation. No old route row is part of the new effect estimate or gate. Source is the unchanged B-local RTL from the opened physical diagnostic (see its recorded SHA-256 below); this study tests generalization of that intervention, not novelty of an untested RTL edit.

## Frozen source, independent comparison and cohort

Use `rtl/kernellum_blocal_mac_array.sv` with SHA-256 `7cdd3223ac401ec9c9df5a792cb41f2e754262dbd2c6fad103752fce7afdc766` and `rtl/similarity_asic_transfer_blocal.sv` with SHA-256 `1f6bd084dab5e368f34dee5c44fb6ca12a68860b4b26fff2f78b85277d50552a`. The top-level `similarity_asic_transfer_broadcast` and `similarity_asic_transfer_local` are the existing matched controls with the same clock, signed INT8 arithmetic and observable accumulator. Candidate B bits and A[7] have distinct preserved local registers; A[6:0] and valids remain stride-two grouped. No topology, RTL, synthesis map, area convention, report parser or physical setting may change based on any observation from this cohort. The exact merge SHA initiating the study is recorded in its functional artifact and frozen as the route provenance.

| Split | Geometries | Platforms | Seeds | Topologies | Routes |
| --- | --- | --- | --- | --- | ---: |
| Discovery | 6x8, 8x6 (48 PE) | NanGate45, Sky130HD | 101, 131, 157 | broadcast, local, blocal | 36 |
| Sealed holdout | 6x9, 9x6 (54 PE) | NanGate45, Sky130HD | 101, 131, 157 | broadcast, local, blocal | 36 |
| Total | 4 never routed shapes | 2 | 3 unused route seeds | 3 | **72** |

The seed values have not been used in any earlier SIMILARITY ASIC routing. Discovery data can aid *diagnosis* after the run but cannot modify the sealed holdout gates. No failed seed is replaced. The whole cohort is launched from the same merged commit; publishing evidence afterward pins the workflow to that commit so it cannot repeat physical routes.

Signed GEMM equivalence against full local must pass on all four new shapes before any physical route in this workflow. The comparator outputs are generated prospectively in the same matrix, not borrowed from the old 40-PE study. Physical settings match the published diagnostic: immutable image `openroad/orfs@sha256:573c1716efa0e286c4f641c26d343e20929d58d27fffbb22be2d0b93f09764f6`, NanGate45 typical and Sky130HD typical (`sky130_fd_sc_hd__tt_025C_1v80`), 20 ns clock, core utilization 35%, placement density 0.50, `CAP_MARGIN=20`, `SLEW_MARGIN=20`, the same post-CTS timing repair setting, QEMU `max` final report and two matching physical seeds per route (`GPL_RANDOM_SEED=GRT_SEED` to the frozen seed). These are open PDK/library experiments on free CI, not tapeout/signoff.

## Exact estimands and all-required gates

For each platform/shape/seed, let `B`, `L`, `C` denote **final routed** broadcast, full-local and B-local `clk period_min`; let `A_B`, `A_L`, `A_C` be their **synthesis cell areas**, and `D_B`, `D_L`, `D_C` their mapped DFF counts. `q_L=(B-L)/B`, `q_C=(B-C)/B`, retained benefit `=(B-C)/(B-L)` when `B>L`, and area-normalized throughput ratios are `B*A_B/(C*A_C)` and `L*A_L/(C*A_C)`. Compute each group's median of the three seed-paired ratios (not a ratio of medians), with **all three seeds required**. The 1% density hurdle means each median ratio must be at least 1.01. No confidence interval is claimed from three seeds.

Every gate must pass:

1. Signed-GEMM equivalence on all four shapes before routing.
2. Exactly 72 unique attempted platform/topology/seed/geometry CSV rows, 18 original route ZIPs, four functional logs and all 72 final critical-path reports. Missing evidence fails.
3. All 72 rows finish with final setup, hold, maximum slew, maximum fanout, maximum capacitance and detailed-route DRC counts zero. Period, cells, DFFs, synthesis area, wirelength and SHA-256 of nonempty GDS/ODB/SPEF/netlist are valid. A route's successful process exit alone is insufficient.
4. All eight platform/shape groups have three fully matched, electrically clean topology trios; full local has strictly positive median period benefit over broadcast in every group.
5. In all 24 matched trios, `D_B < D_C <= 0.90*D_L`, and `A_C < A_L`. No area/DFF missingness or dropped routes are allowed.
6. Each of the four sealed holdout platform/shape groups has median `q_C >= 0.05` and median retained benefit `>=0.70`.
7. At least three of four holdout groups have **both** median area-normalized throughput ratios `>=1.01`, including at least one group on NanGate45 and one on Sky130HD.
8. For each NanGate45 sealed-holdout shape, the median launch-register Q fanout over all three B-local maximum paths is `<=10`; all three maximum-path reports must be parseable, and every planned final report present.

The frozen evaluator is `scripts/similarity_blocal_prospective_validate.py`. A failure of **any** gate is a preregistered null for this exact claim. Preserve every artifact and report every failed gate. Do not change a source or threshold, add seeds, rerun selected seeds, exclude rows or open the holdout as a fresh future cohort. A passing all-gates run establishes only the specified simulated/routed comparison; independent evidence and prior-art scrutiny are required before describing a scientific contribution.

## Prior work and practical boundary

[Eyeriss (ISCA 2016)](https://dspace.mit.edu/entities/publication/f6342515-2b7d-411c-a8ad-a9edb23dd394) already develops local operand reuse in spatial accelerator dataflows; [MAERI (ASPLOS 2018)](https://synergy.ece.gatech.edu/tools/maeri/) studies flexible operand mappings/interconnects; the [TPU architecture (ISCA 2017)](https://arxiv.org/abs/1704.04760) uses a systolic array. These primary works make local versus shared data movement an established design space. This search does not establish that selective local replication by bit significance is new; a targeted novelty review remains necessary. The measured denominator is synthesis cell area, **not** die/core area; no energy, throughput on a real neural network, off-chip memory, actual chip yield or silicon timing is measured. An HAA application can accurately present the experiment and its outcome, but no admissions or funding promise follows.
