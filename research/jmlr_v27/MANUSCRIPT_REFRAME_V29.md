# Project Zero manuscript reframe for post-benchmark v29

Date: 2026-11-14
Source audited: current v26/v28-family manuscript PDF.
Status: pre-outcome editorial lock; final wording waits for standard-benchmark results.

## Principle

Do not rebuild the paper around a false novelty claim. The manuscript should concede classical antecedents where they are genuinely classical, then isolate the ML-specific object:

> a fixed learning problem whose semantic loss tensors are unchanged, while only the represented multiplicity seen by the optimizer is changed.

The JMLR case should rest on (i) this causal intervention and measured ontology, (ii) exact response laws for modern gradient combiners, (iii) the learning-specific Pareto/common-descent boundary and quantitative lower bound, (iv) released-implementation atomicity, and (v) standard-benchmark evidence.

## Abstract corrections

Current abstract sentence:
> "unrestricted mass-preserving refinement stability quantitatively conflicts with Pareto common descent."

Keep this learning-specific boundary, but insert explicit classical provenance for the mean/barycentre forcing step:

Recommended structure:
> "Classical barycentric/decomposability results imply that sufficiently strong refinement consistency collapses aggregation toward a reference-measure barycentre. Specializing this boundary to task gradients, we show that unrestricted mass-preserving refinement neutrality is incompatible with common-descent completeness, and derive a quantitative lower bound on the refinement sensitivity required whenever the reference-measure mean leaves a task's descent half-space."

Do **not** claim as new:
- the general fact that duplicate objectives can alter optimization;
- clone-proof weighting;
- replication sensitivity of Nash bargaining;
- the barycentre/mean characterization itself;
- conditional expectation/convex order under partition refinement.

After Tier A/B, replace the abstract's empirical sentence with the actual NYUv2/QM9 result, including a null if one benchmark is null.

## Contribution 2 rewrite

Current:
> "We use homogeneous-refinement neutrality to organize measured aggregation, explicitly recover a close refinement-symmetry characterization from prior work, and prove new exact and quantitative boundaries between unrestricted refinement stability and Pareto-aware common descent."

Safer:
> "We connect measured objective refinement to classical barycentric/decomposability consistency and recent clone/refinement-robust weighting, then derive the learning-specific consequence: unrestricted mass-preserving neutrality conflicts with common-descent completeness, with an instance-specific quantitative lower bound on the refinement sensitivity any Pareto-aware combiner must exhibit."

This makes the novelty claim land on the consequence, not the mean-forcing lemma.

## Related-work additions required before submission

### Duplicate objectives in optimization
Cite:
- Ishibuchi, Yamane & Nojima (IEEE MCDM 2013), "Effects of Duplicated Objectives in Many-Objective Optimization Problems on the Search Behavior of Hypervolume-Based Evolutionary Algorithms."

Boundary:
They show duplicated objectives can bias SMS-EMOA search. Therefore the broad observation "duplication can matter" is not new. Our contribution is exact training-time gradient-combiner response under a fixed-computation intervention, plus the modern MTL laws and measured-mass framework.

### Clone-proof benchmark aggregation
Promote Berriaud & Wattenhofer (AAMAS 2026) from a passing citation to a dedicated paragraph in Related Work.

Boundary:
Their object is a weighting function on finite metric-space sets; Axiom 6 gives local stability/weight sharing under addition of near clones, with a perfect-clone pseudo-metric extension. They do not analyze training-time gradient aggregation, exact mass-preserving multiset refinement, modern MTL optimizer response laws, or common-descent completeness.

### Redundant objectives in MOO
Add Eichfelder, Gerlach & Kugelmann (2026), "Redundant objectives in multiobjective optimization."

Boundary:
Their Section 6.2 preserves strict common-descent cones/stationarity under removal of monotone-redundant objectives. This is a problem-level redundancy result. Project Zero's central distinction is that problem-level efficient/descent structure can be unchanged while a finite represented-list optimizer still selects a different update.

### Classical barycentric/decomposability theory
Add a compact paragraph citing:
- Kolmogorov/Nagumo quasi-arithmetic means/decomposability;
- Girotto & Holzer, Mathematika 2004, "A characterization of the barycentre";
- Girotto & Holzer, Information Sciences 2019, "Finite quasi-barycentric means in an abstract setting";
- optionally modern barycentric-associativity treatments (Marichal/Teheux/Couceiro).

Boundary:
Theorem 6 is a measured-gradient specialization/bridge, not the headline theorem novelty.

## Theorem presentation

### Theorem 6
Rename from a novelty-forward title such as "Unrestricted refinement collapse" to something provenance-aware, e.g.:

**Proposition 6 (Barycentric consequence of unrestricted refinement consistency).**

Before statement:
> "The following is the measured-gradient specialization of a classical barycentric/decomposability principle; we include it to make the subsequent learning-specific impossibility self-contained."

Keep its one-line proof.

### Theorem 7
Keep as a theorem only after final prior-art audit. Strengthen the statement by making the exact learning-rule domain explicit:
- finite positive masses;
- gradient vectors in R^d;
- deterministic aggregator;
- exact all-refinement invariance;
- singleton consistency;
- common-descent completeness.

Then state clearly that the mathematical proof is short but the point is a design impossibility: exact representation neutrality cannot coexist with a requirement to exploit all available strict common-descent geometry.

### Quantitative theorem
Promote the epsilon lower bound above Theorem 6 in emphasis. This is more useful to ML than the exact-collapse lemma because it applies to approximate systems.

## MGDA terminology correction

Every empirical/theoretical table must distinguish:
- **canonical MGDA**: simplex min-norm combination, clone-invariant as a mathematical direction/update control;
- **released FairGrad MGDA wrapper**: multiplies simplex solution by declared n_tasks and is therefore magnitude-sensitive to represented task count.

Never write "MGDA is clone invariant" without the word **canonical**.

## Empirical section structure after benchmark completion

1. **Intervention validity**
   - same data/targets/heads/forward/loss graph;
   - canonicalized null;
   - exact task-count handling;
   - released-vs-canonical MGDA distinction.

2. **Tier A standard-benchmark update census**
   - NYUv2 + QM9;
   - all frozen parent/k/method cells;
   - response-class ordering;
   - finite Nash solver failures explicitly visible;
   - canonicalized null table.

3. **Tier B downstream trajectories**
   - paired-seed effects;
   - untouched-task/target shifts;
   - Delta-m;
   - bootstrap CIs;
   - parameter distances;
   - any ranking reversals;
   - all null/negative outcomes.

4. **Source-faithfulness and implementation atomicity**
   - QM9 released normalization path;
   - environment-version deviation;
   - Nash finite-solver diagnostic;
   - released MGDA scaling.

5. **Failure modes / limits**
   - original 1,350-cell prereg computational infeasibility;
   - pre-outcome amendment;
   - standard benchmark scope actually completed.

## Claims that must remain forbidden until results

Do not write:
- "standard benchmarks confirm partition dependence";
- "the effect generalizes across NYUv2 and QM9";
- "rankings reverse on standard benchmarks";
- "canonicalization eliminates the effect in practice";
- "submission-ready";
unless the locked analyses actually establish each statement.

## JMLR positioning after these corrections

The defensible headline is not "we discovered objective duplication." It is:

> **Modern ML optimization silently assigns causal importance to represented objective atomicity. We formalize the distinction between semantic mass and represented identity, derive exact response laws and a Pareto-aware neutrality boundary, separate mathematical from released-implementation behavior, and test the resulting predictions under fixed-computation interventions on standard benchmarks.**
