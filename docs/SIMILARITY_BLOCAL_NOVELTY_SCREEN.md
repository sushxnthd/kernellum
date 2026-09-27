# SIMILARITY B-local: final novelty, utility, and closure audit

**Status (27 September 2026): closed negative result. No breakthrough was achieved.**

This document supersedes the interim novelty screen first committed on 25
September 2026. That draft was written before the later prospective evidence
existed and must not be read as a positive novelty assessment. The complete
empirical record now includes four preregistered prospective cohorts, four
separate flow-qualification canaries, raw artifacts, frozen evaluators, and
independently implemented audits. The final flow-qualified report is
[SIMILARITY_BLOCAL_FLOWQUALIFIED_REPORT.md](SIMILARITY_BLOCAL_FLOWQUALIFIED_REPORT.md).

The decision is deliberately narrow:

1. the exact B-local register mask may be an uncommon implementation point;
2. its architectural ingredients and causal motivation have substantial prior
   art; and
3. its own sealed holdouts falsify the preregistered robust performance claim.

An exact wiring pattern that has not been located verbatim is not, by itself,
a useful field-level discovery. No further B-local geometry or seed cohort is
scientifically justified.

## Object and claim boundary

The B-local candidate keeps `B[7:0]` and `A[7]` in per-PE registers while
transporting `A[6:0]` and valid signals through stride-two bounded groups. Its
controls are a broadcast implementation and a full-local implementation. All
three compute exact signed INT8 GEMM in the tested harness.

The intended mechanism was a compromise between two known costs: global
broadcast fanout and full per-PE register replication. The useful empirical
claim was not merely that a particular mask could be built. It was that this
selective mask would retain most of full-local's timing benefit while reducing
register/area cost robustly enough to beat both controls on unseen geometries.

That claim is false under its frozen tests. The result does not establish a
universal impossibility theorem for every bit-selective architecture. It does
close this implementation and the practice of testing it on additional
geometry/seed cohorts.

## Complete empirical reconciliation

| Cohort | Frozen outcome | What remains true | Why it cannot support the claim |
| --- | --- | --- | --- |
| Opened-data physical diagnostic, PR #69 | Exploratory pass | 12/12 routes clean; all four timing/retention groups passed; three of four synthesis-area-normalized groups beat both controls | Opened geometries and seeds; explicitly non-confirmatory |
| First prospective study, PR #71 | Evidence-completeness null | 71/72 rows complete; all four sealed holdouts were descriptively positive | One required row lost complete final evidence after a reporting-process crash |
| Prospective replication, PR #76 | Electrical null | All 72 rows produced evidence; timing/area descriptions remained promising | Only 68/72 routes were electrically clean; failures crossed candidate and controls |
| Flow-qualified prospective study, PR #82 | Runtime/headroom null | Signed-GEMM and flow identity passed | Four routes timed out and one clean control retained 1.97% rather than the frozen 2% capacitance headroom |
| Final flow-qualified replication, PR #86 | Evidence and performance null | Every one of the 71 available routes was clean and complete; all 23 available topology trios passed DFF and both area constraints; raw holdout timing gains were 9.20% to 15.75% | One discovery artifact was absent, NanGate45 8x9 retained only 59.26% of full-local timing benefit, and only 2/4 holdouts passed the synthesis-area-normalized joint-win gate versus 3/4 required |

The reporting, electrical-margin, antenna-margin, and runtime/headroom
canaries in PRs #73, #78, #80, and #84 qualified specific flow repairs only.
They used opened data and cannot be counted as architectural replications.

The final sealed holdouts are particularly informative because their
performance failure is independent of the missing discovery artifact. The
post-route-area-normalized gate passed three of four groups, and all four
groups passed raw timing, wirelength, and targeted fanout gates. Those results
show a real timing/fanout tradeoff. They also show that the tradeoff is
geometry-dependent and too fragile to meet the preregistered joint practical
claim.

## Closest primary technical literature

### Broadcast, locality, and operand movement

The high-level transformation predates this project. Leiserson and Saxe showed
that host broadcast in synchronous systems can be replaced by local
communication; Fortes and Moldovan gave conditions for eliminating broadcasts
or reducing them to small local broadcasts; Wong and Delosme formalized
broadcast-to-propagation conversion for VLSI processor arrays in Yale
technical report YALEU/DCS/TR544
([Leiserson and Saxe 1981](https://doi.org/10.1109/SFCS.1981.34),
[Fortes and Moldovan 1984](https://doi.org/10.1145/800015.808186),
[Yale report index](https://engineering.yale.edu/academic-study/departments/computer-science/technical-reports)). More
recently, Guo et al. identified implicit broadcast as a dominant FPGA HLS
timing problem and improved frequency using broadcast-aware scheduling and
buffered/localized control
([DAC 2020](https://doi.org/10.1109/DAC18072.2020.9218718)).

At accelerator scale, Eyeriss combines PE-local storage, direct inter-PE
communication, and operand reuse; MAERI exposes configurable operand and
reduction networks; the TPU uses an 8-bit systolic matrix unit in a deployed
workload context
([Eyeriss](https://dspace.mit.edu/handle/1721.1/102407),
[MAERI](https://doi.org/10.1145/3173162.3173176),
[TPU](https://doi.org/10.1145/3079856.3080246)). These works do not disclose
the exact B-local mask, but they preclude broad claims that asymmetric operand
delivery, bounded reuse, or localization are new principles.

### Bit-level, signed, and bit-weight dataflows

Bit-level systolic matrix arithmetic dates at least to McCanny and McWhirter,
and two's-complement systolic multiplication was explicitly studied by Roy and
Bayoumi
([McCanny and McWhirter 1983](https://doi.org/10.1049/IP-G-1.1983.0023),
[Roy and Bayoumi 1989](https://doi.org/10.1109/31.41310)). Sibia later built a
signed bit-slice DNN accelerator with sign-aware representation and transport
([HPCA 2023](https://doi.org/10.1109/HPCA56546.2023.10071031)). BitSys maps
individual operand bits into a systolic array, identifies sign-bit partial
products, and uses precision-dependent masks, although it moves bits uniformly
rather than using B-local's sign-local/magnitude-shared rule
([ISQED 2025](https://doi.org/10.1109/ISQED65160.2025.11014376)).

The closest conceptual collision is Wu et al.'s explicit *bit-weight
dimension* for tensor processing engines. Their transformations move bit
weights across spatial and temporal dimensions, move encoding outside the PE
array, and group four PEs to share compressor/DFF resources. Their exact
operand placement differs from B-local, but the scientific idea of optimizing
where different bit weights are encoded, transported, and reduced is already
published with RTL and process-level timing/area/power evaluation
([HPCA 2025](https://doi.org/10.1109/HPCA61900.2025.00058)).

### Factoring arithmetic across processing elements

A possible pivot is to share arithmetic rather than merely stage registers.
That is also established. Ullah et al. factor Booth encoding and hard-multiple
generation across PEs in a radix-8 systolic array; Inayat and Chung factor the
carry-propagation adder and rounding logic out of Gemmini PEs; later work
factors both row- and column-common logic
([DAC 2020](https://doi.org/10.1109/DAC18072.2020.9218585),
[Electronics 2021](https://doi.org/10.3390/ELECTRONICS10060652),
[TVLSI 2024](https://doi.org/10.1109/TVLSI.2024.3378197),
[HEART 2023](https://doi.org/10.1145/3597031.3597056)). These are genuinely
different interventions from B-local, but they are prior art rather than a new
Kernellum hypothesis.

## Patent screen

This is a technical priority screen, not a legal freedom-to-operate or
patentability opinion. Searches covered systolic/bit-serial/bit-slice arrays,
sign-bit and sign-extension handling, staggered operand supply, shared partial
products, and PE-group factoring through 27 September 2026.

The strongest patent collision located was IBM's
[US20190377707A1, *Bit-serial linear algebra processor*](https://patents.google.com/patent/US20190377707A1/en)
(priority 9 June 2018). It claims variable-precision bit-serial MACs in a 1D or
2D parallel array, bit-level memory layout, data reorganization from bytes,
and controlled delivery of bit rows. Its specification describes staggered
per-bit supply to a two-dimensional systolic array. Microsoft's
[EP3552090B1, *Block floating point for neural network implementations*](https://patents.google.com/patent/EP3552090B1/en)
places configurable bit-serial systolic processing in another accelerator
family. Older bit-slice signal-processing hardware includes
[US4791590A](https://patents.google.com/patent/US4791590A/en).

More directly, [EP0471723B1, *Digital processor for two's complement
computations*](https://patents.google.com/patent/EP0471723B1/en) describes a
bit-level systolic array whose coefficient digits contain separate sign and
magnitude/level bits. Its cells gate those fields differently, propagate data
bits along rows, and use flags to suppress unwanted sign-extension partial
products. It is not the B-local register mask, but it is strong prior art for
sign-versus-magnitude-specific behavior inside a systolic dataflow.

None of the reviewed claims was found to state the exact conjunction
`B[7:0]` local, `A[7]` local, and `A[6:0]` shared in stride-two groups. That
negative search result is not evidence of patent novelty, and it does not
restore scientific utility after the prospective performance claim failed.

## Practical-utility audit

### Functional semantics

The repository's signed-GEMM tests establish exact arithmetic equivalence for
the tested shapes, including the candidate's pipeline alignment. They do not
exercise a complete accelerator with memory hierarchy, tiling, launch/fill/
drain costs, host transfers, or model-level scheduling.

### Timing and area

B-local repeatedly reduced raw routed period relative to broadcast and used
fewer DFFs and lower synthesis/post-route cell area than full local. The final
sealed data nevertheless failed the frozen retention and synthesis-area-
normalized robustness requirements. The small margins around the local
comparison, and their reversal on NanGate45 8x9, show that the benefit is
sensitive to geometry and implementation context. Period multiplied by cell
area remains a proxy under equal-work assumptions, not deployed throughput or
cost per inference.

### Power and energy

No study used workload-derived switching activity, measured silicon power, or
board energy. The final study's preserved vectorless estimates place B-local
at 1.74 to 1.99 times full local's median power across the four holdouts. Those
numbers cannot be treated as measured power, but their adverse direction makes
an efficiency claim less credible, not more. A useful energy claim would need
fixed workloads, switching traces, clock-tree and memory costs, and independent
replication.

### Reproducibility

The work is unusually auditable for a negative result: frozen protocols,
original Actions ZIPs, source/image/patch identities, product hashes, raw
reports, official summaries, and independent checkers are preserved. That
supports the null and the documented flow qualifications. It does not supply
external reproduction, another toolchain, fabricated silicon, or physical
measurement.

## Hypothesis decision

The audit considered four continuations:

| Candidate continuation | Decision |
| --- | --- |
| More B-local geometries, seeds, or grouping factors | Rejected. This is cohort/parameter search after multiple opened nulls, not a new causal intervention. |
| Change which sign or magnitude bits are local | Rejected. It is post hoc mask tuning in the same crowded bit-selective design space without a workload-derived mechanism. |
| Replace staging with bit-weight, bit-serial, Booth, or shared-reduction logic | Not a Kernellum novelty claim. Strong primary and patent precedents already cover these mechanisms. A new implementation would be a benchmark or engineering replication unless it introduced and validated an additional principle. |
| Claim system or energy utility from current data | Rejected. The evidence omits workload switching, memory/system costs, measured power, and external replication; the available vectorless direction is adverse. |

No distinct causal architecture hypothesis survived both tests required for a
new prospective experiment: separation from the closest prior art and a useful
falsifiable practical claim motivated by the completed evidence. Free compute
could generate more routes, but route volume cannot repair that scientific
block.

## Final decision

The B-local program is closed as a reproducible negative result. It found a
real but fragile timing/fanout tradeoff, qualified a more reliable open ASIC
flow, and preserved several high-quality null datasets. It did **not** produce
a robust architecture advantage, workload-level efficiency result, priority
claim, field-level breakthrough, or admissions guarantee.

All opened geometries and seeds remain excluded. There will be no selected
retry, replacement row, weakened threshold, post hoc metric substitution, or
additional B-local cohort. A future Kernellum architecture project must start
from a separately justified scientific mechanism, search its own closest prior
art first, and preregister functional semantics, workload utility, evidence,
electrical, timing, routed-area, realistic power/energy, statistical, and
external-replication gates before opening data.

The literature search record is preserved separately at
[Bit-selective operand staging priority](https://app.undermind.ai/projects/b9b51f64-b896-41e7-b9f0-21b0dea6a465?path=%2FBit%20selective%20operand%20staging%20priority).
