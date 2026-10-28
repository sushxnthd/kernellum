# ARC Prize 2026 reboot — Counterfactual Version-Space Centrality

Status: **PRIMARY SURVIVING HYPOTHESIS, NOT YET PROMOTED TO PAPER CLAIM**

## Core question

When several executable programs fit every ARC demonstration exactly, can **unlabeled counterfactual behavior** tell us which program is most likely to generalize?

Let the demonstration-consistent version space be

[
V_D = \{h : h(x_i)=y_i \;\forall (x_i,y_i)\in D\}.
]

Generate a fixed set of label-free probes (P(D)) from demonstration inputs using only transformations that do not require test labels or the ground-truth program. For each (h\in V_D), evaluate its behavior on these probes.

The current selector is behavioral centrality:

[
C_P(h)=\frac{1}{|P|}\sum_{x\in P}
\frac{|\{g\in V_D:g(x)=h(x)\}|}{|V_D|},
]

with semantic duplicate handling as frozen in the experiment.

The hypothesis is **not** that consensus is always correct. It is that, after conditioning on exact demonstration fit, location in the behavioral geometry of the version space contains information about out-of-demonstration generalization.

## Frozen Stage B gate

The practical mechanism survives only if all are true on the ARC-TGI Train replication:

1. at least 6 usable generator families have >=3 distinct demo-perfect mutants;
2. median Spearman correlation between agnostic counterfactual centrality and fresh-input accuracy >= 0.30;
3. median selector gain over the mean demo-perfect mutant >= 0.10 absolute.

No threshold changes after seeing results.

## Current evidence

### Independent ARC-TGI Eval pilot

- 11 families examined
- 4 usable version spaces
- median agnostic Spearman: **0.413**
- median agnostic selector gain: **+10.1 pp**
- effect-size gates pass, usable-family count gate does not

This is mechanism evidence only.

### ARC-TGI Train frozen replication — partial, 45/55 families currently accounted for

- 45 unique families accounted for
- 9 usable version spaces
- median agnostic Spearman: **0.738**
- median agnostic selector gain: **+13.1 pp**
- macro selector accuracy: **92.6%**
- macro mean demo-perfect-mutant accuracy: **79.3%**
- selector improves over the candidate mean in **8/9** usable families
- selector chooses a 100%-held-out-accurate mutant in **5/9** usable families
- 7/9 agnostic correlations are positive

These figures remain **partial** until all 55 families are either evaluated or explicitly classified as an execution/import failure. Do not declare Stage B passed from these figures alone.

## Why this is different from nearby prior work

Nearby ideas include:

- version spaces: maintain all hypotheses consistent with labeled examples;
- query-by-committee / disagreement-based active learning: choose an unlabeled input whose *label should be acquired* because hypotheses disagree;
- CEGIS: obtain a labeled/verifiable counterexample to eliminate incorrect programs;
- Occam/MDL ranking: choose a syntactically simple consistent program;
- ensemble voting: aggregate predictions on the actual query.

The present intervention is different:

1. **no additional labels are acquired**;
2. probes are generated from the demonstrations before seeing any probe outputs;
3. every candidate remains demonstration-perfect;
4. probe outputs are used only to estimate the **behavioral geometry among candidate programs**;
5. the geometry is used to choose a program expected to generalize to fresh inputs.

The closest classical analogy is a version-space medoid under an empirically induced disagreement metric, but applied to executable program induction rather than ordinary classification.

## Main scientific risks

1. **Mutation-pool artifact.** Current version spaces are local AST mutants of an ARC-TGI transform. They may not resemble hypotheses produced by real ARC solvers.
2. **Probe-distribution artifact.** D4/color/roll probes may accidentally align with ARC-TGI generator structure.
3. **Consensus can be wrong.** A dense cluster of shortcut programs can dominate the true/generalizing behavior.
4. **Semantic quotient dependence.** Results must remain stable to duplicate removal and candidate-pool resampling.
5. **Family coverage.** A small number of usable families would make the mechanism brittle.
6. **Query relevance.** Correlation with generic fresh-input accuracy is insufficient. The method must improve selection on the actual hidden query.

## Stage C — locked until Stage B passes

Preregistered in `STAGE_C_QUERY_IDENTIFIABILITY_PREREG.md`.

Primary test: on fresh valid query inputs, compare counterfactual-centrality selection against duplicate-invariant semantic-class plurality.

The practical method survives only if:

- Stage B passed unchanged;
- top-1 query accuracy improves by >=3 pp;
- paired bootstrap CI is not entirely below zero;
- gains occur in >=3 independent families;
- positive gain remains on cases where candidates predict >=2 distinct query outputs.

If Stage C fails, kill the practical method and retain Stage B only as a mechanism result.

## Refinement-collapse branch

Broad “iterative refinement collapses hypothesis diversity” is **not** the primary thesis.

Reasons:

- symbolic tests showed most live-population collapse disappears when search history is archived;
- the first 0.5B actual-model diversity effect was confounded by a prompt-formatting pathology;
- prompt-fixed 1.5B replication produced identical independent/sequential new-class rates (58.3% vs 58.3%);
- strong prior art already documents contextual anchoring / diversity loss in iterative refinement.

Clean 3B and causal anchor-decomposition runs are retained as supporting falsification evidence only.
