# SIMILARITY B-local: primary-source novelty and utility screen

Date: 25 September 2026. **Interim audit while the frozen B-local replication is routing.** No replication results were used to prepare this note. It does not change the RTL, thresholds, cohort, evaluator or interpretation of any earlier null. The replication protocol is [SIMILARITY_BLOCAL_REPLICATION_PREREGISTRATION.md](SIMILARITY_BLOCAL_REPLICATION_PREREGISTRATION.md).

## Exact object being evaluated

The candidate keeps B[7:0] and A[7] in preserved per-PE registers while transporting A[6:0] and valid signals in stride-two groups. The shared, local and candidate arrays use equivalent signed INT8 MAC logic. The frozen physical comparison is a median of three seed-paired routed-period and *synthesis-cell-area* ratios per platform/shape, with separate mapped-DFF, electrical, functional, fanout and artifact-integrity gates. These are two open-cell-library flow experiments, not measured silicon power or an accelerator running a model.

## Direct precedents and their implications

| Primary source | Established precedent | Scope for this project |
| --- | --- | --- |
| [Chen et al., Eyeriss, ISCA 2016, MIT repository](https://dspace.mit.edu/entities/publication/f6342515-2b7d-411c-a8ad-a9edb23dd394) | PE-local storage, direct inter-PE communication and reuse of both filter and activation operands are architecture-level tools for reducing movement. Its claimed energy result uses an explicit energy model and fabricated chip. | Local reuse or asymmetric delivery cannot alone be called a new concept. Its energy claims cannot be imported into our period/area measurements. |
| [Kwon et al., MAERI, ASPLOS 2018, author PDF](https://anands09.github.io/papers/maeri_asplos2018.pdf) | Programmable operand and reduction networks map varied dataflows and alter area/utilization tradeoffs. | Per-operand transport is an established design space; our fixed bit-selective physical implementation is a narrower comparison than MAERI's configurable network. |
| [Jouppi et al., TPU, ISCA 2017, authors' paper](https://arxiv.org/abs/1704.04760) | 8-bit MAC systolic array with operand movement and a deployed workload-level analysis. | Correct INT8 array arithmetic and a routed critical path alone do not establish competitive deployed inference utility. |
| [Yaacoby and Cappello, Bounded Broadcast in Systolic Arrays, author-hosted PDF](https://sites.cs.ucsb.edu/~cappello/papers/1994ijhsc.pdf) | Bounded sharing of a broadcast across processor-array recipients. | Limiting spatial broadcast is an old architectural idea; this source studies different algorithms and does not evaluate our exact RTL. |
| [OpenROAD Gate Resizer documentation](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html) | Buffer insertion, resizing and cloning to address maximum fanout/capacitance and critical timing. | A reduced Q fanout is evidence about this physical implementation, not proof that the underlying repair principle was invented here. |
| [AMD Vivado UG949, register replication](https://docs.amd.com/r/2025.1-English/ug949-vivado-design-methodology/Replicate-High-Fanout-Net-Drivers?contentId=moLqW5V017KYIZOzlJnLnA) | Manual replication and synthesis preservation of high-fanout registers are routine FPGA timing techniques; indiscriminate replication can raise area/power. | This is an FPGA methodology document, not a matching ASIC implementation. It reinforces that register replication per se cannot support a novelty claim. |

These references show substantial prior art for the *ingredients*. This screen has **not** found or ruled out a published design with the exact B[7:0]-local/A[7]-local/A[6:0]-shared mask, identical grouping, signed-GEMM semantics and open-flow cost/timing comparison. Absence from this limited search is not evidence of invention. A proper novelty claim needs an expanded paper and patent search, direct comparison against the closest method, and a precise statement of the distinct result.

## What a complete replication could establish

If and only if every frozen gate passes, the narrow supported result is: in this pinned OpenROAD flow and these two standard-cell libraries, the fixed operand-delivery implementation reproduces a period-versus-synthesis-area tradeoff on a second unseen cohort relative to its two controls. The median of three seeds offers a reproducible benchmark, not a confidence interval. The 1% area-normalized threshold is a small effect and should be reported with every individual seed and its sensitivity.

A `B*A_B/(C*A_C)` or `L*A_L/(C*A_C)` ratio is a **period × synthesis-cell-area proxy** under the assumption of comparable useful work per cycle. It is not measured silicon area, energy efficiency, total system throughput, thermal behavior or cost per inference. The experiments do not supply memory, clocks outside the block, I/O, tiling/launch overhead, or workload energy. Do not translate a positive proxy ratio into an energy or product-performance claim.

The repository's earlier [FPGA compiler-utility confirmation report](SIMILARITY_UTILITY_CONFIRMATION_REPORT.md) is a different study and a frozen null: all 60 routes succeeded, but one independent seed missed two workload-selection gates. Its seed-instability finding makes a single placement seed especially unsuitable as evidence for system-level utility here.

## Next evidence after the frozen replication

1. Audit all 18 original ZIPs, 72 rows, native finish and electrical reports, four functional logs, patch manifests, final output hashes and every seed-paired ratio against the evaluator without dropping failed rows.
2. If all gates pass, characterize complete routed cell area and clock/buffer overhead and report seed-level dispersion. Evaluate representative signed GEMMs with cycle-accurate tiling, fill/drain and memory traffic in the same fixed workload cohort, rather than inferring application speed from `period_min` alone.
3. Measure or model switching activity and power with disclosed assumptions before an energy claim. Assess additional libraries/corners or physical measurement before generalizing beyond these two open-cell flow configurations.
4. Expand prior-art search for bit-selective operand staging and operand-specific spatial replication. Compare the closest implementations under identical synthesis and routing conditions before asserting architectural novelty.

**Status:** An independent empirical engineering result may be credible if the prospective replication passes and its audit is complete. No field-level discovery, architectural originality, power advantage, HAA outcome or rescued earlier null follows from the present evidence.
