# V27 novelty-threat ledger — 2026-11-14

Status: **OPEN / not final novelty clearance**. This ledger is rejection-first. It records antecedents that constrain claims even when they do not subsume the paper.

## Threat A — bargaining replication is classical (already handled in v26)

William Thomson, “Replication invariance of bargaining solutions,” *International Journal of Game Theory* 15 (1986), 59–63, DOI 10.1007/BF01769276.

Thomson analyzes replication of bargaining agents/types and shows that Nash and Kalai–Smorodinsky allocations under replication correspond to asymmetric bargaining weights proportional to replication orders. Therefore:
- **do not claim** replication sensitivity of Nash bargaining itself as new;
- the ML novelty, if retained, is the fixed-learning-problem intervention at the gradient-combiner interface, the optimizer-specific update response/geometry law, and the broader atomicity framework.

Classification: **close antecedent requiring explicit boundary; not theorem-equivalent to the ML mass-refinement/Pareto result.**

## Threat B — POLAR explicitly notes duplication-neutral Pareto optima (new citation required)

Theodore Zhao, Mu Wei, J. Preston, Hoifung Poon, “Pareto Optimal Learning for Estimating Large Language Model Errors,” ACL 2024, DOI 10.18653/v1/2024.acl-long.566.

The paper explicitly states that a Pareto-optimal estimator remains unaffected by arbitrary duplication of an information source. v26 does not cite this paper.

Consequences:
- **do not claim** that duplication-neutrality of the Pareto solution set is new;
- distinguish solution-set invariance from the update selected by a particular gradient combiner/finite implementation;
- our atomicity–Pareto result concerns an aggregator required simultaneously to be invariant to every mass-preserving refinement and to return strict common descent whenever available. POLAR does not establish that incompatibility or the optimizer response laws found in the current search.

Classification: **close ML antecedent / mandatory citation; no established theorem-equivalent collision.**

## Threat C — objective redundancy in MOO is an active 2026 literature (new citation required)

Gabriele Eichfelder, Tobias Gerlach, Christian Kugelmann, “Redundant objectives in multiobjective optimization,” Optimization Online, 23 Sep 2026.

The authors study redundancy defined by preservation of weakly efficient, efficient, and properly efficient solution sets after objective removal, and explicitly mention a stronger redundancy concept relevant to descent-type methods.

Consequences:
- objective redundancy/removal and preservation of Pareto sets cannot be presented as new;
- the paper must explain why exact objective duplication at the *algorithmic update* level can matter even when the optimization problem's efficient set is unchanged;
- the cited “stronger concept” requires full-text comparison before final novelty clearance.

Full-text comparison completed 2026-11-14. Section 6.2 proves preservation of the strict common-descent cone and stationary points when removed objectives are nonnegative monotone functions of retained objectives (Lemma 6.10 / Theorem 6.11). The paper does **not** analyze duplicate identical objectives as separate entries to a gradient combiner, list-multiplicity response of MGDA/CAGrad/Nash-MTL/FairGrad, mass-preserving refinement invariance, singleton consistency, a mean-forcing characterization, or an incompatibility between refinement invariance and common-descent completeness.

This is therefore not theorem-equivalent. It strengthens our related-work boundary: efficient/stationary sets and common-descent *availability* can be unchanged by redundant objectives while a concrete finite gradient aggregator can still select a different update because of represented multiplicity.

Classification: **close 2026 antecedent / mandatory citation; full-text theorem-equivalent threat cleared.**

## Threat D — classical aggregation/decomposability literature

Theorem 6 (unrestricted refinement invariance + singleton consistency forces the mass mean) is intentionally immediate once the domain is explicit and is adjacent to classical decomposability/barycentric-consistency characterizations of means.

Consequences:
- treat Theorem 6 as a boundary lemma, not a flagship novelty claim;
- novelty center should remain the learning-specific incompatibility/quantitative lower bound, exact modern-optimizer response/phase laws, finite-implementation distinctions, and causal benchmark audit.

Classification: **classical antecedent family; framing constraint.**

## Search result so far

Repeated searches across task/objective duplication, redundant objectives, MGDA, CAGrad, Nash-MTL, FairGrad, Aligned-MTL, PCGrad and common-descent/refinement invariance have **not yet located**:
1. an exact prior derivation of the current MGDA/CAGrad/Nash/FairGrad/Aligned-MTL replication-response profile as a unified ML result;
2. the geometry-dependent power-equilibrium implicit law and its bounded/power/linear phases in this task-replication setting;
3. an exact theorem matching the stated mass-refinement-invariance + singleton-consistency + common-descent-completeness incompatibility, or its instance-specific epsilon lower bound.

This is **not** a proof of novelty. The Eichfelder et al. 2026 full-text collision check is now closed as a non-equivalent antecedent; a final citation chase for duplicate/clone-sensitive gradient aggregation and aggregation/decomposability characterizations remains mandatory.


## Threat E — clone-proof benchmark weighting is now explicit ML prior art

Damien Berriaud and Roger Wattenhofer, "Clone-Robust Weights in Metric Spaces: Handling Redundancy Bias in Benchmark Aggregation," AAMAS 2026, DOI 10.65109/MJWJ6521, arXiv:2502.03576v3.

This is a major conceptual antecedent. The paper formalizes weighting functions over finite subsets of a metric space, with axioms for symmetry, continuity, approximate-clone fairness, and locality under addition of clones. Its Axiom 6 requires that adding a sufficiently close clone leave weights of sufficiently distant elements approximately unchanged; Appendix F extends the discussion to perfect clones in pseudo-metric spaces.

Boundary after theorem-level audit:
- domain/object: benchmark/evaluation weighting over finite metric-space sets, not training-time multi-objective gradient aggregation;
- transformation: addition of approximate/metric clones with local weight sharing, not an explicit measured ontology with mass-preserving exact list refinement;
- guarantee: local stability/weight-sharing of the weighting rule, not equality of a downstream parameter update under every mass-preserving refinement;
- no MGDA/CAGrad/Nash-MTL/FairGrad response law;
- no theorem that refinement invariance plus singleton consistency forces a mass mean;
- no incompatibility with common-descent completeness or the quantitative epsilon lower bound.

The manuscript must not claim clone-proof weighting, redundancy-bias mitigation, or "similar tasks should share weight" as new. Berriaud--Wattenhofer should be cited in the main related-work section, not only late discussion. The novelty boundary is training-time optimizer response, measured exact refinement, modern-gradient-combiner response laws, and the Pareto/common-descent boundary.

Classification: **major conceptual ML antecedent / mandatory reframing; no theorem-equivalent collision found.**

## Threat F — duplicated objectives affecting optimization search predates this paper

Hisao Ishibuchi, Masakazu Yamane, and Yusuke Nojima, "Effects of Duplicated Objectives in Many-Objective Optimization Problems on the Search Behavior of Hypervolume-Based Evolutionary Algorithms," IEEE MCDM 2013, pp. 25--32, DOI 10.1109/MCDM.2013.6595440.

The published abstract reports that duplicated objectives bias SMS-EMOA's hypervolume-based evolutionary search toward Pareto-front regions with favorable values on the duplicated objectives.

Consequences:
- **do not claim** that objective duplication affecting an optimization algorithm is newly discovered here;
- distinguish population-based hypervolume selection from differentiable MTL gradient combiners and exact fixed-computation causal refinement;
- the paper contributes no known MGDA/CAGrad/Nash/FairGrad replication law and no mass-refinement/Pareto theorem in the retrieved record.

Classification: **direct historical duplicated-objective antecedent / mandatory citation; optimizer-law and theorem claims remain distinct.**
