# ShiftGuard: Certifiable Learned Bloom Filters Under Query Shift

## Research question

Can a learned Bloom filter retain a meaningful memory advantage while **provably** meeting its false-positive target after the non-key query distribution changes?

The project studies a narrow failure mode that existing PLBF guarantees typically exclude: construction/calibration non-keys are drawn from one distribution, while deployment queries come from another.

## Proposed object

Let a learned score partition the query space into regions (1,ldots,k).

- (g_i): member/key probability mass in region (i)
- (h_i): calibration non-key probability mass in region (i)
- (f_i): Bloom-filter false-positive probability assigned to region (i)
- (F): required global FPR

A nominal PLBF enforces

[
sum_i h_i f_i le F.
]

ShiftGuard instead chooses (f) subject to

[
sup_{q:operatorname{TV}(q,h)le ho} q^	op f le F.
]

The objective is standard Bloom-filter memory plus the serialized learned scorer. No model-memory exclusion is permitted in comparisons with a classical Bloom filter.

## Exact separation oracle

For fixed (f), the TV-ball inner problem is linear. Its maximizer is obtained by moving up to (ho) probability mass from regions with the smallest (f_i) to regions with the largest (f_i), respecting probability capacity.

This gives an exact (O(klog k)) separation oracle after sorting.

### Numerical falsification test

The greedy separation oracle was compared with a generic exact linear-program formulation on 2,500 randomized instances with 2, 3, 5, 8, and 12 regions and arbitrary TV radii.

- maximum absolute objective discrepancy: (5.55	imes10^{-16})
- failures above (10^{-9}): 0

This test is a numerical validation, not a proof.

## Robust allocation

Set (x_i=-log f_i). Ideal Bloom-filter memory is proportional to

[
rac{n}{(ln 2)^2}sum_i g_i x_i.
]

For any fixed candidate deployment distribution (q), the constraint

[
sum_i q_i e^{-x_i}le F
]

is convex. ShiftGuard solves the semi-infinite robust problem using cutting planes:

1. solve against the currently accumulated workload constraints;
2. use the exact TV separation oracle to find the worst workload;
3. add it if it violates (F);
4. terminate only when the exact worst-case workload satisfies the target.

## Theorem targets

### Theorem 1: TV robustness certificate

If ShiftGuard returns an allocation (f) satisfying

[
sup_{operatorname{TV}(q,h)leho}q^	op fle F,
]

then every non-key query distribution (q) inside that TV ball has expected FPR at most (F).

This follows directly from the robust constraint; the substantive component is the exact solution of the TV inner maximization.

### Theorem 2: classical-filter collapse

Let (h) have positive mass over (k) regions. The farthest point of the probability simplex from (h) in total variation is a vertex (e_j) with smallest (h_j), at distance

[
max_{qinDelta_k}operatorname{TV}(q,h)=1-min_j h_j.
]

Therefore, for

[
hoge 1-min_j h_j,
]

the ambiguity set contains the entire simplex. The robust constraint becomes

[
max_i f_ile F.
]

When every region has positive member mass, memory is minimized at (f_i=F) for every region, recovering the classical Bloom-filter bits-per-key rate

[
-rac{log F}{(log 2)^2}.
]

Interpretation: the memory advantage of learning is purchased by assumptions about the future query workload. Requiring robustness to every possible workload removes that advantage.

## Finite-sample deployment certificate

A deployment audit draws verified non-key queries and estimates their region distribution (hat q).

For (k) regions and (n) iid audit queries, use the multinomial (L_1) concentration bound

[
Pr(|hat q-q|_1ge epsilon)
le (2^k-2)e^{-nepsilon^2/2}.
]

At confidence (1-delta), this produces a TV uncertainty radius (r_n=epsilon/2).

If

[
operatorname{TV}(hat q,h)+r_nle ho,
]

the observed deployment workload is CERTIFIED at confidence (1-delta). Otherwise ShiftGuard returns REVIEW/REBUILD rather than silently extending its FPR claim.

The primary experiment fixes (delta=0.05) and audit sizes 250, 500, and 1,000 verified benign queries per temporal block.

## Primary temporal experiment: EMBER2024 PDF

Official dataset chronology:

- 64 weekly cohorts
- 1,000 PDF samples per week
- first 52 weeks are the released train period
- final 12 weeks are the released future test period

To avoid calibration/test leakage:

- weeks 1–40: train a deliberately compact scorer
- weeks 41–52: estimate the pre-deployment benign workload (h)
- malicious samples from weeks 1–52: stored key set
- weeks 53–64: untouched temporal future workload
- FPR is computed only on benign future queries

Targets: (Fin{10^{-2},3	imes10^{-3},10^{-3}}).

Every comparison includes serialized scorer bytes plus backup Bloom-filter memory.

## Pre-registered decisive criteria

These rules were fixed before observing the ShiftGuard EMBER2024 result.

### C1. The failure mode must be real

PASS only if the nominal PLBF's expected FPR on at least one untouched future workload is at least **1.25x its target**.

If ordinary PLBF does not materially fail under genuine temporal shift, this project loses its central empirical motivation on EMBER.

### C2. Certified learning must still buy memory

Using a 95% finite-sample certificate with no more than 1,000 verified benign audit queries per future week:

- at (F=1%), ShiftGuard must retain **at least 15% total-memory savings** versus a classical BF;
- at (F=0.3%) or (F=0.1%), at least one must retain **at least 10% savings**.

Model/scorer memory is included.

### C3. Certification must be usable

At a tested robustness radius, the 1,000-query 95% audit must certify all 12 future weeks for each primary target.

A method that is safe only because it nearly always refuses to certify is not a useful success.

### Primary decision

**PROMOTE** only if C1, C2, and C3 all pass.

Otherwise the current ShiftGuard formulation receives **KILL_OR_PIVOT**. The thresholds are not relaxed after results are observed.

## Gold-tier promotion gate after the primary result

Passing the primary kill criteria is necessary, not sufficient for an INSEF flagship.

Before final presentation, require:

1. EMBER result replicated across multiple seeds/partition counts and with confidence intervals.
2. At least one second real workload with a natural temporal/domain shift.
3. Nominal PLBF, classical BF, sandwiched LBF/PLBF, and relevant adaptive/robust learned-filter baselines.
4. Ablation separating robust allocation, finite-sample audit, and classifier/model-memory choices.
5. Failure cases shown explicitly, including radii where ShiftGuard collapses to classical BF or refuses certification.
6. Runtime/query overhead and audit sample complexity reported.
7. No claim of adversarial robustness unless separately established.

## Current status

The executable experiment is in `research/shiftguard/ember2024_temporal.py`.
Its GitHub workflow is isolated from `main` on `research/shiftguard-ember`.
