# Land V7 Independent Test — Pre-Result Robustness Controls

Status: FROZEN WHILE THE PRIMARY PREREGISTERED EVALUATION IS RUNNING, BEFORE ANY PRIMARY RESULT OR CASE-LEVEL CORRECTNESS OUTPUT WAS OBSERVED.

These controls cannot rescue or redefine the primary D-vs-B_cls endpoint.

## R1. Probe split-half stability

For every primary-usable case, split the 24 frozen mixed probes deterministically into odd/even positions after the frozen task-seeded shuffle.

Recompute semantic centrality on each 12-probe half without changing the already-frozen semantic classes.

Report:
- Spearman correlation between class centralities from the two halves;
- agreement of the selected D class;
- query-prediction agreement of the two half-selectors.

This tests whether centrality is a stable property or a small-probe accident.

## R2. Candidate-origin confound

Using model identity only after the primary has been scored:
- report correctness and centrality by actual/requested model;
- within each usable case containing candidates from both GPT-5.2-xhigh and Gemini-3-high, test whether centrality predicts correctness after demeaning centrality and correctness within model family;
- report a model-stratified AUC where positive/negative comparisons are restricted to candidates/classes whose canonical representatives come from the same model family when possible.

No model identity may enter the primary selector.

## R3. Source-length confound

Join canonical representative SHA to normalized source length.

Report:
- centrality vs source length;
- source length vs correctness;
- centrality vs correctness after residualizing centrality against log source length within case.

Source length remains only a deterministic representative tie-break in the primary.

## R4. Duplicate multiplicity sensitivity

The primary B_cls and D operate on duplicate-invariant semantic classes.

Report separately:
- raw candidate plurality;
- semantic-class plurality;
- correlation between semantic-class size and correctness;
- correlation between class size and centrality.

A gain that exists only when duplicate multiplicity is retained is considered a sampling-frequency effect, not a version-space geometry result.

## R5. Label-permutation null

Within every usable case, keep centrality scores and class structure fixed and randomly permute exact-correctness labels over valid semantic classes 10,000 times with seed 20261028.

Compare the observed case-macro:
- centrality/correctness Spearman;
- centrality AUC;
against the permutation distribution.

This is a mechanism significance diagnostic, not a selector-performance p-value.

## R6. Literal-answer contamination audit

Only after primary scoring:
- canonicalize the true public test grid;
- scan normalized candidate source for exact nested-list serialization, whitespace-normalized serialization, flattened comma-separated sequence, and exact output-shape-plus-full-value constants;
- flag candidates with literal full-answer embedding;
- inspect flagged code paths to distinguish generic constants from direct answer hard-coding;
- repeat primary/association analyses excluding flagged candidates and any semantic class whose canonical representative is flagged.

This audit cannot alter the original primary result.

## R7. Land-verifier sensitivity

Primary eligibility is independent re-verification.

Repeat descriptive coverage/association on:
A. independently verified candidates regardless of Land metadata;
B. intersection with Land verification_status == PASS.

Any divergence is reported as verifier-selection sensitivity.

## R8. Oracle-positive and minority-correct decomposition

Already frozen in the primary preregistration, but report explicitly:
- oracle-negative cases;
- oracle-positive majority-correct cases;
- oracle-positive minority-correct cases.

The minority-correct subset is the hardest practical test because plurality is structurally wrong there.
