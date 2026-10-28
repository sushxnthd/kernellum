# ARC Reboot Stage C — Query Identifiability Preregistration

Status: CONDITIONAL. Do not execute unless the frozen 55-family Stage B replication passes all three gates without modification.

## Stage B gates
1. At least 6 usable ARC-TGI Train families with >=3 distinct demo-perfect mutants.
2. Median Spearman correlation between demo-only agnostic counterfactual centrality and fresh-input held-out accuracy >= 0.30.
3. Median agnostic selector gain over the mean demo-perfect mutant >= 0.10 absolute.

If any gate fails, Stage C is not run and the practical identifiability line is killed.

## Question
Does counterfactual behavioral evidence help choose the correct output for the actual query beyond information already contained in the demo-perfect candidates' predictions on that query?

## Candidate pool
Use the exact same mutation operators, demo-fit filter, semantic deduplication, random seeds, and ARC-TGI families as Stage B. No post-hoc enrichment of mutation operators is allowed.

The original ground-truth transform remains excluded from the candidate selector.

## Evidence
For each family:
- demonstrations: labeled input/output pairs used only for exact-fit filtering;
- queries: exactly 32 fresh valid generator inputs per usable family, generated after candidate-pool construction from the frozen family seed; all 32 outputs are hidden from every selector;
- agnostic probes: generated only from demonstration inputs using the frozen D4, color-permutation, and cyclic-roll operators;
- query truth: used only for final scoring.

## Selectors
A. Query plurality: most common predicted query grid among demo-perfect candidates.
B. Semantic-class plurality: quotient candidates by their complete agnostic-probe behavioral signature. Each class is represented by its minimum-AST candidate, breaking ties by frozen mutation index, and therefore casts exactly one vote for one query grid.
C. Simplicity: choose minimum AST-size candidate; ties are deterministic.
D. Counterfactual centrality: quotient exact agnostic-probe behavioral duplicates first, then compute agreement centrality with equal weight per semantic class. Each class uses the same canonical representative as B. For each distinct query grid, use the maximum centrality of a supporting class.
E. Combined: lexicographic (counterfactual centrality, then canonical-representative AST size, then mutation index), duplicate-invariant.
F. Oracle@2: whether any of the two best distinct query grids from the entire pool is correct. Diagnostic only.

## Endpoints
Primary: task/family-weighted query top-1 accuracy of D vs B.
Secondary: pass@2 of D/E vs B, and D vs C.
Report paired per-query differences, family-macro accuracy, micro accuracy, and a bootstrap 95% CI over family-level D-B accuracy differences. Ties in grid scores are broken by canonical serialized grid order; ties among programs are broken by mutation index.

## Survival rule
The practical method survives only if all are true:
1. Stage B passed.
2. D improves top-1 over semantic-class plurality B by >= 0.03 absolute.
3. Paired bootstrap 95% CI for D-B is not entirely below zero.
4. Improvement occurs in at least 3 independent families and is not driven by one family.
5. D retains a positive gain when restricted to queries where >=2 distinct query outputs are predicted.

A result that only improves raw plurality A, but not duplicate-invariant B, is treated as a duplicate-count artifact and does not survive.

## Interpretation
Mechanism identifiability alone is not sufficient. ARC only requires query correctness. Counterfactual probes count as useful scientific evidence only if they improve selection among demo-consistent hypotheses that disagree on the actual query.

## Frozen execution validity
A candidate program that raises an exception, returns a non-2D/empty/>60 grid, or fails to terminate within 2.0 seconds on a single evaluation is invalid for that evaluation. This operational rule was fixed before any Stage C execution and exists only to prevent malformed AST mutants from killing a family-level run.
