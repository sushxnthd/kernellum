# Land V7 Replication — D4-Weighted Semantic-Class Voting

Status: PREREGISTERED AFTER V27 EXPLORATORY RESULT, BEFORE INSPECTING CORRECTNESS OR SELECTOR PERFORMANCE OF ANY POST-V27 NOTEBOOK VERSION.

## Discovery that motivates replication

On exact paper run V27, the preregistered primary counterfactual-medoid selector D failed.

A preregistered secondary selector, W4, weighted one vote per semantic class by D4-only counterfactual centrality and produced an exploratory improvement over duplicate-invariant semantic-class plurality B_cls.

This document treats that observation as hypothesis generation only.

## Replication-run selection without outcome labels

Consider public Kaggle notebook versions 28 through 39 in ascending chronological order.

Select the **earliest** version satisfying all coverage/integrity conditions:

1. notebook output contains a `logs/` directory or `logs.tgz`;
2. contains at least 100 ARC task/test log groups;
3. frozen codegen-only extractor yields >=30 task/test cases with >=3 unique code hypotheses before independent verification;
4. candidate-set digest differs from V27, proving the run is not a byte-identical copy;
5. public ARC evaluation truth is available for later scoring.

Version selection uses only file/candidate coverage and SHA digests. No candidate `is_correct`, extracted-grid correctness, Land judge ranking, or selector performance is inspected until the version is fixed.

If no V28–V39 version satisfies these conditions, this replication route is declared unavailable rather than choosing an older/favorable run.

## Frozen candidate/execution protocol

Use exactly the V27 independent-test protocol:
- codegen calls only;
- normalized source deduplication by SHA256 within task/test case;
- independently reverify every candidate on every labeled demonstration;
- generated code executes in fresh network-disabled, read-only Docker sandboxes with no evaluation-data mount;
- 2.0 s per grid;
- output must be rectangular, nonempty, <=30x30, colors 0–9.

## Frozen semantic classes

Use the exact V27 primary mixed-probe signatures to define duplicate-invariant semantic classes:
- D4 transforms;
- three nonzero-color permutations per demo preserving zero;
- cyclic row/column rolls ±1;
- deterministic task/test-seeded sampling;
- 24 probes.

Canonical representative remains shortest normalized source then SHA256.

The class definition is unchanged even though W4 uses D4-only weights.

## Replication primary

B_cls:
one equal vote per semantic class for its test-grid prediction.

W4:
- compute class centrality using the frozen D4-only probe set capped at 12;
- each semantic class votes for its test prediction with weight equal to D4 centrality;
- choose maximum total-weight prediction;
- deterministic canonical-grid tie break.

## Usable case

Identical to V27:
- >=3 independently verified candidates;
- >=3 mixed-probe semantic classes;
- >=2 distinct valid test predictions.

## Replication endpoints

Primary:
- top-1 W4 vs B_cls over usable cases.

Secondary:
- pass@2 W4 vs B_cls;
- oracle-positive subset;
- minority-correct subset;
- D4-centrality/correctness association;
- raw candidate plurality.

Task-bootstrap resamples task IDs.

## Frozen replication success rule

W4 replicates as a practical improvement only if all are true:

1. >=30 usable cases;
2. >=20 distinct tasks;
3. W4-B_cls top-1 >= +3.0 percentage points;
4. task-bootstrap 95% CI for W4-B_cls is not entirely below zero;
5. W4 improves >=5 distinct task IDs;
6. W4 is non-inferior on oracle-positive cases;
7. W4 has positive gain on minority-correct cases.

No parameter tuning, probe tuning, temperature, model weighting, task filtering, or threshold selection is allowed on the replication run.

## Interpretation

PASS:
D4-weighted counterfactual semantic voting is a replicated practical selector improvement on independently generated LLM ARC hypotheses.

FAIL WITH POSITIVE CENTRALITY ASSOCIATION:
counterfactual behavior remains a hypothesis-quality signal but W4 is not a robust decision rule.

FAIL WITH NO CENTRALITY ASSOCIATION:
the V27 mechanism itself is unstable across candidate-generation reruns.

NO ELIGIBLE VERSION:
replication unavailable from this notebook lineage; do not count as evidence for or against W4.
