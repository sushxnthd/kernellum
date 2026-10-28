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


## Decision-theoretic interpretation

Let (Q(H\mid D)) be a distribution over programs that remain plausible after observing the demonstrations, and let (P(X)) be the distribution of future task inputs. For any candidate program (h), define posterior predictive centrality

[
C_{Q,P}(h)
=
\mathbb E_{X\sim P}
\Pr_{H\sim Q}\left[H(X)=h(X)\right].
]

Under exact-output disagreement loss,

[
\ell(h,H,X)=\mathbf 1\{h(X)\neq H(X)\},
]

the posterior expected risk is

[
R_{Q,P}(h)
=
\mathbb E_{H\sim Q,X\sim P}\ell(h,H,X)
=
1-C_{Q,P}(h).
]

Therefore

[
\arg\max_{h\in V_D} C_{Q,P}(h)
=
\arg\min_{h\in V_D} R_{Q,P}(h).
]

This is an exact identity, not an ARC-specific heuristic. The practical estimator replaces:

- the unknown posterior (Q) with a semantically quotiented set of demo-perfect candidate programs; and
- the unknown future-input distribution (P) with label-free counterfactual probes constructed from the demonstrations.

This decomposition gives two explicit failure modes: **posterior misspecification** (the candidate pool is a biased representation of plausible programs) and **probe-distribution misspecification** (counterfactual probes do not approximate the behaviorally relevant future-input distribution). The empirical program should test these separately.

### Misspecification bound

Let the practical candidate distribution and probe distribution be \(\tilde Q\) and \(\tilde P\), with total-variation deviations \(\eta_Q=\mathrm{TV}(Q,\tilde Q)\) and \(\eta_P=\mathrm{TV}(P,\tilde P)\). Let empirical centrality over a finite probe set approximate \(C_{\tilde Q,\tilde P}\) uniformly to error \(\epsilon\). If \(\hat h\) maximizes empirical centrality and \(h^*\) minimizes ideal posterior disagreement risk among the same candidates, then the standard plug-in argument gives

\[
R_{Q,P}(\hat h)-R_{Q,P}(h^*)
\le 2(\eta_Q+\eta_P+\epsilon).
\]

This is intentionally a diagnostic bound rather than a claim that the current probes are IID from the true query distribution. It turns the empirical agenda into three falsifiable components: candidate-posterior quality, probe-distribution quality, and finite-probe estimation error.


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


## Stage B final result

The frozen Train replication is complete over all 51 loadable generator classes from the pinned ARC-TGI inventory (55 raw files; four structurally excluded by the frozen loader because their class names do not end in `Generator`: task17cae0c1, task18447a8d, task195ba7dc, task1c02dbbe).

Final Stage B:
- accounted loadable families: **51/51**
- usable demo-perfect version spaces (>=3 semantic mutants): **10**
- median agnostic Spearman: **0.6511**
- median selector gain over mean demo-perfect mutant: **+10.36 pp**
- macro centrality-selected held-out accuracy: **90.00%**
- macro mean demo-perfect-mutant held-out accuracy: **78.88%**
- positive agnostic correlation: **8/10** usable families

This passes all three preregistered Stage B gates without changing thresholds.

The effect is not uniform. Some families are negative, including task1190bc91 (agnostic gain -8.56 pp) and task0e671a1a (-6.67 pp). Therefore the claim is distributional, not that centrality is universally safe.

## Probe-type robustness

A preregistration-independent robustness ablation on the nine originally usable families compared the frozen mixed probe set against restricted probe families.

Macro selector gain over the mean demo-perfect mutant:
- D4-only geometric probes: **+18.87 pp mean, +19.44 pp median, positive in 9/9**
- color-only probes: **+18.50 pp mean, +16.11 pp median, positive in 9/9**
- original mixed probes: **+13.31 pp mean, +13.06 pp median, positive in 8/9**
- cyclic-roll-only probes: **+6.46 pp mean, +11.00 pp median, positive in 7/9**

The roll-only family has a catastrophic failure on task182e5d0f (-35.56 pp), while D4-only never has a negative gain in this nine-family set. This weakens any claim that arbitrary counterfactual perturbations are informative and instead points toward structure-preserving geometric probes as the strongest current mechanism.

## Stage C partial status

Stage C was executed only after the Stage B pass was committed. The frozen primary comparison is counterfactual centrality (D) versus duplicate-invariant semantic-class plurality (B) on exactly 32 fresh queries per usable family.

Partial completed usable families show mostly ties and at least one loss:
- task0bb8deee: B=1.000, D=1.000
- task09c534e7: B=1.000, D=1.000
- task0a2355a6: B=1.000, D=0.875
- task0e671a1a: B=0.59375, D=0.59375
- task1190bc91: B=1.000, D=1.000
- task137f0df0: B=0.875, D=0.875
- task1d0a4b61: B=1.000, D=1.000

Do not infer the final Stage C verdict until shard 9 and the frozen aggregate complete.


## Stage C final result — practical single-mechanism method killed

The preregistered Stage C query-selection experiment completed across all 51 loadable families, with 10 usable version spaces and 32 fresh queries per usable family.

Primary:
- semantic-class plurality B: **90.000%**
- single-class counterfactual centrality D: **89.375%**
- D-B: **-0.625 pp**
- family-bootstrap 95% CI: **[-3.75, +1.875] pp**
- family directions: **1 improved, 1 hurt, 8 tied**
- disagreement-query accuracy: B **82.42%**, D **81.32%**
- disagreement gain: **-1.10 pp**
- pass@2: B=D=**96.5625%**

Frozen Stage C survival:
- >=3 pp macro gain: FAIL
- >=3 improving families: FAIL
- positive disagreement-query gain: FAIL
- bootstrap CI not entirely below zero: PASS

Therefore the practical single-mechanism centrality method is killed.

Secondary, not a rescue of the primary:
- raw candidate plurality A: **93.125%**
- minimum-AST simplicity C: **93.750%**
- lexicographic centrality-then-simplicity E: **93.4375%**

These secondary results motivate, but do not establish, a distinction between selecting one globally plausible mechanism and aggregating predictions for the actual query.

## Query–mechanism gap

Stage B and Stage C together expose two different decision problems.

For global mechanism selection, a central program can minimize expected disagreement over future inputs.

For a fixed query x_q, the loss-minimizing action is instead a predictive decision over outputs. Even if h* is the best single mechanism globally, its output h*(x_q) need not equal the output with maximum aggregate support among plausible mechanisms.

This explains how counterfactual centrality can predict held-out program quality in Stage B while failing to beat semantic-class plurality on Stage C. The next preregistered Stage D tests whether preserving centrality as a weight over semantic classes, rather than collapsing to one class, improves query prediction.


### Correction on Stage C selector C

Selector C was labeled "minimum-AST simplicity", but the frozen mutation operators only replace constants and operators in place; they do not materially change AST node count. Consequently nearly all accepted single-edit mutants have the same AST size, and C resolves primarily by the frozen mutation-index tie-break.

Therefore C=93.75% must **not** be interpreted as evidence for an Occam/shorter-program prior. It is better described as an early-mutation-order baseline. Any future simplicity claim requires a candidate generator with genuinely variable structural complexity and an independently fixed description-length metric.


## Stage D final result — weighted predictive method killed

Stage D retained every Stage C semantic class and weighted each class vote by its counterfactual centrality rather than collapsing to one class.

Across the same 10 usable families and 320 queries:

- B semantic-class plurality top-1: **90.000%**
- W_all all-probe centrality-weighted vote: **90.000%**
- W_D4 D4-centrality-weighted vote: **90.000%**
- W_all - B: **0.000 pp**
- family-bootstrap 95% CI: **[0.000, 0.000]**
- family direction: **0 improved, 0 hurt, 10 tied**
- disagreement-query accuracy: B=W_all=**80.72%**
- pass@2: B=W_all=W_D4=**96.5625%**

Every W_all query decision produced the same correctness outcome as B at the family-aggregate level; no family changed accuracy.

Therefore the practical counterfactual-weighted prediction hypothesis is killed under its preregistered rule.

### Current surviving scientific claim

The surviving result is narrower:

> In local executable version spaces induced by ARC-TGI AST mutations, label-free counterfactual behavioral centrality predicts **global off-demonstration program quality**, but this information does not improve query-level prediction beyond duplicate-invariant semantic-class plurality, either by selecting one central program or by centrality-weighted voting.

The key remaining threat is candidate-generator dependence. The independent enumerative-DSL transfer test is now the primary falsification experiment for the mechanism itself.


## Independent quickstart DSL transfer — inconclusive due coverage

A preregistered leave-one-demo-out transfer test used the independent `hackos-team/arc-agi-quickstart` DSL pinned at commit `2ea62d01162b436854b089a80715728cad2f2a3f`.

Search space:
- 5 primitives;
- every composition depth 1–6;
- 19,530 programs;
- all 400 ARC-AGI-1 public training tasks.

Result:
- usable folds: **3**
- distinct tasks: **3**
- required coverage: >=20 folds from >=10 tasks — **FAIL**
- D centrality accuracy: **33.33%**
- uniform semantic-class expected correctness U: **16.67%**
- D-U: **+16.67 pp**
- semantic plurality B: **33.33%**
- D-B: **0.00 pp**
- task-bootstrap 95% D-U: **[0, +50 pp]**
- positive task direction: **1 positive, 2 zero**
- two of the three usable folds had oracle=0, meaning no surviving DSL semantic class predicted the held-out demonstration correctly.

Interpretation: the transfer test is **inconclusive**, not a mechanism failure. The DSL is too weak/sparse to create enough expressible ambiguous version spaces to satisfy the preregistered coverage gate. A richer independent DSL replication is required.


## Query–mechanism separation: formal statement

The Stage B / C / D pattern follows from a clean distinction between integrated mechanism risk and fixed-query prediction risk.

Let Q be any distribution over candidate programs and P a distribution over future inputs.

### Mechanism decision

For a candidate program h, define integrated disagreement risk

\[
R_{\mathrm{mech}}(h)
=
\mathbb E_{X\sim P,H\sim Q}
\mathbf 1\{h(X)\neq H(X)\}.
\]

The behavioral medoid

\[
h^* \in \arg\min_h R_{\mathrm{mech}}(h)
\]

is equivalently the maximum-centrality candidate. This is the Stage B decision.

### Query decision

For one fixed query x, an output action y has posterior-predictive risk

\[
R_x(y)
=
\Pr_{H\sim Q}[H(x)\neq y].
\]

Therefore the Bayes-optimal output is

\[
y_x^*
\in
\arg\max_y
\Pr_{H\sim Q}[H(x)=y].
\]

Under a uniform distribution over duplicate-invariant semantic classes, this is exactly semantic-class plurality B.

In general,

\[
h^*(x) \neq y_x^*.
\]

Thus a program can be the best global representative of the version space while its answer on a particular query is not the posterior-predictive mode.

This is a classical Bayesian-decision distinction, not claimed as a new theorem. Its role here is explanatory: Stage B evaluates a mechanism-level objective, whereas ARC scoring is a fixed-query output objective. Stage C empirically verifies that success on the former does not imply improvement on the latter.

### Why centrality-weighted voting can be redundant

Let A be the semantic-class probe-agreement matrix and

\[
c_i = \frac1n\sum_j A_{ij}
\]

the class centrality. Stage D scores a query output group G_y by

\[
S(y)
=
\sum_{i\in G_y} c_i
=
\frac1n
\sum_j\sum_{i\in G_y} A_{ij}.
\]

This is total probe-graph degree carried by classes predicting y; it is **not** a calibrated posterior probability that y is correct. When class degrees are similar, S(y) preserves the same ordering as unweighted class count. When degree and query-group size covary, it can merely reinforce plurality.

Stage D observed the extreme empirical case: W_all and B had identical family-level top-1 accuracy on all 10 usable families and identical aggregate accuracy (90.0%).

The negative result therefore rules out treating behavioral centrality itself as a probability-of-truth weight without an additional calibration argument.
